"""Pure scoring rules against LEAGUE_MECHANICS.md tables and worked examples."""

import pytest

from services.scoring import (
    DriverRaceInput,
    completion_points,
    constructor_quali_points,
    constructor_race_points,
    improvement_points,
    overtake_points,
    quali_points,
    race_points,
    rank_constructors,
    rolling_average,
    score_drivers,
    sprint_points,
    teammate_points,
)


def test_position_tables():
    assert [quali_points(p) for p in (1, 2, 10, 22)] == [50, 48, 32, 8]
    assert [race_points(p) for p in (1, 2, 10, 22)] == [100, 97, 73, 37]
    assert [sprint_points(p) for p in (1, 8, 20, 22)] == [22, 15, 3, 1]
    assert quali_points(None) == race_points(None) == sprint_points(None) == 0
    assert quali_points(30) == 0  # never negative


@pytest.mark.parametrize("quali,race,expected", [(10, 5, 15), (3, 1, 6), (5, 8, 0), (None, 3, 0)])
def test_overtakes_use_qualifying_position(quali, race, expected):
    assert overtake_points(quali, race) == expected


@pytest.mark.parametrize("avg,pos,expected", [
    (7, 3, 6),      # worked example: 7th by average, finished 3rd → +4 → 6
    (7, 6, 0),      # +1 earns nothing
    (7, 5, 2),
    (12, 3, 25),    # +9
    (15, 3, 30),    # +12 → capped
    (6.5, 3, 6),    # 6.5 rounds up to 7
    (6.4, 3, 4),
    (None, 1, 0),   # no history
    (3, 5, 0),      # worse than average
])
def test_improvement_points(avg, pos, expected):
    assert improvement_points(avg, pos) == expected


def test_rolling_average_uses_last_eight():
    assert rolling_average([]) is None
    assert rolling_average([4, 6]) == 5
    assert rolling_average([20, 20, 1, 1, 1, 1, 1, 1, 1, 1]) == 1  # oldest two dropped


@pytest.mark.parametrize("pos,mates,expected", [
    (1, [2], 2), (1, [4], 2), (1, [5], 5), (1, [8], 5), (1, [9], 8),
    (1, [13], 8), (1, [14], 12), (5, [3], 0), (5, [], 0), (2, [7, 3], 2),
])
def test_teammate_points(pos, mates, expected):
    assert teammate_points(pos, mates) == expected


def test_completion_points():
    # 78 laps: milestones at laps 19, 39, 58, 70
    assert completion_points(78, 78) == 12
    assert completion_points(60, 78) == 9   # DNF at lap 60 — the documented example
    assert completion_points(58, 78) == 9   # 75% milestone rounds down to lap 58
    assert completion_points(57, 78) == 6
    assert completion_points(0, 78) == 0
    assert completion_points(10, None) == 0


def test_constructor_points_and_ranking():
    assert [constructor_quali_points(r) for r in (1, 11, None)] == [30, 20, 0]
    assert [constructor_race_points(r) for r in (1, 11, 22)] == [60, 40, 18]
    # avg 2.0 vs 2.0 → tie broken by best driver; avg 7.5 last
    ranks = rank_constructors({10: [1, 3], 20: [2, 2], 30: [5, 10], 40: []})
    assert ranks == {10: 1, 20: 2, 30: 3}


def test_score_drivers_full_weekend():
    results = [
        DriverRaceInput(1, 100, quali_pos=3, sprint_pos=1, race_pos=1, laps_completed=50),
        DriverRaceInput(2, 100, quali_pos=1, sprint_pos=4, race_pos=6, laps_completed=50),
        DriverRaceInput(3, 200, quali_pos=2, sprint_pos=2, race_pos=20, laps_completed=10),
    ]
    scores = score_drivers(results, total_laps=50, has_sprint=True,
                           rolling_averages={1: 5.0, 2: 2.0, 3: None})
    winner = scores[1]
    assert (winner.quali_pts, winner.sprint_pts, winner.race_pts) == (46, 22, 100)
    assert winner.overtake_pts == 6           # P3 → P1
    assert winner.improvement_pts == 6        # avg 5 → P1 = +4
    assert winner.teammate_pts == 5           # 5 places ahead of #2
    assert winner.completion_pts == 12
    assert winner.total_pts == 46 + 22 + 100 + 6 + 6 + 5 + 12
    assert scores[2].teammate_pts == 0 and scores[2].overtake_pts == 0
    assert scores[3].teammate_pts == 0        # no teammate in the race
    assert scores[3].completion_pts == 0      # 10 of 50 laps < 25%


def test_sprint_points_only_on_sprint_weekends():
    r = [DriverRaceInput(1, 1, quali_pos=1, sprint_pos=1, race_pos=1, laps_completed=1)]
    assert score_drivers(r, total_laps=1, has_sprint=False, rolling_averages={})[1].sprint_pts == 0
