"""Live scoring: qualifying/sprint scored before the race, without the race
counting as completed."""

from datetime import datetime

import pytest

from app import app
from dependencies import get_openf1
from models import (
    Contract,
    Driver,
    DriverResult,
    DriverScore,
    ElementType,
    FantasyScore,
)
from services import races as race_service
from services.contracts import get_membership
from services.race_weekend import race_weekend
from services.results import (
    ingest_early_sessions,
    process_early_sessions,
    process_race_results,
)
from services.salary import adjust_salaries
from services.weekend import process_due_races
from tests.factories import auth_header, make_race, make_user
from tests.test_results import ENTRIES, QUALI, RACE, SPRINT
from tests.test_results import weekend as weekend  # noqa: F401 — fixture

LOCKDOWN = datetime(2026, 10, 24, 21, 0)
START = datetime(2026, 10, 25, 20, 0)


class LiveClient:
    """OpenF1 mid-weekend: only the sessions in ``done`` have results."""

    def __init__(self, done: set[int]):
        self.sessions = {k: v for k, v in {101: QUALI, 102: SPRINT, 103: RACE}.items() if k in done}

    def fetch_session_result(self, session_key):
        return self.sessions.get(session_key, [])

    def fetch_drivers(self, session_key="latest"):
        return ENTRIES


@pytest.fixture
def race(db, weekend):  # noqa: F811
    weekend.lockdown_at, weekend.race_start_at = LOCKDOWN, START
    db.flush()
    return weekend


def _points(db, race):
    return {s.driver_id: (s.quali_pts, s.sprint_pts, s.race_pts, s.total_pts)
            for s in db.query(DriverScore).filter_by(race_id=race.id)}


def test_nothing_to_score_before_any_session(db, race):
    assert ingest_early_sessions(db, LiveClient(set()), race) is None
    assert db.query(DriverResult).count() == 0


def test_sprint_then_qualifying_scored_live(db, race):
    assert process_early_sessions(db, LiveClient({102}), race).drivers_scored == 4
    rows = {r.driver_id: r for r in db.query(DriverResult).filter_by(race_id=race.id)}
    assert all(r.race_pos is None and r.quali_pos is None for r in rows.values())
    assert sorted(p[1] for p in _points(db, race).values()) == [19, 20, 21, 22]

    process_early_sessions(db, LiveClient({101, 102}), race)
    pts = _points(db, race)
    assert all(race_pts == 0 for _, _, race_pts, _ in pts.values())
    assert sorted(q for q, *_ in pts.values()) == [44, 46, 48, 50]  # RT driver ranks 4th
    # The race isn't completed: it's still the current race, and still locked.
    assert race_service.races_with_results(db) == set()
    assert race_service.current_race(db, 2026).id == race.id


def test_live_points_reach_fantasy_but_not_salaries(db, race):
    user = make_user(db)
    league_id = get_membership(db, user).league_id
    ver = db.query(Driver).filter_by(code="VER").one()
    db.add(Contract(user_id=user.id, league_id=league_id, element_type=ElementType.DRIVER,
                    element_id=ver.id, race_start=1, contract_length=1, signed_salary=1))
    db.flush()
    process_early_sessions(db, LiveClient({101, 102}), race)
    live = db.query(FantasyScore).filter_by(user_id=user.id).one().total_points
    assert live == 50 + 21  # pole + P2 in the sprint
    with pytest.raises(ValueError, match="not been scored"):
        adjust_salaries(db, race)

    process_race_results(db, LiveClient({101, 102, 103}), race)
    assert race_service.races_with_results(db) == {race.id}
    assert db.query(FantasyScore).filter_by(user_id=user.id).one().total_points > live
    # Full ingestion owns the race from now on.
    assert ingest_early_sessions(db, LiveClient({101, 102, 103}), race) is None
    assert adjust_salaries(db, race) > 0


def test_autopilot_scores_locked_weekend_live(db, race):
    log = process_due_races(db, LiveClient({101, 102}), 2026, datetime(2026, 10, 25, 1, 0))
    assert log == ["R1 Round 1 GP: live — 4 drivers scored from qualifying/sprint",
                   "R1 Round 1 GP: not due yet"]
    # Before lockdown nothing is fetched or scored.
    nxt = make_race(db, 2, lockdown_at=datetime(2026, 10, 31, 21), race_start_at=datetime(2026, 11, 1, 20),
                    quali_session_key=101, race_session_key=103)
    log = process_due_races(db, LiveClient({101, 102, 103}), 2026, datetime(2026, 10, 26, 1, 0))
    assert log[0].startswith("R1 Round 1 GP: 4 drivers scored")
    assert log[1:] == ["R2 Round 2 GP: not due yet"]
    assert db.query(DriverResult).filter_by(race_id=nxt.id).count() == 0
    # Race result late: qualifying still scored live.
    log = process_due_races(db, LiveClient({101}), 2026, datetime(2026, 11, 2))
    assert log == ["R2 Round 2 GP: live — 4 drivers scored from qualifying/sprint",
                   "R2 Round 2 GP: no results from OpenF1 yet"]


def test_weekend_view_is_live_without_a_winner(db, race):
    user = make_user(db)
    league_id = get_membership(db, user).league_id
    nor = db.query(Driver).filter_by(code="NOR").one()
    db.add(Contract(user_id=user.id, league_id=league_id, element_type=ElementType.DRIVER,
                    element_id=nor.id, race_start=1, contract_length=1, signed_salary=1))
    db.flush()
    process_early_sessions(db, LiveClient({101, 102}), race)
    w = race_weekend(db, race, league_id, user, datetime(2026, 10, 25, 1, 0))
    assert w.scored and not w.final and w.winners == []
    assert w.lineups[0].points == 48 + 22 and w.lineups[0].rank == 1

    process_race_results(db, LiveClient({101, 102, 103}), race)
    w = race_weekend(db, race, league_id, user, datetime(2026, 10, 26, 1, 0))
    assert w.final and [lu.user.id for lu in w.winners] == [user.id]


def test_admin_results_scores_live_before_the_race(client, db, race):
    admin = make_user(db, "boss@example.com", "boss", is_admin=True)
    app.dependency_overrides[get_openf1] = lambda: LiveClient({101})
    try:
        r = client.post("/api/admin/results", json={"race_id": race.id}, headers=auth_header(admin))
    finally:
        app.dependency_overrides.pop(get_openf1, None)
    assert r.status_code == 200
    assert r.json() == {"race_id": race.id, "drivers_scored": 4, "constructors_scored": 2, "live": True}
    assert client.get(f"/api/races/{race.id}").json()["results_available"] is False
