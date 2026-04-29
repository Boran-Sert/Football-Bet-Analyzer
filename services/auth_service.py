"""Kimlik dogrulama is mantigi ve JWT islemleri."""

from datetime import datetime, timedelta

from passlib.context import CryptContext
from jose import JWTError, jwt

from core.config import settings
from repositories.user_repository import UserRepository
from schemas.auth import TokenData, UserCreate, UserInDB, UserTier

# Şifre hashleme yapilandirmasi (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Kimlik dogrulama ve JWT yonetimi."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Sifre dogrulamasi yapar."""
        return pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Sifreyi hashler."""
        return pwd_context.hash(password)

    def create_access_token(self, user_id: str, tier: UserTier, is_superuser: bool = False) -> str:
        """Kullanici icin yeni bir JWT (Access Token) uretir."""
        expire = datetime.utcnow() + timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES)
        
        to_encode = {
            "sub": user_id,
            "tier": tier.value,
            "is_superuser": is_superuser,
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt

    def create_verification_token(self, email: str) -> str:
        """E-posta dogrulama icin ozel bir JWT uretir (24 saat gecerli)."""
        expire = datetime.utcnow() + timedelta(hours=24)
        to_encode = {"sub": email, "type": "email_verify", "exp": expire}
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    def decode_token(self, token: str) -> TokenData | None:
        """JWT'yi cozer ve TokenData'yi dondurur. Gecersizse None doner."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            user_id: str = payload.get("sub")
            tier_str: str = payload.get("tier")
            is_superuser: bool = payload.get("is_superuser", False)
            
            if user_id is None or tier_str is None:
                return None
                
            return TokenData(
                user_id=user_id,
                tier=UserTier(tier_str),
                is_superuser=is_superuser,
                exp=datetime.utcfromtimestamp(payload.get("exp")) if payload.get("exp") else None
            )
        except JWTError:
            return None

    async def register_user(self, user_in: UserCreate) -> UserInDB | None:
        """Yeni kullanici kaydi olusturur. Email kullanimdaysa None doner."""
        existing = await self.repo.get_by_email(user_in.email)
        if existing:
            return None

        hashed_password = self.get_password_hash(user_in.password)
        new_user = UserInDB(
            email=user_in.email,
            display_name=user_in.display_name,
            hashed_password=hashed_password,
            tier=UserTier.FREE,  # Varsayilan olarak FREE
            is_verified=False,    # Varsayilan olarak dogrulanmamis
            is_superuser=False    # Varsayilan olarak admin degil
        )
        
        return await self.repo.create(new_user)

    async def verify_user_email(self, token: str) -> bool:
        """Dogrulama token'ini cozer ve veritabaninda kullaniciyi dogrular."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            email: str = payload.get("sub")
            token_type: str = payload.get("type")
            
            if not email or token_type != "email_verify":
                return False
                
            user = await self.repo.get_by_email(email)
            if not user:
                return False
                
            # Kullaniciyi dogrulanmis isaretle
            return await self.repo.verify_user(user.id)
            
        except JWTError:
            return False
