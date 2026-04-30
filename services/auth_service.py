"""Kimlik dogrulama is mantigi ve JWT islemleri."""

import asyncio
import secrets
from datetime import datetime, timedelta

from passlib.context import CryptContext
import jwt
from jwt.exceptions import PyJWTError

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

    async def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        # Faz 6 Fix: CPU-bound bcrypt islemi event loop'u kilitlememesi icin thread'e alindi
        return await asyncio.to_thread(pwd_context.verify, plain_password, hashed_password)

    async def get_password_hash(self, password: str) -> str:
        # Faz 6 Fix: CPU-bound bcrypt islemi event loop'u kilitlememesi icin thread'e alindi
        return await asyncio.to_thread(pwd_context.hash, password)

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        user = await self.repo.get_by_id(user_id)
        if not user or not await self.verify_password(current_password, user.hashed_password):
            return False
        
        new_hash = await self.get_password_hash(new_password)
        updated = await self.repo.update_password(user_id, new_hash)
        
        if updated:
            # Faz 6 Fix: Sifre degistiginde tum aktif oturumlari (refresh token) iptal et
            await self.revoke_all_user_tokens(user_id)
            
        return updated

    # ── Brute Force Protection ───────────────────────────────────────────────

    async def is_account_locked(self, email: str) -> bool:
        """Kullanicinin brute-force korumasi nedeniyle kilitli olup olmadigini kontrol eder."""
        redis = redis_manager.get_client()
        lock_key = f"login_lock:{email}"
        return await redis.exists(lock_key)

    async def record_login_failure(self, email: str) -> int:
        """Basarisiz giris denemesini kaydeder, 5 denemede 15 dk kilitler."""
        redis = redis_manager.get_client()
        attempts_key = f"login_attempts:{email}"
        
        attempts = await redis.incr(attempts_key)
        if attempts == 1:
            await redis.expire(attempts_key, 600)  # 10 dk icinde 5 deneme
            
        if attempts >= 5:
            await redis.setex(f"login_lock:{email}", 900, "locked") # 15 dk kilit
            await redis.delete(attempts_key)
            
        return attempts

    async def reset_login_attempts(self, email: str):
        """Basarili giriste deneme sayacini sifirlar."""
        redis = redis_manager.get_client()
        await redis.delete(f"login_attempts:{email}")

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
        except PyJWTError:
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
        
        # Faz 6 Fix: Bellek sızıntısı engellendi (ZSET + Expiry Score)
        # Score = timestamp of expiration
        exp_timestamp = int(datetime.utcnow().timestamp()) + expire_seconds
        set_key = f"user_tokens:{user_id}"
        
        async with redis.pipeline(transaction=True) as pipe:
            # 1. Yeni token'i ekle
            pipe.zadd(set_key, {jti: exp_timestamp})
            # 2. Suresi dolmus olanlari temizle (Memory leak fix)
            pipe.zremrangebyscore(set_key, "-inf", int(datetime.utcnow().timestamp()))
            # 3. Set'in kendisi de bir noktada silinsin
            pipe.expire(set_key, expire_seconds)
            await pipe.execute()
        
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
        except PyJWTError:
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
            user_id = payload.get("sub")
            if not jti:
                return False
            redis = redis_manager.get_client()
            await redis.delete(f"refresh_token:{jti}")
            if user_id:
                await redis.zrem(f"user_tokens:{user_id}", jti)
            return True
        except PyJWTError:
            return False

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """Kullanicinin tum aktif refresh token'larini iptal eder (O(1) performans)."""
        redis = redis_manager.get_client()
        set_key = f"user_tokens:{user_id}"
        
        # 1. Tum JTI'lari al (ZSET versiyonu)
        jtis = await redis.zrange(set_key, 0, -1)
        if not jtis:
            return
            
        # 2. Refresh token'lari sil
        async with redis.pipeline(transaction=True) as pipe:
            for jti in jtis:
                pipe.delete(f"refresh_token:{jti}")
            # 3. Set'i sil
            pipe.delete(set_key)
            await pipe.execute()

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
        except PyJWTError:
            return False

    # ── Email change ──────────────────────────────────────────────────────────

    def create_email_change_token(self, user_id: str, new_email: str) -> str:
        expire = datetime.utcnow() + timedelta(hours=2)
        to_encode = {
            "sub": user_id,
            "new_email": new_email,
            "type": "email_change",
            "exp": expire
        }
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    async def confirm_email_change(self, token: str) -> bool:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            user_id: str = payload.get("sub")
            new_email: str = payload.get("new_email")
            token_type: str = payload.get("type")
            
            if not user_id or not new_email or token_type != "email_change":
                return False
            
            # Check if email is already taken
            existing = await self.repo.get_by_email(new_email)
            if existing:
                return False
                
            return await self.repo.update_email(user_id, new_email)
        except PyJWTError:
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
            new_hash = await self.get_password_hash(new_password)
            return await self.repo.update_password(user.id, new_hash)
        except PyJWTError:
            return False

    # ── Register / Login ──────────────────────────────────────────────────────

    async def register_user(self, user_in: UserCreate) -> UserInDB | None:
        existing = await self.repo.get_by_email(user_in.email)
        if existing:
            return None
        hashed_password = await self.get_password_hash(user_in.password)
        new_user = UserInDB(
            email=user_in.email,
            display_name=user_in.display_name,
            hashed_password=hashed_password,
            tier=UserTier.STANDARD,
            is_verified=False,
            is_superuser=False,
        )
        return await self.repo.create(new_user)

    async def delete_account(self, user_id: str, password: str) -> bool:
        """Kullanici hesabini siler ve tum bagli verileri temizler."""
        user = await self.repo.get_by_id(user_id)
        if not user or not await self.verify_password(password, user.hashed_password):
            return False
        
        return await self.repo.delete(user_id)
