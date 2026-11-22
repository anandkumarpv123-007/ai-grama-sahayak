import os
from typing import List, Optional
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Grama Sahayak"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Database Configuration (PostgreSQL)
    DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Full PostgreSQL connection URL (e.g. postgresql+psycopg://user:pass@host:5432/dbname)",
    )
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "grama_sahayak_db"

    # Security
    SECRET_KEY: str = Field(
        default="CHANGE_THIS_IN_PRODUCTION_DEV_INSECURE_KEY",
        description="Application secret key. Must be replaced with strong secret in production.",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_safety(self) -> "Settings":
        """
        Enforce that development defaults cannot be used silently in production.
        """
        if self.ENVIRONMENT.lower() == "production":
            insecure_markers = ["change_this", "dev_", "insecure", "placeholder", "default_key"]
            if any(marker in self.SECRET_KEY.lower() for marker in insecure_markers) or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "Production safety violation: SECRET_KEY contains development placeholder or is under 32 chars. "
                    "Set a secure, random SECRET_KEY in production."
                )
            if self.POSTGRES_PASSWORD == "postgres" or (self.DATABASE_URL and "postgres:postgres@" in self.DATABASE_URL):
                raise ValueError(
                    "Production safety violation: Default PostgreSQL credentials ('postgres:postgres') detected. "
                    "Configure secure production database credentials."
                )
        return self

    def get_database_url(self) -> str:
        """
        Return verified PostgreSQL connection URL.
        Constructs URL from parameters if DATABASE_URL is not explicitly set.
        """
        if self.DATABASE_URL:
            # Normalize postgres:// to postgresql+psycopg://
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+psycopg://", 1)
            elif url.startswith("postgresql://") and "+psycopg" not in url and "+asyncpg" not in url:
                url = url.replace("postgresql://", "postgresql+psycopg://", 1)
            return url
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
