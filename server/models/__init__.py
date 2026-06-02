"""ORM models package.

Re-exports ``Base`` so Alembic and the app can import a single metadata object.
As models are added (Tier 1, issue 1A), import them here so that
``Base.metadata`` is fully populated for autogenerate migrations.
"""

from models.base import Base

__all__ = ["Base"]
