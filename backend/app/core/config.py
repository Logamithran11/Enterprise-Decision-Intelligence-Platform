from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="Enterprise Decision Intelligence Platform", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    environment: Literal["local", "development", "staging", "production"] = Field(
        default="local",
        alias="APP_ENVIRONMENT",
    )
    debug: bool = Field(default=False, alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="APP_API_V1_PREFIX")
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"],
        alias="APP_CORS_ORIGINS",
    )
    database_url: str = Field(
        default="postgresql+psycopg://enterprise:enterprise@localhost:5432/decision_intelligence",
        alias="APP_DATABASE_URL",
    )
    jwt_secret_key: SecretStr = Field(
        default=SecretStr("change-me-in-production"),
        alias="APP_JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="APP_JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="APP_ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, alias="APP_REFRESH_TOKEN_EXPIRE_DAYS")
    celery_broker_url: str = Field(default="redis://localhost:6379/0", alias="APP_CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/1", alias="APP_CELERY_RESULT_BACKEND")
    log_level: str = Field(default="INFO", alias="APP_LOG_LEVEL")

    @computed_field
    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
