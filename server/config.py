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
    # Base URL for magic links and CORS. On Vercel previews, when unset, it
    # falls back to the deployment's own URL (see the validator below).
    frontend_url: str = "http://localhost:5173"

    # Sign-up: when False (the default), only emails already in the users
    # table can request a magic link. Set REGISTRATION_OPEN=true to allow
    # new accounts (e.g. local dev).
    registration_open: bool = False

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

    # Set by Vercel on every deployment: VERCEL=1, VERCEL_ENV is
    # production/preview, and the URLs are hostnames without a scheme.
    vercel: str | None = None
    vercel_env: str | None = None
    vercel_branch_url: str | None = None
    vercel_url: str | None = None

    @model_validator(mode="after")
    def check_vercel_config(self) -> "Settings":
        if not self.vercel:
            return self
        # The dev default is public, so JWTs signed with it could be forged.
        if self.secret_key == DEV_SECRET_KEY:
            raise ValueError("SECRET_KEY must be set to a strong random value on Vercel")
        # Without Turso the app falls back to dev.db, which can't be opened on
        # Vercel — fail at startup instead of on the first DB query.
        if self.vercel_env == "production" and not self.turso_database_url:
            raise ValueError("TURSO_DATABASE_URL must be set for Vercel production")
        if "frontend_url" not in self.model_fields_set:
            host = self.vercel_branch_url or self.vercel_url
            if host:
                self.frontend_url = f"https://{host}"
        return self


settings = Settings()
