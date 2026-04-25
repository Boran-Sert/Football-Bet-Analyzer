"""Uygulama ayarlari, lig tanimlari, kolon esleme ve sezon yardimcilari.

API Key oncelik sirasi:
  1. OS ortam degiskeni  (ODDS_API_KEY)
  2. Streamlit secrets   (.streamlit/secrets.toml)
  3. Bos string          (calisma zamaninda uyari verir)
"""

import os
from datetime import datetime

# ── .env dosyasindan API key yukle ──
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# ── API Key ──
try:
    import streamlit as st

    API_KEY: str = os.environ.get("ODDS_API_KEY") or st.secrets.get("ODDS_API_KEY", "")
except Exception:
    API_KEY: str = os.environ.get("ODDS_API_KEY", "")


# ═══════════════════════════════════════════════
#  SABITLER
# ═══════════════════════════════════════════════

BASE_URL = "https://www.football-data.co.uk/mmz4281/"
TURKISH_TAX_MARGIN = 0.865

ODDS_API_REGION = "eu"
ODDS_API_MARKETS = "h2h,totals"


# ═══════════════════════════════════════════════
#  LIG TANIMLARI
# ═══════════════════════════════════════════════

# API'lerden gelen takim isimleriyle CSV'deki takim isimleri uyusmazligi
# icin manuel eslestirme sozlugu (sol: API ismi / sag: CSV kisa ismi veya esdegeri)
TEAM_ALIASES = {
    "wolverhampton wanderers": "wolves",
    "manchester united": "man united",
    "manchester city": "man city",
    "tottenham hotspur": "tottenham",
    "newcastle united": "newcastle",
    "west ham united": "west ham",
    "sheffield united": "sheffield",
    "nottingham forest": "nott'm forest",
    "brighton & hove albion": "brighton",
    "paris saint germain": "psg",
}

SUPPORTED_LEAGUES = {
    "Türkiye Süper Lig": {
        "fd_code": "T1",
        "odds_api_sport": "soccer_turkey_super_league",
    },
    "İngiltere Premier Lig": {
        "fd_code": "E0",
        "odds_api_sport": "soccer_epl",
    },
    "İspanya La Liga": {
        "fd_code": "SP1",
        "odds_api_sport": "soccer_spain_la_liga",
    },
    "İtalya Serie A": {
        "fd_code": "I1",
        "odds_api_sport": "soccer_italy_serie_a",
    },
    "Almanya Bundesliga": {
        "fd_code": "D1",
        "odds_api_sport": "soccer_germany_bundesliga",
    },
    "Fransa Ligue 1": {
        "fd_code": "F1",
        "odds_api_sport": "soccer_france_ligue_one",
    },
}


# ═══════════════════════════════════════════════
#  KOLON ESLEME  (football-data.co.uk → Turkce)
# ═══════════════════════════════════════════════

COLUMN_MAPPING = {
    "Date": "Tarih",
    "HomeTeam": "Ev Sahibi",
    "AwayTeam": "Deplasman",
    "FTHG": "Ev Sahibi Gol",
    "FTAG": "Deplasman Gol",
    "HY": "Ev Sahibi Sari Kart",
    "AY": "Deplasman Sari Kart",
    "HR": "Ev Sahibi Kirmizi Kart",
    "AR": "Deplasman Kirmizi Kart",
    "HC": "Ev Sahibi Korner",
    "AC": "Deplasman Korner",
    "B365H": "MS 1",
    "B365D": "MS 0",
    "B365A": "MS 2",
    "B365>2.5": "2.5 Ust",
    "B365<2.5": "2.5 Alt",
    "B365>1.5": "1.5 Ust",
    "B365<1.5": "1.5 Alt",
    "B365HTH": "IY 1",
    "B365HTD": "IY 0",
    "B365HTA": "IY 2",
    "B365BTTS": "KG Var",
}

# Oran olmayan bilgi kolonlari
INFO_COLUMNS = {
    "Tarih",
    "Ev Sahibi",
    "Deplasman",
    "Ev Sahibi Gol",
    "Deplasman Gol",
    "Ev Sahibi Sari Kart",
    "Deplasman Sari Kart",
    "Toplam Sari Kart",
    "Ev Sahibi Kirmizi Kart",
    "Deplasman Kirmizi Kart",
    "Toplam Kirmizi Kart",
    "Ev Sahibi Korner",
    "Deplasman Korner",
    "Toplam Korner",
}

# Benzerlik hesabinda kullanilan oran pazarlari
ALL_ODDS_MARKETS = [
    "MS 1",
    "MS 0",
    "MS 2",
    "2.5 Ust",
    "2.5 Alt",
    "1.5 Ust",
    "1.5 Alt",
    "IY 1",
    "IY 0",
    "IY 2",
    "KG Var",
]


# ═══════════════════════════════════════════════
#  SEZON YARDIMCILARI
# ═══════════════════════════════════════════════


def get_current_season() -> str:
    """Guncel sezonu hesapla. Agustos ve sonrasi → yeni sezon."""
    now = datetime.now()
    year = now.year if now.month >= 8 else now.year - 1
    return f"{year}-{year + 1}"


def get_seasons(count: int = 6) -> list[str]:
    """Guncel sezondan geriye dogru 'count' adet sezon listesi dondur."""
    current = get_current_season()
    start_year = int(current[:4])
    return [f"{start_year - i}-{start_year - i + 1}" for i in range(count)]
