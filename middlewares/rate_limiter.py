"""Redis tabanli IP rate limiter.

rules.md Madde 5: Tum acik endpointlerde Redis tabanli IP sinirlandirmasi olacaktir.
Dakikada 20 istekten fazlasina HTTP 429 (Too Many Requests) doner.
FastAPI Depends() ile kullanilir.
"""

from fastapi import Request, HTTPException, status, Depends

from core.redis_client import redis_manager

# Yapilandirma sabitleri
MAX_REQUESTS = 20
WINDOW_SECONDS = 60


async def rate_limit(request: Request) -> None:
    """IP bazli istek sinirlandirmasi uygular.

    Her istekte Redis'teki sayaci arttirir.
    Sinir asilirsa HTTP 429 firlatir.

    Args:
        request: Gelen HTTP istegi (IP adresi icin).

    Raises:
        HTTPException: Istek limiti asildiysa 429 hatasi.
    """
    client = redis_manager.client
    if client is None:
        # Redis baglantisi yoksa limitleme atlaniyor (graceful degradation)
        return

    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:{client_ip}"

    current = await client.incr(key)

    # Ilk istek ise TTL ata
    if current == 1:
        await client.expire(key, WINDOW_SECONDS)

    if current > MAX_REQUESTS:
        ttl = await client.ttl(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Istek limiti asildi. {ttl} saniye sonra tekrar deneyin.",
        )
