"""Yonetici (Admin) API yonlendiricisi (God Mode)."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel

from schemas.auth import UserInDB, UserTier
from services.auth_service import AuthService
from tasks.ingestion import fetch_upcoming_matches
from utils.dependencies import get_auth_service, require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["Admin (God Mode)"])


class TierUpdateRequest(BaseModel):
    tier: UserTier


@router.put("/users/{user_id}/tier")
async def update_user_tier(
    user_id: str,
    request: TierUpdateRequest,
    current_admin: UserInDB = Depends(require_admin),
    auth_service: AuthService = Depends(get_auth_service)
):
    """(Admin) Istedigin kullanicinin abonelik katmanini (tier) manuel degistirir."""
    # Kullaniciyi bul
    user = await auth_service.repo.get_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanici bulunamadi.")
        
    success = await auth_service.repo.update_tier(user_id, request.tier)
    if not success:
        raise HTTPException(status_code=500, detail="Katman guncellenemedi.")
        
    return {"message": f"Kullanici katmani {request.tier.value} olarak guncellendi."}


@router.post("/system/trigger-ingestion")
async def trigger_ingestion(
    background_tasks: BackgroundTasks,
    current_admin: UserInDB = Depends(require_admin)
):
    """(Admin) Veri cekme (cron job) islemini beklemeden manuel tetikler."""
    # fetch_upcoming_matches zaten icinde Redis lock barindirir.
    # Eger halihazirda calisiyorsa kilit yuzunden sorunsuzca atlar.
    background_tasks.add_task(fetch_upcoming_matches)
    
    return {"message": "Ingestion gorevi arka planda baslatildi."}
