"""Odeme ve abonelik API yonlendiricisi — Provider Agnostic."""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request

from core.pricing import PLANS
from core.database import mongo
from repositories.user_repository import UserRepository
from schemas.auth import UserInDB, UserTier
from services.billing_service import BillingService
from services.payment.iyzico_provider import IyzicoProvider
from services.payment.stripe_provider import StripeProvider
from utils.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])


# ── Dependencies ──────────────────────────────────────────────────────────────

async def get_billing_service() -> BillingService:
    db = mongo.get_db()
    # Varsayilan olarak Iyzico kullaniyoruz. 
    # Ileride settings'den provider seçilebilir: settings.PAYMENT_PROVIDER
    provider = IyzicoProvider() 
    return BillingService(user_repo=UserRepository(db), provider=provider)


# ── Schemas ───────────────────────────────────────────────────────────────────

from pydantic import BaseModel
class CheckoutRequest(BaseModel):
    plan_id: str  # "pro" veya "elite"
    identity_number: str = "11111111111"  # Default test value


class GuestCheckoutRequest(BaseModel):
    plan_id: str
    email: str
    password: str
    display_name: str
    identity_number: str = "11111111111"


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/plans")
async def get_plans():
    """Frontend icin mevcut planlari dondurur."""
    return [
        {
            "id": key,
            "name": val["name"],
            "tier": val["tier"],
            "price_try": val["price_try"],
            "features": val["features"],
        }
        for key, val in PLANS.items()
    ]


@router.post("/checkout")
async def create_checkout_session(
    request: Request,
    body: CheckoutRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    billing_service: BillingService = Depends(get_billing_service),
):
    """Odeme oturumu olusturur."""
    if body.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Gecersiz plan_id.")

    try:
        ip = request.client.host if request.client else "127.0.0.1"
        checkout_url = await billing_service.create_checkout_session(
            user_id=current_user.id,
            user_email=current_user.email,
            plan_id=body.plan_id,
            identity_number=body.identity_number,
            ip=ip,
            registration_date=current_user.created_at,
            last_login_date=current_user.last_login_at
        )
        return {"checkout_url": checkout_url}
    except Exception as exc:
        logger.error("Checkout hatasi [User: %s]: %s", current_user.email, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Ödeme oturumu başlatılamadı. Lütfen daha sonra tekrar deneyiniz.")


@router.post("/guest-checkout")
async def initialize_guest_checkout(
    request: Request,
    body: GuestCheckoutRequest,
    billing_service: BillingService = Depends(get_billing_service),
):
    """Kayit ve odeme islemini birlikte baslatir (Kullanici henuz DB'de yok)."""
    if body.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Gecersiz plan_id.")

    # Email kontrolü
    existing = await billing_service.repo.get_by_email(body.email)
    if existing:
        raise HTTPException(status_code=400, detail="Bu email adresi zaten kullaniliyor.")

    try:
        ip = request.client.host if request.client else "127.0.0.1"
        reg_data = {
            "email": body.email,
            "password": body.password,
            "display_name": body.display_name,
            "identity_number": body.identity_number,
            "ip": ip
        }
        checkout_url = await billing_service.initialize_guest_checkout(reg_data, body.plan_id)
        return {"checkout_url": checkout_url}
    except Exception as exc:
        logger.error("Guest Checkout hatasi [Email: %s]: %s", body.email, exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Ödeme ve kayıt işlemi başlatılamadı. Lütfen bilgilerinizi kontrol edip tekrar deneyiniz.")


from fastapi.responses import RedirectResponse
from core.config import settings

@router.post("/webhook")
async def billing_webhook(
    request: Request,
    billing_service: BillingService = Depends(get_billing_service),
):
    """Odeme saglayicidan gelen webhook/callback olaylarini isler ve kullanıcıyı yönlendirir."""
    # Iyzico'da callback POST ile gelir, Stripe'da JSON payload gelir.
    try:
        payload = await request.json()
    except (json.JSONDecodeError, Exception) as e:
        logger.debug("JSON parse hatasi, form datasi deneniyor: %s", e)
        payload = await request.form()
        payload = dict(payload)

    headers = request.headers
    
    success = await billing_service.handle_webhook(payload, headers)
    
    if success:
        # Odeme basariliysa giris sayfasina yonlendir (veya dashboard)
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/login?payment=success", 
            status_code=303
        )
    
    # Basarisizsa planlar sayfasina hata ile don
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/pricing?error=payment_failed", 
        status_code=303
    )
