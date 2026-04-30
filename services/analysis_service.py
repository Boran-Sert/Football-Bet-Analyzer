"""Benzerlik analizi motoru — GAP 5: MongoDB aggregation pipeline ile optimize edildi.

Onceki sorun:
  - Her istekte 2000 mac Python RAM'ine cekilip O(n) dongu ile isleniyor.
  - Ayni anda 50 kullanici = 50 * 2000 doc = bellek patlamasi.

Yeni yaklasim:
  - Euclidean mesafe hesabi MongoDB $expr + $sqrt ile veritabaninda yapilir.
  - Python'a sadece zaten yakin olan maclar gelir (distance_threshold filtresi).
  - Sonuclar Redis'te 1 saat onbelleklenir, ayni mac icin tekrar DB'ye gitilmez.
"""

import logging
import math
import asyncio
from pydantic import BaseModel

from core.config import TierLimits
from repositories.match_repository import MatchRepository
from schemas.auth import UserTier
from schemas.match import MatchInDB
from utils.cache import cache_response

logger = logging.getLogger(__name__)

DISTANCE_THRESHOLD = 3.0  # Bu degerin ustundeki maclar zaten benzer sayilmaz


class SimilarMatchResult(BaseModel):
    match: MatchInDB
    distance: float
    similarity_percentage: float


class AnalysisService:
    """Yaklasan maclari gecmis verilerle karsilastirir."""

    def __init__(self, match_repo: MatchRepository):
        self.repo = match_repo

    @cache_response(ttl_seconds=3600, prefix="analysis:similar")
    async def find_similar_matches(
        self,
        target_match_id: str,
        user_tier: UserTier,
        is_superuser: bool = False,
        limit_override: int | None = None,
    ) -> list[SimilarMatchResult]:
        """Hedef macin oranlarina en benzeyen gecmis maclari bulur.

        MongoDB aggregation pipeline kullanarak veritabaninda filtreleme yapar.
        Python'a sadece threshold'u gecen sonuclar gelir.
        """
        target = await self.repo.get_by_external_id(target_match_id)
        if not target or target.status.value != "upcoming":
            return []

        if not target.odds or not getattr(target.odds, "h2h", None):
            return []

        target_odds = target.odds.h2h
        if (
            target_odds.home is None
            or target_odds.draw is None
            or target_odds.away is None
        ):
            return []

        # Tier limit
        tier_limit = TierLimits.get_similar_limit(user_tier.value)
        if is_superuser:
            # Hard cap prevents accidental huge queries (GAP 5 fix)
            final_limit = min(limit_override or 50, TierLimits.superuser_max_limit)
        elif user_tier in (UserTier.PRO, UserTier.ELITE) and limit_override:
            final_limit = min(limit_override, tier_limit)
        else:
            final_limit = tier_limit

        # ── MongoDB aggregation: distance computed in DB ──────────────────────
        results = await self._find_similar_via_aggregation(
            home=target_odds.home,
            draw=target_odds.draw,
            away=target_odds.away,
            limit=final_limit * 3,  # Fetch 3x to allow dedup headroom
        )

        # ── Dedup: same day + same teams ─────────────────────────────────────
        seen: set[tuple] = set()
        unique: list[SimilarMatchResult] = []
        for res in results:
            key = (
                res.match.commence_time.date(),
                res.match.home_team,
                res.match.away_team,
            )
            if key not in seen:
                seen.add(key)
                unique.append(res)
            if len(unique) >= final_limit:
                break

        return unique

    async def _find_similar_via_aggregation(
        self,
        home: float,
        draw: float,
        away: float,
        limit: int,
    ) -> list[SimilarMatchResult]:
        """Kabaca filtrelenmis veriyi DB'den ceker, mesafeyi Python'da hesaplar (Faz 6 Fix)."""
        
        # 1. MongoDB'den sadece kabaca filtrelenmis veriyi cek (İndeksli alanlar üzerinden)
        # Bu sayede DB tarafında COLLSCAN ve In-Memory Sort engellenir.
        pipeline = [
            {"$match": {"status": "completed"}},
            {
                "$match": {
                    "odds.h2h.home": {"$gte": home - 1.0, "$lte": home + 1.0},
                    "odds.h2h.draw": {"$gte": draw - 1.0, "$lte": draw + 1.0},
                    "odds.h2h.away": {"$gte": away - 1.0, "$lte": away + 1.0},
                }
            },
            # Bellek dostu limit: Cok fazla veri gelirse bile hard cap koy (Ornegin 2000)
            {"$limit": 2000}
        ]

        db = self.repo.collection.database
        cursor = db.matches.aggregate(pipeline)
        docs = await cursor.to_list(length=2000)

        def process_docs(docs_list):
            results_local = []
            for doc in docs_list:
                try:
                    h = doc["odds"]["h2h"]["home"]
                    d = doc["odds"]["h2h"]["draw"]
                    a = doc["odds"]["h2h"]["away"]
                    
                    # Euclidean mesafe (Python tarafında)
                    dist = math.sqrt(
                        (h - home)**2 + (d - draw)**2 + (a - away)**2
                    )
                    
                    if dist < DISTANCE_THRESHOLD:
                        sim_pct = max(0.0, 100.0 - (dist * 33.3))
                        results_local.append(
                            SimilarMatchResult(
                                match=MatchInDB(**doc),
                                distance=round(dist, 4),
                                similarity_percentage=round(sim_pct, 1),
                            )
                        )
                except Exception:
                    continue
            
            # Python tarafında sıralama (MongoDB In-memory sort limit sorunu yok)
            results_local.sort(key=lambda x: x.distance)
            return results_local[:limit]

        # Agır CPU islemi (2000 objenin traverse edilmesi) oldugu icin thread'e aliyoruz
        return await asyncio.to_thread(process_docs, docs)
