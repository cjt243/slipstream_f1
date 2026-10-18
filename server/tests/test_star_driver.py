"""Star driver: one cheap driver per race whose points count double."""

from datetime import timedelta

import pytest

from models import Contract, DriverScore, ElementType, FantasyScore, StarDriver
from services.contracts import clear_star_driver, release_contract, set_star_driver, sign_contract
from services.fantasy import score_fantasy
from tests.factories import auth_header, make_driver
from tests.test_contracts import NOW
from tests.test_contracts import league as league  # noqa: F401 — fixture

D = ElementType.DRIVER


@pytest.fixture
def team(db, league):  # noqa: F811
    """Two drivers signed for round 2: one at £11M, one at £18M (too dear)."""
    cheap = league["drivers"][0]
    dear = make_driver(db, league["team"], 44, "Pricey Driver", salary=18_000_000)
    for d in (cheap, dear):
        sign_contract(db, league["user"], D, d.id, 2, season=2026, now=NOW)
    return {**league, "cheap": cheap, "dear": dear, "round2": league["races"][1]}


def _star(db, t, driver, now=NOW):
    return set_star_driver(db, t["user"], driver.id, season=2026, now=now)


def test_pick_and_change_star(db, team):
    star = _star(db, team, team["cheap"])
    assert (star.race_id, star.driver_id) == (team["round2"].id, team["cheap"].id)
    other = make_driver(db, team["team"], 45, "Another", salary=12_000_000)
    sign_contract(db, team["user"], D, other.id, 1, season=2026, now=NOW)
    _star(db, team, other)
    assert db.query(StarDriver).one().driver_id == other.id  # replaced, not added


def test_star_must_be_cheap_and_on_your_team(db, team):
    with pytest.raises(ValueError, match="under £18M"):
        _star(db, team, team["dear"])
    with pytest.raises(ValueError, match="isn't on your team"):
        _star(db, team, team["drivers"][3])
    with pytest.raises(LookupError):
        set_star_driver(db, team["user"], 99999, season=2026, now=NOW)


def test_star_locked_at_lockdown(db, team):
    after_lock = team["round2"].lockdown_at + timedelta(minutes=1)
    with pytest.raises(ValueError, match="Lockdown"):
        _star(db, team, team["cheap"], now=after_lock)
    _star(db, team, team["cheap"])
    with pytest.raises(ValueError, match="Lockdown"):
        clear_star_driver(db, team["user"], season=2026, now=after_lock)
    clear_star_driver(db, team["user"], season=2026, now=NOW)
    assert db.query(StarDriver).count() == 0


def test_releasing_the_star_clears_it(db, team):
    _star(db, team, team["cheap"])
    c = db.query(Contract).filter_by(element_id=team["cheap"].id).one()
    release_contract(db, team["user"], c.id, season=2026, now=NOW)
    assert db.query(StarDriver).count() == 0


def test_star_points_count_double(db, team):
    _star(db, team, team["cheap"])
    r2 = team["round2"]
    db.add(DriverScore(race_id=r2.id, driver_id=team["cheap"].id, total_pts=100))
    db.add(DriverScore(race_id=r2.id, driver_id=team["dear"].id, total_pts=150))
    db.flush()
    score_fantasy(db, r2)
    assert db.query(FantasyScore).filter_by(race_id=r2.id).one().total_points == 2 * 100 + 150


def test_star_routes(client, db, team):
    headers = auth_header(team["user"])
    assert client.get("/api/contracts", headers=headers).json()["star_driver_id"] is None
    r = client.put("/api/contracts/star", json={"driver_id": team["cheap"].id}, headers=headers)
    assert r.status_code == 200 and r.json() == {"star_driver_id": team["cheap"].id}
    body = client.get("/api/contracts", headers=headers).json()
    assert body["star_driver_id"] == team["cheap"].id and body["star_max_salary"] == 18_000_000
    r = client.put("/api/contracts/star", json={"driver_id": team["dear"].id}, headers=headers)
    assert r.status_code == 400 and "under £18M" in r.json()["error"]
    assert client.put("/api/contracts/star", json={"driver_id": 99999}, headers=headers).status_code == 404
    r = client.delete("/api/contracts/star", headers=headers)
    assert r.status_code == 200 and r.json() == {"star_driver_id": None}
    assert client.get("/api/contracts", headers=headers).json()["star_driver_id"] is None
