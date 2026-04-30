import json
import uuid
import logging
from typing import Any

from core.pricing import PLANS
from core.redis_client import redis_manager
from repositories.user_repository import UserRepository
from schemas.auth import UserTier, UserInDB
from services.payment.base import BasePaymentProvider
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)


class BillingService:
    """Odeme saglayicisi bagimsiz faturalandirma servisi."""

    def __init__(self, user_repo: UserRepository, provider: BasePaymentProvider):
        self.repo = user_repo
        self.provider = provider
        self.redis = redis_manager.get_client()

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

    async def initialize_guest_checkout(self, reg_data: dict, plan_id: str) -> str:
        """Kayit olmayan kullanici icin odeme baslatir ve verileri gecici olarak saklar."""
        temp_id = f"guest_{uuid.uuid4().hex}"
        # Sifreyi hashleyip saklayalim
        reg_data["hashed_password"] = pwd_context.hash(reg_data["password"])
        del reg_data["password"]
        
        await self.redis.setex(f"pending_reg:{temp_id}", 3600, json.dumps(reg_data))
        
        return await self.provider.create_checkout_session(
            user_id=temp_id,
            user_email=reg_data["email"],
            plan_id=plan_id
        )

    async def handle_webhook(self, payload: Any, headers: Any) -> bool:
        """Webhook olayini isler ve kullanici tier'ini gunceller veya yeni kullanici acar."""
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

        # Eger bu bir misafir kaydiysa (GUEST_ prefix)
        if str(user_id).startswith("guest_"):
            reg_json = await self.redis.get(f"pending_reg:{user_id}")
            if not reg_json:
                logger.error("Misafir kayit verisi bulunamadi: %s", user_id)
                return False
            
            reg_data = json.loads(reg_json)
            # Kullaniciyi DB'ye kaydet
            new_user = UserInDB(
                email=reg_data["email"],
                display_name=reg_data["display_name"],
                hashed_password=reg_data["hashed_password"],
                tier=new_tier,
                is_verified=True, # Odeme yapan dogrulanmis sayilir
                is_superuser=False
            )
            created_user = await self.repo.create(new_user)
            if created_user:
                logger.info("Yeni kullanici odeme sonrasi olusturuldu: %s", created_user.email)
                await self.redis.delete(f"pending_reg:{user_id}")
                return True
            return False

        # Mevcut kullanici yükseltme
        success = await self.repo.update_tier(user_id, new_tier)
        if success:
            logger.info("Kullanici %s → %s katmanina yukseltildi.", user_id, new_tier.value)
            return True
        
        return False
