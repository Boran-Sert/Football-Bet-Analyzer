"""Kimlik dogrulama veri transfer objeleri."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserTier(str, Enum):
    """Kullanici katmani. Tier limitleri core/config.py TierLimits'te."""
    FREE = "free"
    PRO = "pro"
    ELITE = "elite"


class UserCreate(BaseModel):
    """Kayit istegi."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=2, max_length=50)


class UserLogin(BaseModel):
    """Giris istegi."""
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    """MongoDB'deki kullanici dokumani."""
    id: str = Field(default="", alias="_id")
    email: str
    display_name: str
    hashed_password: str
    tier: UserTier = UserTier.FREE
    is_verified: bool = False
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {"from_attributes": True, "populate_by_name": True}


class UserResponse(BaseModel):
    """API yaniti — sifre haric."""
    id: str
    email: str
    display_name: str
    tier: UserTier
    is_verified: bool
    is_superuser: bool
    created_at: datetime


class TokenData(BaseModel):
    """JWT payload."""
    user_id: str
    tier: UserTier
    is_superuser: bool = False
    exp: datetime | None = None


class TokenResponse(BaseModel):
    """Login/Register yaniti."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class EmailVerifyRequest(BaseModel):
    """Email dogrulama token'i."""
    token: str
