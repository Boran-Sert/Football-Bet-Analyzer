"""Asenkron MongoDB baglanti yoneticisi.

Motor (AsyncIOMotorClient) kullanir. Lifespan ile kontrol edilir.
Indeks tanimlari connect() icerisinde otomatik olusturulur.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.config import settings

logger = logging.getLogger(__name__)


class MongoManager:
    """MongoDB baglanti yasam dongusunu yonetir."""

    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._db: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        """Baglanti kur ve indeksleri olustur."""
        self._client = AsyncIOMotorClient(settings.MONGO_URI, tlsAllowInvalidCertificates=True)
        self._db = self._client.get_default_database()

        # Baglanti testi
        await self._client.admin.command("ping")
        logger.info("MongoDB ping basarili. DB: %s", self._db.name)

        # Indeks tanimlari
        await self._ensure_indexes()

    async def _ensure_indexes(self) -> None:
        """Gerekli MongoDB indekslerini olusturur."""
        db = self.get_db()

        # matches koleksiyonu
        await db.matches.create_index("external_id", unique=True)
        await db.matches.create_index("status")
        await db.matches.create_index("odds.h2h.home")
        await db.matches.create_index("odds.h2h.draw")
        await db.matches.create_index("odds.h2h.away")
        
        await db.matches.create_index([
            ("sport", 1),
            ("league_key", 1),
            ("commence_time", -1),
        ])
        await db.matches.create_index([("status", 1), ("commence_time", -1)])

        # users koleksiyonu
        await db.users.create_index("email", unique=True)

        # analytics koleksiyonu — 90 gun sonra otomatik sil
        await db.analytics.create_index(
            "created_at",
            expireAfterSeconds=90 * 24 * 3600,
        )

        logger.info("MongoDB indeksleri olusturuldu/dogrulandi.")

    def get_db(self) -> AsyncIOMotorDatabase:
        """Aktif veritabani nesnesini dondurur."""
        if self._db is None:
            raise RuntimeError("MongoDB baglantisi henuz kurulmadi. connect() cagirin.")
        return self._db

    async def close(self) -> None:
        """Baglantiyi kapat."""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("MongoDB baglantisi kapatildi.")


# Singleton
mongo = MongoManager()
