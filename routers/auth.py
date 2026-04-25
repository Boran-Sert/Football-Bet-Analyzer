"""Kimlik dogrulama endpointleri.

rules.md Madde 2: Router sadece HTTP istegini alir, Service'e paslar, JSON doner.
rules.md Madde 3: AuthService Depends() ile enjekte edilir.
rules.md Madde 5: Rate limiter tum endpointlerde aktif.
rules.md Madde 5: Ham hatalar kullaniciya dondurulmez, temiz HTTP yanit verilir.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from core.database import mongo
from middlewares.rate_limiter import rate_limit
from schemas.auth import (
    RegisterRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
    MessageResponse,
)
from services.auth_service import AuthService, UserRepository

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
    dependencies=[Depends(rate_limit)],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ═══════════════════════════════════════════════
#  DEPENDENCY INJECTION FACTORY'LER
# ═══════════════════════════════════════════════


def get_auth_service() -> AuthService:
    """AuthService'i Depends() ile enjekte etmek icin factory."""
    repo = UserRepository(mongo.db)
    return AuthService(repo)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service),
) -> dict:
    """JWT token'dan aktif kullaniciyi cozumler.

    Korunmus endpointlerde Depends(get_current_user) ile kullanilir.
    """
    user = await service.get_current_user(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Gecersiz veya suresi dolmus token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


# ═══════════════════════════════════════════════
#  ENDPOINTLER
# ═══════════════════════════════════════════════


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni kullanici kaydi",
)
async def register(
    body: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Yeni bir kullanici hesabi olusturur."""
    user = await service.register(
        username=body.username,
        email=body.email,
        password=body.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Bu kullanici adi veya e-posta adresi zaten kullaniliyor.",
        )
    return MessageResponse(
        message="Kayit basarili.",
        detail=f"Hosgeldiniz, {body.username}!",
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Kullanici girisi",
)
async def login(
    body: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Kullanici adi ve sifre ile giris yapar. JWT token doner."""
    result = await service.login(body.username, body.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Kullanici adi veya sifre hatali.",
        )
    return TokenResponse(**result)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Sifre sifirlama talebi",
)
async def forgot_password(
    body: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Kayitli e-posta adresine sifre sifirlama baglantisi gonderir.

    Guvenlik: Kullanici bulunamasa bile ayni mesaj doner
    (e-posta enumeration saldirisini onler).
    """
    await service.forgot_password(body.email)

    # Her durumda ayni yanit (kullanici var/yok farketmez)
    return MessageResponse(
        message="Eger bu e-posta adresi sistemimizde kayitliysa, "
        "sifre sifirlama baglantisi gonderilmistir.",
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Sifre sifirlama",
)
async def reset_password(
    body: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
):
    """Sifre sifirlama token'i ile yeni sifre belirler."""
    success = await service.reset_password(body.token, body.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gecersiz veya suresi dolmus sifirlama token'i.",
        )
    return MessageResponse(message="Sifreniz basariyla guncellendi.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Aktif kullanici profili",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    """JWT token sahibi kullanicinin profil bilgilerini doner."""
    return UserResponse(
        id=current_user["_id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        created_at=current_user["created_at"],
    )
