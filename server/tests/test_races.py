"""Race status rules (pure) and the /races endpoints."""

from datetime import datetime, timedelta

from models import DriverResult
from services.races import COMPLETED, LOCKDOWN, UPCOMING, race_status, utcnow
from tests.factories import make_constructor, make_driver, make_race

NOW = datetime(2026, 10, 18, 12, 0)


def test_race_status_rules(db):
    race = make_race(db, 1, lockdown_at=NOW + timedelta(days=1))
    assert race_status(race, has_results=False, now=NOW) == UPCOMING
    assert race_status(race, has_results=False, now=NOW + timedelta(days=1)) == LOCKDOWN
    assert race_status(race, has_results=True, now=NOW + timedelta(days=2)) == COMPLETED
    race.lockdown_at = None
    assert race_status(race, has_results=False, now=NOW) == UPCOMING


def _add_result(db, race):
    team = make_constructor(db, f"Team {race.round}")
    driver = make_driver(db, team, 100 + race.round)
    db.add(DriverResult(race_id=race.id, driver_id=driver.id, race_pos=1, laps_completed=50))
    db.flush()


def test_list_races_statuses_and_next_race(client, db):
    now = utcnow()
    done = make_race(db, 1, lockdown_at=now - timedelta(days=14))
    locked = make_race(db, 2, lockdown_at=now - timedelta(hours=1))
    future = make_race(db, 3, lockdown_at=now + timedelta(days=6), has_sprint=True,
                       race_start_at=now + timedelta(days=7))
    make_race(db, 1, season=2025)  # other season — excluded
    _add_result(db, done)

    r = client.get("/api/races")
    assert r.status_code == 200
    body = r.json()
    assert [x["round"] for x in body["races"]] == [1, 2, 3]
    assert [x["status"] for x in body["races"]] == [COMPLETED, LOCKDOWN, UPCOMING]
    assert body["next_race"] == locked.id
    upcoming = body["races"][2]
    assert upcoming["id"] == future.id
    assert upcoming["has_sprint"] is True
    assert upcoming["lockdown_at"].endswith("Z")
    assert upcoming["race_start_at"].endswith("Z")


def test_next_race_is_null_when_season_complete(client, db):
    race = make_race(db, 1, lockdown_at=utcnow() - timedelta(days=3))
    _add_result(db, race)
    assert client.get("/api/races").json()["next_race"] is None


def test_race_detail(client, db):
    race = make_race(db, 5, lockdown_at=utcnow() - timedelta(minutes=5), name="Monaco GP")
    r = client.get(f"/api/races/{race.id}")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "Monaco GP"
    assert body["status"] == LOCKDOWN
    assert body["lockdown_active"] is True
    assert body["results_available"] is False


def test_race_detail_404(client):
    r = client.get("/api/races/9999")
    assert r.status_code == 404
    assert r.json() == {"error": "Race not found"}
