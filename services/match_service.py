"""Mac veri yonetimi is mantigi."""

from repositories.match_repository import MatchRepository
from schemas.match import MatchInDB
from utils.cache import cache_response


class MatchService:
    """Mac ve lig sorgularini isler, Redis onbellegini kullanir."""

    def __init__(self, repo: MatchRepository):
        self.repo = repo

    @cache_response(ttl_seconds=300, prefix="matches:upcoming")
    async def get_upcoming_matches(
        self,
        sport: str = "football",
        league_key: str | None = None,
        limit: int = 50,
        skip: int = 0
    ) -> list[MatchInDB]:
        """Yaklasan maclari getirir (5 dakika cache)."""
        return await self.repo.get_upcoming_matches(sport, league_key, limit, skip)

    @cache_response(ttl_seconds=3600, prefix="matches:leagues")
    async def get_available_leagues(self, sport: str = "football") -> list[str]:
        """Sistemdeki ligleri getirir (1 saat cache)."""
        return await self.repo.get_available_leagues(sport)

    async def get_match_by_id(self, external_id: str) -> MatchInDB | None:
        """ID'ye gore mac detayini getirir (cachelenmez)."""
        return await self.repo.get_by_external_id(external_id)
