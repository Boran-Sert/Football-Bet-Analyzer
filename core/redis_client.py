"""Asenkron Redis baglanti altyapisi.

redis.asyncio kullanilarak onbellekleme ve rate-limiting islemleri icin
async/await uyumlu baglanti saglar.
"""

import redis.asyncio as aioredis

from core.config import settings


class RedisManager:
    """Redis baglanti yasam dongusunu yoneten sinif."""

    def __init__(self) -> None:
        self.client: aioredis.Redis | None = None

    async def connect(self) -> None:
        """Redis sunucusuna baglan ve ping at."""
        self.client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
        await self.client.ping()

    async def close(self) -> None:
        """Baglanti havuzunu kapat."""
        if self.client is not None:
            await self.client.close()


redis_manager = RedisManager()
