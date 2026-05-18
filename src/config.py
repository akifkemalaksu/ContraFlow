import os

from pydantic_settings import BaseSettings, SettingsConfigDict

_environment = os.getenv("ENVIRONMENT", "development")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=f".env.{_environment}",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    APP_NAME: str = "ContraFlow"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    SEED_ON_STARTUP: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/contraflow"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Wallet private key encryption (AES-256-GCM) — 64 hex chars (32 bytes)
    WALLET_ENCRYPTION_KEY: str

    # API Key
    API_KEY_SECRET: str
    API_KEY_PREFIX_LENGTH: int = 8

    # CORS
    ALLOWED_ORIGINS: list[str] = ["*"]

    # Hyperliquid
    HYPERLIQUID_USE_TESTNET: bool = True
    HYPERLIQUID_MAINNET_URL: str = "https://api.hyperliquid.xyz"
    HYPERLIQUID_TESTNET_URL: str = "https://api.hyperliquid-testnet.xyz"

    @property
    def hyperliquid_base_url(self) -> str:
        return self.HYPERLIQUID_TESTNET_URL if self.HYPERLIQUID_USE_TESTNET else self.HYPERLIQUID_MAINNET_URL

    @property
    def celery_broker_url(self) -> str:
        return self.REDIS_URL

    @property
    def celery_result_backend(self) -> str:
        return self.REDIS_URL


settings = Settings()
