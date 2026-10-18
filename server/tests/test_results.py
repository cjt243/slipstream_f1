"""Results ingestion + scoring against a fake OpenF1 (no network)."""

import pytest

from app import app
from dependencies import get_openf1
from models import ConstructorResult, ConstructorScore, Driver, DriverResult, DriverScore
from services.results import normalize_session, process_race_results
from tests.factories import auth_header, make_constructor, make_driver, make_race, make_user

ENTRIES = [
    {"driver_number": 1, "name": "Lando Norris", "code": "NOR", "team_name": "McLaren"},
    {"driver_number": 81, "name": "Oscar Piastri", "code": "PIA", "team_name": "McLaren"},
    {"driver_number": 3, "name": "Max Verstappen", "code": "VER", "team_name": "Red Bull Racing"},
    # stand-in not in the seeded roster
    {"driver_number": 40, "name": "Reserve Driver", "code": "RES", "team_name": "Red Bull Racing"},
]

QUALI = [
    {"driver_number": 3, "position": 1, "number_of_laps": 20},
    {"driver_number": 1, "position": 2, "number_of_laps": 20},
    {"driver_number": 81, "position": 3, "number_of_laps": 20},
    {"driver_number": 40, "position": "RT", "number_of_laps": 2},
]
SPRINT = [
    {"driver_number": 1, "position": 1, "number_of_laps": 19},
    {"driver_number": 3, "position": 2, "number_of_laps": 19},
    {"driver_number": 81, "position": 3, "number_of_laps": 19},
    {"driver_number": 40, "position": 4, "number_of_laps": 19},
]
RACE = [
    {"driver_number": 1, "position": 1, "number_of_laps": 60, "dnf": False},
    {"driver_number": 40, "position": 2, "number_of_laps": 60, "dnf": False},
    {"driver_number": 81, "position": None, "number_of_laps": 44, "dnf": True},
    {"driver_number": 3, "position": None, "number_of_laps": 10, "dnf": True},
]


class FakeResultsClient:
    def __init__(self, race_rows=RACE):
        self.sessions = {101: QUALI, 102: SPRINT, 103: race_rows}

    def fetch_session_result(self, session_key):
        return self.sessions.get(session_key, [])

    def fetch_drivers(self, session_key="latest"):
        assert session_key == 103
        return ENTRIES


@pytest.fixture
def weekend(db):
    mcl = make_constructor(db, "McLaren")
    rbr = make_constructor(db, "Red Bull Racing", color="#4781D7")
    make_driver(db, mcl, 1, "Lando Norris", code="NOR")
    make_driver(db, mcl, 81, "Oscar Piastri", code="PIA")
    make_driver(db, rbr, 3, "Max Verstappen", code="VER")
    race = make_race(db, 1, has_sprint=True, quali_session_key=101,
                     sprint_session_key=102, race_session_key=103)
    return race


def test_normalize_session_orders_unclassified_after_classified():
    places = normalize_session([
        {"driver_number": 5, "position": None, "number_of_laps": 7, "dnf": True},
        {"driver_number": 6, "position": None, "number_of_laps": 0, "dns": True},
        {"driver_number": 2, "position": 2, "number_of_laps": 50},
        {"driver_number": 4, "position": None, "number_of_laps": 30, "dnf": True},
        {"driver_number": 1, "position": 1, "number_of_laps": 50},
        {"driver_number": 7, "position": None, "number_of_laps": 50, "dsq": True},
        {"driver_number": 3, "position": "RT", "number_of_laps": 31},
    ])
    assert {n: p.position for n, p in places.items()} == {1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 7: 6, 6: 7}
    assert places[4].dnf and places[7].dnf and not places[1].dnf


