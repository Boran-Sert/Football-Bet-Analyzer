"""Oran veri transfer objeleri."""

from pydantic import BaseModel


class OutcomeOdds(BaseModel):
    """Tek bir sonucun orani (orn: Home, Draw, Away)."""
    name: str
    price: float
    point: float | None = None  # totals/spreads icin


class MarketOdds(BaseModel):
    """Bir pazar turundeki tum sonuclar (orn: h2h)."""
    key: str  # "h2h", "totals", "spreads"
    outcomes: list[OutcomeOdds]


class BookmakerOdds(BaseModel):
    """Tek bir bahis sitesinin oranlari."""
    key: str
    title: str
    last_update: str
    markets: list[MarketOdds]
