"""GET /drivers and /constructors via TestClient."""

from tests.factories import make_constructor, make_driver


def test_drivers_lists_current_season_with_constructor(client, db):
    mcl = make_constructor(db, "McLaren", color="#FF8000")
    make_driver(db, mcl, 81, "Oscar Piastri", code="PIA", salary=30_800_000)
    make_driver(db, mcl, 1, "Lando Norris", code="NOR", salary=34_000_000)
    old = make_constructor(db, "McLaren", season=2025)
    make_driver(db, old, 4, "Lando Norris", season=2025)  # other season — excluded
    benched = make_driver(db, mcl, 40, "Stand In")
    benched.is_active = False  # not on the current grid — excluded

    r = client.get("/api/drivers")
    assert r.status_code == 200
    drivers = r.json()["drivers"]
    assert [d["driver_number"] for d in drivers] == [1, 81]
    assert drivers[0] == {
        "id": drivers[0]["id"],
        "name": "Lando Norris",
        "code": "NOR",
        "driver_number": 1,
        "constructor_id": mcl.id,
        "constructor_name": "McLaren",
        "constructor_color": "#FF8000",
        "salary": 34_000_000,
        "salary_change": None,
        "season": 2026,
    }


def test_constructors_lists_current_season(client, db):
    make_constructor(db, "Mercedes", salary=27_400_000, color="#00D7B6")
    make_constructor(db, "Ferrari", salary=22_200_000, color="#ED1131")
    make_constructor(db, "Kick Sauber", season=2025)

    r = client.get("/api/constructors")
    assert r.status_code == 200
    assert [c["name"] for c in r.json()["constructors"]] == ["Ferrari", "Mercedes"]
    assert r.json()["constructors"][1]["salary"] == 27_400_000


def test_roster_is_empty_before_seeding(client):
    assert client.get("/api/drivers").json() == {"drivers": []}
    assert client.get("/api/constructors").json() == {"constructors": []}
