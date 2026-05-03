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

    async def get_by_external_ids(self, external_ids: list[str]) -> list[dict]:
        """Birden fazla ID'yi tek seferde sorgular (Faz 6 Fix: N+1 engelleme)."""
        cursor = self.collection.find(
            {"external_id": {"$in": external_ids}},
            {"external_id": 1, "updated_at": 1}
        )
        return await cursor.to_list(length=len(external_ids))

    async def find_matches_by_odds_range(
        self,
        home: float,
        draw: float,
        away: float,
        limit: int = 2000
    ) -> list[dict]:
        """Oran aralığına göre tamamlanmış maçları getirir (Benzerlik analizi için)."""
        # Basit ve güvenilir $or sorgusu (Atlas uyumlu)
        query = {
            "status": {"$regex": f"^{MatchStatus.COMPLETED.value}$", "$options": "i"},
            "$or": [
                {
                    "odds.h2h.home": {"$gte": float(home) - 1.0, "$lte": float(home) + 1.0},
                    "odds.h2h.draw": {"$gte": float(draw) - 1.0, "$lte": float(draw) + 1.0},
                    "odds.h2h.away": {"$gte": float(away) - 1.0, "$lte": float(away) + 1.0}
                },
                {
                    "odds.home": {"$gte": float(home) - 1.0, "$lte": float(home) + 1.0},
                    "odds.draw": {"$gte": float(draw) - 1.0, "$lte": float(draw) + 1.0},
                    "odds.away": {"$gte": float(away) - 1.0, "$lte": float(away) + 1.0}
                }
            ]
        }
        
        from core.logger import logger
        logger.info(f"Benzerlik sorgusu baslatildi: H:{home} D:{draw} A:{away}")
        
        cursor = self.collection.find(query).limit(limit)
        docs = await cursor.to_list(length=limit)
        
        logger.info(f"Sorgu tamamlandi. Bulunan ham mac sayisi: {len(docs)}")
        return docs

    async def bulk_upsert(self, entities: list[MatchEntity]) -> dict:
        """Toplu mac guncelleme/ekleme (Faz 6 Fix: Mimari uyum)."""
        if not entities:
            return {"upserted": 0, "modified": 0}
            
        operations = [
            UpdateOne(
                {"external_id": e.external_id},
                {"$set": e.model_dump()},
                upsert=True
            ) for e in entities
        ]
        
        result = await self.collection.bulk_write(operations, ordered=False)
        return {
            "upserted": result.upserted_count,
            "modified": result.modified_count
        }
