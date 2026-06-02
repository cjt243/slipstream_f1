"""Salary table integrity and starting-salary lookups."""

from data.salaries_2025 import (
    CONSTRUCTOR_DEFAULT_SALARY,
    DRIVER_DEFAULT_SALARY,
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


def test_starting_driver_salary_by_rank():
    # Verstappen (#1) is first in the 2025 ranking → top default salary.
    assert starting_driver_salary(1) == DRIVER_DEFAULT_SALARY[1]
    # Unknown driver number falls back to the floor.
    assert starting_driver_salary(999) == DRIVER_DEFAULT_SALARY[22]


def test_starting_constructor_salary_by_rank():
    assert starting_constructor_salary("McLaren") == CONSTRUCTOR_DEFAULT_SALARY[1]
    assert starting_constructor_salary("Unknown Team") == CONSTRUCTOR_DEFAULT_SALARY[11]
