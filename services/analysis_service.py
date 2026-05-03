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
from pydantic import BaseModel

from core.config import TierLimits
from repositories.match_repository import MatchRepository
from schemas.auth import UserTier
from schemas.match import MatchInDB
from utils.cache import cache_response

logger = logging.getLogger(__name__)

DISTANCE_THRESHOLD = 1.5  # Analiz kalitesi için hassasiyeti artırdık (Öneri: 1.5)


class SimilarMatchResult(BaseModel):
    match: MatchInDB
    distance: float
    similarity_percentage: float


class AnalysisService:
    """Yaklasan maclari gecmis verilerle karsilastirir."""

    def __init__(self, match_repo: MatchRepository):
        self.repo = match_repo

    @cache_response(expire=3600, key_prefix="analysis:similar")
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
            final_limit = min(limit_override or 50, TierLimits.superuser_max_limit)
        else:
            final_limit = (
                min(limit_override, tier_limit) if limit_override else tier_limit
            )

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
        """Repository üzerinden hesaplanmış ve sıralanmış veriyi çeker."""

        # 1. DB'den hazır hesaplanmış veriyi çek (Ağır işi DB yaptı)
        docs = await self.repo.find_similar_matches_by_distance(
            home=home, draw=draw, away=away, threshold=DISTANCE_THRESHOLD, limit=limit
        )

        results = []
        # 2. Sadece gelen veriyi Pydantic modeline dönüştür (Artık ağır matematik veya to_thread yok)
        for doc in docs:
            try:
                # MongoDB aggregation 'distance' alanını hesaplayıp içine koydu
                dist = doc.get("distance", 0.0)
                sim_pct = max(0.0, 100.0 - (dist * 33.3))

                results.append(
                    SimilarMatchResult(
                        match=MatchInDB(**doc),
                        distance=round(dist, 4),
                        similarity_percentage=round(sim_pct, 1),
                    )
                )
            except Exception as e:
                logger.error(
                    f"Mac dokumani dogrulama hatasi: {str(e)} | Match ID: {doc.get('external_id')}"
                )
                continue

        return results
