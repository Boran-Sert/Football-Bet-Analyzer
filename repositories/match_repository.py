"""Mac veri erisim katmani.

Veritabani islemlerini (MongoDB) soyutlar. Sadece burada motor kullanilir.
"""

from typing import Any
from datetime import datetime

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import UpdateOne

from schemas.match import MatchEntity, MatchInDB, MatchStatus


class MatchRepository:
    """Mac koleksiyonu uzerinde CRUD ve sorgu islemleri."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.matches

    async def get_by_external_id(self, external_id: str) -> MatchInDB | None:
        """Dis ID'ye gore mac getirir."""
        doc = await self.collection.find_one({"external_id": external_id})
        if doc:
            return MatchInDB(**doc)
        return None

    async def get_upcoming_matches(
        self,
        sport: str = "football",
        league_key: str | None = None,
        limit: int = 50,
        skip: int = 0
    ) -> list[MatchInDB]:
        """Yaklasan maclari zamana gore siralayip getirir."""
        query: dict[str, Any] = {"status": MatchStatus.UPCOMING.value, "sport": sport}
        if league_key:
            query["league_key"] = league_key

        cursor = self.collection.find(query).sort("commence_time", 1).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [MatchInDB(**doc) for doc in docs]

    async def get_completed_matches_for_analysis(
        self,
        sport: str = "football",
        league_key: str | None = None,
        limit: int = 5000
    ) -> list[MatchInDB]:
        """Benzerlik analizi icin tamamlanmis maclari getirir.

        Not: Bu veri service katmaninda Oklid mesafesi ile islenecek.
        """
        query: dict[str, Any] = {"status": MatchStatus.COMPLETED.value, "sport": sport}
        if league_key:
            query["league_key"] = league_key

        # En yeni maclar once
        cursor = self.collection.find(query).sort("commence_time", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [MatchInDB(**doc) for doc in docs]

    async def get_available_leagues(self, sport: str = "football") -> list[str]:
        """Sistemde verisi bulunan benzersiz lig kodlarini dondurur."""
        leagues = await self.collection.distinct("league_key", {"sport": sport})
        return sorted(list(leagues))

    async def count_matches(self, query: dict) -> int:
        """Verilen sorguya uyan mac sayisini dondurur."""
        return await self.collection.count_documents(query)
