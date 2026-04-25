"""Dis API'den mac verisi ceken arka plan gorevi.

rules.md Madde 1: Dis API cagrisi SADECE tasks/ katmaninda yapilir.
rules.md Madde 1: Asenkron httpx.AsyncClient kullanilir.

football-data.org v4 endpointleri kullanilarak maclar cekilir,
MatchRepository ile MongoDB'ye yazilir.
"""

import logging
from datetime import datetime, timezone, timedelta

import httpx

from core.config import settings
from core.database import mongo
from repositories.match_repository import MatchRepository

logger = logging.getLogger(__name__)

# football-data.org ayarlari
_BASE_URL = "https://api.football-data.org/v4"
_HEADERS = {
    "X-Auth-Token": settings.FOOTBALL_DATA_API_KEY,
}

# Takip edilen lig ID'leri (football-data.org formatinda - TIER_ONE)
TRACKED_LEAGUES = {
    "PL": "İngiltere Premier Lig",
    "PD": "İspanya La Liga",
    "SA": "İtalya Serie A",
    "BL1": "Almanya Bundesliga",
    "FL1": "Fransa Ligue 1",
    "DED": "Hollanda Eredivisie",
    "PPL": "Portekiz Primeira Liga",
    "ELC": "İngiltere Championship",
    "BSA": "Brezilya Serie A",
    "CL": "UEFA Champions League",
}


async def _fetch_json(client: httpx.AsyncClient, endpoint: str, params: dict = None) -> dict:
    """football-data.org'a tek bir GET istegi atar ve JSON dondurur."""
    resp = await client.get(
        f"{_BASE_URL}/{endpoint}",
        headers=_HEADERS,
        params=params,
        timeout=15.0,
    )
    if resp.status_code != 200:
        logger.error("API Hatasi: %s - %s", resp.status_code, resp.text)
        resp.raise_for_status()
    return resp.json()


async def fetch_daily_matches() -> None:
    """Takip edilen liglerdeki bugunku ve yaklasan macları ceker.

    Her lig icin:
      1. /competitions/{code}/matches?dateFrom={today}&dateTo={next_7_days}
      2. MatchRepository.upsert_match → Varsa guncelle, yoksa ekle.
    """
    if mongo.db is None:
        logger.error("MongoDB baglantisi yok, gorev atlanıyor.")
        return

    repo = MatchRepository(mongo.db)
    today = datetime.now(timezone.utc).date()
    # football-data.org free plan kısıtlamaları nedeniyle geniş tarih aralığı yerine
    # belirli bir aralık çekiyoruz.
    date_from = today.isoformat()
    date_to = (today + timedelta(days=7)).isoformat()

    async with httpx.AsyncClient() as client:
        for league_code, league_name in TRACKED_LEAGUES.items():
            try:
                await _process_league(
                    client, repo, league_code, league_name, date_from, date_to
                )
            except Exception as exc:
                logger.error("Hata [%s]: %s", league_name, exc)

    logger.info("Veri cekme gorevi tamamlandi.")


async def _process_league(
    client: httpx.AsyncClient,
    repo: MatchRepository,
    league_code: str,
    league_name: str,
    date_from: str,
    date_to: str,
) -> None:
    """Tek bir lig icin mac verisini cekip MongoDB'ye yazar."""

    # Maclari cek
    endpoint = f"competitions/{league_code}/matches"
    params = {"dateFrom": date_from, "dateTo": date_to}
    
    data = await _fetch_json(client, endpoint, params)
    matches = data.get("matches", [])
    
    if not matches:
        logger.info("Mac bulunamadi: %s", league_name)
        return

    upserted = 0
    for match in matches:
        match_doc = _parse_match(match, league_name)
        if match_doc:
            await repo.upsert_match(match_doc)
            upserted += 1

    logger.info("%s: %d mac guncellendi.", league_name, upserted)


def _parse_match(match: dict, league_name: str) -> dict:
    """football-data.org match objesini MatchInDB formatina donusturur."""
    
    status_raw = match.get("status", "")
    if status_raw == "FINISHED":
        status = "finished"
    elif status_raw in ("SCHEDULED", "TIMED"):
        status = "scheduled"
    elif status_raw in ("IN_PLAY", "PAUSED"):
        status = "live"
    else:
        status = "scheduled"

    score = match.get("score", {})
    full_time = score.get("fullTime", {})
    
    season_data = match.get("season", {})
    start_year = season_data.get("startDate", "")[:4]
    end_year = season_data.get("endDate", "")[:4]
    season_str = f"{start_year}-{end_year}" if start_year and end_year else "unknown"

    match_doc = {
        "home_team": match.get("homeTeam", {}).get("name", ""),
        "away_team": match.get("awayTeam", {}).get("name", ""),
        "league": league_name,
        "season": season_str,
        "match_date": datetime.fromisoformat(match.get("utcDate", "").replace("Z", "+00:00")),
        "home_goals": full_time.get("home"),
        "away_goals": full_time.get("away"),
        "status": status,
        # Odds verisi ucretsiz planda genellikle bos gelir
        "odds_home": None,
        "odds_draw": None,
        "odds_away": None,
    }

    return match_doc
