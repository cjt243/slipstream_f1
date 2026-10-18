"""Lineup reminders: email members whose team for the current race is
incomplete in the day before it locks.

Run by the scheduled autopilot (every two hours) and by
``POST /admin/reminders``. Each member gets at most one reminder per race —
a ``notifications`` row is written only after Resend accepts the email, so a
failed send, or one only logged because no API key is set, is retried on the
next run.
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from config import settings
from models import (
    ElementType,
    League,
    LeagueMember,
    Notification,
    NotificationKind,
    Race,
    User,
)
from services import races as race_service
from services.contracts import MAX_ON_ROSTER, roster_contracts
from services.email import send_lineup_reminder
from services.seed import DEFAULT_LEAGUE_INVITE_CODE

REMINDER_WINDOW = timedelta(hours=24)

# Returns True once the email is really sent (see services.email._send).
Sender = Callable[[str, str, str, datetime, list[str], str], bool]


@dataclass(frozen=True)
class ReminderRun:
    race: Race | None
    sent: list[str]  # usernames emailed this run
    logged: list[str]  # usernames whose email was only logged (no Resend key)
    failed: list[str]  # usernames whose email Resend rejected (retried next run)


def missing_elements(db: Session, member: LeagueMember, current_round: int) -> list[str]:
    """What the member's team still needs for ``current_round``, e.g.
    ["2 drivers", "a constructor"]. Empty when the team is full."""
    roster = roster_contracts(db, member, current_round)
    drivers = MAX_ON_ROSTER[ElementType.DRIVER] - sum(c.element_type == ElementType.DRIVER for c in roster)
    constructors = MAX_ON_ROSTER[ElementType.CONSTRUCTOR] - sum(
        c.element_type == ElementType.CONSTRUCTOR for c in roster
    )
    missing = []
    if drivers > 0:
        missing.append(f"{drivers} driver{'s' if drivers != 1 else ''}")
    if constructors > 0:
        missing.append("a constructor")
    return missing


def reminder_due(race: Race | None, now: datetime) -> bool:
    """True from REMINDER_WINDOW before lockdown until lockdown."""
    return bool(race and race.lockdown_at and now < race.lockdown_at <= now + REMINDER_WINDOW)


def send_lineup_reminders(db: Session, season: int, now: datetime,
                          send: Sender = send_lineup_reminder) -> ReminderRun:
    """Email every default-league member with an incomplete team for the
    current race, once, if its lockdown is within REMINDER_WINDOW. Commits
    after each email so a crash part-way never re-sends."""
    race = race_service.current_race(db, season)
    if not reminder_due(race, now):
        return ReminderRun(race, [], [], [])

    already = {
        user_id for (user_id,) in db.query(Notification.user_id).filter_by(
            race_id=race.id, kind=NotificationKind.LINEUP_REMINDER
        )
    }
    members = (
        db.query(LeagueMember, User)
        .join(User, User.id == LeagueMember.user_id)
        .join(League, League.id == LeagueMember.league_id)
        .filter(League.invite_code == DEFAULT_LEAGUE_INVITE_CODE)
        .order_by(User.id)
        .all()
    )
    link = f"{settings.frontend_url.rstrip('/')}/team"
    sent: list[str] = []
    logged: list[str] = []
    failed: list[str] = []
    for member, user in members:
        if user.id in already:
            continue
        missing = missing_elements(db, member, race.round)
        if not missing:
            continue
        try:
            delivered = send(user.email, user.username, race.name, race.lockdown_at, missing, link)
        except RuntimeError:
            failed.append(user.username)
            continue
        if not delivered:
            logged.append(user.username)
            continue
        db.add(Notification(user_id=user.id, race_id=race.id, kind=NotificationKind.LINEUP_REMINDER,
                            sent_at=now))
        db.commit()
        sent.append(user.username)
    return ReminderRun(race, sent, logged, failed)
