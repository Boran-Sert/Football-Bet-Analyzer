"""Uygulama ayarlari.

Pydantic BaseSettings ile cevre degiskenlerini dogrular ve yukler.
.env dosyasindan veya sistem ortam degiskenlerinden okur.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Uygulama genelinde kullanilan yapilandirma degiskenleri."""

    MONGO_URI: str
    REDIS_URL: str = "redis://localhost:6379"
    FOOTBALL_DATA_API_KEY: str

    # JWT ayarlari
    JWT_SECRET_KEY: str = "change-this-to-a-random-secret-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # E-posta ayarlari (Resend - ucretsiz 3000 mail/ay)
    RESEND_API_KEY: str = ""
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
