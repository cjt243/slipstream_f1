"""Magic-link auth endpoints: register, verify, me."""

from fastapi import APIRouter, HTTPException, status

from config import settings
from dependencies import CurrentUser, DbSession
from schemas.auth import (
    AuthResponse,
    MeResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
    VerifyRequest,
)
from services import auth as auth_service
from services.email import send_magic_link

router = APIRouter(prefix="/auth", tags=["auth"])

REGISTER_MESSAGE = "If that email is valid, a magic link has been sent."


@router.post("/register", response_model=RegisterResponse)
def register(body: RegisterRequest, db: DbSession) -> RegisterResponse:
    # Same response for new, existing and (when registration is closed)
    # unknown emails — no account enumeration.
    user = auth_service.get_or_create_user(
        db, body.email, body.username, allow_create=settings.registration_open
    )
    if user is None:
        return RegisterResponse(message=REGISTER_MESSAGE)
    raw_token = auth_service.create_magic_token(db, user.id)
    db.commit()
    try:
        send_magic_link(user.email, auth_service.build_magic_link(raw_token))
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Couldn't send the sign-in email. Try again shortly.",
        ) from exc
    return RegisterResponse(message=REGISTER_MESSAGE)


@router.post("/verify", response_model=AuthResponse)
def verify(body: VerifyRequest, db: DbSession) -> AuthResponse:
    user = auth_service.verify_magic_token(db, body.token)
    db.commit()  # the token is consumed even when expired
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This sign-in link is invalid or has expired.",
        )
    return AuthResponse(
        token=auth_service.create_jwt(user), user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser, db: DbSession) -> MeResponse:
    return MeResponse(
        **UserResponse.model_validate(user).model_dump(),
        bank_balance=auth_service.get_bank_balance(db, user),
    )
