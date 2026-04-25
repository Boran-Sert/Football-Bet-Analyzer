"""Analiz endpointleri.

rules.md Madde 2: Router sadece HTTP istegini alir, Pydantic ile dogrular,
Service katmanina paslar ve JSON doner.
rules.md Madde 3: Service Depends() ile enjekte edilir.
rules.md Madde 5: Rate limiter tum endpointlerde aktif.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from core.database import mongo
from middlewares.rate_limiter import rate_limit
from repositories.match_repository import MatchRepository
from schemas.match import MatchResponse, AnalysisResult
from services.analysis_service import AnalysisService

router = APIRouter(
    prefix="/api/v1",
    tags=["analysis"],
    dependencies=[Depends(rate_limit)],
)


# ═══════════════════════════════════════════════
#  DEPENDENCY INJECTION FACTORY'LER
# ═══════════════════════════════════════════════


def get_analysis_service() -> AnalysisService:
    """AnalysisService'i Depends() ile enjekte etmek icin factory.

    rules.md Madde 3: Global singleton import etmek yasaktir.
    """
    repo = MatchRepository(mongo.db)
    return AnalysisService(repo)


# ═══════════════════════════════════════════════
#  ENDPOINTLER
# ═══════════════════════════════════════════════


@router.get(
    "/matches/{match_id}",
    response_model=MatchResponse,
    summary="Tek bir maci getir",
)
async def get_match(
    match_id: str,
    service: AnalysisService = Depends(get_analysis_service),
):
    """Belirtilen ID'ye sahip maci dondurur."""
    match = await service.get_match_by_id(match_id)
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mac bulunamadi.",
        )
    return match


@router.get(
    "/analysis/{match_id}",
    response_model=AnalysisResult,
    summary="Mac icin benzerlik analizi",
)
async def analyze_match(
    match_id: str,
    top_n: int = Query(default=5, ge=1, le=20, description="Benzer mac sayisi"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """Belirtilen mac icin gecmis verilerden benzerlik analizi yapar."""
    result = await service.analyze_match(match_id, top_n=top_n)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mac bulunamadi veya yeterli gecmis veri yok.",
        )
    return result


@router.get(
    "/matches",
    response_model=list[MatchResponse],
    summary="Maclari listele",
)
async def list_matches(
    league: Optional[str] = Query(default=None, description="Lig filtresi"),
    season: Optional[str] = Query(default=None, description="Sezon filtresi (orn: 2024-2025)"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Durum filtresi (finished/scheduled)"),
    limit: int = Query(default=50, ge=1, le=200, description="Maksimum mac sayisi"),
    service: AnalysisService = Depends(get_analysis_service),
):
    """Maclari filtrelerle listeler. Filtre verilmezse son 50 maci dondurur."""
    query = {}
    if league:
        query["league"] = league
    if season:
        query["season"] = season
    if status_filter:
        query["status"] = status_filter

    docs = await service.repo.find_many(
        query, sort=[("match_date", -1)], limit=limit
    )
    return [AnalysisService._to_response(d) for d in docs]

