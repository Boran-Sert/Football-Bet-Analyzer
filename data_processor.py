"""Veri isleme katmani: donusturme, margin, puan durumu ve cache.

Bu dosya ham veriyi alir, islenmis hale getirir.
Veri cekme islemi data_fetcher.py'de yapilir.
"""

import datetime
import logging

import pandas as pd
import streamlit as st

from config import (
    COLUMN_MAPPING,
    TURKISH_TAX_MARGIN,
    INFO_COLUMNS,
    SUPPORTED_LEAGUES,
)
from data_fetcher import fetch_csv, save_csv, fetch_odds_api

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════
#  MARGIN HESABI
# ═══════════════════════════════════════════════


def apply_margin(val: float) -> float:
    """Uluslararasi orani Turkiye marjina cevir: (oran - 1) * marj + 1."""
    if pd.isna(val) or val <= 1.0:
        return val
    return round((val - 1.0) * TURKISH_TAX_MARGIN + 1.0, 2)


# ═══════════════════════════════════════════════
#  VERI TIP TEMIZLIGI
# ═══════════════════════════════════════════════

# float → Int64 donusumu yapilacak kolonlar
_INT_COLUMNS = [
    "Ev Sahibi Gol",
    "Deplasman Gol",
    "Ev Sahibi Korner",
    "Deplasman Korner",
    "Toplam Korner",
    "Ev Sahibi Sari Kart",
    "Deplasman Sari Kart",
    "Toplam Sari Kart",
    "Ev Sahibi Kirmizi Kart",
    "Deplasman Kirmizi Kart",
    "Toplam Kirmizi Kart",
]


def clean_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Istatistik kolonlarini Int64'e cevir (.0 sorunu icin)."""
    for col in _INT_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
    return df


# ═══════════════════════════════════════════════
#  GECMIS VERI ISLEME
# ═══════════════════════════════════════════════


def _add_totals(df: pd.DataFrame) -> pd.DataFrame:
    """Toplam korner, kart kolonlarini hesapla."""
    pairs = [
        ("Ev Sahibi Korner", "Deplasman Korner", "Toplam Korner"),
        ("Ev Sahibi Sari Kart", "Deplasman Sari Kart", "Toplam Sari Kart"),
        ("Ev Sahibi Kirmizi Kart", "Deplasman Kirmizi Kart", "Toplam Kirmizi Kart"),
    ]
    for home_col, away_col, total_col in pairs:
        if home_col in df.columns and away_col in df.columns:
            df[total_col] = pd.to_numeric(
                df[home_col], errors="coerce"
            ) + pd.to_numeric(df[away_col], errors="coerce")
    return df


def _is_already_processed(df: pd.DataFrame) -> bool:
    """Cache'den okunan CSV zaten Turkce kolonlara sahip mi kontrol et."""
    return "Ev Sahibi" in df.columns and "Deplasman" in df.columns


def process_historical(df: pd.DataFrame) -> pd.DataFrame:
    """Ham CSV verisini isle: kolon esleme, toplam, margin, temizlik.

    Eger veri onceden islenmisse (cache'den), sadece tip temizligi yapar.
    """
    if df.empty:
        return df

    # Zaten islenmis veri ise tekrar esleme/margin yapma
    if _is_already_processed(df):
        df = _add_totals(df)
        return clean_dtypes(df)

    # Kolon esleme (ham Ingilizce → Turkce)
    cols = {k: v for k, v in COLUMN_MAPPING.items() if k in df.columns}
    if not cols:
        return pd.DataFrame()
    df = df[list(cols.keys())].rename(columns=cols)

    # Toplam kolonlar
    df = _add_totals(df)

    # Tip temizligi
    df = clean_dtypes(df)

    # Oran kolonlarina margin uygula
    odds_cols = [c for c in cols.values() if c not in INFO_COLUMNS]
    for c in odds_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce").apply(apply_margin)

    # Oran verisi olmayan satirlari at
    if "MS 1" in df.columns:
        df.dropna(subset=["MS 1"], inplace=True)

    return df


# ═══════════════════════════════════════════════
#  CANLI ORAN ISLEME
# ═══════════════════════════════════════════════


def process_odds(data: list[dict]) -> pd.DataFrame:
    """Odds API JSON'unu DataFrame'e donustur."""
    if not data:
        return pd.DataFrame()

    matches = []
    for m in data:
        home = m.get("home_team", "")
        away = m.get("away_team", "")
        date = m.get("commence_time", "")[:10]

        bkms = m.get("bookmakers", [])
        if not bkms:
            continue

        # bet365 tercih et
        bk = bkms[0]
        for b in bkms:
            if b.get("key") == "bet365":
                bk = b
                break

        row = {
            "Tarih": date,
            "Ev Sahibi": home,
            "Deplasman": away,
            "MS 1": None,
            "MS 0": None,
            "MS 2": None,
            "2.5 Ust": None,
            "2.5 Alt": None,
            "1.5 Ust": None,
            "1.5 Alt": None,
            "KG Var": None,
        }

        for mkt in bk.get("markets", []):
            key = mkt.get("key")
            for o in mkt.get("outcomes", []):
                name = o.get("name")
                price = o.get("price")
                point = o.get("point")

                if key == "h2h":
                    if name == home:
                        row["MS 1"] = price
                    elif name == away:
                        row["MS 2"] = price
                    elif name == "Draw":
                        row["MS 0"] = price

                elif key == "totals":
                    if point == 2.5:
                        row["2.5 Ust" if name == "Over" else "2.5 Alt"] = price
                    elif point == 1.5:
                        row["1.5 Ust" if name == "Over" else "1.5 Alt"] = price

        matches.append(row)

    if not matches:
        return pd.DataFrame()

    df = pd.DataFrame(matches)

    # Margin uygula
    odds_cols = [
        "MS 1",
        "MS 0",
        "MS 2",
        "2.5 Ust",
        "2.5 Alt",
        "1.5 Ust",
        "1.5 Alt",
        "KG Var",
    ]
    for c in odds_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").apply(apply_margin)

    # Tamamen bos kolonlari kaldir
    df.dropna(axis=1, how="all", inplace=True)
    return df


