"""Stripe odeme ve abonelik API yonlendiricisi.

Endpoints:
  POST /api/v1/billing/checkout         — Odeme oturumu olustur
  POST /api/v1/billing/webhook          — Stripe webhook alici
  GET  /api/v1/billing/plans            — Mevcut planlari listele
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from core.config import settings
from core.database import mongo
from repositories.user_repository import UserRepository
from schemas.auth import UserInDB
from services.billing_service import BillingService
from utils.dependencies import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])


# ── Dependencies ──────────────────────────────────────────────────────────────

async def get_billing_service() -> BillingService:
    db = mongo.get_db()
    return BillingService(user_repo=UserRepository(db))


# ── Schemas ───────────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    price_id: str  # Stripe Price ID (stripe_price_pro veya stripe_price_elite)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/plans")
async def get_plans():
    """Frontend icin mevcut planlari ve fiyat ID'lerini dondurur."""
    return [
        {
            "name": "Pro",
            "tier": "pro",
            "price_id": settings.STRIPE_PRICE_PRO,
            "features": ["10 benzer mac analizi", "200 istek/dk", "Lig filtreleme"],
        },
        {
            "name": "Elite",
            "tier": "elite",
            "price_id": settings.STRIPE_PRICE_ELITE,
            "features": ["20 benzer mac analizi", "1000 istek/dk", "Oncelikli destek"],
        },
    ]


@router.post("/checkout")
async def create_checkout_session(
    body: CheckoutRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    billing_service: BillingService = Depends(get_billing_service),
):
    """Stripe Checkout oturumu olusturur. Kullanicinin mevcut tier'inin ustuyle satinalma yapilabilir."""
    allowed_prices = {settings.STRIPE_PRICE_PRO, settings.STRIPE_PRICE_ELITE}
    if body.price_id not in allowed_prices:
        raise HTTPException(status_code=400, detail="Gecersiz price_id.")

    try:
        checkout_url = billing_service.create_checkout_session(
            user_id=current_user.id,
            user_email=current_user.email,
            price_id=body.price_id,
        )
        return {"checkout_url": checkout_url}
    except Exception as exc:
        logger.error("Stripe checkout hatasi: %s", exc)
        raise HTTPException(status_code=500, detail="Odeme oturumu olusturulamadi.")


@router.post("/webhook", status_code=200)
async def stripe_webhook(
    request: Request,
    billing_service: BillingService = Depends(get_billing_service),
):
    """Stripe'dan gelen webhook olaylarini alir ve isler.
    
    Stripe Dashboard'da bu endpoint'i ekleyin:
      https://yourdomain.com/api/v1/billing/webhook
    
    Gerekli olaylar:
      - checkout.session.completed
      - customer.subscription.deleted
      - customer.subscription.paused
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        await billing_service.handle_webhook(payload, sig_header)
        return {"status": "ok"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
