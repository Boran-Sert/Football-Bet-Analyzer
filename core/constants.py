"""Uygulama sabitleri: lig tanimlari, takim eslestirmeleri, marj degeri.

Eski config.py dosyasindan tasinmistir.
Cevre degiskenleri burada BULUNMAZ (onlar core/config.py'de).
"""

from datetime import datetime, timezone


# ═══════════════════════════════════════════════
#  IS MANTIGI SABITLERI
# ═══════════════════════════════════════════════

TURKISH_TAX_MARGIN = 0.865


# ═══════════════════════════════════════════════
#  TAKIM ISMI ESLESMELERI
# ═══════════════════════════════════════════════

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


# ═══════════════════════════════════════════════
#  LIG TANIMLARI
# ═══════════════════════════════════════════════

SUPPORTED_LEAGUES = {
    "Türkiye Süper Lig": {
        "api_football_id": 203,
        "fd_code": "T1",
    },
    "İngiltere Premier Lig": {
        "api_football_id": 39,
        "fd_code": "E0",
    },
    "İspanya La Liga": {
        "api_football_id": 140,
        "fd_code": "SP1",
    },
    "İtalya Serie A": {
        "api_football_id": 135,
        "fd_code": "I1",
    },
    "Almanya Bundesliga": {
        "api_football_id": 78,
        "fd_code": "D1",
    },
    "Fransa Ligue 1": {
        "api_football_id": 61,
        "fd_code": "F1",
    },
}


# ═══════════════════════════════════════════════
#  SEZON YARDIMCILARI
# ═══════════════════════════════════════════════


def get_current_season() -> str:
    """Aktif sezonu hesaplar. Agustos ve sonrasi → yeni sezon."""
    now = datetime.now(timezone.utc)
    year = now.year if now.month >= 8 else now.year - 1
    return f"{year}-{year + 1}"


def get_seasons(count: int = 6) -> list[str]:
    """Guncel sezondan geriye dogru 'count' adet sezon listesi dondurur."""
    current = get_current_season()
    start_year = int(current[:4])
    return [f"{start_year - i}-{start_year - i + 1}" for i in range(count)]
