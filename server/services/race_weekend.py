"""One race weekend at a glance: every team's lineup and points, the
weekend winner, and the qualifying order with how many teams picked each
driver.

Lineups are secret until lockdown: before it, a viewer sees only their own
team and no pick counts. Points are live once qualifying is scored; the winner
is crowned only when the race result is in (``final``).
"""

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy.orm import Session

from models import (
    Constructor,
    ConstructorScore,
    Contract,
    Driver,
    DriverResult,
    DriverScore,
    ElementType,
    FantasyScore,
    LeagueMember,
    Race,
    StarDriver,
    User,
)
from services.fantasy import contracts_for_round
from services.races import races_with_results


@dataclass(frozen=True)
class LineupElement:
    element_type: ElementType
    element_id: int
    name: str
    code: str | None
    color: str | None
    constructor_name: str | None  # drivers only
    points: int | None  # None until the race is scored
    quali_pos: int | None  # drivers only
    race_pos: int | None  # drivers only
    is_star: bool = False  # star driver: points shown already doubled


@dataclass(frozen=True)
class Lineup:
    user: User
    rank: int | None  # None until the race is scored
    points: int | None
    elements: list[LineupElement]


@dataclass(frozen=True)
class QualiEntry:
    driver: Driver
    team: Constructor | None
    quali_pos: int | None
    quali_pts: int | None
    picked_by: int | None  # teams with this driver; None before lockdown


@dataclass(frozen=True)
class Weekend:
    race: Race
    locked: bool
    scored: bool  # some points are in (live after qualifying/sprint)
    final: bool  # the race result is in and scored
    lineups: list[Lineup]  # visible lineups: everyone after lockdown, else the viewer's
    hidden: int  # other members' lineups not shown yet (before lockdown)
    winners: list[Lineup]  # top scorer(s) once scored
    qualifying: list[QualiEntry]  # empty until qualifying results are in


def _ranked(lineups: list[Lineup]) -> list[Lineup]:
    """Order by points (ties share a rank: 1, 2, 2, 4), then username."""
    ordered = sorted(lineups, key=lambda lu: (-(lu.points or 0), lu.user.username.lower()))
    out: list[Lineup] = []
    for i, lu in enumerate(ordered):
        rank = out[-1].rank if out and out[-1].points == lu.points else i + 1
        out.append(Lineup(lu.user, rank, lu.points, lu.elements))
    return out


def race_weekend(db: Session, race: Race, league_id: int, viewer: User | None,
                 now: datetime) -> Weekend:
    locked = bool(race.lockdown_at and race.lockdown_at <= now)
    driver_scores = {s.driver_id: s for s in db.query(DriverScore).filter_by(race_id=race.id)}
    driver_pts = {i: s.total_pts for i, s in driver_scores.items()}
    team_pts = {s.constructor_id: s.total_pts
                for s in db.query(ConstructorScore).filter_by(race_id=race.id)}
    scored = bool(driver_scores)
    final = scored and race.id in races_with_results(db, [race.id])
    results = {r.driver_id: r for r in db.query(DriverResult).filter_by(race_id=race.id)}
    fantasy = {f.user_id: f.total_points
               for f in db.query(FantasyScore).filter_by(race_id=race.id, league_id=league_id)}
    teams = {t.id: t for t in db.query(Constructor).filter_by(season=race.season)}
    drivers = {d.id: d for d in db.query(Driver).filter_by(season=race.season)}

    stars = {s.user_id: s.driver_id
             for s in db.query(StarDriver).filter_by(race_id=race.id, league_id=league_id)}
    by_user: dict[int, list[Contract]] = {}
    for c in contracts_for_round(db, race.round):
        if c.league_id == league_id:
            by_user.setdefault(c.user_id, []).append(c)

    def element(c: Contract) -> LineupElement:
        if c.element_type == ElementType.DRIVER:
            d = drivers.get(c.element_id)
            res = results.get(c.element_id)
            team = teams.get(res.constructor_id if res and res.constructor_id else (d.constructor_id if d else -1))
            star = stars.get(c.user_id) == c.element_id
            return LineupElement(
                c.element_type, c.element_id, d.name if d else "Unknown", d.code if d else None,
                team.color if team else None, team.name if team else None,
                driver_pts.get(c.element_id, 0) * (2 if star else 1) if scored else None,
                res.quali_pos if res else None, res.race_pos if res else None, star,
            )
        t = teams.get(c.element_id)
        return LineupElement(
            c.element_type, c.element_id, t.name if t else "Unknown", None, t.color if t else None,
            None, team_pts.get(c.element_id, 0) if scored else None, None, None,
        )

    def lineup(user: User) -> Lineup:
        contracts = by_user.get(user.id, [])
        elements = sorted((element(c) for c in contracts),
                          key=lambda e: (e.element_type != ElementType.DRIVER, -(e.points or 0), e.name))
        points = fantasy.get(user.id, 0) if scored else None
        return Lineup(user, None, points, elements)

    members = (
        db.query(User)
        .join(LeagueMember, LeagueMember.user_id == User.id)
        .filter(LeagueMember.league_id == league_id)
        .all()
    )
    visible = [u for u in members if locked or (viewer is not None and u.id == viewer.id)]
    lineups = [lineup(u) for u in visible]
    if scored:
        lineups = _ranked(lineups)
    else:
        lineups.sort(key=lambda lu: lu.user.username.lower())
    winners = [lu for lu in lineups if lu.rank == 1 and lu.elements] if final and locked else []

    picks: dict[int, int] = {}
    for contracts in by_user.values():
        for c in contracts:
            if c.element_type == ElementType.DRIVER:
                picks[c.element_id] = picks.get(c.element_id, 0) + 1
    qualifying = [
        QualiEntry(
            driver=drivers[r.driver_id],
            team=teams.get(r.constructor_id) if r.constructor_id else None,
            quali_pos=r.quali_pos,
            quali_pts=driver_scores[r.driver_id].quali_pts if r.driver_id in driver_scores else None,
            picked_by=picks.get(r.driver_id, 0) if locked else None,
        )
        for r in results.values()
        if r.driver_id in drivers and r.quali_pos is not None
    ]
    qualifying.sort(key=lambda q: q.quali_pos)

    return Weekend(race, locked, scored, final, lineups, len(members) - len(visible), winners, qualifying)
