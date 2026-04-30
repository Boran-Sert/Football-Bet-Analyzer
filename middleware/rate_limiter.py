"""Redis tabanli Sliding Window Rate Limiter — GAP 6.

Onceki sorun (Fixed Window):
  Dakika siniri her 60 saniyede bir sifirlaniyordu. Bu, bir kullanicinin
  59. saniyede 60 istek yapip 61. saniyede 60 istek daha yapmasina izin
  veriyordu: 2x burst oluyor ve limit anlamsizlasiyordu.

Yeni yaklasim (Sliding Window — Redis Sorted Set):
  Her istek, o anki timestamp ile bir sorted set'e eklenir.
  "Son 60 saniye" penceresi her istekte dinamik olarak hesaplanir.
  Esik asiminda HTTP 429 firlatilir.
  Redis arizi durumunda fail-open (istege izin verilir).
"""

import time
import uuid

from fastapi import Request, HTTPException
from core.config import TierLimits
from core.redis_client import redis_manager
from schemas.auth import UserTier


class RateLimiter:
    """Sliding window Redis rate limiter.
    
    Dependency olarak kullanilir: `dependencies=[Depends(RateLimiter())]`
    """

    def __init__(self, requests_per_minute: int | None = None):
        self.rpm = requests_per_minute

    async def __call__(self, request: Request) -> None:
        # Adminler icin limit yok
        is_superuser = getattr(request.state, "is_superuser", False)
        if is_superuser:
            return

        user_tier = getattr(request.state, "user_tier", UserTier.STANDARD.value)
        user_id = getattr(request.state, "user_id", None)

        # Identifier: giris yapildiysa user_id, yapilmadiysa IP
        if user_id:
            identifier = f"user:{user_id}"
        else:
            # Faz 6 Fix: Rate Limiter Spoofing Engellendi.
            # X-Forwarded-For basligina uygulama katmaninda guvenilmez (spoofing riski).
            # En saglikli yol, Load Balancer arkasinda "ProxyHeadersMiddleware" (Uvicorn)
            # kullanmaktir. Boylece request.client.host LB tarafindan dogrulanmis IP olur.
            identifier = request.client.host if request.client else "unknown_ip"

        # Limit: init'te override varsa o kullanilir, yoksa tier'dan gelir
        limit = self.rpm if self.rpm is not None else TierLimits.get_rate_limit(user_tier)
        if limit == -1:
            return  # Sinirsiz

        redis_key = f"rate_limit:sw:{identifier}"
        now = time.time()
        window_start = now - 60.0  # 60 saniyelik kayan pencere

        try:
            redis = redis_manager.get_client()

            # Pipeline: eski kayitlari temizle → yeni kaydi ekle → say → TTL ayarla
            async with redis.pipeline(transaction=True) as pipe:
                pipe.zremrangebyscore(redis_key, "-inf", window_start)
                # Faz 6 Fix: Member unique olmali (uuid eklendi)
                pipe.zadd(redis_key, {f"{now}:{uuid.uuid4().hex}": now})
                pipe.zcard(redis_key)
                pipe.expire(redis_key, 60)
                results = await pipe.execute()

            current_count = results[2]  # zcard sonucu

            if current_count > limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Max {limit} requests per minute.",
                    headers={"Retry-After": "60"},
                )
        except HTTPException:
            raise
        except Exception:
            # Redis arizasi durumunda guvenlik icin istegi reddet (fail-closed) - Faz 1
            raise HTTPException(
                status_code=503,
                detail="Rate limiter servisi su an kullanilamiyor. Lutfen daha sonra tekrar deneyin."
            )
