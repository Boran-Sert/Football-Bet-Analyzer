"""Redis caching utility (Faz 4)."""

import typing
import orjson
from functools import wraps
from typing import Any, Callable
from core.redis_client import redis_manager
from core.logger import logger

from pydantic import BaseModel
from pydantic_core import to_jsonable_python


def _make_serializable(data: Any) -> Any:
    # Performans için pydantic_core'un en hızlı metodunu kullanıyoruz
    try:
        return to_jsonable_python(data)
    except Exception:
        return str(data)  # En kötü ihtimalle string'e çevir ki json.dumps patlamasın


def _deserialize_cached(raw: Any, hint: Any) -> Any:
    """Cache'ten gelen ham dict/list'i return type hint'ine gore Pydantic modele cevirir.

    KRİTİK-3 Fix: Cache hit'te orjson.loads() ham dict/list doner,
    uygulama kodu .attribute erisimi yaparsa AttributeError firlatir.
    Bu fonksiyon return type hint'ini analiz edip uygun modele cevirir.
    """
    if hint is None:
        return raw

    origin = typing.get_origin(hint)
    args = typing.get_args(hint)

    # list[SomeModel] durumu
    if origin is list and args and isinstance(raw, list):
        model_cls = args[0]
        if isinstance(model_cls, type) and issubclass(model_cls, BaseModel):
            return [model_cls(**item) if isinstance(item, dict) else item for item in raw]
        return raw

    # Tekil Model durumu
    if isinstance(hint, type) and issubclass(hint, BaseModel) and isinstance(raw, dict):
        return hint(**raw)

    return raw


def cache_response(expire: int = 300, key_prefix: str = "cache"):
    """
    Decorator to cache FastAPI endpoint responses in Redis.
    Default expiry: 5 minutes.
    """

    def decorator(func: Callable):
        # Return type hint'ini analiz et (KRİTİK-3 Fix)
        _return_hint = typing.get_type_hints(func).get("return")

        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate a unique key based on function name, args, and kwargs
            key_parts = [key_prefix, func.__name__]

            # Args (skipping 'self' or 'cls' if it's a method)
            # func has __qualname__ which contains class name if it's a method
            start_idx = 1 if "." in func.__qualname__ else 0
            for arg in args[start_idx:]:
                key_parts.append(str(arg))

            for k, v in sorted(kwargs.items()):
                if k in ["auth_service", "current_user", "db", "service"]:
                    continue
                # Enum'ları .value ile stringe çevir
                val = v.value if hasattr(v, "value") else str(v)
                key_parts.append(f"{k}:{val}")

            cache_key = ":".join(key_parts)
            redis = redis_manager.get_client()

            try:
                # Check cache
                cached_val = await redis.get(cache_key)
                if cached_val:
                    logger.debug(f"Cache hit: {cache_key}")
                    raw = orjson.loads(cached_val)
                    return _deserialize_cached(raw, _return_hint)
            except Exception as e:
                logger.error(f"Cache read error: {str(e)}")

            # Execute function
            result = await func(*args, **kwargs)

            try:
                # Faz 6 Fix: orjson.dumps kullanildi (json.dumps'tan cok daha hizli)
                serializable_result = _make_serializable(result)

                await redis.setex(
                    cache_key, expire, orjson.dumps(serializable_result).decode("utf-8")
                )
                logger.debug(f"Cache stored: {cache_key}")
            except Exception as e:
                logger.error(f"Cache write error: {str(e)}")

            return result

        return wrapper

    return decorator
