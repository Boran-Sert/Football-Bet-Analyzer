"""Mac veri erisim katmani.

Veritabani islemlerini (MongoDB) soyutlar. Sadece burada motor kullanilir.
"""

from typing import Any
from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import UpdateOne
from core.logger import logger
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
        start_hour: int | None = None,
        end_hour: int | None = None,
        limit: int = 50,
        skip: int = 0,
    ) -> list[MatchInDB]:
        """Yaklasan maclari zamana ve saate gore siralayip getirir."""
        now = datetime.now(timezone.utc)
        query: dict[str, Any] = {
            "status": MatchStatus.UPCOMING.value, 
            "sport": sport,
            "commence_time": {"$gte": now}
        }
        if league_key:
            query["league_key"] = league_key

        # Saat bazlı filtreleme (Local saat üzerinden: UTC+3)
        if start_hour is not None and end_hour is not None:
            # MongoDB veriyi UTC tutar. +3 saat (3 * 3600 * 1000 ms) ekleyip saati kontrol ediyoruz.
            utc_offset_ms = 3 * 3600 * 1000
            
            # 24:00 durumunu handle etmek için (20-24 aralığı gibi)
            query["$expr"] = {
                "$and": [
                    {"$gte": [{"$hour": {"$add": ["$commence_time", utc_offset_ms]}}, start_hour]},
                    {"$lt": [{"$hour": {"$add": ["$commence_time", utc_offset_ms]}}, end_hour]}
                ]
            }

        cursor = (
            self.collection.find(query).sort("commence_time", 1).skip(skip).limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [MatchInDB(**doc) for doc in docs]

    async def get_completed_matches_for_analysis(
        self, sport: str = "football", league_key: str | None = None, limit: int = 5000
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
            {"external_id": {"$in": external_ids}}, {"external_id": 1, "updated_at": 1}
        )
        return await cursor.to_list(length=len(external_ids))

    async def find_similar_matches_by_distance(
        self,
        home: float,
        draw: float,
        away: float,
        threshold: float = 1.5,
        limit: int = 50,
    ) -> list[dict]:
        """Oranlara göre Euclidean Distance hesabını %100 MongoDB içinde yapar."""

        logger.info(f"Aggregation Pipeline baslatildi: H:{home} D:{draw} A:{away}")

        pipeline = [
            {
                "$match": {
                    "status": MatchStatus.COMPLETED.value,
                    "odds.h2h.home": {"$type": "number"},
                    "odds.h2h.draw": {"$type": "number"},
                    "odds.h2h.away": {"$type": "number"},
                }
            },
            {
                "$addFields": {
                    "distance": {
                        "$sqrt": {
                            "$add": [
                                {
                                    "$pow": [
                                        {"$subtract": ["$odds.h2h.home", float(home)]},
                                        2,
                                    ]
                                },
                                {
                                    "$pow": [
                                        {"$subtract": ["$odds.h2h.draw", float(draw)]},
                                        2,
                                    ]
                                },
                                {
                                    "$pow": [
                                        {"$subtract": ["$odds.h2h.away", float(away)]},
                                        2,
                                    ]
                                },
                            ]
                        }
                    }
                }
            },
            {"$match": {"distance": {"$lte": threshold}}},
            {"$sort": {"distance": 1}},
            {"$limit": limit},
        ]

        cursor = self.collection.aggregate(pipeline)
        docs = await cursor.to_list(length=limit)

        logger.info(f"Aggregation tamamlandi. Bulunan eslesme: {len(docs)}")
        return docs

    async def bulk_upsert(self, entities: list[MatchEntity]) -> dict:
        """Toplu mac guncelleme/ekleme (Faz 6 Fix: Mimari uyum)."""
        if not entities:
            return {"upserted": 0, "modified": 0}

        operations = [
            UpdateOne(
                {"external_id": e.external_id}, {"$set": e.model_dump()}, upsert=True
            )
            for e in entities
        ]

        result = await self.collection.bulk_write(operations, ordered=False)
        return {"upserted": result.upserted_count, "modified": result.modified_count}

    async def delete_expired_upcoming_matches(self) -> int:
        """Baslama saati gecmis ama hala UPCOMING olan maclari temizler."""
        now = datetime.now(timezone.utc)
        result = await self.collection.delete_many({
            "status": MatchStatus.UPCOMING.value,
            "commence_time": {"$lt": now}
        })
        if result.deleted_count > 0:
            logger.info(f"Temizlik: {result.deleted_count} adet suresi dolmus mac silindi.")
        return result.deleted_count
