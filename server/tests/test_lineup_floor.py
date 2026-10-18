"""Forgotten-lineup floor: incomplete teams score at least 600, capped at the
lowest complete team, once the race result is in."""

import pytest

from models import Contract, DriverResult, DriverScore, ElementType, FantasyScore
from services.contracts import get_membership
from services.fantasy import LINEUP_FLOOR, score_fantasy
from services.race_weekend import race_weekend
from services.races import utcnow
from tests.factories import auth_header, make_constructor, make_driver, make_race, make_user


@pytest.fixture
def league(db):
    """Round 1: Alice has a full team, Bob 3 drivers, Cara nothing."""
    team = make_constructor(db, "McLaren")
    drivers = [make_driver(db, team, i) for i in range(1, 6)]
    race = make_race(db, 1, lockdown_at=utcnow())
    users = {n: make_user(db, f"{n}@example.com", n) for n in ("alice", "bob", "cara")}
    league_id = get_membership(db, users["alice"]).league_id

    def sign(user, element_type, element_id):
        db.add(Contract(user_id=user.id, league_id=league_id, element_type=element_type,
                        element_id=element_id, race_start=1, contract_length=1, signed_salary=1))

    for d in drivers:
        sign(users["alice"], ElementType.DRIVER, d.id)
    sign(users["alice"], ElementType.CONSTRUCTOR, team.id)
    for d in drivers[:3]:
        sign(users["bob"], ElementType.DRIVER, d.id)
    db.flush()
    return {"race": race, "drivers": drivers, "league_id": league_id, **users}


def _result(db, lg, driver_pts, *, final=True):
    """Store a result (race_pos set when ``final``) and score fantasy teams."""
    for i, (d, pts) in enumerate(zip(lg["drivers"], driver_pts), start=1):
        db.add(DriverResult(race_id=lg["race"].id, driver_id=d.id, quali_pos=i, race_pos=i if final else None))
        db.add(DriverScore(race_id=lg["race"].id, driver_id=d.id, total_pts=pts))
    db.flush()
    score_fantasy(db, lg["race"])
    return {f.user_id: (f.total_points, f.floor_applied) for f in db.query(FantasyScore)}


def test_incomplete_and_empty_teams_get_the_floor(db, league):
    scores = _result(db, league, [200, 180, 150, 140, 130])  # Alice 800, Bob 530
    assert scores[league["alice"].id] == (800, False)
    assert scores[league["bob"].id] == (LINEUP_FLOOR, True)
    assert scores[league["cara"].id] == (LINEUP_FLOOR, True)


def test_floor_never_beats_the_lowest_complete_team(db, league):
    scores = _result(db, league, [100, 90, 80, 70, 60])  # Alice 400, Bob 270
    assert scores[league["alice"].id] == (400, False)
    assert scores[league["bob"].id] == (400, True)
    assert scores[league["cara"].id] == (400, True)


def test_incomplete_team_above_the_floor_keeps_its_score(db, league):
    scores = _result(db, league, [300, 250, 200, 100, 100])  # Alice 950, Bob 750
    assert scores[league["bob"].id] == (750, False)


def test_no_floor_while_live_or_without_complete_teams(db, league):
    scores = _result(db, league, [200, 180, 150, 140, 130], final=False)
    assert scores[league["bob"].id] == (530, False) and league["cara"].id not in scores

    db.query(Contract).filter_by(user_id=league["alice"].id, element_type=ElementType.CONSTRUCTOR).delete()
    db.query(DriverResult).update({DriverResult.race_pos: DriverResult.quali_pos})
    db.flush()
    score_fantasy(db, league["race"])
    rows = {f.user_id: f.floor_applied for f in db.query(FantasyScore)}
    assert not any(rows.values()) and league["cara"].id not in rows


def test_weekend_view_and_leaderboard_show_the_floor(client, db, league):
    _result(db, league, [200, 180, 150, 140, 130])
    w = race_weekend(db, league["race"], league["league_id"], None, utcnow())
    by_name = {lu.user.username: lu for lu in w.lineups}
    assert (by_name["cara"].points, by_name["cara"].floor_applied) == (LINEUP_FLOOR, True)
    assert by_name["alice"].floor_applied is False
    standings = client.get(f"/api/leaderboard/{league['race'].id}", headers=auth_header(league["cara"])).json()
    assert {s["username"]: s["race_points"] for s in standings["standings"]}["cara"] == LINEUP_FLOOR
