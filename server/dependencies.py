"""Database engine/session factory and FastAPI auth dependencies.

Engine selection:
- ``TURSO_DATABASE_URL`` set  -> connect to Turso (libSQL) with the auth token.
- unset                       -> fall back to a local ``dev.db`` sqlite file.
- auth token set but no URL   -> raise a startup error (misconfiguration guard).
"""

from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings
from models.user import User
from services.auth import decode_jwt_user_id


def _build_db_url() -> str:
    """Resolve the SQLAlchemy URL from settings."""
    if settings.turso_database_url:
        # secure=true selects TLS. The auth token is NOT put in the URL: the
        # libsql driver ignores ``?authToken=`` and only reads ``auth_token``.
        url = settings.turso_database_url.replace("libsql://", "sqlite+libsql://")
        return f"{url}?secure=true"
    if settings.turso_auth_token:
        raise RuntimeError(
            "TURSO_AUTH_TOKEN is set but TURSO_DATABASE_URL is missing — "
            "refusing to start with an ambiguous database configuration."
        )
    # Local development fallback — same libSQL dialect as Turso for parity.
    return "sqlite+libsql:///dev.db"


def _build_connect_args() -> dict[str, bool | str]:
    """Driver kwargs; carries the Turso auth token when connecting remotely."""
    args: dict[str, bool | str] = {"check_same_thread": False}
    if settings.turso_database_url and settings.turso_auth_token:
        args["auth_token"] = settings.turso_auth_token
    return args


engine = create_engine(
    _build_db_url(),
    echo=False,
    connect_args=_build_connect_args(),
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped DB session, always closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- Auth dependencies -----------------------------------------------------

_bearer = HTTPBearer(auto_error=False)
_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)

DbSession = Annotated[Session, Depends(get_db)]
BearerCreds = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def _lookup_user(db: Session, creds: HTTPAuthorizationCredentials | None) -> User | None:
    if creds is None:
        return None
    user_id = decode_jwt_user_id(creds.credentials)
    if user_id is None:
        return None
    return db.get(User, user_id)


def get_current_user(db: DbSession, creds: BearerCreds) -> User:
    """Return the authenticated User, or raise 401."""
    user = _lookup_user(db, creds)
    if user is None:
        raise _CREDENTIALS_EXC
    return user


def get_optional_user(db: DbSession, creds: BearerCreds) -> User | None:
    """Return the authenticated User or None — never raises."""
    return _lookup_user(db, creds)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_admin_user(user: CurrentUser) -> User:
    """Return the authenticated User if they are an admin, else raise 403."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return user
