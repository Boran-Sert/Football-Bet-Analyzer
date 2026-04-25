"""Mac verileri icin MongoDB repository katmani.

BaseRepository'den miras alir.
Sadece veritabani sorgulari yer alir; analiz mantigi YOKTUR (rules.md Madde 2).
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from repositories.base import BaseRepository
from schemas.match import MatchInDB


class MatchRepository(BaseRepository[MatchInDB]):
    """matches koleksiyonuna ozel asenkron sorgular."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, "matches")

    async def get_matches_by_date(
        self,
        date: datetime,
        league: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Belirtilen tarihteki maclari getirir.

        Args:
            date: Hedef gun (saat bilgisi kesilir).
            league: Opsiyonel lig filtresi.
        """
        start = datetime(date.year, date.month, date.day)
        end = datetime(date.year, date.month, date.day, 23, 59, 59)

        query: Dict[str, Any] = {
            "match_date": {"$gte": start, "$lte": end},
        }
        if league:
            query["league"] = league

        return await self.find_many(query, sort=[("match_date", 1)])

    async def get_matches_by_league_and_season(
        self,
        league: str,
        season: str,
    ) -> List[Dict[str, Any]]:
        """Lig ve sezon bazinda tum maclari getirir."""
        return await self.find_many(
            {"league": league, "season": season},
            sort=[("match_date", 1)],
        )

    async def get_upcoming_matches(
        self,
        league: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Henuz oynanmamis (scheduled) maclari getirir."""
        query: Dict[str, Any] = {"status": "scheduled"}
        if league:
            query["league"] = league

        return await self.find_many(query, sort=[("match_date", 1)])

    async def update_match_data(
        self,
        home_team: str,
        away_team: str,
        match_date: datetime,
        data: Dict[str, Any],
    ) -> int:
        """Belirli bir macin verilerini gunceller (oran, skor vb.).

        Args:
            home_team: Ev sahibi takim adi.
            away_team: Deplasman takim adi.
            match_date: Mac tarihi.
            data: Guncellenecek alanlar sozlugu.

        Returns:
            Guncellenen belge sayisi (0 veya 1).
        """
        data["updated_at"] = datetime.utcnow()
        return await self.update_one(
            {
                "home_team": home_team,
                "away_team": away_team,
                "match_date": match_date,
            },
            data,
        )

    async def upsert_match(self, match_data: Dict[str, Any]) -> str:
        """Mac verisi varsa guncelle, yoksa yeni ekle.

        Args:
            match_data: MatchInDB semasina uygun sozluk.

        Returns:
            Eklenen veya guncellenen belgenin ID'si.
        """
        query = {
            "home_team": match_data["home_team"],
            "away_team": match_data["away_team"],
            "match_date": match_data["match_date"],
        }
        match_data["updated_at"] = datetime.utcnow()

        result = await self.collection.update_one(
            query,
            {"$set": match_data},
            upsert=True,
        )
        return str(result.upserted_id or "updated")
