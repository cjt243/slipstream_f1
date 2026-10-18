"""OpenF1 client tests against a mocked HTTP transport (no network)."""

import httpx
import pytest

from services.openf1 import OpenF1Client

DRIVERS = [
    {"driver_number": 1, "full_name": "Max Verstappen", "name_acronym": "VER",
     "team_name": "Red Bull Racing", "team_colour": "3671C6"},
    {"driver_number": 1, "full_name": "Max Verstappen", "name_acronym": "VER",
     "team_name": "Red Bull Racing", "team_colour": "3671C6"},  # duplicate
    {"driver_number": 4, "full_name": "Lando NORRIS", "first_name": "Lando",
     "last_name": "Norris", "name_acronym": "NOR",
     "team_name": "McLaren", "team_colour": "#FF8000"},
]

MEETINGS = [
    {"meeting_key": 9, "year": 2025, "meeting_name": "Pre-Season Testing",
     "circuit_short_name": "Sakhir", "date_start": "2025-02-20T00:00:00+00:00"},
    {"meeting_key": 8, "year": 2025, "meeting_name": "Cancelled GP", "is_cancelled": True,
     "circuit_short_name": "Imola", "date_start": "2025-03-04T00:00:00+00:00"},
    {"meeting_key": 2, "year": 2025, "meeting_name": "China GP",
     "circuit_short_name": "Shanghai", "date_start": "2025-03-08T00:00:00+00:00"},
    {"meeting_key": 1, "year": 2025, "meeting_name": "Bahrain GP",
     "circuit_short_name": "Sakhir", "date_start": "2025-03-01T00:00:00+00:00"},
]

SESSIONS = {
    9: [
        {"session_key": 900, "session_name": "Day 1", "session_type": "Practice",
         "date_start": "2025-02-20T07:00:00+00:00"},
    ],
    8: [
        {"session_key": 800, "session_name": "Race", "session_type": "Race",
         "date_start": "2025-03-05T15:00:00+00:00"},
    ],
    1: [
        {"session_key": 100, "session_name": "Practice 1", "session_type": "Practice",
         "date_start": "2025-03-01T11:00:00+00:00"},
        {"session_key": 101, "session_name": "Qualifying", "session_type": "Qualifying",
         "date_start": "2025-03-01T15:00:00+00:00"},
        {"session_key": 102, "session_name": "Race", "session_type": "Race",
         "date_start": "2025-03-02T15:00:00+00:00"},
    ],
    2: [
        {"session_key": 200, "session_name": "Practice 1", "session_type": "Practice",
         "date_start": "2025-03-08T03:30:00+00:00"},
        {"session_key": 201, "session_name": "Sprint Qualifying", "session_type": "Qualifying",
         "date_start": "2025-03-08T07:30:00+00:00"},
        {"session_key": 202, "session_name": "Sprint", "session_type": "Race",
         "date_start": "2025-03-09T03:00:00+00:00"},
        {"session_key": 203, "session_name": "Qualifying", "session_type": "Qualifying",
         "date_start": "2025-03-08T11:00:00+00:00"},
        {"session_key": 204, "session_name": "Race", "session_type": "Race",
         "date_start": "2025-03-09T07:00:00+00:00"},
    ],
}


def _handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    params = dict(request.url.params)
    if path.endswith("/drivers"):
        return httpx.Response(200, json=DRIVERS)
    if path.endswith("/meetings"):
        return httpx.Response(200, json=MEETINGS)
    if path.endswith("/sessions"):
        mk = int(params["meeting_key"])
        return httpx.Response(200, json=SESSIONS[mk])
    if path.endswith("/session_result"):
        return httpx.Response(404, json={"detail": "No results found."})
    return httpx.Response(404, json=[])


@pytest.fixture
def client():
    transport = httpx.MockTransport(_handler)
    c = OpenF1Client(client=httpx.Client(transport=transport), min_interval=0, per_minute=0)
    yield c
    c.close()


def test_fetch_drivers_dedupes_and_normalizes_color(client):
    drivers = client.fetch_drivers()
    assert len(drivers) == 2  # duplicate #1 collapsed
    ver = next(d for d in drivers if d["driver_number"] == 1)
    assert ver["name"] == "Max Verstappen"
    assert ver["code"] == "VER"
    assert ver["team_color"] == "#3671C6"  # '#' prepended
    nor = next(d for d in drivers if d["driver_number"] == 4)
    assert nor["name"] == "Lando Norris"  # proper case from first/last name
    assert nor["team_color"] == "#FF8000"  # already had '#'


def test_fetch_constructors_unique_teams(client):
    teams = {c["name"] for c in client.fetch_constructors()}
    assert teams == {"Red Bull Racing", "McLaren"}


def test_fetch_races_orders_and_flags(client):
    races = client.fetch_races(2025)
    assert [r["round"] for r in races] == [1, 2]  # sorted by date_start
    bahrain, china = races
    assert bahrain["name"] == "Bahrain GP"
    assert bahrain["has_sprint"] is False
    assert bahrain["quali_session_key"] == 101
    assert bahrain["race_session_key"] == 102
    # lockdown = first non-practice session start
    assert bahrain["lockdown_at"] == "2025-03-01T15:00:00+00:00"
    assert bahrain["race_start_at"] == "2025-03-02T15:00:00+00:00"

    assert china["has_sprint"] is True
    assert china["sprint_session_key"] == 202
    assert china["quali_session_key"] == 203
    # earliest competitive session is Sprint Qualifying on Friday
    assert china["lockdown_at"] == "2025-03-08T07:30:00+00:00"


def test_fetch_races_skips_testing_and_cancelled_meetings(client):
    names = [r["name"] for r in client.fetch_races(2025)]
    assert names == ["Bahrain GP", "China GP"]


def test_session_result_404_means_no_results(client):
    assert client.fetch_session_result(12345) == []


def test_retries_after_rate_limit():
    calls = []

    def handler(request):
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, json={"detail": "Too many requests"})
        return httpx.Response(200, json=DRIVERS)

    c = OpenF1Client(client=httpx.Client(transport=httpx.MockTransport(handler)),
                     min_interval=0, per_minute=0, retry_wait=0)
    assert len(c.fetch_drivers()) == 2
    assert len(calls) == 2


def test_throttle_respects_per_minute_cap(monkeypatch):
    clock = [0.0]
    slept = []
    monkeypatch.setattr("services.openf1.time.monotonic", lambda: clock[0])

    def fake_sleep(seconds):
        slept.append(seconds)
        clock[0] += seconds

    monkeypatch.setattr("services.openf1.time.sleep", fake_sleep)
    c = OpenF1Client(client=httpx.Client(transport=httpx.MockTransport(_handler)),
                     min_interval=0, per_minute=2)
    for _ in range(3):
        c.fetch_drivers()
    # the third request in the same minute waits for the window to roll over
    assert slept == [60.0]
