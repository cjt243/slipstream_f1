"""Auth service: users, magic tokens, JWTs (direct, no HTTP)."""

from datetime import timedelta

from models import LeagueMember, MagicToken, STARTING_BUDGET, User
from services import auth


def test_new_user_is_enrolled_in_default_league_with_starting_budget(db):
    user = auth.get_or_create_user(db, "  Lando@Example.COM ", "lando")
    assert user.email == "lando@example.com"
    assert auth.get_bank_balance(db, user) == STARTING_BUDGET
    assert db.query(LeagueMember).filter_by(user_id=user.id).count() == 1


def test_existing_user_is_returned_unchanged(db):
    first = auth.get_or_create_user(db, "max@example.com", "max")
    again = auth.get_or_create_user(db, "MAX@example.com", "someone_else")
    assert again.id == first.id
    assert again.username == "max"  # can't rename an account by knowing its email
    assert db.query(User).count() == 1
    assert db.query(LeagueMember).filter_by(user_id=first.id).count() == 1


def test_magic_token_is_stored_hashed_and_single_use(db):
    user = auth.get_or_create_user(db, "oscar@example.com", "oscar")
    raw = auth.create_magic_token(db, user.id)

    stored = db.query(MagicToken).filter_by(user_id=user.id).one()
    assert stored.token_hash != raw
    assert len(stored.token_hash) == 64

    assert auth.verify_magic_token(db, raw).id == user.id
    assert auth.verify_magic_token(db, raw) is None
    assert db.query(MagicToken).count() == 0


def test_expired_token_is_rejected_and_consumed(db):
    user = auth.get_or_create_user(db, "charles@example.com", "charles")
    raw = auth.create_magic_token(db, user.id)
    token = db.query(MagicToken).one()
    token.expires_at = auth._utcnow() - timedelta(seconds=1)
    db.flush()

    assert auth.verify_magic_token(db, raw) is None
    assert db.query(MagicToken).count() == 0


def test_unknown_token_is_rejected(db):
    assert auth.verify_magic_token(db, "not-a-real-token") is None


def test_new_token_clears_users_expired_tokens(db):
    user = auth.get_or_create_user(db, "george@example.com", "george")
    auth.create_magic_token(db, user.id)
    db.query(MagicToken).one().expires_at = auth._utcnow() - timedelta(minutes=1)
    db.flush()

    auth.create_magic_token(db, user.id)
    assert db.query(MagicToken).filter_by(user_id=user.id).count() == 1


def test_jwt_round_trip_and_tampering(db):
    user = auth.get_or_create_user(db, "lewis@example.com", "lewis")
    token = auth.create_jwt(user)
    assert auth.decode_jwt_user_id(token) == user.id
    assert auth.decode_jwt_user_id(token + "x") is None
    assert auth.decode_jwt_user_id("garbage") is None


def test_magic_link_points_at_frontend_verify_page(monkeypatch):
    monkeypatch.setattr(auth.settings, "frontend_url", "https://slipstream.example/")
    assert auth.build_magic_link("abc") == "https://slipstream.example/auth/verify?token=abc"


def test_unknown_email_is_not_created_when_creation_disallowed(db):
    assert auth.get_or_create_user(db, "new@example.com", "new", allow_create=False) is None
    assert db.query(User).count() == 0

    existing = auth.get_or_create_user(db, "max@example.com", "max")
    assert auth.get_or_create_user(db, "max@example.com", "max", allow_create=False).id == existing.id


def test_registration_is_closed_by_default(monkeypatch):
    from config import Settings

    monkeypatch.delenv("REGISTRATION_OPEN", raising=False)
    assert Settings(_env_file=None).registration_open is False
