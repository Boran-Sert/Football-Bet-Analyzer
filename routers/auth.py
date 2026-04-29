"""Kimlik dogrulama API yonlendiricisi."""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from clients.email_client import email_client
from core.config import settings

from schemas.auth import TokenResponse, UserCreate, UserInDB, UserResponse
from services.auth_service import AuthService
from utils.dependencies import get_auth_service, get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Yeni kullanici kaydi olusturur ve dogrulama e-postasi gonderir."""
    user = await auth_service.register_user(user_in)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email adresi ile kayitli bir kullanici zaten var."
        )
    
    # Dogrulama token'i uret ve e-posta gonderimini arka plana ekle
    token = auth_service.create_verification_token(user.email)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    background_tasks.add_task(email_client.send_verification_email, user.email, verify_url)
    
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Email ve sifre ile giris yapar, JWT dondurur."""
    user = await auth_service.repo.get_by_email(form_data.username)
    if not user or not auth_service.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Hatali e-posta veya sifre",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = auth_service.create_access_token(
        user_id=user.id, 
        tier=user.tier, 
        is_superuser=user.is_superuser
    )
    
    return {
        "access_token": access_token,
        "refresh_token": "not-implemented-yet",
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserInDB = Depends(get_current_user)):
    """Mevcut giris yapmis kullanicinin bilgilerini dondurur."""
    return current_user

@router.get("/verify-email")
async def verify_email(
    token: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """E-posta dogrulama linkini isler."""
    is_valid = await auth_service.verify_user_email(token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gecersiz veya suresi dolmus dogrulama token'i."
        )
    return {"message": "E-posta adresiniz basariyla dogrulandi."}
