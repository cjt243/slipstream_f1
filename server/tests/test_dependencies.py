"""Startup configuration: Turso URL / auth token and secret-key guards (no network)."""

import pytest
from pydantic import ValidationError

import dependencies
from config import Settings, settings


@pytest.fixture
def turso_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "turso_database_url", "libsql://slipstream.turso.io")
    monkeypatch.setattr(settings, "turso_auth_token", "tok123")


def test_turso_token_goes_to_driver_not_url(turso_settings: None) -> None:
    # The libsql driver ignores ?authToken= in the URL (it sends an empty
    # bearer token), so the token must travel as the auth_token kwarg.
    url = dependencies._build_db_url()
    assert url == "sqlite+libsql://slipstream.turso.io?secure=true"
    assert "tok123" not in url
    assert dependencies._build_connect_args()["auth_token"] == "tok123"


def test_local_fallback_has_no_auth_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "turso_database_url", None)
    monkeypatch.setattr(settings, "turso_auth_token", None)
    assert dependencies._build_db_url() == "sqlite+libsql:///dev.db"
    assert "auth_token" not in dependencies._build_connect_args()


def test_token_without_url_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "turso_database_url", None)
    monkeypatch.setattr(settings, "turso_auth_token", "tok123")
    with pytest.raises(RuntimeError):
        dependencies._build_db_url()


def test_dev_secret_key_is_refused_on_vercel(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        Settings(_env_file=None)

    monkeypatch.setenv("SECRET_KEY", "a-real-secret")
    assert Settings(_env_file=None).secret_key == "a-real-secret"


@pytest.fixture
def on_vercel(monkeypatch: pytest.MonkeyPatch) -> pytest.MonkeyPatch:
    for key in ("FRONTEND_URL", "TURSO_DATABASE_URL", "VERCEL_BRANCH_URL", "VERCEL_URL"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("VERCEL", "1")
    monkeypatch.setenv("SECRET_KEY", "a-real-secret")
    return monkeypatch


def test_vercel_production_requires_turso(on_vercel: pytest.MonkeyPatch) -> None:
    on_vercel.setenv("VERCEL_ENV", "production")
    with pytest.raises(ValidationError, match="TURSO_DATABASE_URL"):
        Settings(_env_file=None)

    on_vercel.setenv("TURSO_DATABASE_URL", "libsql://slipstream.turso.io")
    Settings(_env_file=None)


def test_vercel_preview_does_not_require_turso(on_vercel: pytest.MonkeyPatch) -> None:
    on_vercel.setenv("VERCEL_ENV", "preview")
    Settings(_env_file=None)


def test_frontend_url_falls_back_to_vercel_branch_url(on_vercel: pytest.MonkeyPatch) -> None:
    on_vercel.setenv("VERCEL_ENV", "preview")
    on_vercel.setenv("VERCEL_URL", "slipstream-abc123.vercel.app")
    on_vercel.setenv("VERCEL_BRANCH_URL", "slipstream-git-feature.vercel.app")
    assert Settings(_env_file=None).frontend_url == "https://slipstream-git-feature.vercel.app"

    # An explicit FRONTEND_URL always wins.
    on_vercel.setenv("FRONTEND_URL", "https://slipstreamf1.vercel.app")
    assert Settings(_env_file=None).frontend_url == "https://slipstreamf1.vercel.app"
