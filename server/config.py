"""Application configuration, loaded from environment / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Server
    port: int = 3001
    frontend_url: str = "http://localhost:5173"

    # Auth / JWT
    secret_key: str = "dev-secret-change-me"
    jwt_expiry_days: int = 7

    # Database — Turso (libSQL). If unset, falls back to a local sqlite file.
    turso_database_url: str | None = None
    turso_auth_token: str | None = None

    # Email (magic links). If unset, links are logged to the console.
    resend_api_key: str | None = None


settings = Settings()
