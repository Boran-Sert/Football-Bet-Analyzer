"""Mac veri transfer objeleri (DTO).

MatchEntity: Adapter ciktisi, sistemin ortak dili.
MatchInDB: MongoDB dokuman formati.
MatchResponse: API yanit formati.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, GetCoreSchemaHandler
from pydantic_core import core_schema
from bson import ObjectId

class PyObjectId(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.union_schema([
                core_schema.is_instance_schema(ObjectId),
                core_schema.str_schema(),
            ]),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )



class MatchStatus(str, Enum):
    """Mac durumu."""
    UPCOMING = "upcoming"
    LIVE = "live"
    COMPLETED = "completed"


class MatchSource(str, Enum):
    """Veri kaynagi."""
    ODDS_API = "odds_api"
    FOOTBALL_DATA_CSV = "football_data_csv"


# ═══════════════════════════════════════════════
#  ORAN SCHEMALARI (Sadeleştirilmiş)
#  Sadece: h2h, totals, btts
# ═══════════════════════════════════════════════

class H2HOdds(BaseModel):
    """Maç Sonucu 1-X-2 oranları."""
    home: float
    draw: float
    away: float

class TotalsOdds(BaseModel):
    """Alt/Üst gol oranları."""
    over_1_5: float | None = None
    under_1_5: float | None = None
    over_2_5: float | None = None
    under_2_5: float | None = None
    over_3_5: float | None = None
    under_3_5: float | None = None

class BTTSOdds(BaseModel):
    """Karşılıklı Gol (BTTS) oranları."""
    yes: float | None = None
    no: float | None = None


class MatchOdds(BaseModel):
    """Bir maçın tüm oran verileri."""
    h2h: H2HOdds | None = None
    totals: TotalsOdds | None = None
    btts: BTTSOdds | None = None

    model_config = {"extra": "allow"}


# ═══════════════════════════════════════════════
#  MAÇ METRİKLERİ (İstatistikler)
# ═══════════════════════════════════════════════

class MatchMetrics(BaseModel):
    """Tamamlanmış maçların istatistikleri."""
    home_goals: int | None = None
    away_goals: int | None = None
    total_goals: int | None = None
    
    home_ht_goals: int | None = None
    away_ht_goals: int | None = None

    home_corners: int | None = None
    away_corners: int | None = None
    total_corners: int | None = None
    
    home_yellow: int | None = None
    away_yellow: int | None = None
    total_yellow: int | None = None
    
    home_red: int | None = None
    away_red: int | None = None
    total_red: int | None = None


# ═══════════════════════════════════════════════
#  ANA MAÇ MODELLERİ
# ═══════════════════════════════════════════════

class MatchEntity(BaseModel):
    """Adapter ciktisi — sistemin standart mac formati.

    Tum dis kaynaklar bu formata donusturulur.
    `metrics` alani spor-bagimsiz esneklik saglar.
    """

    external_id: str = Field(..., description="Benzersiz kaynak ID (API event id veya CSV hash)")
    sport: str = Field(default="football")
    league_key: str = Field(..., description="Odds API sport key: soccer_epl, soccer_turkey_super_league, ...")
    league_title: str = Field(default="", description="Insan-okunur lig adi: Premier League")
    home_team: str = Field(..., description="Normalize edilmis ev sahibi takim")
    away_team: str = Field(..., description="Normalize edilmis deplasman takimi")
    commence_time: datetime = Field(..., description="Mac baslama zamani (UTC)")
    status: MatchStatus = Field(default=MatchStatus.UPCOMING)
    odds: MatchOdds = Field(
        default_factory=MatchOdds,
        description="Oran verileri: h2h, totals (2.5 ust/alt), btts",
    )
    metrics: MatchMetrics = Field(
        default_factory=MatchMetrics,
        description="Spor-ozel istatistikler: goller, kartlar, kornerler, iy skoru",
    )
    source: MatchSource = Field(default=MatchSource.ODDS_API)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class MatchInDB(MatchEntity):
    """MongoDB'deki dokuman formati. _id MongoDB tarafindan eklenir."""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }



class MatchResponse(BaseModel):
    """API yanit formati. Hassas alanlar cikarilmis hali."""

    external_id: str
    sport: str
    league_key: str
    league_title: str
    home_team: str
    away_team: str
    commence_time: datetime
    status: MatchStatus
    odds: MatchOdds
    metrics: MatchMetrics

    model_config = {"from_attributes": True}


class MatchListResponse(BaseModel):
    """Sayfalanmis mac listesi yaniti."""

    data: list[MatchResponse]
    total: int
    page: int
    per_page: int
