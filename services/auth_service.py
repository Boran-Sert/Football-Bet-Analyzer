"""Kimlik dogrulama is mantigi ve JWT islemleri."""

import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext
from jose import JWTError, jwt

from core.config import settings
from core.redis_client import redis_manager
from repositories.user_repository import UserRepository
from schemas.auth import TokenData, UserCreate, UserInDB, UserTier

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Kimlik dogrulama ve JWT yonetimi."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    # ── Password ──────────────────────────────────────────────────────────────

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        return pwd_context.hash(password)

    # ── Access token ──────────────────────────────────────────────────────────

    def create_access_token(self, user_id: str, tier: UserTier, is_superuser: bool = False) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
        to_encode = {
            "sub": user_id,
            "tier": tier.value,
            "is_superuser": is_superuser,
            "exp": expire,
        }
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def decode_token(self, token: str) -> TokenData | None:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            tier_str: str = payload.get("tier")
            is_superuser: bool = payload.get("is_superuser", False)
            if user_id is None or tier_str is None:
                return None
            return TokenData(
                user_id=user_id,
                tier=UserTier(tier_str),
                is_superuser=is_superuser,
                exp=datetime.utcfromtimestamp(payload["exp"]) if payload.get("exp") else None,
            )
        except JWTError:
            return None

    # ── Refresh token (revocable) ─────────────────────────────────────────────

    async def create_refresh_token(
        self, user_id: str, tier: UserTier, is_superuser: bool = False
    ) -> str:
        """Refresh token uretir ve JTI'sini Redis'e yazar (iptal edilebilir)."""
        jti = secrets.token_hex(32)
        expire_seconds = settings.JWT_REFRESH_EXPIRE_DAYS * 86400
        expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS)

        to_encode = {
            "sub": user_id,
            "tier": tier.value,
            "is_superuser": is_superuser,
            "type": "refresh",
            "jti": jti,
            "exp": expire,
        }
        token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        redis = redis_manager.get_client()
        await redis.setex(f"refresh_token:{jti}", expire_seconds, user_id)
        return token

    async def verify_refresh_token(self, token: str) -> TokenData | None:
        """Token tipini, imzasini ve Redis kaydini dogrular."""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                return None

            jti = payload.get("jti")
            user_id = payload.get("sub")
            tier_str = payload.get("tier")

            if not jti or not user_id or not tier_str:
                return None

            redis = redis_manager.get_client()
            stored = await redis.get(f"refresh_token:{jti}")
            if not stored:
                return None  # Revoked or expired

            return TokenData(
                user_id=user_id,
                tier=UserTier(tier_str),
                is_superuser=payload.get("is_superuser", False),
            )
        except JWTError:
            return None

    async def revoke_refresh_token(self, token: str) -> bool:
        """JTI'yi Redis'ten silerek token'i iptal eder."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                options={"verify_exp": False},  # Suresi dolmus token'lari da iptal et
            )
            jti = payload.get("jti")
            if not jti:
                return False
            redis = redis_manager.get_client()
            await redis.delete(f"refresh_token:{jti}")
            return True
        except JWTError:
            return False

    # ── Email verification ────────────────────────────────────────────────────

    def create_verification_token(self, email: str) -> str:
        expire = datetime.utcnow() + timedelta(hours=24)
        to_encode = {"sub": email, "type": "email_verify", "exp": expire}
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    async def verify_user_email(self, token: str) -> bool:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            if not email or token_type != "email_verify":
                return False
            user = await self.repo.get_by_email(email)
            if not user:
                return False
            return await self.repo.verify_user(user.id)
        except JWTError:
            return False

    # ── Password reset ────────────────────────────────────────────────────────

    def create_password_reset_token(self, email: str) -> str:
        """1 saatlik password reset JWT uretir."""
        expire = datetime.utcnow() + timedelta(hours=1)
        to_encode = {"sub": email, "type": "password_reset", "exp": expire}
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Token gecerliyse sifreyi gunceller."""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            if not email or token_type != "password_reset":
                return False
            user = await self.repo.get_by_email(email)
            if not user:
                return False
            new_hash = self.get_password_hash(new_password)
            return await self.repo.update_password(user.id, new_hash)
        except JWTError:
            return False

    # ── Register / Login ──────────────────────────────────────────────────────

    async def register_user(self, user_in: UserCreate) -> UserInDB | None:
        existing = await self.repo.get_by_email(user_in.email)
        if existing:
            return None
        hashed_password = self.get_password_hash(user_in.password)
        new_user = UserInDB(
            email=user_in.email,
            display_name=user_in.display_name,
            hashed_password=hashed_password,
            tier=UserTier.FREE,
            is_verified=False,
            is_superuser=False,
        )
        return await self.repo.create(new_user)
