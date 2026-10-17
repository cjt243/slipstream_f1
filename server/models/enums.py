"""Shared enum types. Import these everywhere — never use raw strings for
typed fields (element type, session type, contract status)."""

import enum


class ElementType(str, enum.Enum):
    DRIVER = "driver"
    CONSTRUCTOR = "constructor"


class SessionType(str, enum.Enum):
    QUALI = "quali"
    SPRINT = "sprint"
    RACE = "race"


class ContractStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
