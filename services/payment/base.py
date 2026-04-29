"""Odeme saglayicilari icin abstract base class."""

from abc import ABC, abstractmethod
from typing import Any
from schemas.auth import UserTier

class BasePaymentProvider(ABC):
    """Tüm ödeme sağlayıcılarının (Stripe, Iyzico vb.) uyması gereken arayüz."""

    @abstractmethod
    async def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        plan_id: str,
        **kwargs
    ) -> str:
        """Odeme oturumu olusturur ve odeme URL'sini dondurur."""
        pass

    @abstractmethod
    async def validate_webhook(self, payload: Any, headers: Any) -> dict | None:
        """Webhook verisini dogrular ve anlamli bir event dondurur."""
        pass
