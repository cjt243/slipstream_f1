"""Application configuration, loaded from environment / .env."""

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEV_SECRET_KEY = "dev-secret-change-me"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Server
    port: int = 3001
    frontend_url: str = "http://localhost:5173"

    # Auth / JWT
    secret_key: str = DEV_SECRET_KEY
    jwt_expiry_days: int = 7

    # Database — Turso (libSQL). If unset, falls back to a local sqlite file.
    turso_database_url: str | None = None
    turso_auth_token: str | None = None

    # Email (magic links). If unset, links are logged to the console.
    resend_api_key: str | None = None
    # Resend's shared test sender only delivers to the Resend account's own
    # address; set a verified-domain sender for real users.
    email_from: str = "Slipstream <onboarding@resend.dev>"

    # Set by Vercel on every deployment (production and previews).
    vercel: str | None = None

    @model_validator(mode="after")
    def require_real_secret_on_vercel(self) -> "Settings":
        # The dev default is public, so JWTs signed with it could be forged.
        if self.vercel and self.secret_key == DEV_SECRET_KEY:
            raise ValueError("SECRET_KEY must be set to a strong random value on Vercel")
        return self


settings = Settings()
