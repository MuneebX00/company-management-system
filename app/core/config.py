from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    PROJECT_NAME: str = "Company Management System"
    API_V1_PREFIX: str = "/api/v1"
    VERSION: str = "0.1.0"

    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    DATABASE_URL: str = (
        "postgresql+psycopg://company_app:change-me@localhost:5432/company_management"
    )

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SEED_ADMIN_EMAIL: str = "admin@example.com"
    SEED_ADMIN_PASSWORD: str = "Admin123!"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
