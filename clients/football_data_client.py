"""Football-data.co.uk CSV istemcisi.

Tarihsel mac istatistiklerini CSV formatinda indirir.
"""

import csv
import io
import logging

from clients.base_client import BaseAPIClient

logger = logging.getLogger(__name__)

FOOTBALL_DATA_BASE_URL = "https://www.football-data.co.uk"


class FootballDataClient(BaseAPIClient):
    """Football-data.co.uk CSV istemcisi."""

    def __init__(self) -> None:
        super().__init__(base_url=FOOTBALL_DATA_BASE_URL, timeout=60.0, verify_ssl=False)

    def _build_headers(self) -> dict[str, str]:
        return {"Accept": "text/csv"}

    async def fetch_season_csv(
        self,
        league_code: str,
        season: str,
    ) -> list[dict]:
        """Belirli bir lig ve sezon icin CSV verisini indirir ve parse eder.

        Args:
            league_code: Lig kodu (orn: "E0", "SP1", "T1").
            season: Sezon kodu (orn: "2425" -> 2024-2025).

        Returns:
            CSV satirlarinin dict listesi.
        """
        path = f"/mmz4281/{season}/{league_code}.csv"
        try:
            response = await self.get(path)
            text = response.text
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
            logger.info(
                "Football-data: %s/%s icin %d satir alindi.",
                league_code, season, len(rows),
            )
            return rows
        except Exception as exc:
            logger.error(
                "Football-data CSV indirme basarisiz: %s/%s — %s",
                league_code, season, str(exc),
            )
            return []

    async def fetch_local_csv(self, file_path: str) -> list[dict]:
        """Yerel CSV dosyasini okur (data/ klasorundan).

        Args:
            file_path: CSV dosyasinin yolu.

        Returns:
            CSV satirlarinin dict listesi.
        """
        import aiofiles

        try:
            async with aiofiles.open(file_path, mode="r", encoding="utf-8") as f:
                content = await f.read()
            reader = csv.DictReader(io.StringIO(content))
            rows = list(reader)
            logger.info("Yerel CSV: %s — %d satir okundu.", file_path, len(rows))
            return rows
        except FileNotFoundError:
            logger.error("CSV dosyasi bulunamadi: %s", file_path)
            return []
