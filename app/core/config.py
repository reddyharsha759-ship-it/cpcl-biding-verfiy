from functools import lru_cache
from typing import Optional
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application
    APP_NAME: str = "GeM Bid Compliance Verification Platform"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "gem-compliance-super-secret-key-change-in-production"

    # PostgreSQL Database
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "gem_compliance"

    DATABASE_URL: Optional[str] = None
    SYNC_DATABASE_URL: Optional[str] = None

    # Redis & Celery
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    # Statutory Integration Settings
    USE_MOCK_PORTALS: bool = True
    PORTAL_REQUEST_TIMEOUT_SECONDS: float = 10.0
    PORTAL_MAX_RETRIES: int = 3
    PORTAL_RETRY_BACKOFF_FACTOR: float = 0.5

    # External Portal Endpoints (Optional in Production)
    GSTN_API_URL: Optional[str] = None
    GSTN_API_KEY: Optional[str] = None
    UDYAM_API_URL: Optional[str] = None
    UDYAM_API_KEY: Optional[str] = None
    INCOME_TAX_API_URL: Optional[str] = None
    INCOME_TAX_API_KEY: Optional[str] = None
    CPPP_DEBARMENT_API_URL: Optional[str] = None
    CPPP_DEBARMENT_API_KEY: Optional[str] = None
    EPFO_API_URL: Optional[str] = None
    EPFO_API_KEY: Optional[str] = None

    @computed_field
    @property
    def async_database_uri(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def sync_database_uri(self) -> str:
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def redis_uri(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
