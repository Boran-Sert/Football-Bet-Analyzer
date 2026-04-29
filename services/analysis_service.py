"""Benzerlik analizi (Oklid mesafesi) motoru."""

import math
from pydantic import BaseModel

from core.config import TierLimits
from repositories.match_repository import MatchRepository
from schemas.auth import UserTier
from schemas.match import MatchInDB
from utils.cache import cache_response


class SimilarMatchResult(BaseModel):
    """Benzer mac yanit objesi."""
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
        limit_override: int | None = None
    ) -> list[SimilarMatchResult]:
        """Yaklasan bir macin oranlarina en benzeyen gecmis maclari bulur.

        Args:
            target_match_id: Hedef yaklasan macin ID'si.
            user_tier: Kullanicinin katmani (FREE, PRO, ELITE).
            limit_override: PRO kullanicilarin sectigi ozel limit.

        Kullanici yetkisine gore dondurulen sonuc sayisi (limit) belirlenir.
        Sonuclar Redis'te onbelleklenir.
        """
        # Hedef maci bul
        target = await self.repo.get_by_external_id(target_match_id)
        if not target or target.status.value != "upcoming":
            return []

        # Hedef h2h oranlari yoksa analiz yapilamaz
        if not target.odds or not getattr(target.odds, "h2h", None):
            return []
            
        target_odds = target.odds.h2h
        if target_odds.home is None or target_odds.draw is None or target_odds.away is None:
            return []

        # Tier'a gore limit belirle
        tier_limit = TierLimits.get_similar_limit(user_tier.value)
        
        # ELITE veya Superuser limitleri
        final_limit = tier_limit
        if is_superuser:
            final_limit = limit_override or 50 # Adminlere varsayilan 50
        elif user_tier == UserTier.PRO and limit_override:
            # Pro kullanici kendi limitini belirleyebilir (ama max limitinden fazla olamaz)
            final_limit = min(limit_override, tier_limit)
        elif user_tier == UserTier.ELITE and limit_override:
            # Elite kullanici da kendi limitini belirleyebilir
            final_limit = min(limit_override, tier_limit)

        # Gecmis maclari cek
        # Performans icin lig kilitli cekilebilir, ama daha iyi analiz icin genel cekiyoruz.
        # RAM'de islem yapacagimiz icin son 2000 mac yeterli olacaktir.
        historical_matches = await self.repo.get_completed_matches_for_analysis(limit=2000)

        # Oklid hesaplamasi yap
        results: list[SimilarMatchResult] = []
        for match in historical_matches:
            if not getattr(match, "odds", None) or not getattr(match.odds, "h2h", None):
                continue
                
            hist_odds = match.odds.h2h
            if hist_odds.home is None or hist_odds.draw is None or hist_odds.away is None:
                continue

            # sqrt((x2 - x1)^2 + (y2 - y1)^2 + (z2 - z1)^2)
            distance = math.sqrt(
                (target_odds.home - hist_odds.home) ** 2 +
                (target_odds.draw - hist_odds.draw) ** 2 +
                (target_odds.away - hist_odds.away) ** 2
            )

            # Sadece makul derecede benzer olanlari al (esnetildi: 3.0)
            if distance < 3.0:
                # distance: 0 tamamen ayni, buyudukce benzemez
                # Yuzdelik benzerlik skoruna cevirme (orneksel)
                sim_pct = max(0.0, 100.0 - (distance * 33.3))
                
                results.append(SimilarMatchResult(
                    match=match,
                    distance=round(distance, 4),
                    similarity_percentage=round(sim_pct, 1)
                ))

        # Mesafeye gore artan sirala (en yakin once)
        results.sort(key=lambda x: x.distance)

        # Mukerrerleri engelle (Ayni gun, ayni takimlar)
        seen_matches = set()
        unique_results = []
        for res in results:
            match_key = (
                res.match.commence_time.date(),
                res.match.home_team,
                res.match.away_team
            )
            if match_key not in seen_matches:
                seen_matches.add(match_key)
                unique_results.append(res)
            
            if len(unique_results) >= final_limit:
                break

        return unique_results
