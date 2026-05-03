"""Kimlik dogrulama API yonlendiricisi.

Endpoints:
  POST /api/v1/auth/register        — Yeni kayit
  POST /api/v1/auth/login           — Giris (access + refresh token)
  POST /api/v1/auth/refresh         — Access token yenile (GAP 3)
  POST /api/v1/auth/logout          — Refresh token iptal et (GAP 3)
  POST /api/v1/auth/verify-email    — Email dogrulama
  POST /api/v1/auth/forgot-password — Sifre sifirlama linki gonder (GAP 2)
  POST /api/v1/auth/reset-password  — Yeni sifre belirle (GAP 2)
  GET  /api/v1/auth/me              — Profil bilgisi
"""

import hashlib
from typing import Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    BackgroundTasks,
    Response,
    Request,
)

from clients.email_client import email_client
from core.config import settings
from schemas.auth import (
    EmailChangeRequest,
    EmailVerifyRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserInDB,
    UserLogin,
    UserResponse,
    AccountDeleteRequest,
)
from services.auth_service import AuthService
from utils.dependencies import get_auth_service, get_current_active_user

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


# ── Register ──────────────────────────────────────────────────────────────────


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_in: UserCreate,
    response: Response,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    user = await auth_service.register_user(user_in)
    if not user:
        raise HTTPException(
            status_code=409, detail="Bu email adresi zaten kullaniliyor."
        )

    verify_token = auth_service.create_verification_token(user.email)
    verify_url = f"{settings.FRONTEND_URL}/verify-email?token={verify_token}"
    background_tasks.add_task(
        email_client.send_verification_email, user.email, verify_url
    )

    if not user.id:
        raise HTTPException(status_code=500, detail="User ID generation failed.")

    access_token = auth_service.create_access_token(
        user.id, user.tier, user.is_superuser
    )
    refresh_token = await auth_service.create_refresh_token(
        user.id, user.tier, user.is_superuser
    )

    # Cookie tabanli auth (Faz 1)
    is_prod = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 3600,
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ── Login ─────────────────────────────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    # Brute-force check
    if await auth_service.is_account_locked(credentials.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla başarısız deneme. Hesabınız 15 dakika süreyle kilitlendi.",
        )

    user = await auth_service.repo.get_by_email(credentials.email)
    if not user or not await auth_service.verify_password(
        credentials.password, user.hashed_password
    ):
        await auth_service.record_login_failure(credentials.email)
        raise HTTPException(status_code=401, detail="Email veya sifre hatali.")

    # Success: Reset attempts
    await auth_service.reset_login_attempts(credentials.email)

    if not user.id:
        raise HTTPException(status_code=500, detail="User ID is missing in database.")

    access_token = auth_service.create_access_token(
        user.id, user.tier, user.is_superuser
    )
    refresh_token = await auth_service.create_refresh_token(
        user.id, user.tier, user.is_superuser
    )

    # Cookie tabanli auth (Faz 1)
    is_prod = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 3600,
    )

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ── Refresh token (GAP 3) ─────────────────────────────────────────────────────


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    request: Request,
    response: Response,
    body: Optional[RefreshRequest] = None,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Gecerli bir refresh token ile yeni bir access + refresh token cifti uretir.

    Eski refresh token otomatik olarak iptal edilir (token rotation).
    """
    refresh_token = (body.refresh_token if body else None) or request.cookies.get(
        "refresh_token"
    )

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token bulunamadi.")

    # Distributed Lock (Faz 6 Fix: Race Condition / Token Cloning)
    from core.redis_client import redis_manager

    redis = redis_manager.get_client()
    lock_key = f"lock:refresh:{hashlib.md5(refresh_token.encode()).hexdigest()}"

    async with redis.lock(lock_key, timeout=10):
        token_data = await auth_service.verify_refresh_token(refresh_token)
        if not token_data:
            raise HTTPException(
                status_code=401, detail="Gecersiz veya suresi dolmus refresh token."
            )

        # Rotate: revoke old, issue new pair
        await auth_service.revoke_refresh_token(refresh_token)
        new_access = auth_service.create_access_token(
            token_data.user_id, token_data.tier, token_data.is_superuser
        )
        new_refresh = await auth_service.create_refresh_token(
            token_data.user_id, token_data.tier, token_data.is_superuser
        )

    # Cookie tabanli auth (Faz 1)
    is_prod = settings.ENVIRONMENT == "production"
    response.set_cookie(
        key="access_token",
        value=new_access,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.JWT_ACCESS_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh,
        httponly=True,
        secure=is_prod,
        samesite="lax",
        max_age=settings.JWT_REFRESH_EXPIRE_DAYS * 24 * 3600,
    )

    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


# ── Logout (GAP 3) ────────────────────────────────────────────────────────────


@router.post("/logout", status_code=200)
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh token'i iptal eder ve cookieleri temizler."""
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        await auth_service.revoke_refresh_token(refresh_token)
    # Cookieleri temizle (Faz 6 Fix: Ghost Cookies)
    is_prod = settings.ENVIRONMENT == "production"
    cookie_params = {
        "path": "/",
        "httponly": True,
        "secure": is_prod,
        "samesite": "lax",
    }
    response.delete_cookie("access_token", **cookie_params)
    response.delete_cookie("refresh_token", **cookie_params)

    return {"message": "Basariyla cikis yapildi."}


