"""Fantasy points per team, team-value floor, leaderboard and the post-race pipeline."""

from datetime import timedelta

import pytest

from models import (
    ConstructorScore,
    Contract,
    DriverResult,
    DriverScore,
    ElementType,
    FantasyScore,
    LeagueMember,
)
from services.fantasy import apply_team_value_floor, score_fantasy, season_standings
from services.races import utcnow
from services.seed import seed_default_league
from services.weekend import finalize_race
from tests.factories import auth_header, make_constructor, make_driver, make_race, make_user

D, C = ElementType.DRIVER, ElementType.CONSTRUCTOR


@pytest.fixture
def world(db):
    team = make_constructor(db, "McLaren", salary=20_000_000)
    d1 = make_driver(db, team, 1, "Lando Norris", salary=30_000_000)
    d2 = make_driver(db, team, 81, "Oscar Piastri", salary=10_000_000)
    races = [make_race(db, n, lockdown_at=utcnow() + timedelta(days=n)) for n in (1, 2, 3)]
    alice = make_user(db, "alice@example.com", "alice")
    bob = make_user(db, "bob@example.com", "bob")
    carol = make_user(db, "carol@example.com", "carol")  # never signs anyone
    league = seed_default_league(db)
    return {"team": team, "d1": d1, "d2": d2, "races": races, "alice": alice, "bob": bob,
            "carol": carol, "league": league}


def _contract(db, w, user, kind, element, start, length, **kw):
    c = Contract(user_id=user.id, league_id=w["league"].id, element_type=kind,
                 element_id=element.id, race_start=start, contract_length=length,
                 signed_salary=element.salary, **kw)
    db.add(c)
    db.flush()
    return c


def _score(db, race, driver_pts, team_pts):
    for driver, pts in driver_pts.items():
        db.add(DriverScore(race_id=race.id, driver_id=driver.id, total_pts=pts))
        db.add(DriverResult(race_id=race.id, driver_id=driver.id, race_pos=1,
                            constructor_id=driver.constructor_id))
    for team, pts in team_pts.items():
        db.add(ConstructorScore(race_id=race.id, constructor_id=team.id, total_pts=pts))
    db.flush()


def test_team_points_sum_contracts_covering_the_round(db, world):
    w = world
    r1, r2, _ = w["races"]
    _contract(db, w, w["alice"], D, w["d1"], 1, 2)
    _contract(db, w, w["alice"], C, w["team"], 1, 1)
    _contract(db, w, w["bob"], D, w["d2"], 2, 1)
    _contract(db, w, w["bob"], D, w["d1"], 1, 3, released_early=True, released_at_race=1)
    _score(db, r1, {w["d1"]: 150, w["d2"]: 90}, {w["team"]: 80})
    _score(db, r2, {w["d1"]: 100, w["d2"]: 120}, {w["team"]: 70})

    assert score_fantasy(db, r1) == 2
    assert score_fantasy(db, r2) == 2
    pts = {(f.user_id, f.race_id): f.total_points for f in db.query(FantasyScore)}
    assert pts[(w["alice"].id, r1.id)] == 150 + 80
    assert pts[(w["alice"].id, r2.id)] == 100          # constructor contract ended at R1
    assert pts[(w["bob"].id, r1.id)] == 150            # released after R1 still counts for R1
    assert pts[(w["bob"].id, r2.id)] == 120            # …but not R2
    assert (w["carol"].id, r1.id) not in pts           # no team, no row

    score_fantasy(db, r1)  # idempotent
    assert db.query(FantasyScore).filter_by(race_id=r1.id).count() == 2

    standings = season_standings(db, w["league"].id, 2026)
    assert [(s.user.username, s.rank, s.points) for s in standings] == [
        ("alice", 1, 330), ("bob", 2, 270), ("carol", 3, 0)]


def test_ties_share_a_rank(db, world):
    w = world
    r1 = w["races"][0]
    _contract(db, w, w["alice"], D, w["d1"], 1, 1)
    _contract(db, w, w["bob"], D, w["d1"], 1, 1)
    _score(db, r1, {w["d1"]: 100}, {})
    score_fantasy(db, r1)
    ranks = [(s.user.username, s.rank) for s in season_standings(db, w["league"].id, 2026)]
    assert ranks == [("alice", 1), ("bob", 1), ("carol", 3)]


def test_team_value_floor_tops_up_cash(db, world):
    w = world
    member = db.query(LeagueMember).filter_by(user_id=w["alice"].id).one()
    _contract(db, w, w["alice"], D, w["d1"], 1, 3)
    member.bank_balance = 100_000_000 - 30_000_000
    w["d1"].salary = 26_000_000  # lost £4M of value
    assert apply_team_value_floor(db, current_round=2) == 1
    assert member.bank_balance == 74_000_000  # 74 + 26 = 100


def test_finalize_race_adjusts_settles_and_floors(db, world):
    w = world
    r1 = w["races"][0]
    c = _contract(db, w, w["alice"], D, w["d2"], 1, 1)
    member = db.query(LeagueMember).filter_by(user_id=w["alice"].id).one()
    member.bank_balance -= c.signed_salary
    _score(db, r1, {w["d1"]: 50, w["d2"]: 200}, {w["team"]: 60})
    assert finalize_race(db, r1) == 3
    assert w["d2"].salary == 12_000_000          # top scorer: +2M cap
    assert c.released_at_race == 1               # expired and settled…
    assert member.bank_balance == 102_000_000    # …at the post-race salary
    with pytest.raises(ValueError, match="already adjusted"):
        finalize_race(db, r1)


def test_leaderboard_routes(client, db, world):
    w = world
    r1 = w["races"][0]
    _contract(db, w, w["alice"], D, w["d1"], 1, 2)
    _score(db, r1, {w["d1"]: 150}, {})
    score_fantasy(db, r1)

    body = client.get("/api/leaderboard", headers=auth_header(w["bob"])).json()
    assert [s["username"] for s in body["standings"]] == ["alice", "bob", "carol"]
    alice, bob = body["standings"][:2]
    assert alice["total_points"] == 150 and alice["rank"] == 1
    assert alice["team_value"] == 100_000_000 + w["d1"].salary  # cash untouched in this setup
    assert bob["is_current_user"] is True and alice["is_current_user"] is False
    assert body["races"] == [{"id": r1.id, "round": 1, "name": r1.name}]

    race = client.get(f"/api/leaderboard/{r1.id}").json()
    assert race["standings"][0] == {"rank": 1, "user_id": w["alice"].id, "username": "alice",
                                    "race_points": 150, "is_current_user": False}
    assert client.get("/api/leaderboard/9999").status_code == 404
