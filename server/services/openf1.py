"""OpenF1 API client.

The single service class in the project that owns external-IO state (the
rate limiter). Only the four endpoints the app needs are wrapped:
``/drivers``, ``/meetings``, ``/sessions``, ``/session_result``.

See DATA_SOURCES.md for the full field mapping. Methods return plain dicts in
*our* vocabulary; turning them into ORM rows is the seed/ingestion layer's job.
"""

import time
from collections import deque

import httpx

BASE_URL = "https://api.openf1.org/v1"
# Free tier: 3 requests/second and 30 requests/minute.
MIN_INTERVAL = 1 / 3
PER_MINUTE = 30
MAX_RETRIES = 4


class OpenF1Client:
    def __init__(self, base_url: str = BASE_URL, *, client: httpx.Client | None = None,
                 min_interval: float = MIN_INTERVAL, per_minute: int = PER_MINUTE,
                 retry_wait: float = 10.0):
        self._base_url = base_url.rstrip("/")
        self._min_interval = min_interval
        self._per_minute = per_minute
        self._retry_wait = retry_wait
        self._recent: deque[float] = deque()  # request times in the last minute
        self._client = client or httpx.Client(timeout=30.0)

    # --- low-level ---------------------------------------------------------

    def _throttle(self) -> None:
        now = time.monotonic()
        while self._recent and now - self._recent[0] >= 60:
            self._recent.popleft()
        waits = []
        if self._recent:
            waits.append(self._min_interval - (now - self._recent[-1]))
        if self._per_minute and len(self._recent) >= self._per_minute:
            waits.append(60 - (now - self._recent[0]))
        wait = max(waits, default=0)
        if wait > 0:
            time.sleep(wait)
        self._recent.append(time.monotonic())

    def _get(self, path: str, params: dict) -> list[dict]:
        """GET a list endpoint. OpenF1 answers 404 when nothing matches (e.g. a
        session with no results yet) — that is returned as an empty list."""
        for attempt in range(MAX_RETRIES + 1):
            self._throttle()
            resp = self._client.get(f"{self._base_url}{path}", params=params)
            if resp.status_code == 429 and attempt < MAX_RETRIES:
                time.sleep(self._retry_wait * (attempt + 1))
                continue
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            return resp.json()
        raise RuntimeError("unreachable")

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
                "name": _display_name(r),
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
        session keys later used for results ingestion.

        Cancelled meetings and meetings without a Race session (pre-season
        testing) are skipped, so rounds count only real race weekends."""
        meetings = sorted(self.fetch_meetings(year), key=lambda m: m.get("date_start") or "")
        races: list[dict] = []
        for m in meetings:
            if m.get("is_cancelled"):
                continue
            sessions = self.fetch_sessions(m["meeting_key"])
            if _session_key(sessions, "Race") is None:
                continue
            races.append(_build_race(m, sessions, round_number=len(races) + 1))
        return races

    # --- results -----------------------------------------------------------

    def fetch_session_result(self, session_key: int) -> list[dict]:
        return self._get("/session_result", {"session_key": session_key})

    def close(self) -> None:
        self._client.close()


def _display_name(row: dict) -> str | None:
    """'Lando Norris' — OpenF1's full_name upper-cases the surname."""
    first, last = row.get("first_name"), row.get("last_name")
    if first and last:
        return f"{first} {last}"
    return row.get("full_name")


def _hex(color: str | None) -> str | None:
    """OpenF1 returns colours like 'FF8000' without the leading '#'."""
    if not color:
        return None
    return color if color.startswith("#") else f"#{color}"


def _session_start(sessions: list[dict], name: str) -> str | None:
    for s in sessions:
        if s.get("session_name") == name and not s.get("is_cancelled"):
            return s.get("date_start")
    return None


def _session_key(sessions: list[dict], name: str) -> int | None:
    for s in sessions:
        if s.get("session_name") == name and not s.get("is_cancelled"):
            return s.get("session_key")
    return None


def _build_race(meeting: dict, sessions: list[dict], round_number: int) -> dict:
    # OpenF1 types the Sprint as session_type "Race" (and Sprint Qualifying as
    # "Qualifying"), so the sprint is identified by name.
    has_sprint = _session_key(sessions, "Sprint") is not None

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
        "race_start_at": _session_start(sessions, "Race"),
        "meeting_key": meeting.get("meeting_key"),
        "quali_session_key": _session_key(sessions, "Qualifying"),
        "sprint_session_key": _session_key(sessions, "Sprint"),
        "race_session_key": _session_key(sessions, "Race"),
    }
