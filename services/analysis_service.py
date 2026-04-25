"""Analiz is mantigi servisi.

rules.md Madde 2: Service katmani HTTP Request almaz, DB baglantisinı bilmez.
Sadece Repository kullanarak veri okur ve is mantigi uygular.
rules.md Madde 3: Router'dan Depends() ile enjekte edilir.
"""

from typing import Optional

from bson import ObjectId

from repositories.match_repository import MatchRepository
from schemas.match import MatchResponse, AnalysisResult


class AnalysisService:
    """Mac analizi is mantigi. Repository uzerinden veri okur."""

    def __init__(self, repo: MatchRepository) -> None:
        """Dependency Injection ile repository alir."""
        self.repo = repo

    async def get_match_by_id(self, match_id: str) -> Optional[MatchResponse]:
        """Tek bir maci ID ile getirir."""
        doc = await self.repo.find_one({"_id": ObjectId(match_id)})
        if not doc:
            return None
        return self._to_response(doc)

    async def analyze_match(self, match_id: str, top_n: int = 5) -> Optional[AnalysisResult]:
        """Belirtilen mac icin benzerlik analizi yapar.

        Args:
            match_id: Hedef macin MongoDB ID'si.
            top_n: Dondurulecek benzer mac sayisi.

        Returns:
            AnalysisResult veya None (mac bulunamazsa).
        """
        target = await self.repo.find_one({"_id": ObjectId(match_id)})
        if not target:
            return None

        # Ayni lig ve sezondaki tamamlanmis maclari getir
        history = await self.repo.find_many(
            {
                "league": target["league"],
                "status": "finished",
                "odds_home": {"$exists": True, "$ne": None},
            },
            sort=[("match_date", -1)],
            limit=200,
        )

        if not history:
            return None

        # Oklid mesafesi ile benzerlik hesapla
        scored = self._calculate_similarity(target, history)
        top_matches = sorted(scored, key=lambda x: x[1])[:top_n]
        similar = [self._to_response(m) for m, _ in top_matches]

        # Istatistik hesapla
        stats = self._compute_stats([m for m, _ in top_matches])

        return AnalysisResult(
            target_match=self._to_response(target),
            similar_matches=similar,
            **stats,
        )

    def _calculate_similarity(self, target: dict, history: list[dict]) -> list[tuple]:
        """Oklid mesafesi ile oran benzerligi hesaplar."""
        odds_keys = ["odds_home", "odds_draw", "odds_away", "odds_over_25", "odds_under_25"]
        target_vec = [target.get(k) for k in odds_keys]

        if any(v is None for v in target_vec):
            return []

        results = []
        for match in history:
            if str(match.get("_id")) == str(target.get("_id")):
                continue
            match_vec = [match.get(k) for k in odds_keys]
            if any(v is None for v in match_vec):
                continue

            distance = sum((a - b) ** 2 for a, b in zip(target_vec, match_vec)) ** 0.5
            results.append((match, distance))

        return results

    def _compute_stats(self, matches: list[dict]) -> dict:
        """Benzer maclardan istatistik ozeti cikarir."""
        total = len(matches)
        if total == 0:
            return {"home_win_pct": 0, "draw_pct": 0, "away_win_pct": 0, "avg_total_goals": 0}

        home_wins = sum(1 for m in matches if (m.get("home_goals") or 0) > (m.get("away_goals") or 0))
        draws = sum(1 for m in matches if (m.get("home_goals") or 0) == (m.get("away_goals") or 0))
        away_wins = total - home_wins - draws
        avg_goals = sum((m.get("home_goals") or 0) + (m.get("away_goals") or 0) for m in matches) / total

        return {
            "home_win_pct": round(home_wins / total * 100, 1),
            "draw_pct": round(draws / total * 100, 1),
            "away_win_pct": round(away_wins / total * 100, 1),
            "avg_total_goals": round(avg_goals, 2),
        }

    @staticmethod
    def _to_response(doc: dict) -> MatchResponse:
        """MongoDB belgesini MatchResponse semasina donusturur."""
        return MatchResponse(
            id=str(doc["_id"]),
            home_team=doc["home_team"],
            away_team=doc["away_team"],
            league=doc["league"],
            match_date=doc["match_date"],
            home_goals=doc.get("home_goals"),
            away_goals=doc.get("away_goals"),
            odds_home=doc.get("odds_home"),
            odds_draw=doc.get("odds_draw"),
            odds_away=doc.get("odds_away"),
            odds_over_25=doc.get("odds_over_25"),
            odds_under_25=doc.get("odds_under_25"),
            status=doc.get("status", "scheduled"),
        )
