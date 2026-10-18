"""Migrations must never lose data on a populated database.

Turso enforces foreign keys. When Alembic's SQLite batch mode rebuilds a table
(copy → DROP → rename), the DROP cascades to every child table with
ON DELETE CASCADE — this once wiped driver_results/driver_scores in
production. This test fills every table at the initial revision, upgrades to
head with foreign keys ON (as on Turso), and checks no rows disappeared.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool

SERVER_DIR = Path(__file__).resolve().parent.parent
BASE_REVISION = "3edaa5134da6"

SEED_SQL = [
    "INSERT INTO users (id, email, username, is_admin, created_at) VALUES (1, 'a@b.c', 'a', 0, '2026-01-01')",
    "INSERT INTO leagues (id, name, invite_code, owner_id) VALUES (1, 'L', 'SLIPSTREAM', 1)",
    "INSERT INTO league_members (id, league_id, user_id, bank_balance) VALUES (1, 1, 1, 100000000)",
    "INSERT INTO magic_tokens (id, user_id, token_hash, expires_at) VALUES (1, 1, 'h', '2026-01-01')",
    "INSERT INTO constructors (id, name, color, salary, season) VALUES (1, 'McLaren', '#F47600', 1, 2026)",
    "INSERT INTO drivers (id, name, driver_number, code, constructor_id, salary, season)"
    " VALUES (1, 'Lando Norris', 1, 'NOR', 1, 1, 2026)",
    "INSERT INTO races (id, season, round, name, has_sprint) VALUES (1, 2026, 1, 'GP', 0)",
    "INSERT INTO contracts (id, user_id, league_id, element_type, element_id, race_start,"
    " contract_length, signed_salary, released_early) VALUES (1, 1, 1, 'DRIVER', 1, 1, 1, 1, 0)",
    "INSERT INTO driver_results (id, race_id, driver_id, laps_completed, dnf) VALUES (1, 1, 1, 50, 0)",
    "INSERT INTO constructor_results (id, race_id, constructor_id) VALUES (1, 1, 1)",
    "INSERT INTO driver_scores (id, race_id, driver_id, quali_pts, sprint_pts, race_pts, overtake_pts,"
    " improvement_pts, teammate_pts, completion_pts, total_pts) VALUES (1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0)",
    "INSERT INTO constructor_scores (id, race_id, constructor_id, quali_pts, race_pts, total_pts)"
    " VALUES (1, 1, 1, 0, 0, 0)",
    "INSERT INTO fantasy_scores (id, user_id, league_id, race_id, total_points) VALUES (1, 1, 1, 1, 0)",
    "INSERT INTO salary_history (id, element_type, element_id, race_id, salary_before, salary_after)"
    " VALUES (1, 'DRIVER', 1, 1, 1, 1)",
]


def _counts(conn) -> dict[str, int]:
    tables = [r[0] for r in conn.execute(text(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        " AND name != 'alembic_version'"))]
    return {t: conn.execute(text(f'SELECT count(*) FROM "{t}"')).scalar() for t in tables}


def test_upgrade_preserves_rows_with_foreign_keys_enforced():
    engine = create_engine("sqlite://", poolclass=StaticPool)

    @event.listens_for(engine, "connect")
    def enforce_fks(dbapi_conn, _):  # Turso's behaviour
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    cfg = Config(str(SERVER_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(SERVER_DIR / "alembic"))
    with engine.connect() as conn:
        cfg.attributes["connection"] = conn
        command.upgrade(cfg, BASE_REVISION)
        for stmt in SEED_SQL:
            conn.execute(text(stmt))
        conn.commit()
        before = _counts(conn)
        assert all(before.values()), f"seed every table: {before}"

        command.upgrade(cfg, "head")
        after = _counts(conn)
        assert conn.execute(text("PRAGMA foreign_keys")).scalar() == 1  # restored
    assert {t: after[t] for t in before} == before
    engine.dispose()
