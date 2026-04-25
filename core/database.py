"""Asenkron MongoDB baglanti altyapisi.

motor.motor_asyncio kullanilarak async/await uyumlu calisir.
Baglanti uygulama baslatilirken (lifespan) acilir, kapatilirken kapatilir.
"""

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from core.config import settings


class MongoManager:
    """MongoDB baglanti yasam dongusunu yoneten sinif."""

    def __init__(self) -> None:
        self.client: AsyncIOMotorClient | None = None
        self.db: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        """Veritabanina baglan ve ping at."""
        self.client = AsyncIOMotorClient(settings.MONGO_URI)
        self.db = self.client.get_default_database("football_saas")
        await self.client.admin.command("ping")

    async def close(self) -> None:
        """Baglanti havuzunu kapat."""
        if self.client is not None:
            self.client.close()


mongo = MongoManager()
