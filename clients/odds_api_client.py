"""The Odds API istemcisi.

Sadece yaklasan maclarin oranlarini cekmek icin kullanilir.
Gecmis mac verileri Football-data.co.uk CSV'lerinden yuklenir.
"""

import logging

from clients.base_client import BaseAPIClient, APIClientError
from core.config import settings

logger = logging.getLogger(__name__)


class OddsAPIClient(BaseAPIClient):
    """The Odds API v4 istemcisi."""

    def __init__(self) -> None:
        super().__init__(base_url=settings.ODDS_API_BASE_URL)
        self._api_key = settings.ODDS_API_KEY

    def _build_headers(self) -> dict[str, str]:
        return {"Accept": "application/json"}

    async def fetch_sports(self) -> list[dict]:
        """Aktif sporlarin listesini dondurur (kota harcamaz).

        Returns:
            Spor objelerinin listesi: [{"key": "soccer_epl", ...}, ...]
        """
        response = await self.get("/sports/", params={"apiKey": self._api_key})
        return response.json()

    async def fetch_soccer_leagues(self) -> list[dict]:
        """Sadece Soccer grubundaki aktif ve hedef listemizde olan ligleri dondurur."""
        sports = await self.fetch_sports()
        return [
            s for s in sports
            if s.get("group", "").lower() == "soccer"
            and s.get("active", False)
            and s.get("key") in settings.TARGET_LEAGUES
        ]

    async def fetch_upcoming_odds(
        self,
        sport_key: str,
        regions: str | None = None,
        markets: str | None = None,
    ) -> list[dict]:
        """Belirli bir lig icin yaklasan maclarin oranlarini toplu getirir.

        Tek istekte h2h + totals + btts oranlarini alir.
        Eger 422 hatasi alirsa btts olmadan tekrar dener (fallback).

        Args:
            sport_key: Odds API sport key (orn: "soccer_epl").
            regions: Bahis bolgesi (orn: "eu,uk"). Varsayilan: settings'ten.
            markets: Pazar turleri (orn: "h2h,totals,btts"). Varsayilan: settings'ten.

        Returns:
            Mac + oran objeleri listesi.
        """
        requested_markets = markets or settings.ODDS_API_MARKETS
        params = {
            "apiKey": self._api_key,
            "regions": regions or settings.ODDS_API_REGIONS,
            "markets": requested_markets,
            "oddsFormat": "decimal",
            "dateFormat": "iso",
        }

        try:
            response = await self.get(f"/sports/{sport_key}/odds/", params=params)
            data = response.json()
            logger.info(
                "Odds API: %s icin %d mac alindi (markets=%s).",
                sport_key, len(data), requested_markets,
            )
            return data

        except APIClientError as exc:
            # 422 = desteklenmeyen market (bazi ligler btts desteklemiyor)
            if exc.status_code == 422 and "btts" in requested_markets:
                logger.warning(
                    "Lig [%s] btts desteklemiyor, h2h+totals ile tekrar deneniyor.",
                    sport_key,
                )
                # Fallback: btts olmadan tekrar dene
                fallback_markets = "h2h,totals"
                params["markets"] = fallback_markets
                response = await self.get(f"/sports/{sport_key}/odds/", params=params)
                data = response.json()
                logger.info(
                    "Odds API fallback: %s icin %d mac alindi (markets=%s).",
                    sport_key, len(data), fallback_markets,
                )
                return data
            raise  # Diger hatalari yukari firsat

    async def fetch_scores(
        self,
        sport_key: str,
        days_from: int = 3,
    ) -> list[dict]:
        """Son gunlerdeki mac skorlarini getirir.

        Args:
            sport_key: Odds API sport key.
            days_from: Kac gun geriye bakacak.

        Returns:
            Skor objeleri listesi.
        """
        params = {
            "apiKey": self._api_key,
            "daysFrom": days_from,
        }
        response = await self.get(f"/sports/{sport_key}/scores/", params=params)
        return response.json()
