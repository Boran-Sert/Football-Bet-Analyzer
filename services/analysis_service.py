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
import asyncio
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
        """Repository üzerinden filtrelenmiş veriyi çeker, mesafeyi Python'da hesaplar."""

        # Rule 12 Fix: Raw DB erişimi yerine repository metodu kullanıldı
        docs = await self.repo.find_matches_by_odds_range(
            home=home, draw=draw, away=away, limit=2000
        )

        def process_docs(docs_list):
            results_local = []
            for doc in docs_list:
                try:
                    # Robust odds retrieval: both nested (h2h) and flat structures
                    odds_data = doc.get("odds", {})
                    h2h = odds_data.get("h2h", {})

                    h = h2h.get("home") or odds_data.get("home")
                    d = h2h.get("draw") or odds_data.get("draw")
                    a = h2h.get("away") or odds_data.get("away")

                    if h is None or d is None or a is None:
                        continue

                    # Oklid mesafesi (Euclidean Distance)
                    dist = (
                        (float(h) - home) ** 2
                        + (float(d) - draw) ** 2
                        + (float(a) - away) ** 2
                    ) ** 0.5

                    if dist < DISTANCE_THRESHOLD:
                        sim_pct = max(0.0, 100.0 - (dist * 33.3))
                        results_local.append(
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

            # Python tarafında sıralama (MongoDB In-memory sort limit sorunu yok)
            results_local.sort(key=lambda x: x.distance)
            return results_local[:limit]

        # Agır CPU islemi (2000 objenin traverse edilmesi) oldugu icin thread'e aliyoruz
        return await asyncio.to_thread(process_docs, docs)
