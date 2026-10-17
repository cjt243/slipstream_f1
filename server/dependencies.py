"""Database engine/session factory and FastAPI auth dependencies.

Engine selection:
- ``TURSO_DATABASE_URL`` set  -> connect to Turso (libSQL) with the auth token.
- unset                       -> fall back to a local ``dev.db`` sqlite file.
- auth token set but no URL   -> raise a startup error (misconfiguration guard).
"""

from datetime import datetime, timedelta, timezone
from typing import Annotated, Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import settings

JWT_ALGORITHM = "HS256"


def _build_db_url() -> str:
    """Resolve the SQLAlchemy URL from settings (reuses the spike's pattern)."""
    if settings.turso_database_url:
        url = settings.turso_database_url.replace("libsql://", "sqlite+libsql://")
        if settings.turso_auth_token:
            url += f"?authToken={settings.turso_auth_token}&secure=true"
        return url
    if settings.turso_auth_token:
        raise RuntimeError(
            "TURSO_AUTH_TOKEN is set but TURSO_DATABASE_URL is missing — "
            "refusing to start with an ambiguous database configuration."
        )
    # Local development fallback — same libSQL dialect as Turso for parity.
    return "sqlite+libsql:///dev.db"


engine = create_engine(
    _build_db_url(),
    echo=False,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a request-scoped DB session, always closed afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- JWT helpers -----------------------------------------------------------

def create_access_token(user_id: int) -> str:
    """Encode a signed JWT for ``user_id`` (used by the auth service in 2A)."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_expiry_days)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=JWT_ALGORITHM)


def _decode_user_id(token: str) -> int | None:
    """Return the user id from a valid token, or None if invalid/expired."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[JWT_ALGORITHM])
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except (JWTError, ValueError):
        return None


# --- Auth dependencies -----------------------------------------------------
# ``User`` is imported lazily so this module stays importable before the model
# layer (issue 1A) exists.

_bearer = HTTPBearer(auto_error=False)
_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)

DbSession = Annotated[Session, Depends(get_db)]
BearerCreds = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


def _lookup_user(db: Session, creds: HTTPAuthorizationCredentials | None):
    if creds is None:
        return None
    user_id = _decode_user_id(creds.credentials)
    if user_id is None:
        return None
    from models.user import User  # lazy: model defined in issue 1A

    return db.get(User, user_id)


def get_current_user(db: DbSession, creds: BearerCreds):
    """Return the authenticated User, or raise 401."""
    user = _lookup_user(db, creds)
    if user is None:
        raise _CREDENTIALS_EXC
    return user


def get_optional_user(db: DbSession, creds: BearerCreds):
    """Return the authenticated User or None — never raises."""
    return _lookup_user(db, creds)


CurrentUser = Annotated[object, Depends(get_current_user)]


def get_admin_user(user: CurrentUser):
    """Return the authenticated User if they are an admin, else raise 403."""
    if not getattr(user, "is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required"
        )
    return user
