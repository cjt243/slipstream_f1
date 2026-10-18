"""Seed orchestration + idempotency, using a fake OpenF1 client (no network)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from datetime import datetime

from models import Base, Constructor, Driver, League, Race
from services.seed import _representative_session_key, seed_all, seed_constructors, seed_drivers

RACES_DATA = [
    {"season": 2025, "round": 1, "name": "Bahrain GP", "circuit": "Sakhir",
     "has_sprint": False, "lockdown_at": "2025-03-01T15:00:00+00:00",
     "meeting_key": 1, "quali_session_key": 101, "sprint_session_key": None,
     "race_session_key": 102},
    {"season": 2025, "round": 2, "name": "China GP", "circuit": "Shanghai",
     "has_sprint": True, "lockdown_at": "2025-03-08T07:30:00+00:00",
     "meeting_key": 2, "quali_session_key": 203, "sprint_session_key": 202,
     "race_session_key": 204},
]

DRIVERS_DATA = [
    {"driver_number": 1, "name": "Max Verstappen", "code": "VER",
     "team_name": "Red Bull Racing", "team_color": "#3671C6"},
    {"driver_number": 4, "name": "Lando Norris", "code": "NOR",
     "team_name": "McLaren", "team_color": "#FF8000"},
    {"driver_number": 81, "name": "Oscar Piastri", "code": "PIA",
     "team_name": "McLaren", "team_color": "#FF8000"},
]


class FakeClient:
    def __init__(self):
        self.race_calls = 0
        self.driver_calls = 0

    def fetch_races(self, season):
        self.race_calls += 1
        return RACES_DATA

    def fetch_drivers(self, session_key="latest"):
        self.driver_calls += 1
        # the season's most recent started weekend, not "latest"
        assert session_key == 204
        return DRIVERS_DATA


@pytest.fixture
def seed_db():
    """Fresh isolated in-memory DB that tolerates commits."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session
    engine.dispose()


def _counts(db):
    return (
        db.query(Constructor).count(),
        db.query(Driver).count(),
        db.query(Race).count(),
        db.query(League).count(),
    )


def test_seed_all_populates(seed_db):
    result = seed_all(seed_db, FakeClient(), 2025)
    assert _counts(seed_db) == (2, 3, 2, 1)  # 2 teams, 3 drivers, 2 races, 1 league
    assert result["drivers"] == 3

    # salaries assigned from the static table
    nor = seed_db.query(Driver).filter_by(driver_number=4).one()
    assert nor.salary > 0
    mclaren = seed_db.query(Constructor).filter_by(name="McLaren").one()
    assert mclaren.salary > 0
    # sprint flag + session keys captured
    china = seed_db.query(Race).filter_by(round=2).one()
    assert china.has_sprint is True
    assert china.race_session_key == 204


def test_seed_all_is_idempotent(seed_db):
    seed_all(seed_db, FakeClient(), 2025)
    first = _counts(seed_db)
    seed_all(seed_db, FakeClient(), 2025)  # run again
    assert _counts(seed_db) == first  # no duplicate rows


def test_representative_session_is_latest_started_weekend():
    before_season = datetime(2025, 2, 1)
    mid_season = datetime(2025, 3, 5)
    assert _representative_session_key(RACES_DATA, now=before_season) == 102
    assert _representative_session_key(RACES_DATA, now=mid_season) == 102
    assert _representative_session_key(RACES_DATA, now=datetime(2025, 4, 1)) == 204


def test_reseed_moves_driver_to_new_team_but_keeps_salary(seed_db):
    seed_all(seed_db, FakeClient(), 2025)
    ver = seed_db.query(Driver).filter_by(driver_number=1).one()
    ver.salary = 12_300_000  # adjusted by the salary engine since seeding
    moved = [dict(DRIVERS_DATA[0], team_name="McLaren", team_color="#FF8000")]
    constructors = seed_constructors(seed_db, moved, 2025)
    seed_drivers(seed_db, moved, 2025, constructors)
    seed_db.refresh(ver)
    assert ver.constructor.name == "McLaren"
    assert ver.salary == 12_300_000


def test_2026_starting_salaries_follow_ranking(seed_db):
    data = [
        {"driver_number": 1, "name": "Lando Norris", "code": "NOR", "team_name": "McLaren"},
        {"driver_number": 41, "name": "Arvid Lindblad", "code": "LIN", "team_name": "Racing Bulls"},
    ]
    constructors = seed_constructors(seed_db, data, 2026)
    nor, lin = seed_drivers(seed_db, data, 2026, constructors)
    assert nor.salary == 34_000_000
    assert lin.salary == 400_000
    assert constructors["McLaren"].salary == 30_000_000
