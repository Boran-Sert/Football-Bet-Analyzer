"""Uygulama yapilandirmasi.

Tum cevresel degiskenler Pydantic BaseSettings ile dogrulanir.
Kullanici tier limitleri buradan merkezi olarak yonetilir.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import ClassVar


class TierLimits:
    """Kullanici katmani (tier) bazli limitler.

    Bu sinifi degistirerek tum uygulamadaki tier limitlerini
    tek noktadan yonetebilirsin.

    Attributes:
        similar_matches: Her tier icin max benzer mac sayisi.
            -1 = sinirsiz
        rate_limit_per_minute: Her tier icin dakikadaki istek limiti.
    """

    similar_matches: ClassVar[dict[str, int]] = {
        "free": 3,
        "pro": 10,
        "elite": 20,
    }

    rate_limit_per_minute: ClassVar[dict[str, int]] = {
        "free": 60,
        "pro": 200,
        "elite": 1000,
    }

    @classmethod
    def get_similar_limit(cls, tier: str) -> int:
        """Verilen tier icin max benzer mac limitini dondurur."""
        return cls.similar_matches.get(tier, cls.similar_matches["free"])

    @classmethod
    def get_rate_limit(cls, tier: str) -> int:
        """Verilen tier icin dakika basina istek limitini dondurur."""
        return cls.rate_limit_per_minute.get(tier, cls.rate_limit_per_minute["free"])


class Settings(BaseSettings):
    """Uygulama ayarlari. .env dosyasindan otomatik yuklenir."""

    # ── Veritabani ──
    MONGO_URI: str
    REDIS_URL: str = "redis://localhost:6379"

    # ── Dis API Anahtarlari ──
    ODDS_API_KEY: str
    FOOTBALL_DATA_API_KEY: str = ""

    # ── JWT ──
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_EXPIRE_DAYS: int = 7

    # ── Email (Resend) ──
    RESEND_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    # ── Scheduler (UTC saatleri — TR 17:00 = UTC 14:00, TR 21:00 = UTC 18:00) ──
    SCHEDULER_SLOTS: list[dict] = [
        {"hour": 14, "minute": 0},
        {"hour": 18, "minute": 0},
    ]

    # ── Aktif Sporlar ──
    ACTIVE_SPORTS: list[str] = Field(default=["football"])

    # ── CORS ──
    ALLOWED_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )

    # ── Odds API ──
    ODDS_API_BASE_URL: str = "https://api.the-odds-api.com/v4"
    ODDS_API_REGIONS: str = "eu,uk"
    ODDS_API_MARKETS: str = "h2h,totals,btts"
    TARGET_LEAGUES: list[str] = [
        "soccer_epl", "soccer_efl_champ",
        "soccer_spain_la_liga", "soccer_spain_segunda_division",
        "soccer_germany_bundesliga", "soccer_germany_bundesliga2",
        "soccer_italy_serie_a", "soccer_italy_serie_b",
        "soccer_france_ligue_one", "soccer_france_ligue_two",
        "soccer_turkey_super_league",
        "soccer_netherlands_eredivisie",
        "soccer_belgium_first_div"
    ]
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings nesnesi
settings = Settings()
