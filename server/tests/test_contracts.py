"""Contract signing, release, cooldown and expiry (LEAGUE_MECHANICS.md §5–§6)."""

from datetime import timedelta

import pytest

from models import Contract, DriverResult, ElementType, LeagueMember
from services.contracts import (
    ContractConflict,
    InsufficientFunds,
    release_contract,
    settle_expired_contracts,
    sign_contract,
)
from services.races import utcnow
from tests.factories import auth_header, make_constructor, make_driver, make_race, make_user

D, C = ElementType.DRIVER, ElementType.CONSTRUCTOR
NOW = utcnow()


@pytest.fixture
def league(db):
    """Round 1 completed, round 2 open (locks in 2 days), rounds 3–4 to come."""
    team = make_constructor(db, "McLaren", salary=25_000_000)
    other = make_constructor(db, "Ferrari", salary=20_000_000)
    drivers = [make_driver(db, team if i % 2 else other, i, salary=10_000_000 + i * 1_000_000)
               for i in range(1, 8)]
    r1 = make_race(db, 1, lockdown_at=NOW - timedelta(days=12))
    db.add(DriverResult(race_id=r1.id, driver_id=drivers[0].id, race_pos=1))
    races = [r1] + [make_race(db, n, lockdown_at=NOW + timedelta(days=2 + 7 * (n - 2)))
                    for n in (2, 3, 4)]
    user = make_user(db)
    return {"user": user, "team": team, "other": other, "drivers": drivers, "races": races}


def _cash(db, user):
    return db.query(LeagueMember).filter_by(user_id=user.id).one().bank_balance


def _sign(db, lg, element, length=1, kind=D, now=NOW):
    return sign_contract(db, lg["user"], kind, element.id, length, season=2026, now=now)


def test_sign_moves_salary_from_cash(db, league):
    d = league["drivers"][0]
    c = _sign(db, league, d, length=3)
    assert (c.race_start, c.contract_length, c.signed_salary) == (2, 3, d.salary)
    assert _cash(db, league["user"]) == 100_000_000 - d.salary


@pytest.mark.parametrize("length", [0, 6])
def test_length_must_be_1_to_5(db, league, length):
    with pytest.raises(ValueError, match="1–5"):
        _sign(db, league, league["drivers"][0], length=length)


def test_length_cannot_outrun_the_season(db, league):
    with pytest.raises(ValueError, match="Only 3 races left"):
        _sign(db, league, league["drivers"][0], length=4)


def test_roster_limits(db, league):
    for d in league["drivers"][:5]:
        _sign(db, league, d)
    with pytest.raises(ValueError, match="already has 5 drivers"):
        _sign(db, league, league["drivers"][5])
    _sign(db, league, league["team"], kind=C)
    with pytest.raises(ValueError, match="already has 1 constructor"):
        _sign(db, league, league["other"], kind=C)


def test_duplicate_is_a_conflict(db, league):
    _sign(db, league, league["drivers"][0])
    with pytest.raises(ContractConflict, match="already on your team"):
        _sign(db, league, league["drivers"][0])


def test_budget(db, league):
    member = db.query(LeagueMember).filter_by(user_id=league["user"].id).one()
    member.bank_balance = 5_000_000
    with pytest.raises(InsufficientFunds):
        _sign(db, league, league["drivers"][0])


def test_inactive_driver_cannot_be_signed(db, league):
    league["drivers"][0].is_active = False
    with pytest.raises(ValueError, match="current grid"):
        _sign(db, league, league["drivers"][0])


def test_no_changes_during_lockdown(db, league):
    after_lock = NOW + timedelta(days=2, hours=1)
    with pytest.raises(ValueError, match="Lockdown is active"):
        _sign(db, league, league["drivers"][0], now=after_lock)
    c = _sign(db, league, league["drivers"][0])
    with pytest.raises(ValueError, match="Lockdown is active"):
        release_contract(db, league["user"], c.id, season=2026, now=after_lock)


def test_release_before_first_race_is_free_cancellation(db, league):
    d = league["drivers"][0]
    c = _sign(db, league, d)
    result = release_contract(db, league["user"], c.id, season=2026, now=NOW)
    assert (result.penalty, result.refund) == (0, d.salary)
    assert _cash(db, league["user"]) == 100_000_000
    assert db.query(Contract).count() == 0
    _sign(db, league, d)  # no cooldown after a cancellation


