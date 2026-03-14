"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "AccessibleAI"
    app_version: str = "0.1.0"
    debug: bool = False
    base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://accessibleai:accessibleai_dev_password@localhost:5432/accessibleai"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Security
    secret_key: str = "CHANGE_THIS_IN_PRODUCTION_USE_ENVIRONMENT_VARIABLE"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    # CORS
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # AI
    openai_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    # Prices
    stripe_price_id_free: str = ""
    stripe_price_id_starter: str = ""
    stripe_price_id_pro: str = ""
    stripe_price_id_agency: str = ""

    # Monitoring
    sentry_dsn: str = ""

    # Email (for future use)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@accessibleai.com"

    # Scanning
    scan_timeout_seconds: int = 60
    max_pages_per_scan: int = 100
    scan_concurrency: int = 5

    # Subscription limits
    limits: dict = Field(
        default={
            "free": {"websites": 1, "scans_per_month": 5},
            "starter": {"websites": 3, "scans_per_month": -1},  # -1 = unlimited
            "pro": {"websites": 10, "scans_per_month": -1},
            "agency": {"websites": -1, "scans_per_month": -1},
        }
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
