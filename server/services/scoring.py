"""Fantasy scoring rules (LEAGUE_MECHANICS.md §3–§11).

Everything here is pure: plain values in, plain values out, no DB session.
``services/results.py`` loads results, calls these, and stores the scores.

Positions are 1-based and always set for every driver who took part in a
session — ingestion places unclassified drivers after the classified ones —
so ``None`` means the driver didn't take part in that session at all.
"""

from dataclasses import dataclass

IMPROVEMENT_TABLE = {1: 0, 2: 2, 3: 4, 4: 6, 5: 9, 6: 12, 7: 16, 8: 20, 9: 25}
IMPROVEMENT_MAX = 30
ROLLING_WINDOW = 8
COMPLETION_MILESTONES = (0.25, 0.50, 0.75, 0.90)
COMPLETION_POINTS = 3


# --- Driver categories ---------------------------------------------------------

def quali_points(pos: int | None) -> int:
    """P1 = 50, −2 per place (P22 = 8)."""
    return max(0, 50 - 2 * (pos - 1)) if pos else 0


def race_points(pos: int | None) -> int:
    """P1 = 100, −3 per place (P22 = 37)."""
    return max(0, 100 - 3 * (pos - 1)) if pos else 0


def sprint_points(pos: int | None) -> int:
    """P1 = 22, −1 per place."""
    return max(0, 22 - (pos - 1)) if pos else 0


def overtake_points(quali_pos: int | None, race_pos: int | None) -> int:
    """+3 per place gained from the qualifying position (not the grid)."""
    if not quali_pos or not race_pos:
        return 0
    return max(0, quali_pos - race_pos) * 3


def rolling_average(previous_positions: list[int]) -> float | None:
    """Average of the most recent 8 race finishes (oldest first in, newest last)."""
    recent = previous_positions[-ROLLING_WINDOW:]
    return sum(recent) / len(recent) if recent else None


def improvement_points(rolling_avg: float | None, race_pos: int | None) -> int:
    """Points for beating the rolling-average finish by 2+ places (max 30)."""
    if rolling_avg is None or not race_pos:
        return 0
    improved = int(rolling_avg + 0.5) - race_pos  # round half up
    if improved <= 0:
        return 0
    if improved >= 10:
        return IMPROVEMENT_MAX
    return IMPROVEMENT_TABLE[improved]


def teammate_points(race_pos: int | None, teammate_positions: list[int]) -> int:
    """2/5/8/12 for finishing 1–3 / 4–7 / 8–12 / 13+ places ahead of the best teammate."""
    if not race_pos or not teammate_positions:
        return 0
    margin = min(teammate_positions) - race_pos
    if margin <= 0:
        return 0
    if margin <= 3:
        return 2
    if margin <= 7:
        return 5
    if margin <= 12:
        return 8
    return 12


def completion_points(laps_completed: int, total_laps: int | None) -> int:
    """+3 at each of 25/50/75/90% of race distance (milestone laps rounded down)."""
    if not total_laps or laps_completed <= 0:
        return 0
    return sum(
        COMPLETION_POINTS
        for pct in COMPLETION_MILESTONES
        if laps_completed >= int(total_laps * pct)
    )


# --- Whole-race scoring -----------------------------------------------------------

@dataclass(frozen=True)
class DriverRaceInput:
    driver_id: int
    constructor_id: int | None
    quali_pos: int | None
    sprint_pos: int | None
    race_pos: int | None
    laps_completed: int


@dataclass(frozen=True)
class DriverPoints:
    quali_pts: int
    sprint_pts: int
    race_pts: int
    overtake_pts: int
    improvement_pts: int
    teammate_pts: int
    completion_pts: int

    @property
    def total_pts(self) -> int:
        return (self.quali_pts + self.sprint_pts + self.race_pts + self.overtake_pts
                + self.improvement_pts + self.teammate_pts + self.completion_pts)


def score_drivers(
    results: list[DriverRaceInput],
    *,
    total_laps: int | None,
    has_sprint: bool,
    rolling_averages: dict[int, float | None],
) -> dict[int, DriverPoints]:
    """Score every driver in one race weekend, keyed by driver_id."""
    scores: dict[int, DriverPoints] = {}
    for r in results:
        teammates = [
            o.race_pos for o in results
            if o.driver_id != r.driver_id and o.race_pos
            and r.constructor_id is not None and o.constructor_id == r.constructor_id
        ]
        scores[r.driver_id] = DriverPoints(
            quali_pts=quali_points(r.quali_pos),
            sprint_pts=sprint_points(r.sprint_pos) if has_sprint else 0,
            race_pts=race_points(r.race_pos),
            overtake_pts=overtake_points(r.quali_pos, r.race_pos),
            improvement_pts=improvement_points(rolling_averages.get(r.driver_id), r.race_pos),
            teammate_pts=teammate_points(r.race_pos, teammates),
            completion_pts=completion_points(r.laps_completed, total_laps),
        )
    return scores


# --- Constructors ------------------------------------------------------------------

def constructor_quali_points(rank: int | None) -> int:
    """P1 = 30, −1 per place."""
    return max(0, 30 - (rank - 1)) if rank else 0


def constructor_race_points(rank: int | None) -> int:
    """P1 = 60, −2 per place."""
    return max(0, 60 - 2 * (rank - 1)) if rank else 0


def rank_constructors(positions: dict[int, list[int]]) -> dict[int, int]:
    """Rank teams by the average position of their drivers in a session
    (lower is better); ties go to the team with the better best driver.
    The rules don't specify the aggregation, so this is the league's choice."""
    ordered = sorted(
        (cid for cid, pos in positions.items() if pos),
        key=lambda cid: (sum(positions[cid]) / len(positions[cid]), min(positions[cid])),
    )
    return {cid: rank for rank, cid in enumerate(ordered, start=1)}
