"""Kullanici kimlik dogrulama servisi (async).

passlib ile sifre hashleme, python-jose ile JWT token yonetimi.
rules.md Madde 2: Service katmani DB baglantisinı bilmez, Repository kullanir.
rules.md Madde 3: Depends() ile enjekte edilir.
"""

import datetime
import logging

from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from repositories.base import BaseRepository
from utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_reset_token,
    decode_token,
)
from core.config import settings

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """users koleksiyonuna ozel repository."""

    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        super().__init__(db, "users")

    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """E-posta adresine gore kullanici bulur."""
        return await self.find_one({"email": email})

    async def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Kullanici adina gore kullanici bulur."""
        return await self.find_one({"username": username})

    async def update_password(self, username: str, new_hashed_pw: str) -> int:
        """Kullanicinin sifresini gunceller."""
        return await self.update_one(
            {"username": username},
            {"password": new_hashed_pw},
        )


class AuthService:
    """Kullanici kayit, giris ve sifre sifirlama islemlerini yoneten servis."""

    def __init__(self, repo: UserRepository) -> None:
        """Dependency Injection ile repository alir."""
        self.repo = repo

    async def register(
        self, username: str, email: str, password: str, role: str = "user"
    ) -> Optional[Dict[str, Any]]:
        """Yeni kullanici kaydeder.

        Kullanici adi veya e-posta zaten alinmissa None doner.
        """
        if await self.repo.find_by_username(username):
            return None
        if await self.repo.find_by_email(email):
            return None

        user_data = {
            "username": username,
            "email": email,
            "password": hash_password(password),
            "role": role,
            "created_at": datetime.datetime.now(datetime.timezone.utc),
        }
        inserted_id = await self.repo.insert_one(user_data)
        user_data["_id"] = inserted_id
        user_data.pop("password")
        return user_data

    async def login(self, username: str, password: str) -> Optional[Dict[str, str]]:
        """Giris bilgilerini dogrular. Basariliysa JWT token doner."""
        user = await self.repo.find_by_username(username)
        if not user:
            return None

        if not verify_password(password, user["password"]):
            return None

        token = create_access_token(
            data={"sub": user["username"], "role": user.get("role", "user")}
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        }

    async def forgot_password(self, email: str) -> bool:
        """Sifre sifirlama token'i olusturur ve e-posta ile gonderir.

        Kullanici bulunamazsa False doner.
        """
        user = await self.repo.find_by_email(email)
        if not user:
            return False

        token = create_reset_token(user["username"])

        # E-posta gonder
        from utils.email import send_reset_email

        sent = await send_reset_email(
            to_email=email,
            username=user["username"],
            reset_token=token,
        )

        if not sent:
            logger.warning(
                "E-posta gonderilemedi (kullanici: %s). Token loglandi.",
                user["username"],
            )
            # E-posta servisi calismazsa token'i loglayarak erisime ac
            logger.info("Reset token (fallback): %s", token)

        return True

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Sifre sifirlama token'ini dogrulayip yeni sifreyi kaydeder."""
        payload = decode_token(token)
        if not payload:
            return False

        if payload.get("purpose") != "reset":
            return False

        username = payload.get("sub")
        if not username:
            return False

        user = await self.repo.find_by_username(username)
        if not user:
            return False

        new_hash = hash_password(new_password)
        updated = await self.repo.update_password(username, new_hash)
        return updated > 0

    async def get_current_user(self, token: str) -> Optional[Dict[str, Any]]:
        """JWT token'dan aktif kullaniciyi dondurur."""
        payload = decode_token(token)
        if not payload:
            return None

        username = payload.get("sub")
        if not username:
            return None

        user = await self.repo.find_by_username(username)
        if not user:
            return None

        user.pop("password", None)
        user["_id"] = str(user["_id"])
        return user
