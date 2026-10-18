"""Race weekend view: lineup visibility, points, winner and qualifying."""

from datetime import timedelta

import pytest

from models import ConstructorScore, Contract, DriverResult, DriverScore, ElementType, FantasyScore
from services import races
from services.contracts import get_membership
from services.race_weekend import race_weekend
from tests.factories import auth_header, make_constructor, make_driver, make_race, make_user

NOW = races.utcnow()


@pytest.fixture
def weekend(db):
    """Round 1 (locked 2 days ago) and round 2 (locks in 2 days). Alice and
    Bob have teams for both; Cara has none."""
    mclaren = make_constructor(db, "McLaren", color="#FF8000")
    ferrari = make_constructor(db, "Ferrari", color="#E80020")
    nor = make_driver(db, mclaren, 1, "Lando Norris", code="NOR")
    pia = make_driver(db, mclaren, 81, "Oscar Piastri", code="PIA")
    lec = make_driver(db, ferrari, 16, "Charles Leclerc", code="LEC")
    r1 = make_race(db, 1, lockdown_at=NOW - timedelta(days=2))
    r2 = make_race(db, 2, lockdown_at=NOW + timedelta(days=2))
    alice = make_user(db, "alice@example.com", "alice")
    bob = make_user(db, "bob@example.com", "bob")
    cara = make_user(db, "cara@example.com", "cara")
    league_id = get_membership(db, alice).league_id
    for user, elements in ((alice, [(ElementType.DRIVER, nor.id), (ElementType.CONSTRUCTOR, ferrari.id)]),
                           (bob, [(ElementType.DRIVER, nor.id), (ElementType.DRIVER, lec.id)])):
        for element_type, element_id in elements:
            db.add(Contract(user_id=user.id, league_id=league_id, element_type=element_type,
                            element_id=element_id, race_start=1, contract_length=2, signed_salary=1))
    db.flush()
    return {"r1": r1, "r2": r2, "alice": alice, "bob": bob, "cara": cara, "league_id": league_id,
            "nor": nor, "pia": pia, "lec": lec, "mclaren": mclaren, "ferrari": ferrari}


def _score(db, w):
    """Qualifying LEC P1, NOR P2, PIA P3; fantasy points as scoring would write them."""
    r1 = w["r1"]
    for driver, team, q, pts in ((w["lec"], w["ferrari"], 1, 150), (w["nor"], w["mclaren"], 2, 140),
                                 (w["pia"], w["mclaren"], 3, 120)):
        db.add(DriverResult(race_id=r1.id, driver_id=driver.id, constructor_id=team.id, quali_pos=q,
                            race_pos=q))
        db.add(DriverScore(race_id=r1.id, driver_id=driver.id, quali_pts=52 - 2 * q, total_pts=pts))
    db.add(ConstructorScore(race_id=r1.id, constructor_id=w["ferrari"].id, total_pts=150))
    db.add(FantasyScore(user_id=w["alice"].id, league_id=w["league_id"], race_id=r1.id, total_points=290))
    db.add(FantasyScore(user_id=w["bob"].id, league_id=w["league_id"], race_id=r1.id, total_points=290))
    db.flush()


def test_lineups_hidden_until_lockdown(db, weekend):
    w = race_weekend(db, weekend["r2"], weekend["league_id"], weekend["alice"], NOW)
    assert not w.locked
    assert [lu.user.username for lu in w.lineups] == ["alice"]
    assert w.hidden == 2
    assert w.winners == [] and w.qualifying == []

    anon = race_weekend(db, weekend["r2"], weekend["league_id"], None, NOW)
    assert anon.lineups == [] and anon.hidden == 3


def test_locked_unscored_weekend_shows_everyone(db, weekend):
    w = race_weekend(db, weekend["r1"], weekend["league_id"], None, NOW)
    assert w.locked and not w.scored
    assert [lu.user.username for lu in w.lineups] == ["alice", "bob", "cara"]
    alice = w.lineups[0]
    assert [(e.name, e.points) for e in alice.elements] == [("Lando Norris", None), ("Ferrari", None)]
    assert w.lineups[2].elements == [] and alice.rank is None


def test_scored_weekend_ranks_teams_and_crowns_winners(db, weekend):
    _score(db, weekend)
    w = race_weekend(db, weekend["r1"], weekend["league_id"], weekend["bob"], NOW)
    assert [(lu.user.username, lu.rank, lu.points) for lu in w.lineups] == [
        ("alice", 1, 290), ("bob", 1, 290), ("cara", 3, 0)]
    assert [lu.user.username for lu in w.winners] == ["alice", "bob"]  # tie; Cara had no team
    bob = w.lineups[1]
    assert [(e.code, e.points, e.quali_pos) for e in bob.elements] == [("LEC", 150, 1), ("NOR", 140, 2)]
    assert [(q.driver.code, q.quali_pos, q.quali_pts, q.picked_by) for q in w.qualifying] == [
        ("LEC", 1, 50, 1), ("NOR", 2, 48, 2), ("PIA", 3, 46, 0)]


def test_weekend_route(client, db, weekend):
    _score(db, weekend)
    r = client.get(f"/api/weekend/{weekend['r1'].id}", headers=auth_header(weekend["alice"]))
    assert r.status_code == 200
    body = r.json()
    assert body["race"]["round"] == 1 and body["race"]["results_available"]
    assert body["locked"] and body["scored"] and body["hidden_lineups"] == 0
    assert [lu["username"] for lu in body["winners"]] == ["alice", "bob"]
    assert body["lineups"][0]["is_current_user"] and not body["lineups"][1]["is_current_user"]
    assert body["lineups"][0]["elements"][0] == {
        "element_type": "driver", "element_id": weekend["nor"].id, "name": "Lando Norris", "code": "NOR",
        "color": "#FF8000", "constructor_name": "McLaren", "points": 140, "quali_pos": 2, "race_pos": 2,
        "is_star": False}
    assert body["qualifying"][0]["driver_name"] == "Charles Leclerc"

    upcoming = client.get(f"/api/weekend/{weekend['r2'].id}").json()
    assert upcoming["lineups"] == [] and upcoming["hidden_lineups"] == 3
    assert client.get("/api/weekend/999").status_code == 404
