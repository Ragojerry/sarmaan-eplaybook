"""Centralised, environment-driven configuration. Nothing here should be hardcoded
per-deployment — see docs/prototype-analysis.md §8 for the list of values that
must NOT be literals in code."""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    environment: str = "development"
    debug: bool = True

    # Database
    database_url: str = "postgresql+psycopg://sarmaan:sarmaan@localhost:5432/sarmaan_eplaybook"

    # Auth
    jwt_secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30

    # CORS
    cors_allow_origins: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Storage
    storage_backend: str = "local"  # "local" | "s3"
    storage_local_path: str = "../content/media"
    s3_endpoint_url: str | None = None
    s3_bucket: str | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None

    # AI
    ai_online_provider: str = "none"  # e.g. "openai", "anthropic" — configured in a later phase
    ai_online_api_key: str | None = None
    embedding_model_name: str = "not-yet-configured"


@lru_cache
def get_settings() -> Settings:
    return Settings()
