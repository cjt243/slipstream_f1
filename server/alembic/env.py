"""Alembic environment.

Uses the application's own engine and metadata so migrations always target the
same database the app does (Turso when configured, local ``dev.db`` otherwise).
A caller may inject a live connection via ``config.attributes['connection']`` —
the test suite uses this to run migrations against an in-memory SQLite engine.
"""

from logging.config import fileConfig

from alembic import context

# Application metadata + engine (server/ is on sys.path via prepend_sys_path).
from dependencies import engine as app_engine
from models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

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


def run_migrations_online() -> None:
    # Reuse an injected connection (tests) or the app engine.
    connectable = config.attributes.get("connection", None)

    if connectable is not None:
        context.configure(
            connection=connectable,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()
        return

    with app_engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
