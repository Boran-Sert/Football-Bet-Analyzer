"""Kullanici veri erisim katmani."""

from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId

from schemas.auth import UserInDB, UserTier


class UserRepository:
    """Kullanici koleksiyonu islemleri."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.users

    async def create(self, user: UserInDB) -> UserInDB:
        doc = user.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return UserInDB(**doc)

    async def get_by_email(self, email: str) -> UserInDB | None:
        doc = await self.collection.find_one({"email": email})
        if doc:
            doc["_id"] = str(doc["_id"])
            return UserInDB(**doc)
        return None

    async def get_by_id(self, user_id: str) -> UserInDB | None:
        try:
            doc = await self.collection.find_one({"_id": ObjectId(user_id)})
            if doc:
                doc["_id"] = str(doc["_id"])
                return UserInDB(**doc)
        except Exception:
            pass
        return None

    async def update_tier(self, user_id: str, new_tier: UserTier) -> bool:
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"tier": new_tier.value}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def verify_user(self, user_id: str) -> bool:
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"is_verified": True}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    # ── GAP 2: Password reset ─────────────────────────────────────────────────

    async def update_password(self, user_id: str, new_hashed_password: str) -> bool:
        """Kullanicinin hashlenmi sifresini gunceller."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"hashed_password": new_hashed_password}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def update_email(self, user_id: str, new_email: str) -> bool:
        """Kullanicinin email adresini gunceller."""
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"email": new_email, "is_verified": False}},  # Re-verify maybe?
            )
            return result.modified_count > 0
        except Exception:
            return False

    async def delete(self, user_id: str) -> bool:
        """Kullanici kaydini kalici olarak siler (KVKK/GDPR)."""
        try:
            result = await self.collection.delete_one({"_id": ObjectId(user_id)})
            return result.deleted_count > 0
        except Exception:
            return False
