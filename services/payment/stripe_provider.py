"""Stripe odeme saglayicisi uygulamasi."""

import asyncio
import stripe
from typing import Any
from core.config import settings
from core.pricing import PLANS
from services.payment.base import BasePaymentProvider

class StripeProvider(BasePaymentProvider):
    """Stripe Checkout oturumu entegrasyonu."""

    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY

    async def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        plan_id: str,
        **kwargs
    ) -> str:
        """Stripe Checkout oturumu olusturur."""
        plan = PLANS.get(plan_id)
        if not plan:
            raise ValueError(f"Gecersiz plan: {plan_id}")

        # Stripe USD kullaniyor varsayiyoruz
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            payment_method_types=["card"],
            mode="payment", # Abonelik yerine tek seferlik odeme (basitlik icin)
            customer_email=user_email,
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {"name": plan["name"]},
                    "unit_amount": int(plan["price_usd"] * 100),
                },
                "quantity": 1,
            }],
            success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
            metadata={"user_id": user_id, "plan_id": plan_id},
        )
        return session.url

    async def validate_webhook(self, payload: Any, headers: Any) -> dict | None:
        """Stripe webhook imzasi dogrular."""
        sig_header = headers.get("stripe-signature")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
            
            if event["type"] == "checkout.session.completed":
                session = event["data"]["object"]
                return {
                    "event": "payment.success",
                    "user_id": session.get("metadata", {}).get("user_id"),
                    "plan_id": session.get("metadata", {}).get("plan_id"),
                }
        except Exception:
            return None
        return None
