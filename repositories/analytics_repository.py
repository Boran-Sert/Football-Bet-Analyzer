"""Telemetri ve log veri erisim katmani."""

from motor.motor_asyncio import AsyncIOMotorDatabase

from schemas.analytics import RequestLog


class AnalyticsRepository:
    """Request/Analytics loglarini asenkron olarak yazar."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.analytics

    async def insert_log(self, log: RequestLog) -> None:
        """Yeni bir log kaydi ekler.

        Fire-and-forget mantigi ile calisacagi icin sonuc beklemesi kritik degildir.
        TTL indexi sayesinde MongoDB bunlari otomatik olarak 90 gun sonra silecek.
        """
        doc = log.model_dump()
        await self.collection.insert_one(doc)
