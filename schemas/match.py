"""Mac verileri icin Pydantic v2 sema tanimlari.

API yanitlari (Response) ve veritabani modelleri ayri tutulur.
rules.md Madde 2: DB modelleri ve API yanitlari kesinlikle ayrilacaktir.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════
#  VERITABANI MODELLERI (MongoDB'ye yazilan)
# ═══════════════════════════════════════════════


class MatchInDB(BaseModel):
    """MongoDB'deki matches koleksiyonundaki belge yapisi."""

    home_team: str
    away_team: str
    league: str
    season: str
    match_date: datetime
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None

    odds_home: Optional[float] = None
    odds_draw: Optional[float] = None
    odds_away: Optional[float] = None
    odds_over_25: Optional[float] = None
    odds_under_25: Optional[float] = None

    status: str = "scheduled"
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ═══════════════════════════════════════════════
#  API YANIT SEMALARI (Kullaniciya donen)
# ═══════════════════════════════════════════════


class MatchResponse(BaseModel):
    """Tek bir mac icin API yanit semasi."""

    id: str
    home_team: str
    away_team: str
    league: str
    match_date: datetime
    home_goals: Optional[int] = None
    away_goals: Optional[int] = None

    odds_home: Optional[float] = None
    odds_draw: Optional[float] = None
    odds_away: Optional[float] = None
    odds_over_25: Optional[float] = None
    odds_under_25: Optional[float] = None

    status: str


class AnalysisResult(BaseModel):
    """Benzerlik analizi sonucu icin API yanit semasi."""

    target_match: MatchResponse
    similar_matches: list[MatchResponse]
    home_win_pct: float = Field(description="Ev sahibi galibiyet yuzdesi")
    draw_pct: float = Field(description="Beraberlik yuzdesi")
    away_win_pct: float = Field(description="Deplasman galibiyet yuzdesi")
    avg_total_goals: float = Field(description="Ortalama toplam gol")
