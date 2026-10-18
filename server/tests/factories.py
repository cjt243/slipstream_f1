"""Small builders for test rows. Each flushes so ids are populated."""

from datetime import datetime

from sqlalchemy.orm import Session

from models import Constructor, Driver, League, LeagueMember, Race, User
from services.auth import create_jwt
from services.seed import seed_default_league


def make_constructor(db: Session, name: str = "McLaren", *, salary: int = 30_000_000,
                     season: int = 2026, color: str | None = "#FF8000") -> Constructor:
    c = Constructor(name=name, salary=salary, season=season, color=color)
    db.add(c)
    db.flush()
    return c


def make_driver(db: Session, constructor: Constructor, number: int, name: str | None = None, *,
                code: str | None = None, salary: int = 20_000_000, season: int = 2026) -> Driver:
    d = Driver(name=name or f"Driver {number}", code=code, driver_number=number,
               constructor_id=constructor.id, salary=salary, season=season)
    db.add(d)
    db.flush()
    return d


def make_race(db: Session, rnd: int, *, season: int = 2026, lockdown_at: datetime | None = None,
              has_sprint: bool = False, name: str | None = None, **fields: object) -> Race:
    r = Race(season=season, round=rnd, name=name or f"Round {rnd} GP", circuit=f"Circuit {rnd}",
             has_sprint=has_sprint, lockdown_at=lockdown_at, **fields)
    db.add(r)
    db.flush()
    return r


def make_user(db: Session, email: str = "user@example.com", username: str = "user", *,
              is_admin: bool = False, bank_balance: int = 100_000_000) -> User:
    u = User(email=email, username=username, is_admin=is_admin)
    db.add(u)
    db.flush()
    league: League = seed_default_league(db)
    db.add(LeagueMember(league_id=league.id, user_id=u.id, bank_balance=bank_balance))
    db.flush()
    return u


def auth_header(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_jwt(user)}"}
