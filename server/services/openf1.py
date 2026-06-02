"""OpenF1 API client.

The single service class in the project that owns external-IO state (the
rate limiter). Only the four endpoints the app needs are wrapped:
``/drivers``, ``/meetings``, ``/sessions``, ``/session_result``.

See DATA_SOURCES.md for the full field mapping. Methods return plain dicts in
*our* vocabulary; turning them into ORM rows is the seed/ingestion layer's job.
"""

import time

import httpx

BASE_URL = "https://api.openf1.org/v1"
MIN_INTERVAL = 1 / 3  # 3 requests/second (free tier)


class OpenF1Client:
    def __init__(self, base_url: str = BASE_URL, *, client: httpx.Client | None = None,
                 min_interval: float = MIN_INTERVAL):
        self._base_url = base_url.rstrip("/")
        self._min_interval = min_interval
        self._last_request = 0.0
        self._client = client or httpx.Client(timeout=30.0)

    # --- low-level ---------------------------------------------------------

    def _get(self, path: str, params: dict) -> list[dict]:
        wait = self._min_interval - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        resp = self._client.get(f"{self._base_url}{path}", params=params)
        self._last_request = time.monotonic()
        resp.raise_for_status()
        return resp.json()

    # --- drivers & constructors -------------------------------------------

    def fetch_drivers(self, session_key: str | int = "latest") -> list[dict]:
        """Drivers for a session, deduped by driver_number."""
        rows = self._get("/drivers", {"session_key": session_key})
        by_number: dict[int, dict] = {}
        for r in rows:
            num = r.get("driver_number")
            if num is None or num in by_number:
                continue
            by_number[num] = {
                "driver_number": num,
                "name": r.get("full_name"),
                "code": r.get("name_acronym"),
                "team_name": r.get("team_name"),
                "team_color": _hex(r.get("team_colour")),
                "headshot_url": r.get("headshot_url"),
                "country_code": r.get("country_code"),
            }
        return list(by_number.values())

    def fetch_constructors(self, session_key: str | int = "latest") -> list[dict]:
        """Unique teams derived from the driver list (no dedicated endpoint)."""
        seen: dict[str, dict] = {}
        for d in self.fetch_drivers(session_key):
            team = d["team_name"]
            if team and team not in seen:
                seen[team] = {"name": team, "color": d["team_color"]}
        return list(seen.values())

    # --- races (meetings + sessions) --------------------------------------

    def fetch_meetings(self, year: int) -> list[dict]:
        return self._get("/meetings", {"year": year})

    def fetch_sessions(self, meeting_key: int) -> list[dict]:
        return self._get("/sessions", {"meeting_key": meeting_key})

    def fetch_races(self, year: int) -> list[dict]:
        """Full season calendar with sprint flag, lockdown time, and the
        session keys later used for results ingestion."""
        meetings = sorted(self.fetch_meetings(year), key=lambda m: m.get("date_start") or "")
        races: list[dict] = []
        for idx, m in enumerate(meetings, start=1):
            sessions = self.fetch_sessions(m["meeting_key"])
            races.append(_build_race(m, sessions, round_number=idx))
        return races

    # --- results -----------------------------------------------------------

    def fetch_session_result(self, session_key: int) -> list[dict]:
        return self._get("/session_result", {"session_key": session_key})

    def close(self) -> None:
        self._client.close()


def _hex(color: str | None) -> str | None:
    """OpenF1 returns colours like 'FF8000' without the leading '#'."""
    if not color:
        return None
    return color if color.startswith("#") else f"#{color}"


def _session_key(sessions: list[dict], name: str) -> int | None:
    for s in sessions:
        if s.get("session_name") == name:
            return s.get("session_key")
    return None


def _build_race(meeting: dict, sessions: list[dict], round_number: int) -> dict:
    has_sprint = any(s.get("session_type") == "Sprint" for s in sessions)

    # Lockdown = start of the first non-practice (competitive) session:
    # Friday qualifying on sprint weekends, Saturday qualifying otherwise.
    competitive = [
        s.get("date_start") for s in sessions
        if s.get("session_type") not in ("Practice", None) and s.get("date_start")
    ]
    lockdown_at = min(competitive) if competitive else None

    return {
        "season": meeting.get("year"),
        "round": round_number,
        "name": meeting.get("meeting_name"),
        "circuit": meeting.get("circuit_short_name"),
        "has_sprint": has_sprint,
        "lockdown_at": lockdown_at,
        "meeting_key": meeting.get("meeting_key"),
        "quali_session_key": _session_key(sessions, "Qualifying"),
        "sprint_session_key": _session_key(sessions, "Sprint"),
        "race_session_key": _session_key(sessions, "Race"),
    }
