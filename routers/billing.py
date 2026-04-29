"""Odeme ve abonelik API yonlendiricisi — Provider Agnostic."""

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
    body: CheckoutRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    billing_service: BillingService = Depends(get_billing_service),
):
    """Odeme oturumu olusturur."""
    if body.plan_id not in PLANS:
        raise HTTPException(status_code=400, detail="Gecersiz plan_id.")

    try:
        checkout_url = await billing_service.create_checkout_session(
            user_id=current_user.id,
            user_email=current_user.email,
            plan_id=body.plan_id,
        )
        return {"checkout_url": checkout_url}
    except Exception as exc:
        logger.error("Checkout hatasi: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/webhook")
async def billing_webhook(
    request: Request,
    billing_service: BillingService = Depends(get_billing_service),
):
    """Odeme saglayicidan gelen webhook/callback olaylarini isler."""
    # Iyzico'da callback POST ile gelir, Stripe'da JSON payload gelir.
    # BaseProvider her ikisini de handle edecek sekilde tasarlandi.
    
    # Payload'u her ihtimale karsi hem form hem json olarak deniyoruz
    try:
        payload = await request.json()
    except:
        payload = await request.form()
        payload = dict(payload)

    headers = request.headers
    
    success = await billing_service.handle_webhook(payload, headers)
    if success:
        return {"status": "ok"}
    
    raise HTTPException(status_code=400, detail="Webhook islenemedi.")
