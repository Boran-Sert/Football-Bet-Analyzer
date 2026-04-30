import logging
import asyncio
import iyzipay
from typing import Any
from datetime import datetime
from core.config import settings
from core.pricing import PLANS
from services.payment.base import BasePaymentProvider

logger = logging.getLogger(__name__)


class IyzicoProvider(BasePaymentProvider):
    """Iyzico Checkout Form entegrasyonu."""

    def __init__(self):
        self.options = {
            "api_key": settings.IYZICO_API_KEY,
            "secret_key": settings.IYZICO_SECRET_KEY,
            "base_url": settings.IYZICO_BASE_URL,
        }

    async def create_checkout_session(
        self, user_id: str, user_email: str, plan_id: str, **kwargs
    ) -> str:
        """Iyzico Checkout Form baslatir."""
        plan = PLANS.get(plan_id)
        if not plan:
            raise ValueError(f"Gecersiz plan: {plan_id}")

        request = {
            "locale": "tr",
            "conversationId": user_id,
            "price": str(plan["price_try"]),
            "paidPrice": str(plan["price_try"]),
            "currency": "TRY",
            "basketId": f"B_{user_id}",
            "paymentGroup": "LISTING",
            "callbackUrl": f"{settings.API_BASE_URL}/api/v1/billing/webhook",
            "enabledInstallments": ["1"],
            "buyer": {
                "id": user_id,
                "name": kwargs.get("display_name", "User"),
                "surname": "User",
                "email": user_email,
                "identityNumber": kwargs.get("identity_number", "11111111111"),
                "lastLoginDate": self._format_date(kwargs.get("last_login_date")),
                "registrationDate": self._format_date(kwargs.get("registration_date")),
                "registrationAddress": "N/A",
                "ip": kwargs.get("ip", "127.0.0.1"),
                "city": "Istanbul",
                "country": "Turkey",
                "zipCode": "34000",
            },
            "shippingAddress": {
                "contactName": "User Surname",
                "city": "Istanbul",
                "country": "Turkey",
                "address": "N/A",
                "zipCode": "34000",
            },
            "billingAddress": {
                "contactName": "User Surname",
                "city": "Istanbul",
                "country": "Turkey",
                "address": "N/A",
                "zipCode": "34000",
            },
            "basketItems": [
                {
                    "id": plan_id,
                    "name": plan["name"],
                    "category1": "Subscription",
                    "itemType": "VIRTUAL",
                    "price": str(plan["price_try"]),
                }
            ],
        }

        # iyzipay senkron oldugu icin executor'da calistiriyoruz (Rule 1.3)
        checkout_form_initialize = await asyncio.to_thread(
            iyzipay.CheckoutFormInitialize().create, request, self.options
        )

        response = checkout_form_initialize.read().decode("utf-8")
        import json

        res_json = json.loads(response)

        if res_json.get("status") != "success":
            raise Exception(f"Iyzico hatasi: {res_json.get('errorMessage')}")

        return res_json.get("paymentPageUrl")

    async def validate_webhook(self, payload: Any, headers: Any) -> dict | None:
        """Iyzico webhook/callback sonucunu dogrular."""
        # Not: Iyzico'da callbackUrl'e bir POST istegi gelir.
        # Bu metod callback icinden token ile sorgu yapmak icin kullanilabilir.
        token = payload.get("token")
        if not token:
            return None

        request = {"locale": "tr", "token": token}

        checkout_form = await asyncio.to_thread(
            iyzipay.CheckoutForm().retrieve, request, self.options
        )

        response = checkout_form.read().decode("utf-8")
        import json

        res_json = json.loads(response)

        logger.info("Iyzico Retrieve Response: %s", res_json)

        if (
            res_json.get("status") == "success"
            and res_json.get("paymentStatus") == "SUCCESS"
        ):
            # Iyzico Sandbox bazen conversationId donmeyebilir, basketId'den ayiklayalim
            basket_id = res_json.get("basketId", "")
            user_id = res_json.get("conversationId") or basket_id.replace("B_", "")
            
            # Paket bilgisini itemTransactions icinden alalim
            item_transactions = res_json.get("itemTransactions", [])
            plan_id = item_transactions[0].get("itemId") if item_transactions else None

            return {
                "event": "payment.success",
                "user_id": user_id,
                "plan_id": plan_id,
            }

        logger.warning("Iyzico odeme dogrulanamadi: %s", res_json.get("errorMessage"))
        return None

    def _format_date(self, dt: datetime | None) -> str:
        """Iyzico icin tarihi YYYY-MM-DD HH:mm:ss formatina donusturur."""
        if not dt:
            dt = datetime.utcnow()
        return dt.strftime("%Y-%m-%d %H:%M:%S")
