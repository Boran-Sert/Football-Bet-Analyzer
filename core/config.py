"""Uygulama yapilandirmasi."""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import ClassVar


class TierLimits:
    similar_matches: ClassVar[dict[str, int]] = {
        "standard": 3,
        "pro": 10,
        "elite": 20,
    }

    rate_limit_per_minute: ClassVar[dict[str, int]] = {
        "standard": 60,
        "pro": 300,
        "elite": 1000,
    }

    # Hard cap for superuser limit_override (GAP 5 fix)
    superuser_max_limit: ClassVar[int] = 100

    @classmethod
    def get_similar_limit(cls, tier: str) -> int:
        return cls.similar_matches.get(tier, cls.similar_matches["standard"])

    @classmethod
    def get_rate_limit(cls, tier: str) -> int:
        return cls.rate_limit_per_minute.get(tier, cls.rate_limit_per_minute["standard"])


class Settings(BaseSettings):
    # ── Database ──
    MONGO_URI: str
    REDIS_URL: str = "redis://localhost:6379"

    # ── External APIs ──
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

    # ── Stripe (GAP 4) ──────────────────────────────────────────────────────
    # Get these from https://dashboard.stripe.com/apikeys
    STRIPE_SECRET_KEY: str = ""
    # Get this from https://dashboard.stripe.com/webhooks
    STRIPE_WEBHOOK_SECRET: str = ""
    # Get these from https://dashboard.stripe.com/products (after creating products)
    STRIPE_PRICE_PRO: str = ""    # e.g. price_1ABC...
    STRIPE_PRICE_ELITE: str = ""  # e.g. price_1XYZ...

    # ── Iyzico (GAP 7) ──────────────────────────────────────────────────────
    IYZICO_API_KEY: str = ""
    IYZICO_SECRET_KEY: str = ""
    IYZICO_BASE_URL: str = "sandbox-api.iyzipay.com"  # Iyzico SDK HTTPSConnection için protokol içermemeli

    # ── Scheduler ──
    SCHEDULER_SLOTS: list[dict] = [
        {"hour": 14, "minute": 0},
        {"hour": 18, "minute": 0},
    ]

    # ── Active sports ──
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
        "soccer_belgium_first_div",
    ]
    
    @field_validator("IYZICO_BASE_URL", mode="before")
    @classmethod
    def sanitize_iyzico_url(cls, v: str) -> str:
        if not v:
            return v
        return v.replace("https://", "").replace("http://", "").rstrip("/")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
