"""Analiz ve benzerlik API yonlendiricisi."""

from fastapi import APIRouter, Depends, HTTPException, Query

from middleware.rate_limiter import RateLimiter
from schemas.auth import UserInDB
from services.analysis_service import AnalysisService
from utils.dependencies import get_analysis_service, get_current_active_user

router = APIRouter(prefix="/api/v1/football/analysis", tags=["Football Analysis"])


@router.get("/similar/{match_id}", dependencies=[Depends(RateLimiter())])
async def get_similar_matches(
    match_id: str,
    limit: int | None = Query(None, ge=1, le=20, description="PRO/ELITE kullanicilar icin ozel limit belirleme"),
    current_user: UserInDB = Depends(get_current_active_user),
    service: AnalysisService = Depends(get_analysis_service)
):
    """
    Yaklasan bir macin oranlarina en benzeyen gecmis maclari bulur.
    Kullanicinin tier'ina gore (STANDARD, PRO, ELITE) sonuclar sinirlandirilir.
    """
    results = await service.find_similar_matches(
        target_match_id=match_id,
        user_tier=current_user.tier,
        is_superuser=current_user.is_superuser,
        limit_override=limit
    )
    
    # Sonuclari dondur (Bos olabilir, Frontend bunu handle eder)
    return results
