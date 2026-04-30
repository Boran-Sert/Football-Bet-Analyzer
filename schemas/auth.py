"""Kimlik dogrulama veri transfer objeleri."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class UserTier(str, Enum):
    STANDARD = "standard"
    PRO = "pro"
    ELITE = "elite"


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=2, max_length=50)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(BaseModel):
    id: str = Field(default="", alias="_id")
    email: str
    display_name: str
    hashed_password: str
    tier: UserTier = UserTier.STANDARD
    is_verified: bool = False
    is_superuser: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True, "populate_by_name": True}


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    tier: UserTier
    is_verified: bool
    is_superuser: bool
    created_at: datetime
    last_login_at: datetime | None = None


class TokenData(BaseModel):
    user_id: str
    tier: UserTier
    is_superuser: bool = False
    exp: datetime | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class EmailVerifyRequest(BaseModel):
    token: str


# ── GAP 2: Password reset ─────────────────────────────────────────────────────

class PasswordResetRequest(BaseModel):
    """Forgot-password isteği — sadece email."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Reset-password isteği — token + yeni sifre."""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── GAP 3: Refresh token ──────────────────────────────────────────────────────

class RefreshRequest(BaseModel):
    """Token yenileme veya logout isteği."""
    refresh_token: str


# ── Password Change ───────────────────────────────────────────────────────────

class PasswordChangeRequest(BaseModel):
    """Sifre degistirme isteği."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


# ── Email Change ──────────────────────────────────────────────────────────────

class EmailChangeRequest(BaseModel):
    """Email degistirme isteği."""
    new_email: EmailStr

# ── Account Deletion (GDPR) ───────────────────────────────────────────────────

class AccountDeleteRequest(BaseModel):
    """Hesap silme isteği."""
    password: str