# ── Email verification ────────────────────────────────────────────────────────


@router.post("/verify-email", status_code=200)
async def verify_email(
    body: EmailVerifyRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    success = await auth_service.verify_user_email(body.token)
    if not success:
        raise HTTPException(
            status_code=400, detail="Gecersiz veya suresi dolmus dogrulama token'i."
        )
    return {"message": "Email basariyla dogrulandi."}


# ── Forgot password (GAP 2) ───────────────────────────────────────────────────


@router.post("/forgot-password", status_code=200)
async def forgot_password(
    body: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Her zaman 200 doner — email enumeration'i onlemek icin.

    Kullanici varsa arka planda sifre sifirlama e-postasi gonderilir.
    """
    user = await auth_service.repo.get_by_email(body.email)
    if user:
        reset_token = auth_service.create_password_reset_token(user.email)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        background_tasks.add_task(
            email_client.send_password_reset_email, user.email, reset_url
        )
    return {
        "message": "Email adresiniz sistemde kayitliysa, sifre sifirlama linki gonderildi."
    }


# ── Reset password (GAP 2) ────────────────────────────────────────────────────


@router.post("/reset-password", status_code=200)
async def reset_password(
    body: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service),
):
    success = await auth_service.reset_password(body.token, body.new_password)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Gecersiz veya suresi dolmus sifre sifirlama token'i.",
        )
    return {"message": "Sifreniz basariyla guncellendi. Lutfen yeniden giris yapin."}


@router.post("/change-password", status_code=200)
async def change_password(
    body: PasswordChangeRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Mevcut sifreyi dogrulayarak yeni sifre belirler."""
    if not current_user.id:
        raise HTTPException(status_code=401, detail="User identity is incomplete.")
        
    success = await auth_service.change_password(
        current_user.id, body.current_password, body.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail="Mevcut sifre hatali.")
    return {"message": "Sifreniz basariyla degistirildi."}


# ── Me ────────────────────────────────────────────────────────────────────────


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserInDB = Depends(get_current_active_user)):
    if not current_user.id:
        raise HTTPException(status_code=401, detail="User identity is incomplete.")
        
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        tier=current_user.tier,
        is_verified=current_user.is_verified,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
    )


# ── Change e-mail ──────────────────────────────────────────────────────────────


@router.post("/request-email-change", status_code=200)
async def request_email_change(
    body: EmailChangeRequest,
    background_tasks: BackgroundTasks,
    current_user: UserInDB = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Yeni email adresine dogrulama linki gonderir."""
    # Check if email is already taken
    existing = await auth_service.repo.get_by_email(body.new_email)
    if existing:
        raise HTTPException(
            status_code=400, detail="Bu email adresi zaten kullaniliyor."
        )

    if not current_user.id:
        raise HTTPException(status_code=401, detail="User identity is incomplete.")

    token = auth_service.create_email_change_token(current_user.id, body.new_email)
    confirm_url = f"{settings.FRONTEND_URL}/confirm-email-change?token={token}"

    background_tasks.add_task(
        email_client.send_verification_email, body.new_email, confirm_url
    )
    return {"message": "Yeni email adresinize dogrulama linki gonderildi."}


@router.get("/confirm-email-change", status_code=200)
async def confirm_email_change(
    token: str,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Token gecerliyse email adresini gunceller."""
    success = await auth_service.confirm_email_change(token)
    if not success:
        raise HTTPException(
            status_code=400, detail="Gecersiz veya suresi dolmus dogrulama token'i."
        )
    return {"message": "Email adresiniz basariyla guncellendi."}


# ── Account Deletion (GDPR) ───────────────────────────────────────────────────


@router.delete("/account", status_code=status.HTTP_200_OK)
async def delete_account(
    body: AccountDeleteRequest,
    response: Response,
    current_user: UserInDB = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Kullanicinin hesabini ve verilerini kalici olarak siler (GDPR)."""
    if not current_user.id:
        raise HTTPException(status_code=401, detail="User identity is incomplete.")

    success = await auth_service.delete_account(current_user.id, body.password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sifre hatali veya hesap silinemedi.",
        )

    # Cookieleri temizle
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"message": "Hesabiniz ve tum verileriniz basariyla silindi."}
