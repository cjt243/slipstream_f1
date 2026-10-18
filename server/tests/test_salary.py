"""Salary adjustment (LEAGUE_MECHANICS.md §12)."""

import pytest

from models import ConstructorScore, DriverResult, DriverScore, ElementType, SalaryHistory
from services.salary import adjust_salaries, adjusted_salary, rank_by_points
from tests.factories import make_constructor, make_driver, make_race

D, C = ElementType.DRIVER, ElementType.CONSTRUCTOR


def test_worked_example():
    # £15.8M driver ranked 8th (default £22.8M): +7.0M / 4 → +1.7M
    assert adjusted_salary(15_800_000, 8, D) == 17_500_000


@pytest.mark.parametrize("current,rank,kind,expected", [
    (10_000_000, 1, D, 12_000_000),     # +24M/4 capped at +2M
    (34_000_000, 22, D, 32_000_000),    # capped at −2M
    (10_000_000, 1, C, 13_000_000),     # constructor cap ±3M
    (30_000_000, 1, C, 30_000_000),     # exactly at target → no move
    (21_100_000, 9, D, 21_200_000),     # +100k/4 rounds to 0 → minimum +100k
    (21_300_000, 9, D, 21_200_000),     # minimum −100k
    (20_000_000, 9, D, 20_300_000),     # +1.2M/4 = +300k
    (22_350_000, 9, D, 22_150_000),     # −1.15M/4 = −287.5k → toward zero −200k
    (5_000_000, 30, D, 3_900_000),      # ranks past the table use the last row
])
def test_adjustment_rules(current, rank, kind, expected):
    assert adjusted_salary(current, rank, kind) == expected


def test_rank_by_points_breaks_ties_on_finish():
    assert rank_by_points([(1, 100, 5), (2, 120, 9), (3, 100, 2)]) == {2: 1, 3: 2, 1: 3}


def _scored_race(db, rnd, scores):
    """scores: list of (driver, total_pts, race_pos)"""
    race = make_race(db, rnd)
    for driver, pts, pos in scores:
        db.add(DriverScore(race_id=race.id, driver_id=driver.id, total_pts=pts))
        db.add(DriverResult(race_id=race.id, driver_id=driver.id, race_pos=pos,
                            constructor_id=driver.constructor_id))
    db.flush()
    return race


def test_adjust_salaries_records_history_once_and_in_order(db):
    team = make_constructor(db, "McLaren", salary=20_000_000)
    a = make_driver(db, team, 1, salary=10_000_000)
    b = make_driver(db, team, 2, salary=34_000_000)
    r1 = _scored_race(db, 1, [(a, 200, 1), (b, 50, 2)])
    db.add(ConstructorScore(race_id=r1.id, constructor_id=team.id, total_pts=90))
    r2 = _scored_race(db, 2, [(a, 100, 2), (b, 150, 1)])

    with pytest.raises(ValueError, match="Adjust round 1"):
        adjust_salaries(db, r2)

    assert adjust_salaries(db, r1) == 3
    assert a.salary == 12_000_000          # rank 1 → +2M cap
    assert b.salary == 33_600_000          # rank 2: (32.4 − 34)/4 = −400k
    assert team.salary == 22_500_000       # rank 1 constructor: +10M/4 = +2.5M (under the 3M cap)
    hist = db.query(SalaryHistory).filter_by(race_id=r1.id, element_type=D, element_id=a.id).one()
    assert (hist.salary_before, hist.salary_after) == (10_000_000, 12_000_000)

    with pytest.raises(ValueError, match="already adjusted"):
        adjust_salaries(db, r1)
    assert adjust_salaries(db, r2) == 2


def test_cannot_adjust_unscored_race(db):
    race = make_race(db, 1)
    with pytest.raises(ValueError, match="not been scored"):
        adjust_salaries(db, race)


def test_admin_salary_adjust_and_roster_shows_change(client, db):
    from tests.factories import auth_header, make_user

    admin = make_user(db, "boss@example.com", "boss", is_admin=True)
    team = make_constructor(db, "McLaren", salary=20_000_000)
    a = make_driver(db, team, 1, salary=10_000_000)
    race = _scored_race(db, 1, [(a, 200, 1)])

    r = client.post("/api/admin/salary-adjust", json={"race_id": race.id}, headers=auth_header(admin))
    assert r.status_code == 200
    assert r.json() == {"race_id": race.id, "adjustments": 1}
    again = client.post("/api/admin/salary-adjust", json={"race_id": race.id}, headers=auth_header(admin))
    assert again.status_code == 409

    driver = client.get("/api/drivers").json()["drivers"][0]
    assert driver["salary"] == 12_000_000
    assert driver["salary_change"] == 2_000_000
    team_row = client.get("/api/constructors").json()["constructors"][0]
    assert team_row["salary_change"] is None  # constructor had no score this race