# ═══════════════════════════════════════════════
#  PUAN DURUMU
# ═══════════════════════════════════════════════


def calculate_standings(df: pd.DataFrame) -> pd.DataFrame:
    """Mac verilerinden lig puan durumunu hesapla."""
    required = ["Ev Sahibi", "Deplasman", "Ev Sahibi Gol", "Deplasman Gol"]
    if df.empty or not all(c in df.columns for c in required):
        return pd.DataFrame()

    standings = {}

    def init(team):
        if team not in standings:
            standings[team] = {
                "Takım": team,
                "Maç Sayısı": 0,
                "Galibiyet": 0,
                "Beraberlik": 0,
                "Mağlubiyet": 0,
                "Atılan": 0,
                "Yenilen": 0,
                "Averaj": 0,
                "Puan": 0,
            }

    for _, row in df.dropna(subset=["Ev Sahibi Gol", "Deplasman Gol"]).iterrows():
        home, away = row["Ev Sahibi"], row["Deplasman"]
        hg, ag = row["Ev Sahibi Gol"], row["Deplasman Gol"]

        if pd.isna(home) or pd.isna(away) or pd.isna(hg) or pd.isna(ag):
            continue

        init(home)
        init(away)

        # Mac sayisi ve goller
        standings[home]["Maç Sayısı"] += 1
        standings[away]["Maç Sayısı"] += 1
        standings[home]["Atılan"] += hg
        standings[away]["Atılan"] += ag
        standings[home]["Yenilen"] += ag
        standings[away]["Yenilen"] += hg

        # Sonuc → puan
        if hg > ag:
            standings[home]["Galibiyet"] += 1
            standings[away]["Mağlubiyet"] += 1
            standings[home]["Puan"] += 3
        elif hg < ag:
            standings[away]["Galibiyet"] += 1
            standings[home]["Mağlubiyet"] += 1
            standings[away]["Puan"] += 3
        else:
            standings[home]["Beraberlik"] += 1
            standings[away]["Beraberlik"] += 1
            standings[home]["Puan"] += 1
            standings[away]["Puan"] += 1

    # Averaj hesapla
    for t in standings.values():
        t["Averaj"] = t["Atılan"] - t["Yenilen"]

    result = pd.DataFrame(list(standings.values()))
    if result.empty:
        return result

    # Puan > Averaj > Atilan Gol siralamasiyla siralama
    result = result.sort_values(
        by=["Puan", "Averaj", "Atılan"], ascending=False
    ).reset_index(drop=True)
    result.index = result.index + 1
    return result


# ═══════════════════════════════════════════════
#  CACHE YARDIMCILARI
# ═══════════════════════════════════════════════


def get_standings_cache_key() -> str:
    """Her gun 06:00 ve 18:00'de degisen cache anahtari."""
    now = datetime.datetime.now()
    if now.hour < 6:
        d = (now.date() - datetime.timedelta(days=1)).isoformat()
        return f"{d}_18"
    elif now.hour < 18:
        return f"{now.date().isoformat()}_06"
    else:
        return f"{now.date().isoformat()}_18"


# ═══════════════════════════════════════════════
#  CACHED VERI ERISIM FONKSIYONLARI
#  (app.py bu fonksiyonlari cagirir)
# ═══════════════════════════════════════════════


def fetch_and_process(league: str, season: str, force: bool = False) -> pd.DataFrame:
    """CSV indir → isle → kaydet. Force=True cache'i atlar."""
    raw = fetch_csv(league, season, force=force)
    if raw.empty:
        return raw
    df = process_historical(raw)
    if not df.empty:
        save_csv(df, league, season)
    return df


@st.cache_data(show_spinner=False, ttl=3600)
def get_season_data(league: str, season: str) -> pd.DataFrame:
    """Gecmis sezon verisi (1 saat cache)."""
    return fetch_and_process(league, season, force=False)


@st.cache_data(show_spinner=False)
def get_league_standings(league: str, season: str, cache_key: str) -> pd.DataFrame:
    """Puan durumu (cache_key degistiginde yenilenir)."""
    df = fetch_and_process(league, season, force=False)
    return calculate_standings(df)


@st.cache_data(ttl=3600, show_spinner=False)
def get_upcoming_fixtures(league: str) -> pd.DataFrame:
    """Yaklasan maclar ve oranlar (1 saat cache)."""
    data = fetch_odds_api(league)
    return process_odds(data)
