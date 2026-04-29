"""Iyzico odeme saglayicisi uygulamasi."""

import asyncio
import iyzipay
from typing import Any
from core.config import settings
from core.pricing import PLANS
from services.payment.base import BasePaymentProvider

class IyzicoProvider(BasePaymentProvider):
    """Iyzico Checkout Form entegrasyonu."""

    def __init__(self):
        self.options = {
            'api_key': settings.IYZICO_API_KEY,
            'secret_key': settings.IYZICO_SECRET_KEY,
            'base_url': settings.IYZICO_BASE_URL
        }

    async def create_checkout_session(
        self,
        user_id: str,
        user_email: str,
        plan_id: str,
        **kwargs
    ) -> str:
        """Iyzico Checkout Form baslatir."""
        plan = PLANS.get(plan_id)
        if not plan:
            raise ValueError(f"Gecersiz plan: {plan_id}")

        request = {
            'locale': iyzipay.BaseRequest.LOCALE_TR,
            'conversationId': user_id,
            'price': str(plan["price_try"]),
            'paidPrice': str(plan["price_try"]),
            'currency': iyzipay.BaseRequest.CURRENCY_TRY,
            'basketId': f"B_{user_id}",
            'paymentGroup': iyzipay.BaseRequest.PAYMENT_GROUP_LISTING,
            'callbackUrl': f"{settings.FRONTEND_URL}/billing/success",
            'enabledInstallments': ['1'],
            'buyer': {
                'id': user_id,
                'name': 'User',
                'surname': 'Surname',
                'email': user_email,
                'identityNumber': '11111111111',
                'lastLoginDate': '2023-10-05 12:43:35',
                'registrationDate': '2023-10-05 12:43:35',
                'registrationAddress': 'N/A',
                'ip': '85.34.78.112',
                'city': 'Istanbul',
                'country': 'Turkey',
                'zipCode': '34000'
            },
            'shippingAddress': {
                'contactName': 'User Surname',
                'city': 'Istanbul',
                'country': 'Turkey',
                'address': 'N/A',
                'zipCode': '34000'
            },
            'billingAddress': {
                'contactName': 'User Surname',
                'city': 'Istanbul',
                'country': 'Turkey',
                'address': 'N/A',
                'zipCode': '34000'
            },
            'basketItems': [
                {
                    'id': plan_id,
                    'name': plan["name"],
                    'category1': 'Subscription',
                    'itemType': iyzipay.BaseRequest.BASKET_ITEM_TYPE_VIRTUAL,
                    'price': str(plan["price_try"])
                }
            ]
        }

        # iyzipay senkron oldugu icin executor'da calistiriyoruz (Rule 1.3)
        checkout_form_initialize = await asyncio.to_thread(
            iyzipay.CheckoutFormInitialize().create, request, self.options
        )
        
        response = checkout_form_initialize.read().decode('utf-8')
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

        request = {'locale': iyzipay.BaseRequest.LOCALE_TR, 'token': token}
        
        checkout_form = await asyncio.to_thread(
            iyzipay.CheckoutForm().retrieve, request, self.options
        )
        
        response = checkout_form.read().decode('utf-8')
        import json
        res_json = json.loads(response)

        if res_json.get("status") == "success" and res_json.get("paymentStatus") == "SUCCESS":
            return {
                "event": "payment.success",
                "user_id": res_json.get("conversationId"),
                "plan_id": res_json.get("basketItems")[0].get("id") if res_json.get("basketItems") else None
            }
        return None
