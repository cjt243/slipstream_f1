"""
Spike: Test SQLAlchemy + Turso (libSQL) connectivity.

Tests:
1. Local SQLite file via sqlalchemy-libsql dialect
2. Remote Turso DB (if TURSO_DATABASE_URL and TURSO_AUTH_TOKEN are set)

Run: uv run python test_connection.py
"""

import os
import sys
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    create_engine,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship


# --- Models (subset of the schema from CLAUDE.md) ---

class Base(DeclarativeBase):
    pass


class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    team = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Driver {self.name} ({self.team}) ${self.price}>"


class Constructor(Base):
    __tablename__ = "constructors"

    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    price = Column(Integer, nullable=False)
    season = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<Constructor {self.name} ${self.price}>"


# --- Test functions ---

def test_crud(engine):
    """Test basic CRUD operations."""
    Base.metadata.create_all(engine)

    # CREATE
    with Session(engine) as session:
        session.add_all([
            Driver(id="ver", name="Max Verstappen", team="Red Bull", price=30, season=2025),
            Driver(id="nor", name="Lando Norris", team="McLaren", price=25, season=2025),
            Driver(id="lec", name="Charles Leclerc", team="Ferrari", price=24, season=2025),
            Constructor(id="rb", name="Red Bull Racing", price=28, season=2025),
            Constructor(id="mcl", name="McLaren", price=26, season=2025),
        ])
        session.commit()
        print("  [OK] INSERT — added 3 drivers and 2 constructors")

    # READ
    with Session(engine) as session:
        drivers = session.query(Driver).filter(Driver.season == 2025).all()
        assert len(drivers) == 3, f"Expected 3 drivers, got {len(drivers)}"
        print(f"  [OK] SELECT — found {len(drivers)} drivers: {drivers}")

        constructors = session.query(Constructor).all()
        assert len(constructors) == 2
        print(f"  [OK] SELECT — found {len(constructors)} constructors")

    # UPDATE
    with Session(engine) as session:
        ver = session.get(Driver, "ver")
        ver.price = 32
        session.commit()

    with Session(engine) as session:
        ver = session.get(Driver, "ver")
        assert ver.price == 32, f"Expected price 32, got {ver.price}"
        print(f"  [OK] UPDATE — Verstappen price now ${ver.price}")

    # DELETE
    with Session(engine) as session:
        nor = session.get(Driver, "nor")
        session.delete(nor)
        session.commit()

    with Session(engine) as session:
        remaining = session.query(Driver).count()
        assert remaining == 2, f"Expected 2 drivers, got {remaining}"
        print(f"  [OK] DELETE — {remaining} drivers remaining")

    # RAW SQL
    with engine.connect() as conn:
        result = conn.execute(text("SELECT sqlite_version()"))
        version = result.scalar()
        print(f"  [OK] RAW SQL — SQLite version: {version}")

    print("  --- All CRUD tests passed ---")


def test_local():
    """Test with a local SQLite file using the libsql dialect."""
    db_path = "file:spike_test.db"
    engine = create_engine(f"sqlite+libsql:///{db_path}", echo=False)

    try:
        test_crud(engine)
    finally:
        engine.dispose()
        # Clean up test DB
        if os.path.exists("spike_test.db"):
            os.remove("spike_test.db")


def test_turso():
    """Test with a remote Turso database."""
    url = os.environ.get("TURSO_DATABASE_URL")
    token = os.environ.get("TURSO_AUTH_TOKEN")

    if not url or not token:
        print("\n[SKIP] Remote Turso test — set TURSO_DATABASE_URL and TURSO_AUTH_TOKEN to test")
        return False

    # Convert libsql:// to the sqlalchemy-libsql format
    # Turso URLs: libsql://your-db.turso.io
    # SQLAlchemy:  sqlite+libsql://your-db.turso.io?authToken=xxx&secure=true
    sa_url = url.replace("libsql://", "sqlite+libsql://")
    sa_url += f"?authToken={token}&secure=true"

    engine = create_engine(sa_url, echo=False)

    try:
        test_crud(engine)
        return True
    finally:
        # Clean up: drop test tables from remote DB
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS drivers"))
            conn.execute(text("DROP TABLE IF EXISTS constructors"))
            conn.commit()
        engine.dispose()


def main():
    print("=" * 50)
    print("SQLAlchemy + Turso (libSQL) Spike")
    print("=" * 50)

    print("\n[1/2] Local SQLite via libsql dialect...")
    try:
        test_local()
        print("[PASS] Local test succeeded\n")
    except Exception as e:
        print(f"[FAIL] Local test failed: {e}\n")
        import traceback
        traceback.print_exc()

    print("[2/2] Remote Turso database...")
    try:
        result = test_turso()
        if result:
            print("[PASS] Remote Turso test succeeded\n")
    except Exception as e:
        print(f"[FAIL] Remote Turso test failed: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
