"""Lineup reminders: who gets one, when, and only once per race."""

from datetime import datetime, timedelta

import pytest

from models import Contract, DriverResult, ElementType, Notification
from services import email, races
from services.contracts import get_membership
from services.notifications import missing_elements, send_lineup_reminders
from tests.factories import (
    auth_header,
    make_constructor,
    make_driver,
    make_race,
    make_user,
)

NOW = datetime(2026, 10, 24, 0, 0)


class Outbox:
    def __init__(self, delivered: bool = True, fail_for: set[str] | None = None):
        self.sent: list[tuple[str, list[str]]] = []
        self.delivered = delivered
        self.fail_for = fail_for or set()

    def __call__(self, address: str, username: str, race_name: str, lockdown_at: datetime,
                 missing: list[str], link: str) -> bool:
        if address in self.fail_for:
            raise RuntimeError("Resend said no")
        self.sent.append((address, missing))
        return self.delivered


@pytest.fixture
def league(db):
    """Round 1 done; round 2 locks 21h from NOW. Alice has a full team, Bob
    has 3 drivers, Cara has nothing."""
    team = make_constructor(db, "McLaren")
    drivers = [make_driver(db, team, i) for i in range(1, 7)]
    r1 = make_race(db, 1, lockdown_at=NOW - timedelta(days=7))
    db.add(DriverResult(race_id=r1.id, driver_id=drivers[0].id, race_pos=1))
    r2 = make_race(db, 2, lockdown_at=NOW + timedelta(hours=21), name="United States Grand Prix")
    alice = make_user(db, "alice@example.com", "alice")
    bob = make_user(db, "bob@example.com", "bob")
    cara = make_user(db, "cara@example.com", "cara")
    league_id = get_membership(db, alice).league_id

    def sign(user, element_type, element_id, start=2, length=1):
        db.add(Contract(user_id=user.id, league_id=league_id, element_type=element_type,
                        element_id=element_id, race_start=start, contract_length=length,
                        signed_salary=1))

    for d in drivers[:5]:
        sign(alice, ElementType.DRIVER, d.id)
    sign(alice, ElementType.CONSTRUCTOR, team.id)
    for d in drivers[:3]:
        sign(bob, ElementType.DRIVER, d.id)
    sign(bob, ElementType.DRIVER, drivers[5].id, start=1, length=1)  # expired after round 1
    db.flush()
    return {"race": r2, "alice": alice, "bob": bob, "cara": cara}


def test_missing_elements(db, league):
    member = get_membership(db, league["bob"])
    assert missing_elements(db, member, 2) == ["2 drivers", "a constructor"]
    assert missing_elements(db, get_membership(db, league["alice"]), 2) == []
    assert missing_elements(db, get_membership(db, league["cara"]), 2) == ["5 drivers", "a constructor"]


def test_reminds_incomplete_teams_once(db, league):
    outbox = Outbox()
    run = send_lineup_reminders(db, 2026, NOW, send=outbox)
    assert run.sent == ["bob", "cara"]
    assert outbox.sent == [("bob@example.com", ["2 drivers", "a constructor"]),
                           ("cara@example.com", ["5 drivers", "a constructor"])]
    assert db.query(Notification).filter_by(race_id=league["race"].id).count() == 2

    again = send_lineup_reminders(db, 2026, NOW + timedelta(hours=2), send=outbox)
    assert again.sent == [] and len(outbox.sent) == 2


@pytest.mark.parametrize("hours_before", [25, 0, -1])
def test_only_in_the_day_before_lockdown(db, league, hours_before):
    outbox = Outbox()
    now = league["race"].lockdown_at - timedelta(hours=hours_before)
    assert send_lineup_reminders(db, 2026, now, send=outbox).sent == []
    assert outbox.sent == []


def test_failed_or_logged_sends_are_retried(db, league):
    run = send_lineup_reminders(db, 2026, NOW, send=Outbox(fail_for={"bob@example.com"}))
    assert run.sent == ["cara"] and run.failed == ["bob"]
    run = send_lineup_reminders(db, 2026, NOW, send=Outbox(delivered=False))
    assert run.logged == ["bob"] and run.sent == []
    assert send_lineup_reminders(db, 2026, NOW, send=Outbox()).sent == ["bob"]


def test_reminder_email_is_logged_without_resend_key(monkeypatch, capsys):
    monkeypatch.setattr(email.settings, "resend_api_key", None)
    delivered = email.send_lineup_reminder("a@example.com", "al", "Mexico City Grand Prix",
                                           datetime(2026, 10, 31, 21), ["a constructor"],
                                           "https://x/team")
    assert delivered is False
    out = capsys.readouterr().out
    assert "Mexico City Grand Prix lineup needs a constructor" in out
    assert "Sat 31 Oct, 21:00 UTC" in out and "https://x/team" in out


def test_admin_reminders_route(client, db, league, monkeypatch):
    monkeypatch.setattr(email.settings, "resend_api_key", None)
    monkeypatch.setattr(races, "utcnow", lambda: NOW)
    admin = make_user(db, "boss@example.com", "boss", is_admin=True)
    assert client.post("/api/admin/reminders", headers=auth_header(league["bob"])).status_code == 403
    r = client.post("/api/admin/reminders", headers=auth_header(admin))
    assert r.status_code == 200
    body = r.json()
    # No Resend key: emails are only logged, and not recorded.
    assert body == {"race_id": league["race"].id, "race_name": "United States Grand Prix",
                    "due": True, "sent": [], "logged": ["bob", "cara", "boss"], "failed": []}
    assert db.query(Notification).count() == 0
