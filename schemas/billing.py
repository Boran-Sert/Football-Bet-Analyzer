"""Faturalandirma veri transfer objeleri (DTO)."""

from pydantic import BaseModel, EmailStr, Field


class CheckoutRequest(BaseModel):
    """Mevcut kullanici icin odeme baslat."""
    plan_id: str  # "pro" veya "elite"
    identity_number: str = "11111111111"  # Default test value


class GuestCheckoutRequest(BaseModel):
    """Kayit olmamis kullanici icin odeme + kayit baslat."""
    plan_id: str
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str = Field(..., min_length=2, max_length=50)
    identity_number: str = "11111111111"
