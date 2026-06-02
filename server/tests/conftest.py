"""Pytest fixtures.

Spins up an in-memory SQLite database and applies the real Alembic migrations
against it (same code path as production), so tests exercise the migrated
schema rather than ``create_all``. Each test runs inside a transaction that is
rolled back afterwards — no teardown, no file cleanup, never touches Turso or
``dev.db``.
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

import models  # noqa: F401 — ensures Base.metadata is fully populated

SERVER_DIR = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def db_engine():
    """In-memory engine with the full schema applied via Alembic.

    StaticPool keeps a single underlying connection alive so the ``:memory:``
    database persists across the session.
    """
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    cfg = Config(str(SERVER_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(SERVER_DIR / "alembic"))

    with engine.connect() as conn:
        cfg.attributes["connection"] = conn  # consumed by alembic/env.py
        command.upgrade(cfg, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def db(db_engine):
    """Function-scoped session wrapped in a transaction that is rolled back."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
