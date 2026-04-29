"""Stripe odeme ve abonelik yonetimi."""

import logging
import stripe

from core.config import settings
from repositories.user_repository import UserRepository
from schemas.auth import UserTier

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY

# Stripe Price ID → UserTier mapping
# Bu ID'leri Stripe Dashboard'dan alip .env'e ekleyin
PRICE_TO_TIER: dict[str, UserTier] = {
    settings.STRIPE_PRICE_PRO: UserTier.PRO,
    settings.STRIPE_PRICE_ELITE: UserTier.ELITE,
}


class BillingService:
    """Stripe Checkout oturumu olusturur ve webhook olaylarini isler."""

    def __init__(self, user_repo: UserRepository):
        self.repo = user_repo

    def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        price_id: str,
    ) -> str:
        """Stripe Checkout oturumu olusturur ve URL'yi dondurur."""
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=user_email,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.FRONTEND_URL}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/billing/cancel",
            metadata={"user_id": user_id},  # Webhook'ta kullanmak icin
        )
        return session.url

    async def handle_webhook(self, payload: bytes, sig_header: str) -> None:
        """Stripe webhook olayini dogrular ve isler."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError) as exc:
            logger.warning("Gecersiz Stripe webhook imzasi: %s", exc)
            raise ValueError("Invalid webhook signature") from exc

        event_type = event["type"]
        logger.info("Stripe webhook alindi: %s", event_type)

        if event_type == "checkout.session.completed":
            await self._on_checkout_completed(event["data"]["object"])

        elif event_type in ("customer.subscription.deleted", "customer.subscription.paused"):
            await self._on_subscription_ended(event["data"]["object"])

    async def _on_checkout_completed(self, session: dict) -> None:
        """Odeme tamamlaninca kullanicinin tier'ini gunceller."""
        user_id = session.get("metadata", {}).get("user_id")
        if not user_id:
            logger.error("Webhook: user_id metadata eksik — session: %s", session.get("id"))
            return

        # Subscription'dan price_id al
        subscription_id = session.get("subscription")
        if not subscription_id:
            return

        subscription = stripe.Subscription.retrieve(subscription_id)
        price_id = subscription["items"]["data"][0]["price"]["id"]
        new_tier = PRICE_TO_TIER.get(price_id)

        if not new_tier:
            logger.warning("Bilinmeyen price_id: %s", price_id)
            return

        success = await self.repo.update_tier(user_id, new_tier)
        if success:
            logger.info("Kullanici %s → %s katmanina yukseltildi.", user_id, new_tier.value)
        else:
            logger.error("Tier guncellenemedi: user_id=%s", user_id)

    async def _on_subscription_ended(self, subscription: dict) -> None:
        """Abonelik iptal edilince kullaniciya FREE tier verilir."""
        # Stripe'da customer metadata'sindan user_id al
        customer_id = subscription.get("customer")
        if not customer_id:
            return

        customer = stripe.Customer.retrieve(customer_id)
        user_email = customer.get("email")
        if not user_email:
            return

        user = await self.repo.get_by_email(user_email)
        if user:
            await self.repo.update_tier(user.id, UserTier.FREE)
            logger.info("Abonelik bitti: %s → FREE katmanina dusuruldu.", user_email)
