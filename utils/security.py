"""Sifre hashleme ve JWT token islemleri icin guvenlik yardimcilari.

bcrypt: Sifre hashleme (passlib yerine dogrudan kullanilir).
python-jose: JWT token olusturma ve dogrulama.
"""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt, JWTError

from core.config import settings


def hash_password(password: str) -> str:
    """Sifreyi bcrypt ile hashler."""
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Duz sifre ile hash'i karsilastirir."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(data: dict, expires_minutes: int = None) -> str:
    """JWT erisim token'i olusturur.

    Args:
        data: Token icine gomulecek veri (sub, role vb.).
        expires_minutes: Gecerlilik suresi (dakika). None ise config'den alinir.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_reset_token(username: str) -> str:
    """Sifre sifirlama icin kisa omurlu JWT token olusturur."""
    return create_access_token(
        data={"sub": username, "purpose": "reset"},
        expires_minutes=settings.RESET_TOKEN_EXPIRE_MINUTES,
    )


def decode_token(token: str) -> dict | None:
    """JWT token'i cozumler. Gecersiz veya suresi dolmussa None doner."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None
