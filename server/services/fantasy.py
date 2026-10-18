"""Per-user fantasy points and the league leaderboard.

A user's points for a race are the summed fantasy points of every driver and
constructor on their team for that round: contracts covering the round that
hadn't been released before it. Their star driver's points count twice.

Forgotten-lineup floor: once the race result is in, a member whose team that
round was incomplete (or empty) scores at least LINEUP_FLOOR — capped at the
lowest complete team's score, so skipping a lineup never beats playing one.
No complete team that race (e.g. before the league started) → no floor. Rows are only written for members with a
team that race, so pre-league races don't clutter the standings.
"""

from dataclasses import dataclass

from sqlalchemy import func
from sqlalchemy.orm import Session

from models import (
    ConstructorScore,
    Contract,
    DriverScore,
    ElementType,
    FantasyScore,
    LeagueMember,
    Race,
    StarDriver,
    User,
)
from models.league import STARTING_BUDGET
from services.contracts import MAX_ON_ROSTER, get_element, last_round, roster_contracts
from services.races import races_with_results

LINEUP_FLOOR = 600


def contracts_for_round(db: Session, rnd: int) -> list[Contract]:
    """Contracts on a team for round ``rnd`` (cancelled ones no longer exist)."""
    rows = db.query(Contract).filter(Contract.race_start <= rnd).all()
    return [
        c for c in rows
        if last_round(c) >= rnd and (c.released_at_race is None or c.released_at_race >= rnd)
    ]


def score_fantasy(db: Session, race: Race) -> int:
    """(Re)compute every team's points for a scored race. Returns teams scored."""
    driver_pts = {s.driver_id: s.total_pts for s in db.query(DriverScore).filter_by(race_id=race.id)}
    team_pts = {s.constructor_id: s.total_pts
                for s in db.query(ConstructorScore).filter_by(race_id=race.id)}
    stars = {(s.user_id, s.league_id): s.driver_id for s in db.query(StarDriver).filter_by(race_id=race.id)}
    totals: dict[tuple[int, int], int] = {}
    counts: dict[tuple[int, int], dict[ElementType, int]] = {}
    for c in contracts_for_round(db, race.round):
        pts = (driver_pts if c.element_type == ElementType.DRIVER else team_pts).get(c.element_id, 0)
        key = (c.user_id, c.league_id)
        if c.element_type == ElementType.DRIVER and stars.get(key) == c.element_id:
            pts *= 2
        totals[key] = totals.get(key, 0) + pts
        per_type = counts.setdefault(key, {})
        per_type[c.element_type] = per_type.get(c.element_type, 0) + 1

    floored: set[tuple[int, int]] = set()
    if race.id in races_with_results(db, [race.id]):
        complete = {key for key, per_type in counts.items() if per_type == MAX_ON_ROSTER}
        for league_id in {lid for _, lid in complete}:
            floor = min(LINEUP_FLOOR, min(totals[k] for k in complete if k[1] == league_id))
            members = db.query(LeagueMember.user_id).filter_by(league_id=league_id)
            for (user_id,) in members:
                key = (user_id, league_id)
                if key not in complete and totals.get(key, 0) < floor:
                    totals[key] = floor
                    floored.add(key)

    existing = {(f.user_id, f.league_id): f for f in db.query(FantasyScore).filter_by(race_id=race.id)}
    for key, row in existing.items():
        if key not in totals:
            db.delete(row)  # team was emptied since a previous scoring run
    for (user_id, league_id), points in totals.items():
        row = existing.get((user_id, league_id)) or FantasyScore(
            user_id=user_id, league_id=league_id, race_id=race.id
        )
        row.total_points = points
        row.floor_applied = (user_id, league_id) in floored
        db.add(row)
    db.flush()
    return len(totals)


def team_value(db: Session, member: LeagueMember, current_round: int | None) -> int:
    """Cash plus the current salary of everything under contract."""
    value = member.bank_balance
    for c in roster_contracts(db, member, current_round):
        element = get_element(db, c.element_type, c.element_id)
        value += element.salary if element else c.signed_salary
    return value


def apply_team_value_floor(db: Session, current_round: int | None) -> int:
    """Top cash up so no team is worth less than the starting £100M
    (LEAGUE_MECHANICS.md §6.3). Returns how many members were topped up."""
    topped = 0
    for member in db.query(LeagueMember).all():
        shortfall = STARTING_BUDGET - team_value(db, member, current_round)
        if shortfall > 0:
            member.bank_balance += shortfall
            topped += 1
    db.flush()
    return topped


@dataclass(frozen=True)
class Standing:
    rank: int
    user: User
    points: int
    member: LeagueMember


def _ranked(rows: list[tuple[User, LeagueMember, int]]) -> list[Standing]:
    """Rank by points; equal points share a rank (1, 2, 2, 4)."""
    ordered = sorted(rows, key=lambda r: (-r[2], r[0].username.lower()))
    standings: list[Standing] = []
    for i, (user, member, points) in enumerate(ordered):
        rank = standings[-1].rank if standings and standings[-1].points == points else i + 1
        standings.append(Standing(rank, user, points, member))
    return standings


def season_standings(db: Session, league_id: int, season: int) -> list[Standing]:
    totals = dict(
        db.query(FantasyScore.user_id, func.sum(FantasyScore.total_points))
        .join(Race, Race.id == FantasyScore.race_id)
        .filter(FantasyScore.league_id == league_id, Race.season == season)
        .group_by(FantasyScore.user_id)
        .all()
    )
    members = (
        db.query(User, LeagueMember)
        .join(LeagueMember, LeagueMember.user_id == User.id)
        .filter(LeagueMember.league_id == league_id)
        .all()
    )
    return _ranked([(u, m, int(totals.get(u.id, 0))) for u, m in members])


def race_standings(db: Session, league_id: int, race_id: int) -> list[Standing]:
    points = dict(
        db.query(FantasyScore.user_id, FantasyScore.total_points)
        .filter(FantasyScore.league_id == league_id, FantasyScore.race_id == race_id)
        .all()
    )
    members = (
        db.query(User, LeagueMember)
        .join(LeagueMember, LeagueMember.user_id == User.id)
        .filter(LeagueMember.league_id == league_id)
        .all()
    )
    return _ranked([(u, m, points.get(u.id, 0)) for u, m in members])


def scored_races(db: Session, league_id: int, season: int) -> list[Race]:
    """Races with fantasy points in this league, by round."""
    return (
        db.query(Race)
        .join(FantasyScore, FantasyScore.race_id == Race.id)
        .filter(FantasyScore.league_id == league_id, Race.season == season)
        .distinct()
        .order_by(Race.round)
        .all()
    )
