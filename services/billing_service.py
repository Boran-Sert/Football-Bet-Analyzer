"""Odeme ve abonelik yonetimi — Provider Agnostic."""

import logging
from typing import Any

from core.pricing import PLANS
from repositories.user_repository import UserRepository
from schemas.auth import UserTier
from services.payment.base import BasePaymentProvider

logger = logging.getLogger(__name__)


class BillingService:
    """Odeme saglayicisi bagimsiz faturalandirma servisi."""

    def __init__(self, user_repo: UserRepository, provider: BasePaymentProvider):
        self.repo = user_repo
        self.provider = provider

    async def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        plan_id: str,
    ) -> str:
        """Secili provider uzerinden odeme oturumu olusturur."""
        return await self.provider.create_checkout_session(
            user_id=user_id,
            user_email=user_email,
            plan_id=plan_id
        )

    async def handle_webhook(self, payload: Any, headers: Any) -> bool:
        """Webhook olayini isler ve kullanici tier'ini gunceller."""
        event_data = await self.provider.validate_webhook(payload, headers)
        
        if not event_data or event_data.get("event") != "payment.success":
            return False

        user_id = event_data.get("user_id")
        plan_id = event_data.get("plan_id")
        
        plan = PLANS.get(plan_id)
        if not plan or not user_id:
            logger.error("Webhook verisi gecersiz: user=%s, plan=%s", user_id, plan_id)
            return False

        new_tier = plan["tier"]
        success = await self.repo.update_tier(user_id, new_tier)
        
        if success:
            logger.info("Kullanici %s → %s katmanina yukseltildi.", user_id, new_tier.value)
            return True
        
        return False
