"""Salary table integrity and starting-salary lookups."""

from data.salaries import (
    CONSTRUCTOR_DEFAULT_SALARY,
    DRIVER_DEFAULT_SALARY,
    STARTING_CONSTRUCTOR_RANKING,
    STARTING_DRIVER_RANKING,
    starting_constructor_salary,
    starting_driver_salary,
)


def test_driver_default_table_matches_published_pattern():
    # 1st = £34M, −£1.6M per rank, floor £400k at P22.
    assert DRIVER_DEFAULT_SALARY[1] == 34_000_000
    assert DRIVER_DEFAULT_SALARY[22] == 400_000
    for rank in range(2, 23):
        assert DRIVER_DEFAULT_SALARY[rank] == DRIVER_DEFAULT_SALARY[rank - 1] - 1_600_000


def test_constructor_default_table_matches_published_pattern():
    assert CONSTRUCTOR_DEFAULT_SALARY[1] == 30_000_000
    assert CONSTRUCTOR_DEFAULT_SALARY[11] == 4_000_000
    for rank in range(2, 12):
        assert CONSTRUCTOR_DEFAULT_SALARY[rank] == CONSTRUCTOR_DEFAULT_SALARY[rank - 1] - 2_600_000


def test_2026_rankings_cover_the_full_grid_without_duplicates():
    drivers = STARTING_DRIVER_RANKING[2026]
    teams = STARTING_CONSTRUCTOR_RANKING[2026]
    assert len(drivers) == len(set(drivers)) == 22
    assert len(teams) == len(set(teams)) == 11


def test_starting_driver_salary_by_code():
    # Norris won the 2025 title → top default salary in 2026.
    assert starting_driver_salary(2026, "NOR") == DRIVER_DEFAULT_SALARY[1]
    assert starting_driver_salary(2026, "LIN") == DRIVER_DEFAULT_SALARY[22]
    # Unknown driver, unknown season, or no code falls back to the floor.
    assert starting_driver_salary(2026, "XXX") == DRIVER_DEFAULT_SALARY[22]
    assert starting_driver_salary(1999, "NOR") == DRIVER_DEFAULT_SALARY[22]
    assert starting_driver_salary(2026, None) == DRIVER_DEFAULT_SALARY[22]


def test_starting_constructor_salary_by_name():
    assert starting_constructor_salary(2026, "McLaren") == CONSTRUCTOR_DEFAULT_SALARY[1]
    assert starting_constructor_salary(2026, "Cadillac") == CONSTRUCTOR_DEFAULT_SALARY[11]
    assert starting_constructor_salary(2026, "Unknown Team") == CONSTRUCTOR_DEFAULT_SALARY[11]
