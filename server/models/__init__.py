"""ORM models package.

Imports every model so ``Base.metadata`` is fully populated for Alembic
autogenerate and for the test fixtures that create the schema.
"""

from models.base import Base
from models.enums import ContractStatus, ElementType, SessionType
from models.user import User
from models.magic_token import MagicToken
from models.league import League, LeagueMember, STARTING_BUDGET
from models.constructor import Constructor
from models.driver import Driver
from models.race import Race
from models.contract import Contract
from models.results import ConstructorResult, DriverResult
from models.scores import ConstructorScore, DriverScore, FantasyScore
from models.salary_history import SalaryHistory

__all__ = [
    "Base",
    "ContractStatus",
    "ElementType",
    "SessionType",
    "STARTING_BUDGET",
    "User",
    "MagicToken",
    "League",
    "LeagueMember",
    "Constructor",
    "Driver",
    "Race",
    "Contract",
    "DriverResult",
    "ConstructorResult",
    "DriverScore",
    "ConstructorScore",
    "FantasyScore",
    "SalaryHistory",
]
