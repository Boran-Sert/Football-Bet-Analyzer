"""FastAPI bagimliliklari (Dependencies).

Veritabani repolarini, servisleri ve kimlik dogrulamayi HTTP endpointlerine enjekte eder.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer

from core.database import mongo
from repositories.match_repository import MatchRepository
from repositories.user_repository import UserRepository
from services.analysis_service import AnalysisService
from services.auth_service import AuthService
from services.match_service import MatchService
from schemas.auth import UserInDB, UserTier

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_user_repo() -> UserRepository:
    db = mongo.get_db()
    return UserRepository(db)


async def get_match_repo() -> MatchRepository:
    db = mongo.get_db()
    return MatchRepository(db)


async def get_auth_service(repo: UserRepository = Depends(get_user_repo)) -> AuthService:
    return AuthService(repo)


async def get_match_service(repo: MatchRepository = Depends(get_match_repo)) -> MatchService:
    return MatchService(repo)


async def get_analysis_service(repo: MatchRepository = Depends(get_match_repo)) -> AnalysisService:
    return AnalysisService(repo)


async def get_current_user(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: AuthService = Depends(get_auth_service),
    user_repo: UserRepository = Depends(get_user_repo),
) -> UserInDB:
    """Gecerli kullaniciyi dondurur, ayni zamanda Request.state uzerine yazar."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Gecersiz kimlik dogrulama bilgileri",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = auth_service.decode_token(token)
    if token_data is None:
        raise credentials_exception
        
    user = await user_repo.get_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
        
    # Request state'ine atayalim ki middleware'ler kullanabilsin
    request.state.user_id = user.id
    request.state.user_tier = user.tier.value
    request.state.is_superuser = user.is_superuser
    
    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Dogrulanmis ve aktif bir kullanici mi diye kontrol eder (Email verify vs.)."""
    # Eger email dogrulamasi kati kuralsa:
    # if not current_user.is_verified:
    #     raise HTTPException(status_code=400, detail="Kullanici dogrulanmamis")
    return current_user


async def require_pro_tier(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Sadece PRO veya ELITE katmanindaki kullanicilarin erisimine izin verir."""
    if current_user.tier not in [UserTier.PRO, UserTier.ELITE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu islem icin daha yuksek bir uyelik katmani gereklidir."
        )
    return current_user


async def require_admin(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Sadece sistem yoneticilerinin (is_superuser=True) erisimine izin verir."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bu islem icin sistem yoneticisi (Admin) yetkisi gereklidir."
        )
    return current_user
