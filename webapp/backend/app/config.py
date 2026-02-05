"""
Application configuration using Pydantic Settings.
All config loaded from environment variables.
"""

from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional, List
import sys


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # App
    app_name: str = "Research Dossier API"
    debug: bool = False
    api_version: str = "v1"

    # Database
    database_url: str = "sqlite:///./research.db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Auth
    jwt_secret: str = "CHANGE_ME_IN_PRODUCTION_USE_RANDOM_256_BIT_KEY"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Stripe
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_price_single: Optional[str] = None
    stripe_price_starter: Optional[str] = None
    stripe_price_pro: Optional[str] = None

    # Email
    resend_api_key: Optional[str] = None
    from_email: str = "reports@example.com"

    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None

    # LLM (for dossier synthesis)
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"  # Cost-effective, good quality

    # URLs
    frontend_url: str = "http://localhost:3000"
    api_url: str = "http://localhost:8000"

    # Research
    research_scripts_path: str = "../../execution"
    research_output_path: str = "../../.tmp"

    # Credits pricing
    credit_cost_quick: int = 1
    credit_cost_standard: int = 2
    credit_cost_deep: int = 4

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


def validate_settings(settings: Settings) -> None:
    """
    Validate settings on startup. Fails fast if critical vars are missing in production.

    Production requirements (when debug=False):
    - JWT_SECRET must be changed from default
    - DATABASE_URL should be PostgreSQL (warning only)

    Warnings (logged but don't fail):
    - Missing Stripe keys (payments won't work)
    - Missing Resend key (emails won't send)
    - Missing Google OAuth (social login won't work)
    - Missing OpenAI key (research generation won't work)
    """
    errors: List[str] = []
    warnings: List[str] = []

    # Critical: JWT secret must be changed in production
    default_jwt = "CHANGE_ME_IN_PRODUCTION_USE_RANDOM_256_BIT_KEY"
    if not settings.debug and settings.jwt_secret == default_jwt:
        errors.append(
            "JWT_SECRET is using insecure default value. "
            "Set JWT_SECRET environment variable to a random 256-bit key."
        )

    # Warning: SQLite in production
    if not settings.debug and settings.database_url.startswith("sqlite"):
        warnings.append(
            "Using SQLite in production. Consider PostgreSQL for better performance. "
            "Set DATABASE_URL=postgresql://user:pass@host:5432/dbname"
        )

    # Warning: Missing payment integration
    if not settings.stripe_secret_key:
        warnings.append("STRIPE_SECRET_KEY not set - payments will not work")
    if not settings.stripe_webhook_secret:
        warnings.append("STRIPE_WEBHOOK_SECRET not set - payment webhooks will fail")

    # Warning: Missing email integration
    if not settings.resend_api_key:
        warnings.append("RESEND_API_KEY not set - emails will not send")

    # Warning: Missing OAuth
    if not settings.google_client_id or not settings.google_client_secret:
        warnings.append("Google OAuth not configured - social login will not work")

    # Warning: Missing LLM
    if not settings.openai_api_key:
        warnings.append("OPENAI_API_KEY not set - research generation will not work")

    # Print warnings
    if warnings:
        print("\n" + "=" * 60)
        print("WARNING: CONFIGURATION WARNINGS:")
        print("=" * 60)
        for w in warnings:
            print(f"  * {w}")
        print("=" * 60 + "\n")

    # Fail on errors
    if errors:
        print("\n" + "=" * 60)
        print("ERROR: FATAL CONFIGURATION ERRORS:")
        print("=" * 60)
        for e in errors:
            print(f"  * {e}")
        print("=" * 60)
        print("\nApplication cannot start with these configuration errors.")
        print("Please fix the above issues and restart.\n")
        sys.exit(1)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_validated_settings() -> Settings:
    """Get settings and validate them. Call this on app startup."""
    settings = get_settings()
    validate_settings(settings)
    return settings
