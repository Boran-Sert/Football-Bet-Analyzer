"""Kimlik dogrulama (Auth) icin Pydantic v2 sema tanimlari.

Istek (Request) ve yanit (Response) semalari ayri tutulur.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr


# ═══════════════════════════════════════════════
#  ISTEK SEMALARI (Frontend → Backend)
# ═══════════════════════════════════════════════


class RegisterRequest(BaseModel):
    """Kullanici kayit istegi."""

    username: str = Field(min_length=3, max_length=30, description="Kullanici adi")
    email: EmailStr = Field(description="E-posta adresi")
    password: str = Field(min_length=6, max_length=128, description="Sifre")


class LoginRequest(BaseModel):
    """Kullanici giris istegi."""

    username: str
    password: str


class ForgotPasswordRequest(BaseModel):
    """Sifre sifirlama talebi."""

    email: EmailStr = Field(description="Kayitli e-posta adresi")


class ResetPasswordRequest(BaseModel):
    """Sifre sifirlama islemi."""

    token: str = Field(description="Sifirlama token'i")
    new_password: str = Field(min_length=6, max_length=128, description="Yeni sifre")


# ═══════════════════════════════════════════════
#  YANIT SEMALARI (Backend → Frontend)
# ═══════════════════════════════════════════════


class TokenResponse(BaseModel):
    """Basarili giris sonrasi donen JWT token."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Token gecerlilik suresi (saniye)")


class UserResponse(BaseModel):
    """Kullanici profil bilgisi."""

    id: str
    username: str
    email: str
    role: str
    created_at: datetime


class MessageResponse(BaseModel):
    """Genel basari/bilgi mesaji."""

    message: str
    detail: Optional[str] = None
