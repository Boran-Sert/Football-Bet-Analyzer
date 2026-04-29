"""Redis onbellekleme decorator'u.

Service katmanindaki okuma metodlarini (GET) hizlandirmak icin kullanilir.
"""

import functools
import hashlib
import inspect
import logging

import orjson

from pydantic import TypeAdapter

from core.redis_client import redis_manager

logger = logging.getLogger(__name__)


def cache_response(ttl_seconds: int = 3600, prefix: str = "cache"):
    """Metod ciktisini Redis uzerinde onbellege alir.

    Serilestirme icin `orjson` kullanir (Pydantic modelleriyle uyumlu, standart json'dan hizli).
    Eger Redis baglantisinda sorun varsa sessizce bypass eder ve orijinal metodu calistirir.

    Args:
        ttl_seconds: Cache yasam suresi (saniye).
        prefix: Redis key on eki.
    """
    def decorator(func):
        return_type = inspect.signature(func).return_annotation
        type_adapter = TypeAdapter(return_type) if return_type is not inspect.Signature.empty else None

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Key uretimi: prefix:func_name:hash(args+kwargs)
            # args[0] genelde 'self' (Service instance) oldugu icin hash'e dahil etmeyiz
            call_args = inspect.getcallargs(func, *args, **kwargs)
            call_args.pop("self", None)

            # Argumanlari string'e cevirip hash'le
            args_str = orjson.dumps(call_args, option=orjson.OPT_SORT_KEYS).decode("utf-8")
            args_hash = hashlib.md5(args_str.encode("utf-8")).hexdigest()

            cache_key = f"{prefix}:{func.__name__}:{args_hash}"

            redis = None
            try:
                redis = redis_manager.get_client()
                cached_data = await redis.get(cache_key)

                if cached_data:
                    # Cache HIT
                    parsed = orjson.loads(cached_data)
                    if type_adapter:
                        return type_adapter.validate_python(parsed)
                    return parsed

            except Exception as exc:
                logger.warning("Redis cache okuma hatasi (%s): %s", cache_key, exc)

            # Cache MISS veya Redis hatasi — orijinal metodu cagir
            result = await func(*args, **kwargs)

            # Pydantic objelerini veya liste objelerini serialize etmek icin dict'e cevir
            # Eger sonuc listeyse her bir elemani model_dump yap (Pydantic)
            serializable_result = result
            if isinstance(result, list):
                serializable_result = [
                    item.model_dump() if hasattr(item, "model_dump") else item
                    for item in result
                ]
            elif hasattr(result, "model_dump"):
                serializable_result = result.model_dump()

            # Redis'e yaz
            if redis and result is not None:
                try:
                    serialized_data = orjson.dumps(serializable_result)
                    await redis.setex(cache_key, ttl_seconds, serialized_data)
                except Exception as exc:
                    logger.warning("Redis cache yazma hatasi (%s): %s", cache_key, exc)

            return result

        return wrapper
    return decorator
