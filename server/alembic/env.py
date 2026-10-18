"""Alembic environment.

Uses the application's own engine and metadata so migrations always target the
same database the app does (Turso when configured, local ``dev.db`` otherwise).
A caller may inject a live connection via ``config.attributes['connection']`` —
the test suite uses this to run migrations against an in-memory SQLite engine.
"""

from contextlib import contextmanager
from logging.config import fileConfig
from typing import Iterator

from alembic import context
from sqlalchemy.engine import Connection

# Application metadata + engine (server/ is on sys.path via prepend_sys_path).
from dependencies import engine as app_engine
from models import Base

config = context.config

if config.config_file_name is not None:
    # Keep app loggers alive when migrations run in-process (e.g. the tests).
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=str(app_engine.url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


@contextmanager
def foreign_keys_off(connection: Connection) -> Iterator[None]:
    """Disable SQLite/libSQL foreign-key enforcement for the migration.

    Batch mode rebuilds tables (copy → DROP → rename). With enforcement on —
    Turso's default — the DROP cascades and deletes every child row
    (this once wiped driver_results/driver_scores in production). The pragma
    is a no-op inside a transaction, so it's set and committed first.
    See tests/test_migrations.py.
    """
    if connection.dialect.name != "sqlite":
        yield
        return
    was_on = connection.exec_driver_sql("PRAGMA foreign_keys").scalar()
    connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
    connection.commit()
    try:
        yield
    finally:
        if was_on:
            connection.exec_driver_sql("PRAGMA foreign_keys=ON")
            connection.commit()


def _run(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with foreign_keys_off(connection):
        with context.begin_transaction():
            context.run_migrations()
        connection.commit()


def run_migrations_online() -> None:
    # Reuse an injected connection (tests) or the app engine.
    connectable = config.attributes.get("connection", None)
    if connectable is not None:
        _run(connectable)
        return
    with app_engine.connect() as connection:
        _run(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
