from core.config import settings
from services.payment.iyzico_provider import IyzicoProvider
from services.payment.stripe_provider import StripeProvider
from services.payment.base_provider import PaymentProvider

class PaymentProviderFactory:
    """Payment providerlar icin Strategy Pattern Factory."""
    
    _providers = {
        "stripe": StripeProvider,
        "iyzico": IyzicoProvider
    }

    @classmethod
    def get_provider(cls, provider_name: str) -> PaymentProvider:
        provider_class = cls._providers.get(provider_name.lower())
        if not provider_class:
            raise ValueError(f"Desteklenmeyen odeme saglayicisi: {provider_name}")
        return provider_class()
