"""Magic-link authentication: users, single-use tokens, and JWTs.

Pure service layer — no FastAPI imports. Raw magic tokens are only ever held
in memory and emailed; the database stores their SHA-256 hash.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from config import settings
from models import League, LeagueMember, MagicToken, User
from services.seed import DEFAULT_LEAGUE_INVITE_CODE, seed_default_league

JWT_ALGORITHM = "HS256"
MAGIC_TOKEN_TTL = timedelta(minutes=15)


def _utcnow() -> datetime:
    # Naive UTC, matching how DateTime columns round-trip through SQLite.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def normalize_email(email: str) -> str:
    return email.strip().lower()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter_by(email=normalize_email(email)).one_or_none()


def get_or_create_user(db: Session, email: str, username: str) -> User:
    """Return the user for ``email``, creating them if new.

    New users are enrolled in the default league with the starting budget.
    An existing user's username is left unchanged — otherwise anyone who knows
    an email could rename that account.
    """
    user = get_user_by_email(db, email)
    if user is not None:
        return user

    user = User(email=normalize_email(email), username=username.strip())
    db.add(user)
    db.flush()

    league = seed_default_league(db)
    db.add(LeagueMember(league_id=league.id, user_id=user.id))
    db.flush()
    return user


def get_bank_balance(db: Session, user: User) -> int | None:
    """The user's balance in the default league, or None if not a member."""
    member = (
        db.query(LeagueMember)
        .join(League)
        .filter(League.invite_code == DEFAULT_LEAGUE_INVITE_CODE, LeagueMember.user_id == user.id)
        .one_or_none()
    )
    return member.bank_balance if member is not None else None


def create_magic_token(db: Session, user_id: int) -> str:
    """Store a hashed single-use token for ``user_id`` and return the raw token.

    Also clears the user's expired tokens so the table doesn't grow unbounded.
    """
    now = _utcnow()
    db.query(MagicToken).filter(
        MagicToken.user_id == user_id, MagicToken.expires_at <= now
    ).delete(synchronize_session=False)

    raw_token = secrets.token_urlsafe(32)
    db.add(
        MagicToken(
            user_id=user_id,
            token_hash=_hash_token(raw_token),
            expires_at=now + MAGIC_TOKEN_TTL,
        )
    )
    db.flush()
    return raw_token


def verify_magic_token(db: Session, raw_token: str) -> User | None:
    """Consume ``raw_token``: return its user if valid, else None.

    The token row is deleted whether it was valid or expired, so a token can
    never be used twice.
    """
    token = db.query(MagicToken).filter_by(token_hash=_hash_token(raw_token)).one_or_none()
    if token is None:
        return None

    expired = token.expires_at <= _utcnow()
    user_id = token.user_id
    db.delete(token)
    db.flush()
    if expired:
        return None
    return db.get(User, user_id)


def create_jwt(user: User) -> str:
    """Encode a signed session JWT for ``user``."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expiry_days)
    payload = {"sub": str(user.id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def decode_jwt_user_id(token: str) -> int | None:
    """Return the user id from a valid JWT, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (JWTError, ValueError):
        return None


def build_magic_link(raw_token: str) -> str:
    return f"{settings.frontend_url.rstrip('/')}/auth/verify?token={raw_token}"
