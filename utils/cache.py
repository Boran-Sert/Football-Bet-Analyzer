"""Redis caching utility (Faz 4)."""

import orjson
from functools import wraps
from typing import Any, Callable
from core.redis_client import redis_manager
from core.logger import logger

from pydantic_core import to_jsonable_python

def _make_serializable(data: Any) -> Any:
    """pydantic_core kullanarak veriyi JSON uyumlu hale getirir (Yuksek performans)."""
    try:
        # Faz 6 Fix: orjson + pydantic_core kombinasyonu ile en hizli serilestirme
        return to_jsonable_python(data)
    except Exception:
        return data

def cache_response(expire: int = 300, key_prefix: str = "cache"):
    """
    Decorator to cache FastAPI endpoint responses in Redis.
    Default expiry: 5 minutes.
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate a unique key based on function name and arguments
            key_parts = [key_prefix, func.__name__]
            for k, v in sorted(kwargs.items()):
                if k == "current_user" and hasattr(v, "tier"):
                    key_parts.append(f"tier:{v.tier}")
                elif k not in ["auth_service", "current_user", "db", "service"]:
                    key_parts.append(f"{k}:{v}")
            
            cache_key = ":".join(key_parts)
            redis = redis_manager.get_client()

            try:
                # Check cache
                cached_val = await redis.get(cache_key)
                if cached_val:
                    logger.debug(f"Cache hit: {cache_key}")
                    return orjson.loads(cached_val)
            except Exception as e:
                logger.error(f"Cache read error: {str(e)}")

            # Execute function
            result = await func(*args, **kwargs)

            try:
                # Faz 6 Fix: orjson.dumps kullanildi (json.dumps'tan cok daha hizli)
                serializable_result = _make_serializable(result)
                
                await redis.setex(
                    cache_key,
                    expire,
                    orjson.dumps(serializable_result).decode("utf-8")
                )
                logger.debug(f"Cache stored: {cache_key}")
            except Exception as e:
                logger.error(f"Cache write error: {str(e)}")

            return result
        return wrapper
    return decorator
