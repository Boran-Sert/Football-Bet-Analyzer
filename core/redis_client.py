"""Asenkron Redis baglanti yoneticisi.

redis.asyncio kullanir. Connection pool ile verimli baglanti yonetimi.
"""

import logging
import redis.asyncio as aioredis

from core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis baglanti yasam dongusunu yonetir."""

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    async def connect(self) -> None:
        self._client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=5,  # ← bağlantı timeout
            socket_timeout=5,  # ← komut timeout
            retry_on_timeout=True,  # ← timeout'ta retry yap
            health_check_interval=30,  # ← 30s'de bir ping at, bağlantıyı canlı tut
        )
        await self._client.ping()
        logger.info("Redis bağlantısı kuruldu: %s", settings.REDIS_URL)

    def get_client(self) -> aioredis.Redis:
        """Aktif Redis istemcisini dondurur."""
        if self._client is None:
            raise RuntimeError("Redis baglantisi henuz kurulmadi. connect() cagirin.")
        return self._client

    async def close(self) -> None:
        """Baglantiyi kapat."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Redis baglantisi kapatildi.")


# Singleton
redis_manager = RedisManager()
