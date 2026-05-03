"""Analiz ve benzerlik API yonlendiricisi."""

from fastapi import Query
from fastapi import APIRouter, Depends, Request

from middleware.rate_limiter import RateLimiter
from schemas.auth import UserInDB
from services.analysis_service import AnalysisService
from utils.dependencies import get_analysis_service, get_current_active_user

router = APIRouter(prefix="/api/v1/football/analysis", tags=["Football Analysis"])


@router.get("/similar/{match_id}")
async def get_similar_matches(
    request: Request,
    match_id: str,
    limit: int | None = Query(None, ge=1, le=100),
    current_user: UserInDB = Depends(get_current_active_user),
    service: AnalysisService = Depends(get_analysis_service),
):
    await RateLimiter()(request)

    results = await service.find_similar_matches(
        target_match_id=match_id,
        user_tier=current_user.tier,
        is_superuser=current_user.is_superuser,
        limit_override=limit,
    )
    return results
