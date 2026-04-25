"""Veri cekme katmani: CSV indirme ve Odds API istekleri.

Guvenlik:
  - Sezon formati regex ile dogrulanir
  - Path traversal korunmasi
  - API timeout 15s
  - API kota takibi
"""

import re
import os
import logging

import pandas as pd
import requests
import streamlit as st

from config import (
    BASE_URL,
    SUPPORTED_LEAGUES,
    API_KEY,
    ODDS_API_REGION,
    ODDS_API_MARKETS,
)

logger = logging.getLogger(__name__)

# Sezon format kontrolu
_SEASON_RE = re.compile(r"^\d{4}-\d{4}$")
_MAX_CSV_BYTES = 10 * 1024 * 1024  # 10 MB


# ═══════════════════════════════════════════════
#  DOGRULAMA
# ═══════════════════════════════════════════════


def validate_season(season: str) -> bool:
    """'2024-2025' formatini ve mantiksal aralik kontrolu yapar."""
    if not isinstance(season, str) or not _SEASON_RE.match(season):
        return False
    s, e = int(season[:4]), int(season[5:])
    return e == s + 1 and 2000 <= s <= 2030


def _season_code(season: str) -> str:
    """'2024-2025' → '2425' (football-data.co.uk URL formati)."""
    return season[2:4] + season[7:9]


# ═══════════════════════════════════════════════
#  GECMIS VERI  (football-data.co.uk CSV)
# ═══════════════════════════════════════════════


def fetch_csv(league_name: str, season: str, force: bool = False) -> pd.DataFrame:
    """Gecmis sezon CSV'sini indir, data/ klasorune kaydet.

    Returns:
        Ham (islenmemis) DataFrame veya bos DataFrame.
    """
    if not validate_season(season) or league_name not in SUPPORTED_LEAGUES:
        logger.warning("Gecersiz giris: season=%s, league=%s", season, league_name)
        return pd.DataFrame()

    fd_code = SUPPORTED_LEAGUES[league_name]["fd_code"]

    os.makedirs("data", exist_ok=True)
    fpath = os.path.join("data", f"{fd_code}_{season}.csv")

    # Path traversal korumasi
    if not os.path.abspath(fpath).startswith(os.path.abspath("data")):
        return pd.DataFrame()

    # Yerel cache kontrolu
    if not force and os.path.exists(fpath):
        try:
            if os.path.getsize(fpath) > _MAX_CSV_BYTES:
                os.remove(fpath)
            else:
                return pd.read_csv(fpath)
        except Exception:
            pass

    # Internetten indir
    url = f"{BASE_URL}{_season_code(season)}/{fd_code}.csv"
    try:
        df = pd.read_csv(url)
    except Exception as exc:
        logger.error("CSV indirilemedi %s: %s", url, exc)
        return pd.DataFrame()

    return df


def save_csv(df: pd.DataFrame, league_name: str, season: str) -> None:
    """Islenmis veriyi data/ klasorune kaydet."""
    if df.empty or league_name not in SUPPORTED_LEAGUES:
        return
    fd_code = SUPPORTED_LEAGUES[league_name]["fd_code"]
    fpath = os.path.join("data", f"{fd_code}_{season}.csv")
    df.to_csv(fpath, index=False)


# ═══════════════════════════════════════════════
#  CANLI ORANLAR  (The Odds API)
# ═══════════════════════════════════════════════


def fetch_odds_api(league_name: str) -> list[dict]:
    """The Odds API'den canli oranlari cek.

    Returns:
        API JSON listesi veya bos liste.
    """
    if not API_KEY:
        st.warning(
            "API anahtari bulunamadi. .env veya Streamlit Secrets'a "
            "ODDS_API_KEY ekleyin."
        )
        return []

    if league_name not in SUPPORTED_LEAGUES:
        return []

    sport = SUPPORTED_LEAGUES[league_name]["odds_api_sport"]
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"

    params = {
        "apiKey": API_KEY,
        "regions": ODDS_API_REGION,
        "markets": ODDS_API_MARKETS,
        "oddsFormat": "decimal",
    }

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.HTTPError:
        detail = ""
        try:
            detail = resp.json().get("message", "")
        except Exception:
            pass
        st.error(f"API Hatasi ({resp.status_code}): {detail or 'Bilinmeyen hata'}")
        return []
    except requests.exceptions.ConnectionError:
        st.error("Internet baglantisi kurulamadi.")
        return []
    except requests.exceptions.Timeout:
        st.error("API istegi zaman asimina ugradi (15s).")
        return []
    except Exception as exc:
        logger.exception("Beklenmeyen API hatasi")
        st.error(f"Beklenmeyen hata: {type(exc).__name__}")
        return []

    if not data:
        st.info("Bu lig icin yaklasan mac orani bulunamadi.")
        return []

    # Kota takibi
    remaining = resp.headers.get("x-requests-remaining")
    if remaining is not None:
        try:
            if int(remaining) < 10:
                st.sidebar.warning(f"API kota uyarisi: {remaining} istek kaldi.")
        except ValueError:
            pass

    return data
