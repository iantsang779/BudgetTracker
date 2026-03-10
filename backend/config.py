from __future__ import annotations
"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite+aiosqlite:///./budget.db"
    api_port: int = 8000
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    exchangerate_api_key: str = ""
    bls_api_key: str = ""


settings = Settings()
