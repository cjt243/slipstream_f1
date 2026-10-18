"""Admin endpoints: auth gating and seeding via a fake OpenF1 client."""

import pytest

from app import app
from dependencies import get_openf1
from models import Driver, Race
from tests.factories import auth_header, make_user
from tests.test_seed import FakeClient


@pytest.fixture
def fake_openf1():
    fake = FakeClient()
    app.dependency_overrides[get_openf1] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_openf1, None)


def test_admin_requires_auth(client, fake_openf1):
    assert client.post("/api/admin/seed", json={}).status_code == 401


def test_admin_requires_admin(client, db, fake_openf1):
    user = make_user(db, "fan@example.com", "fan")
    r = client.post("/api/admin/seed", json={}, headers=auth_header(user))
    assert r.status_code == 403
    assert fake_openf1.race_calls == 0


def test_admin_seed(client, db, fake_openf1):
    admin = make_user(db, "boss@example.com", "boss", is_admin=True)
    r = client.post("/api/admin/seed", json={"season": 2025}, headers=auth_header(admin))
    assert r.status_code == 200
    assert r.json() == {"season": 2025, "constructors": 2, "drivers": 3, "races": 2,
                        "league": "Slipstream League"}
    assert db.query(Driver).filter_by(season=2025).count() == 3
    assert db.query(Race).filter_by(season=2025).count() == 2
