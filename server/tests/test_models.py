"""Schema + ORM sanity tests against the migrated in-memory database."""

from datetime import datetime, timezone

from sqlalchemy import inspect

import models
from models import (
    Constructor,
    Contract,
    Driver,
    League,
    LeagueMember,
    STARTING_BUDGET,
    User,
)
from models.enums import ElementType


EXPECTED_TABLES = {
    "users",
    "magic_tokens",
    "leagues",
    "league_members",
    "constructors",
    "drivers",
    "races",
    "contracts",
    "driver_results",
    "constructor_results",
    "driver_scores",
    "constructor_scores",
    "fantasy_scores",
    "salary_history",
}


def test_migration_creates_all_tables(db_engine):
    tables = set(inspect(db_engine).get_table_names())
    assert EXPECTED_TABLES <= tables
    assert "alembic_version" in tables  # schema applied via Alembic, not create_all


def test_user_league_membership_default_balance(db):
    user = User(email="a@example.com", username="ace")
    league = League(name="Default League", invite_code="SLIP01")
    db.add_all([user, league])
    db.flush()

    member = LeagueMember(league_id=league.id, user_id=user.id)
    db.add(member)
    db.flush()

    assert member.bank_balance == STARTING_BUDGET == 100_000_000
    assert user.is_admin is False
    assert member in db.query(LeagueMember).all()


def test_driver_constructor_relationship(db):
    rb = Constructor(name="Red Bull Racing", salary=28_000_000, season=2025, color="#3671C6")
    db.add(rb)
    db.flush()
    ver = Driver(
        name="Max Verstappen", driver_number=1, code="VER",
        constructor_id=rb.id, salary=30_000_000, season=2025,
    )
    db.add(ver)
    db.flush()

    assert ver.constructor.name == "Red Bull Racing"
    assert rb.drivers[0].code == "VER"


def test_contract_stores_enum_value(db):
    user = User(email="b@example.com", username="bee")
    league = League(name="L", invite_code="SLIP02")
    db.add_all([user, league])
    db.flush()

    contract = Contract(
        user_id=user.id, league_id=league.id,
        element_type=ElementType.DRIVER, element_id=1,
        race_start=1, contract_length=3, signed_salary=30_000_000,
    )
    db.add(contract)
    db.flush()

    fetched = db.get(Contract, contract.id)
    assert fetched.element_type is ElementType.DRIVER
    assert fetched.released_early is False
    assert fetched.released_at_race is None
