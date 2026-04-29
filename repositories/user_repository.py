"""Kullanici veri erisim katmani."""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from schemas.auth import UserInDB, UserTier


class UserRepository:
    """Kullanici koleksiyonu islemleri."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.users

    async def create(self, user: UserInDB) -> UserInDB:
        """Yeni kullanici olusturur."""
        doc = user.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return UserInDB(**doc)

    async def get_by_email(self, email: str) -> UserInDB | None:
        """Email adresine gore kullanici getirir."""
        doc = await self.collection.find_one({"email": email})
        if doc:
            # MongoDB'den gelen _id ObjectId tipindedir, string'e cevirmek gerekir
            doc["_id"] = str(doc["_id"])
            return UserInDB(**doc)
        return None

    async def get_by_id(self, user_id: str) -> UserInDB | None:
        """ID'ye gore kullanici getirir."""
        try:
            doc = await self.collection.find_one({"_id": ObjectId(user_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return UserInDB(**doc)
        except Exception:
            pass
        return None

    async def update_tier(self, user_id: str, new_tier: UserTier) -> bool:
        """Kullanici katmanini gunceller."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"tier": new_tier.value}}
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def verify_user(self, user_id: str) -> bool:
        """Kullanicinin e-posta dogrulamasini tamamlar."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_verified": True}}
            )
            return result.modified_count > 0
        except Exception:
            return False
