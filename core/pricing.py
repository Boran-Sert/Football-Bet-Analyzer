"""Merkezi fiyatlandirma ve plan yonetimi."""

from typing import Any
from schemas.auth import UserTier

# Plan tanımları
PLANS: dict[str, dict[str, Any]] = {
    "standard": {
        "name": "Standard Plan",
        "tier": UserTier.STANDARD,
        "price_try": 100.00,
        "price_usd": 4.90,
        "features": [
            "3 benzer mac analizi",
            "60 istek/dk",
            "Temel istatistikler"
        ]
    },
    "pro": {
        "name": "Pro Plan",
        "tier": UserTier.PRO,
        "price_try": 149.90,  # TL bazlı fiyat (Iyzico için)
        "price_usd": 9.90,    # USD bazlı fiyat (Stripe vb. için)
        "features": [
            "10 benzer mac analizi",
            "200 istek/dk",
            "Lig filtreleme"
        ]
    },
    "elite": {
        "name": "Elite Plan",
        "tier": UserTier.ELITE,
        "price_try": 299.90,
        "price_usd": 19.90,
        "features": [
            "20 benzer mac analizi",
            "1000 istek/dk",
            "Oncelikli destek"
        ]
    }
}

def get_plan_by_tier(tier: UserTier) -> dict[str, Any] | None:
    """Tier degerine gore plan detaylarini dondurur."""
    for plan in PLANS.values():
        if plan["tier"] == tier:
            return plan
    return None
