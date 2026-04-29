"""Redis tabanli Rate Limiter bagimliligi."""

from fastapi import Request, HTTPException
import time

from core.config import TierLimits
from core.redis_client import redis_manager
from schemas.auth import UserTier


class RateLimiter:
    """Sliding window veya Fixed window Redis tabanli IP/User limitleme.
    
    Bu bir FastAPI Dependency (Depends) olarak kullanilacaktir.
    Eger user_tier verilmisse ona gore limit alir.
    Verilmemisse IP bazli FREE tier limiti uygular.
    """

    def __init__(self, requests_per_minute: int | None = None):
        self.rpm = requests_per_minute

    async def __call__(self, request: Request) -> None:
        """Bagimlilik calistiginda devreye girer."""
        redis = redis_manager.get_client()
        
        # User auth middleware'inden (veya dependencysinden) tier ve admin durumu aliniyor
        user_tier = getattr(request.state, "user_tier", UserTier.FREE.value)
        is_superuser = getattr(request.state, "is_superuser", False)
        identifier = getattr(request.state, "user_id", None)
        
        # Adminler icin rate limit yok
        if is_superuser:
            return
        
        if not identifier:
            # Login degilse IP kullan. Load Balancer destegi (X-Forwarded-For, X-Real-IP)
            x_forwarded_for = request.headers.get("x-forwarded-for")
            if x_forwarded_for:
                identifier = x_forwarded_for.split(",")[0].strip()
            else:
                identifier = request.headers.get("x-real-ip", request.client.host if request.client else "unknown_ip")
        
        # Limit belirle (init ile override edilmisse o kullanilir, degilse tier limit)
        limit = self.rpm if self.rpm is not None else TierLimits.get_rate_limit(user_tier)
        
        # Eger -1 ise sinirsiz
        if limit == -1:
            return

        # Fixed window basit limitleme (1 dakikalik bucket)
        current_minute = int(time.time() / 60)
        key = f"rate_limit:{identifier}:{current_minute}"

        try:
            current_count = await redis.incr(key)
            if current_count == 1:
                await redis.expire(key, 60)  # Anahtar 60 sn sonra dussun
            
            if current_count > limit:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Try again later."
                )
        except HTTPException:
            raise
        except Exception:
            # Redis arizasi durumunda limiti bypass et
            pass
