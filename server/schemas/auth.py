"""Auth request/response schemas (see docs/api-contracts.md#auth)."""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Deliberately loose — the magic link itself proves the address works.
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class RegisterRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    email: str = Field(max_length=254)
    username: str = Field(min_length=1, max_length=30)

    @field_validator("email")
    @classmethod
    def email_looks_valid(cls, value: str) -> str:
        if not EMAIL_RE.match(value):
            raise ValueError("Enter a valid email address")
        return value


class RegisterResponse(BaseModel):
    message: str


class VerifyRequest(BaseModel):
    token: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    username: str
    is_admin: bool


class AuthResponse(BaseModel):
    token: str
    user: UserResponse


class MeResponse(UserResponse):
    bank_balance: int | None
