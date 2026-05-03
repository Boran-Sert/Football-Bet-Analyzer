"""Odeme ve abonelik API yonlendiricisi — Provider Agnostic."""

import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Request

from core.pricing import PLANS
from core.database import mongo
from repositories.user_repository import UserRepository
from schemas.auth import UserInDB, UserTier
from services.billing_service import BillingService
from utils.dependencies import get_current_active_user
from fastapi.responses import RedirectResponse
from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/billing", tags=["Billing"])


# ── Dependencies ──────────────────────────────────────────────────────────────

from services.payment.factory import PaymentProviderFactory


async def get_billing_service() -> BillingService:
    db = mongo.get_db()

    # Faz 6 Fix: Strategy Pattern Factory kullanimi
    provider = PaymentProviderFactory.get_provider(settings.PAYMENT_PROVIDER)

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
        if not current_user.id:
            raise HTTPException(status_code=401, detail="User identity is incomplete.")

        checkout_url = await billing_service.create_checkout_session(
            user_id=current_user.id,
            user_email=current_user.email,
            plan_id=body.plan_id,
            identity_number=body.identity_number,
            ip=ip,
            registration_date=current_user.created_at,
            last_login_date=current_user.last_login_at,
        )
        return {"checkout_url": checkout_url}
    except Exception as exc:
        logger.error(
            "Checkout hatasi [User: %s]: %s", current_user.email, exc, exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Ödeme oturumu başlatılamadı. Lütfen daha sonra tekrar deneyiniz.",
        )


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
        raise HTTPException(
            status_code=400, detail="Bu email adresi zaten kullaniliyor."
        )

    try:
        ip = request.client.host if request.client else "127.0.0.1"
        reg_data = {
            "email": body.email,
            "password": body.password,
            "display_name": body.display_name,
            "identity_number": body.identity_number,
            "ip": ip,
        }
        checkout_url = await billing_service.initialize_guest_checkout(
            reg_data, body.plan_id
        )
        return {"checkout_url": checkout_url}
    except Exception as exc:
        logger.error(
            "Guest Checkout hatasi [Email: %s]: %s", body.email, exc, exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Ödeme ve kayıt işlemi başlatılamadı. Lütfen bilgilerinizi kontrol edip tekrar deneyiniz.",
        )


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

    # Idempotency Kontrolü (Faz 5 Fix: Provider-Specific Unique ID + Atomic SET NX)
    # Iyzico 'token' veya 'paymentId' gönderir. Stripe 'id' (event id) gönderir.
    unique_id = (
        payload.get("token")
        or payload.get("paymentId")
        or payload.get("id")
        or headers.get("X-Idempotency-Key")
    )

    if unique_id:
        from core.redis_client import redis_manager

        redis = redis_manager.get_client()
        lock_key = f"idempotency:billing:{unique_id}"

        # Atomic SET NX: Sadece anahtar yoksa yaz ve True dön. (Race condition engellenir)
        is_new = await redis.set(
            lock_key, "processing", ex=300, nx=True
        )  # Başlangıçta 5 dk kilit
        if not is_new:
            current_status = await redis.get(lock_key)
            if current_status == "processing":
                logger.warning("Webhook hala isleniyor (409): %s", unique_id)
                raise HTTPException(
                    status_code=409,
                    detail="Payment is currently being processed. Please try again later.",
                )

            logger.info(
                "Mükerrer webhook isteği engellendi (Already processed): %s", unique_id
            )
            return {"status": "already_processed"}

    try:
        success = await billing_service.handle_webhook(payload, headers)

        if success:
            if unique_id:
                # İşlem başarılıysa kilidi 24 saate uzat (artık 'processed')
                await redis.setex(lock_key, 86400, "processed")

            return RedirectResponse(
                url=f"{settings.FRONTEND_URL}/login?payment=success", status_code=303
            )
        else:
            # İşlem başarısızsa kilidi kaldır (retry için)
            if unique_id:
                await redis.delete(lock_key)
    except Exception as e:
        logger.error("Webhook işleme hatası: %s", str(e))
        if unique_id:
            await redis.delete(lock_key)
        raise HTTPException(status_code=500, detail="Webhook processing failed")

    # Başarısızsa planlar sayfasina hata ile don
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/pricing?error=payment_failed", status_code=303
    )
