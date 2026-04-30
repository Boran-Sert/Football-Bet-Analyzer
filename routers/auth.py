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

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks

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

    access_token = auth_service.create_access_token(
        user.id, user.tier, user.is_superuser
    )
    refresh_token = await auth_service.create_refresh_token(
        user.id, user.tier, user.is_superuser
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ── Login ─────────────────────────────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
):
    # Brute-force check
    if await auth_service.is_account_locked(credentials.email):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Çok fazla başarısız deneme. Hesabınız 15 dakika süreyle kilitlendi."
        )

    user = await auth_service.repo.get_by_email(credentials.email)
    if not user or not auth_service.verify_password(
        credentials.password, user.hashed_password
    ):
        await auth_service.record_login_failure(credentials.email)
        raise HTTPException(status_code=401, detail="Email veya sifre hatali.")

    # Success: Reset attempts
    await auth_service.reset_login_attempts(credentials.email)

    access_token = auth_service.create_access_token(
        user.id, user.tier, user.is_superuser
    )
    refresh_token = await auth_service.create_refresh_token(
        user.id, user.tier, user.is_superuser
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


# ── Refresh token (GAP 3) ─────────────────────────────────────────────────────


@router.post("/refresh", response_model=TokenResponse)
async def refresh_access_token(
    body: RefreshRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Gecerli bir refresh token ile yeni bir access + refresh token cifti uretir.

    Eski refresh token otomatik olarak iptal edilir (token rotation).
    """
    token_data = await auth_service.verify_refresh_token(body.refresh_token)
    if not token_data:
        raise HTTPException(
            status_code=401, detail="Gecersiz veya suresi dolmus refresh token."
        )

    # Rotate: revoke old, issue new pair
    await auth_service.revoke_refresh_token(body.refresh_token)
    new_access = auth_service.create_access_token(
        token_data.user_id, token_data.tier, token_data.is_superuser
    )
    new_refresh = await auth_service.create_refresh_token(
        token_data.user_id, token_data.tier, token_data.is_superuser
    )
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


# ── Logout (GAP 3) ────────────────────────────────────────────────────────────


@router.post("/logout", status_code=200)
async def logout(
    body: RefreshRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Refresh token'i iptal eder. Access token kendi TTL'i dolana kadar gecerli kalir
    (kisa TTL — 30 dk — bunu tolere edilebilir kilar)."""
    await auth_service.revoke_refresh_token(body.refresh_token)
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
    success = await auth_service.change_password(
        current_user.id, body.current_password, body.new_password
    )
    if not success:
        raise HTTPException(status_code=400, detail="Mevcut sifre hatali.")
    return {"message": "Sifreniz basariyla degistirildi."}


# ── Me ────────────────────────────────────────────────────────────────────────


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserInDB = Depends(get_current_active_user)):
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
