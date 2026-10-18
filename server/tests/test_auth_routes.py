"""Auth endpoints end-to-end via TestClient (magic link captured, not emailed)."""

import pytest

from routes import auth as auth_routes


@pytest.fixture(autouse=True)
def open_registration(monkeypatch):
    # Most tests exercise sign-up; the closed-registration tests override this.
    monkeypatch.setattr(auth_routes.settings, "registration_open", True)


@pytest.fixture
def sent_links(monkeypatch):
    links: list[tuple[str, str]] = []
    monkeypatch.setattr(auth_routes, "send_magic_link", lambda email, link: links.append((email, link)))
    return links


def _token_from(link: str) -> str:
    return link.split("token=", 1)[1]


def test_register_verify_me_flow(client, sent_links):
    r = client.post("/api/auth/register", json={"email": "Lando@Example.com", "username": "lando"})
    assert r.status_code == 200
    assert r.json() == {"message": auth_routes.REGISTER_MESSAGE}
    assert sent_links[0][0] == "lando@example.com"

    r = client.post("/api/auth/verify", json={"token": _token_from(sent_links[0][1])})
    assert r.status_code == 200
    body = r.json()
    assert body["user"] == {
        "id": body["user"]["id"],
        "email": "lando@example.com",
        "username": "lando",
        "is_admin": False,
    }

    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {body['token']}"})
    assert r.status_code == 200
    assert r.json()["bank_balance"] == 100_000_000
    assert r.json()["username"] == "lando"


def test_register_response_is_identical_for_existing_email(client, sent_links):
    first = client.post("/api/auth/register", json={"email": "max@example.com", "username": "max"})
    second = client.post("/api/auth/register", json={"email": "max@example.com", "username": "max"})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()
    assert len(sent_links) == 2


def test_verify_rejects_reused_token(client, sent_links):
    client.post("/api/auth/register", json={"email": "oscar@example.com", "username": "oscar"})
    token = _token_from(sent_links[0][1])
    assert client.post("/api/auth/verify", json={"token": token}).status_code == 200

    r = client.post("/api/auth/verify", json={"token": token})
    assert r.status_code == 401
    assert "error" in r.json()


def test_me_requires_valid_token(client):
    assert client.get("/api/auth/me").status_code == 401
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401
    assert r.json() == {"error": "Not authenticated"}


def test_register_validates_input_with_error_shape(client, sent_links):
    r = client.post("/api/auth/register", json={"email": "not-an-email", "username": "x"})
    assert r.status_code == 422
    assert r.json()["error"].startswith("email:")
    assert sent_links == []


def test_register_returns_502_when_email_fails(client, monkeypatch):
    def boom(email: str, link: str) -> None:
        raise RuntimeError("resend down")

    monkeypatch.setattr(auth_routes, "send_magic_link", boom)
    r = client.post("/api/auth/register", json={"email": "a@example.com", "username": "a"})
    assert r.status_code == 502
    assert "error" in r.json()


def test_register_rejects_blank_username(client, sent_links):
    r = client.post("/api/auth/register", json={"email": "a@example.com", "username": "   "})
    assert r.status_code == 422
    assert r.json()["error"].startswith("username:")


def test_unhandled_errors_use_error_shape(db, monkeypatch):
    from fastapi.testclient import TestClient

    from app import app
    from dependencies import get_db
    from services import auth as auth_service

    def boom(*args: object) -> None:
        raise RuntimeError("database exploded")

    monkeypatch.setattr(auth_service, "verify_magic_token", boom)
    app.dependency_overrides[get_db] = lambda: db
    try:
        r = TestClient(app, raise_server_exceptions=False).post("/api/auth/verify", json={"token": "x"})
    finally:
        app.dependency_overrides.pop(get_db, None)
    assert r.status_code == 500
    assert r.json() == {"error": "Internal server error"}


def test_closed_registration_ignores_unknown_emails(client, sent_links, db, monkeypatch):
    from models import User

    monkeypatch.setattr(auth_routes.settings, "registration_open", False)
    r = client.post("/api/auth/register", json={"email": "stranger@example.com", "username": "s"})
    # Identical response to a real sign-in request, but nothing is created or sent.
    assert r.status_code == 200
    assert r.json() == {"message": auth_routes.REGISTER_MESSAGE}
    assert sent_links == []
    assert db.query(User).filter_by(email="stranger@example.com").count() == 0


def test_closed_registration_still_signs_in_existing_users(client, sent_links, monkeypatch):
    client.post("/api/auth/register", json={"email": "owner@example.com", "username": "owner"})
    monkeypatch.setattr(auth_routes.settings, "registration_open", False)

    r = client.post("/api/auth/register", json={"email": "Owner@Example.com", "username": "x"})
    assert r.status_code == 200
    assert [email for email, _ in sent_links] == ["owner@example.com", "owner@example.com"]
    token = _token_from(sent_links[-1][1])
    assert client.post("/api/auth/verify", json={"token": token}).status_code == 200
