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
        if target_odds.home is None or target_odds.draw is None or target_odds.away is None:
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
        """MongoDB aggregation pipeline ile Euclidean mesafeyi DB'de hesaplar."""
        pipeline = [
            # 1. Sadece tamamlanmis maclar
            {"$match": {"status": "completed"}},
            # 2. h2h odds mevcut olanlar
            {"$match": {
                "odds.h2h.home": {"$exists": True, "$ne": None},
                "odds.h2h.draw": {"$exists": True, "$ne": None},
                "odds.h2h.away": {"$exists": True, "$ne": None},
            }},
            # 3. Euclidean mesafeyi hesapla
            {"$addFields": {
                "distance": {
                    "$sqrt": {
                        "$add": [
                            {"$pow": [{"$subtract": ["$odds.h2h.home", home]}, 2]},
                            {"$pow": [{"$subtract": ["$odds.h2h.draw", draw]}, 2]},
                            {"$pow": [{"$subtract": ["$odds.h2h.away", away]}, 2]},
                        ]
                    }
                }
            }},
            # 4. Sadece DISTANCE_THRESHOLD altindakileri al
            {"$match": {"distance": {"$lt": DISTANCE_THRESHOLD}}},
            # 5. En yakin once sirala
            {"$sort": {"distance": 1}},
            # 6. Sadece ihtiyac kadar cek
            {"$limit": limit},
        ]

        db = self.repo.collection.database
        cursor = db.matches.aggregate(pipeline)
        docs = await cursor.to_list(length=limit)

        results: list[SimilarMatchResult] = []
        for doc in docs:
            try:
                distance = float(doc.get("distance", 999))
                sim_pct = max(0.0, 100.0 - (distance * 33.3))
                results.append(
                    SimilarMatchResult(
                        match=MatchInDB(**{k: v for k, v in doc.items() if k != "distance"}),
                        distance=round(distance, 4),
                        similarity_percentage=round(sim_pct, 1),
                    )
                )
            except Exception as exc:
                logger.warning("Aggregation doc parse hatasi: %s", exc)
                continue

        return results