def test_process_race_ingests_and_scores(db, weekend):
    processed = process_race_results(db, FakeResultsClient(), weekend)
    assert processed.drivers_scored == 4
    assert processed.constructors_scored == 2
    assert weekend.total_laps == 60

    reserve = db.query(Driver).filter_by(driver_number=40).one()
    assert reserve.salary == 400_000  # created at the floor
    assert reserve.is_active is False  # stand-ins aren't signable until seeded
    res = {r.driver_id: r for r in db.query(DriverResult).filter_by(race_id=weekend.id)}
    assert res[reserve.id].quali_pos == 4  # "RT" placed after timed drivers
    assert res[reserve.id].race_pos == 2
    assert res[reserve.id].constructor_id == reserve.constructor_id

    nor = db.query(Driver).filter_by(driver_number=1).one()
    score = db.query(DriverScore).filter_by(race_id=weekend.id, driver_id=nor.id).one()
    # Q2 (48) + sprint P1 (22) + race P1 (100) + 1 place gained (3)
    # + beat Piastri (P3) by 2 (2) + full distance (12); no history → 0 improvement
    assert (score.quali_pts, score.sprint_pts, score.race_pts) == (48, 22, 100)
    assert (score.overtake_pts, score.teammate_pts, score.completion_pts) == (3, 2, 12)
    assert score.total_pts == 187

    ver = db.query(Driver).filter_by(driver_number=3).one()
    ver_score = db.query(DriverScore).filter_by(race_id=weekend.id, driver_id=ver.id).one()
    assert ver_score.race_pts == 91  # unclassified, placed P4
    assert ver_score.completion_pts == 0  # 10 of 60 laps

    ranks = {c.constructor_id: (c.quali_pos, c.race_pos)
             for c in db.query(ConstructorResult).filter_by(race_id=weekend.id)}
    # Quali averages tie at 2.5; Red Bull has the better best driver (P1).
    # Race: McLaren avg 2.0 (P1, P3) beats Red Bull 3.0 (P2, P4).
    assert ranks[nor.constructor_id] == (2, 1)
    assert ranks[ver.constructor_id] == (1, 2)
    team_score = db.query(ConstructorScore).filter_by(
        race_id=weekend.id, constructor_id=nor.constructor_id).one()
    assert team_score.total_pts == 29 + 60


def test_reprocessing_is_idempotent(db, weekend):
    process_race_results(db, FakeResultsClient(), weekend)
    process_race_results(db, FakeResultsClient(), weekend)
    assert db.query(DriverResult).filter_by(race_id=weekend.id).count() == 4
    assert db.query(DriverScore).filter_by(race_id=weekend.id).count() == 4


def test_no_results_yet(db, weekend):
    assert process_race_results(db, FakeResultsClient(race_rows=[]), weekend) is None
    assert db.query(DriverResult).count() == 0


def test_improvement_uses_previous_rounds(db, weekend):
    process_race_results(db, FakeResultsClient(), weekend)
    # round 2: Verstappen (P4 last time) wins → avg 4 → +3 → 4 improvement pts
    round2 = make_race(db, 2, quali_session_key=101, race_session_key=103)
    swapped = [dict(r) for r in RACE]
    swapped[0], swapped[3] = dict(swapped[3], position=1, number_of_laps=60, dnf=False), \
        dict(swapped[0], position=None, number_of_laps=5, dnf=True)
    process_race_results(db, FakeResultsClient(race_rows=swapped), round2)
    ver = db.query(Driver).filter_by(driver_number=3).one()
    score = db.query(DriverScore).filter_by(race_id=round2.id, driver_id=ver.id).one()
    assert score.improvement_pts == 4


# --- routes ------------------------------------------------------------------------

@pytest.fixture
def fake_openf1():
    app.dependency_overrides[get_openf1] = lambda: FakeResultsClient()
    yield
    app.dependency_overrides.pop(get_openf1, None)


def test_admin_results_then_public_scores(client, db, weekend, fake_openf1):
    admin = make_user(db, "boss@example.com", "boss", is_admin=True)
    assert client.get(f"/api/scores/{weekend.id}/drivers").status_code == 409

    r = client.post("/api/admin/results", json={"race_id": weekend.id}, headers=auth_header(admin))
    assert r.status_code == 200
    assert r.json() == {"race_id": weekend.id, "drivers_scored": 4, "constructors_scored": 2}

    drivers = client.get(f"/api/scores/{weekend.id}/drivers").json()["scores"]
    assert drivers[0]["driver_name"] == "Lando Norris"
    assert drivers[0]["total_pts"] == 187
    assert drivers[0]["constructor_name"] == "McLaren"
    assert drivers[0]["race_pos"] == 1
    assert [d["total_pts"] for d in drivers] == sorted((d["total_pts"] for d in drivers), reverse=True)

    teams = client.get(f"/api/scores/{weekend.id}/constructors").json()["scores"]
    assert teams[0]["constructor_name"] == "McLaren"  # 29 + 60 beats 30 + 58
    assert teams[0]["race_rank"] == 1

    race = client.get(f"/api/races/{weekend.id}").json()
    assert race["status"] == "completed" and race["results_available"] is True
    assert race["total_laps"] == 60


def test_admin_results_errors(client, db, weekend):
    admin = make_user(db, "boss@example.com", "boss", is_admin=True)
    app.dependency_overrides[get_openf1] = lambda: FakeResultsClient(race_rows=[])
    try:
        r = client.post("/api/admin/results", json={"race_id": weekend.id}, headers=auth_header(admin))
        assert r.status_code == 409
        r = client.post("/api/admin/results", json={"race_id": 9999}, headers=auth_header(admin))
        assert r.status_code == 404
    finally:
        app.dependency_overrides.pop(get_openf1, None)
    assert client.get("/api/scores/9999/drivers").status_code == 404