def _complete(db, race, driver):
    db.add(DriverResult(race_id=race.id, driver_id=driver.id, race_pos=1))
    db.flush()


def test_early_release_after_racing_pays_current_salary_less_3pct(db, league):
    d = league["drivers"][0]
    c = _sign(db, league, d, length=3)
    _complete(db, league["races"][1], d)  # round 2 done; round 3 is open
    d.salary = 12_000_000                 # salary moved after the race
    result = release_contract(db, league["user"], c.id, season=2026, now=NOW)
    assert result.penalty == 360_000
    assert result.refund == 11_640_000
    assert _cash(db, league["user"]) == 100_000_000 - c.signed_salary + 11_640_000
    assert c.released_early and c.released_at_race == 2
    # one-race interval: not for round 3…
    with pytest.raises(ContractConflict, match="just left"):
        _sign(db, league, d)
    # …but fine for round 4
    _complete(db, league["races"][2], d)
    _sign(db, league, d)


def test_expiry_pays_post_race_salary_and_starts_cooldown(db, league):
    d = league["drivers"][0]
    c = _sign(db, league, d, length=1)
    _complete(db, league["races"][1], d)
    d.salary = 13_500_000
    assert settle_expired_contracts(db, league["races"][1]) == 1
    assert settle_expired_contracts(db, league["races"][1]) == 0  # idempotent
    assert c.released_at_race == 2 and not c.released_early
    assert _cash(db, league["user"]) == 100_000_000 - c.signed_salary + 13_500_000
    with pytest.raises(ContractConflict):
        _sign(db, league, d)


def test_release_unknown_or_someone_elses_contract(db, league):
    c = _sign(db, league, league["drivers"][0])
    stranger = make_user(db, "x@example.com", "x")
    assert release_contract(db, stranger, c.id, season=2026, now=NOW) is None
    assert release_contract(db, league["user"], 9999, season=2026, now=NOW) is None


# --- routes ------------------------------------------------------------------------

def test_contract_routes(client, db, league):
    h = auth_header(league["user"])
    d0, d1 = league["drivers"][:2]
    r = client.post("/api/contracts", json={"element_type": "driver", "element_id": d0.id,
                                            "contract_length": 2}, headers=h)
    assert r.status_code == 201
    body = r.json()
    assert body["element_name"] == d0.name
    assert body["races_remaining"] == 2 and body["last_round"] == 3
    assert body["cancellable"] is True

    r = client.post("/api/contracts", json={"element_type": "constructor",
                                            "element_id": league["team"].id, "contract_length": 1},
                    headers=h)
    assert r.status_code == 201

    team = client.get("/api/contracts", headers=h).json()
    assert [c["element_type"] for c in team["contracts"]] == ["driver", "constructor"]
    assert team["contract_value"] == d0.salary + league["team"].salary
    assert team["team_value"] == 100_000_000
    assert team["current_race"]["round"] == 2 and team["current_race"]["locked"] is False
    assert team["current_race"]["races_left"] == 3

    codes = {
        "dup": client.post("/api/contracts", json={"element_type": "driver", "element_id": d0.id,
                                                   "contract_length": 1}, headers=h).status_code,
        "len": client.post("/api/contracts", json={"element_type": "driver", "element_id": d1.id,
                                                   "contract_length": 9}, headers=h).status_code,
        "missing": client.post("/api/contracts", json={"element_type": "driver", "element_id": 999,
                                                       "contract_length": 1}, headers=h).status_code,
        "anon": client.get("/api/contracts").status_code,
    }
    assert codes == {"dup": 409, "len": 400, "missing": 404, "anon": 401}

    r = client.delete(f"/api/contracts/{body['id']}", headers=h)
    assert r.status_code == 200
    assert r.json()["penalty"] == 0 and r.json()["released"] is True
    assert client.delete(f"/api/contracts/{body['id']}", headers=h).status_code == 404


def test_contracts_insufficient_funds_is_402(client, db, league):
    db.query(LeagueMember).filter_by(user_id=league["user"].id).one().bank_balance = 1
    r = client.post("/api/contracts", json={"element_type": "driver",
                                            "element_id": league["drivers"][0].id,
                                            "contract_length": 1}, headers=auth_header(league["user"]))
    assert r.status_code == 402
