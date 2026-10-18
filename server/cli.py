"""Admin CLI. Run from server/:

    uv run python cli.py seed [--season 2026]
    uv run python cli.py ingest-results --round 17 [--season 2026]
    uv run python cli.py ingest-season [--season 2026]
    uv run python cli.py create-admin --email you@example.com

Connects to whatever database the environment selects (dev.db locally, Turso
when TURSO_DATABASE_URL is set) — see dependencies.py.
"""

import json

import typer

from config import settings
from dependencies import SessionLocal
from models import User
from services import races as race_service
from services.openf1 import OpenF1Client
from services.results import process_race_results
from services.seed import seed_all

app = typer.Typer(help="Slipstream admin commands.", no_args_is_help=True)


def _echo(result: dict) -> None:
    typer.echo(json.dumps(result, indent=2, default=str))


@app.command()
def seed(season: int = typer.Option(settings.season, help="Season to seed.")) -> None:
    """Seed races, constructors, drivers and the default league (idempotent)."""
    client = OpenF1Client()
    try:
        with SessionLocal() as db:
            _echo(seed_all(db, client, season))
    finally:
        client.close()


@app.command("ingest-results")
def ingest_results(
    round: int = typer.Option(..., "--round", help="Race round."),
    season: int = typer.Option(settings.season, help="Season."),
) -> None:
    """Ingest and score one race's results (safe to re-run)."""
    client = OpenF1Client()
    try:
        with SessionLocal() as db:
            race = race_service.get_race_by_round(db, season, round)
            if race is None:
                typer.echo(f"No round {round} in {season}", err=True)
                raise typer.Exit(1)
            processed = process_race_results(db, client, race)
            _echo({"round": round, "result": processed.__dict__ if processed else "no results yet"})
    finally:
        client.close()


@app.command("ingest-season")
def ingest_season(season: int = typer.Option(settings.season, help="Season.")) -> None:
    """Ingest and score every race that has results, in round order."""
    client = OpenF1Client()
    try:
        with SessionLocal() as db:
            for race in race_service.list_races(db, season):
                processed = process_race_results(db, client, race)
                if processed is None:
                    typer.echo(f"R{race.round} {race.name}: no results — stopping")
                    break
                typer.echo(f"R{race.round} {race.name}: {processed.drivers_scored} drivers scored")
    finally:
        client.close()


@app.command("create-admin")
def create_admin(email: str = typer.Option(..., help="Existing user's email.")) -> None:
    """Grant admin to an existing user."""
    with SessionLocal() as db:
        user = db.query(User).filter_by(email=email.strip().lower()).one_or_none()
        if user is None:
            typer.echo(f"No user with email {email}", err=True)
            raise typer.Exit(1)
        user.is_admin = True
        db.commit()
        typer.echo(f"{user.username} is now an admin")


if __name__ == "__main__":
    app()
