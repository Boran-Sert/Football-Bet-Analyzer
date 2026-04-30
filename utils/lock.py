import functools
import logging
from typing import Any, Callable
from core.redis_client import redis_manager

logger = logging.getLogger(__name__)

def distributed_lock(lock_key: str, timeout: int = 600, blocking_timeout: int = 1):
    """Redis tabanli dagitik kilit dekoratörü (Faz 6 Fix: Merkezi kilit yönetimi)."""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            redis = redis_manager.get_client()
            lock = redis.lock(lock_key, timeout=timeout, blocking_timeout=blocking_timeout)
            
            acquired = False
            try:
                acquired = await lock.acquire()
                if not acquired:
                    logger.warning(f"Lock alinamadi: {lock_key}. Gorev zaten calisiyor olabilir.")
                    return None
                
                logger.info(f"Lock alindi: {lock_key}")
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Lock hatasi ({lock_key}): {e}")
                raise
            finally:
                if acquired:
                    try:
                        await lock.release()
                        logger.info(f"Lock serbest birakildi: {lock_key}")
                    except Exception:
                        pass
        return wrapper
    return decorator
