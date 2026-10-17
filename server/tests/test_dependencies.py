"""Engine configuration: Turso URL / auth token resolution (no network)."""

import pytest

import dependencies
from config import settings


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
