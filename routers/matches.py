"""Mac ve Lig listeleme API yonlendiricisi."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, HTTPException

from middleware.rate_limiter import RateLimiter
from schemas.match import MatchResponse, MatchListResponse
from services.match_service import MatchService
from utils.dependencies import get_match_service

router = APIRouter(prefix="/api/v1/football/matches", tags=["Football Matches"])


@router.get("/", response_model=MatchListResponse, dependencies=[Depends(RateLimiter())])
async def get_upcoming_matches(
    league: str | None = Query(None, description="Lig koduna gore filtrele (orn: soccer_epl)"),
    page: int = Query(1, ge=1, description="Sayfa numarasi"),
    per_page: int = Query(20, ge=1, le=100, description="Sayfa basina mac sayisi"),
    service: MatchService = Depends(get_match_service)
):
    """Yaklasan futbol maclarini listeler (Onbellekli)."""
    skip = (page - 1) * per_page
    
    matches = await service.get_upcoming_matches(
        sport="football",
        league_key=league,
        limit=per_page,
        skip=skip
    )
    
    # Gercek total sayisini almak icin count sorgusu yapilabilir, 
    # simdilik list uzunluguna gore tahmin yurutebilir veya ayri bir count sorgusu cagirabiliriz.
    total = await service.repo.count_matches({"status": "upcoming", "sport": "football"} | ({"league_key": league} if league else {}))

    return {
        "data": matches,
        "total": total,
        "page": page,
        "per_page": per_page
    }


@router.get("/leagues", response_model=list[str], dependencies=[Depends(RateLimiter())])
async def get_leagues(service: MatchService = Depends(get_match_service)):
    """Sistemde aktif verisi bulunan ligleri listeler."""
    return await service.get_available_leagues(sport="football")


@router.get("/{match_id}", response_model=MatchResponse, dependencies=[Depends(RateLimiter())])
async def get_match_detail(
    match_id: str,
    service: MatchService = Depends(get_match_service)
):
    """Tekil mac detayini getirir."""
    match = await service.get_match_by_id(match_id)
    if not match:
        raise HTTPException(status_code=404, detail="Mac bulunamadi")
    return match
