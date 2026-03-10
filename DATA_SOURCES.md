# Data Source Specification — OpenF1 API Mapping

This document maps every app feature to its OpenF1 data source, documents the exact endpoints/fields used, and identifies data that must be derived or maintained internally.

**OpenF1 Base URL:** `https://api.openf1.org/v1`
**Rate Limits:** 3 req/s, 30 req/min (free tier, no auth required for historical data)
**Data Available:** 2023 season onwards

---

## 1. Season Setup — Drivers & Constructors

### Drivers
**App need:** Populate `drivers` table with name, constructor, headshot, number for current season.

| Field | OpenF1 Source |
|---|---|
| `name` | `GET /drivers?session_key=latest` → `full_name` |
| `abbreviation` | → `name_acronym` |
| `number` | → `driver_number` |
| `constructor_id` | → `team_name` (map to our constructor records) |
| `team_color` | → `team_colour` (hex, e.g. `#3671C6`) |
| `headshot_url` | → `headshot_url` |
| `country_code` | → `country_code` |

**Notes:**
- Deduplicate by `driver_number` (drivers appear once per session they participate in).
- `session_key=latest` returns the most recent session's driver list. For season start, use the first race session's key.
- **Salary is NOT from OpenF1** — assigned from hardcoded table in `server/data/salaries_2025.py`.

### Constructors
**App need:** Populate `constructors` table with team names.

**OpenF1 source:** Derived from driver data — unique `team_name` values from `/drivers`.

| Field | Source |
|---|---|
| `name` | Unique `team_name` from driver endpoint |
| `color` | `team_colour` from any driver on that team |
| `salary` | Hardcoded table (not from OpenF1) |

**No dedicated constructor endpoint exists.** Constructors are inferred from driver team assignments.

---

## 2. Season Setup — Race Schedule

**App need:** Populate `races` table with full season calendar, session times, sprint flags.

### Race Weekends (Meetings)
```
GET /meetings?year=2025
```

| Field | OpenF1 Source |
|---|---|
| `name` | → `meeting_name` (e.g. "Belgian Grand Prix") |
| `circuit` | → `circuit_short_name` (e.g. "Spa-Francorchamps") |
| `country` | → `country_name` |
| `round` | Derived from ordering by `date_start` |
| `meeting_key` | → `meeting_key` (used to fetch sessions) |

### Sessions per Weekend
```
GET /sessions?meeting_key={meeting_key}
```

| Field | OpenF1 Source |
|---|---|
| `session_type` | → `session_type` (Practice, Qualifying, Sprint, Race) |
| `session_name` | → `session_name` (e.g. "Sprint Qualifying", "Race") |
| `date_start` | → `date_start` (ISO 8601) |
| `session_key` | → `session_key` (primary key for result queries) |

**Derived fields:**
- `has_sprint`: `true` if any session in the meeting has `session_type = "Sprint"`
- `lockdown_at`: Use `date_start` of the Qualifying session (or Sprint Qualifying for sprint weekends)
- `total_laps`: **Not available from OpenF1 at season start.** Must be hardcoded per circuit or fetched from race results after the event (`number_of_laps` from leader's result).

---

## 3. Race Results Ingestion

After each race weekend, admin triggers ingestion. Multiple OpenF1 calls per race weekend.

### Step 1: Identify Session Keys
```
GET /sessions?meeting_key={meeting_key}
```
Filter results to find `session_key` for each session type: Qualifying, Sprint (if exists), Race.

### Step 2: Qualifying Results
```
GET /session_result?session_key={qualifying_session_key}
```

| App Field | OpenF1 Source |
|---|---|
| `quali_pos` | → `position` |
| `driver_number` | → `driver_number` (map to our driver record) |

**Populates:** `driver_results.quali_pos`

### Step 3: Sprint Results (if applicable)
```
GET /session_result?session_key={sprint_session_key}
```

| App Field | OpenF1 Source |
|---|---|
| `sprint_pos` | → `position` |
| `sprint_dnf` | → `dnf` (boolean) |

**Populates:** `driver_results.sprint_pos`

### Step 4: Race Results
```
GET /session_result?session_key={race_session_key}
```

| App Field | OpenF1 Source |
|---|---|
| `race_pos` | → `position` |
| `laps_completed` | → `number_of_laps` |
| `dnf` | → `dnf` (boolean) |
| `dns` | → `dns` (boolean) |
| `dsq` | → `dsq` (boolean) |
| `gap_to_leader` | → `gap_to_leader` (for display, not scoring) |

**Populates:** `driver_results.race_pos`, `driver_results.laps_completed`, `driver_results.dnf`

### Step 5: Total Race Laps
From the race leader's result (position = 1): `number_of_laps` = total race laps.
**Populates:** `races.total_laps` (update if not already set).

---

## 4. Scoring Engine — Data Source Mapping

Each scoring category and where its inputs come from:

### 4.1 Qualifying Position Points
- **Input:** `driver_results.quali_pos` (from OpenF1 `/session_result`)
- **Formula:** `50 - 2 * (pos - 1)` for pos 1–22
- **OpenF1 dependency:** Qualifying `session_result.position`

### 4.2 Race Position Points
- **Input:** `driver_results.race_pos` (from OpenF1 `/session_result`)
- **Formula:** `100 - 3 * (pos - 1)` for pos 1–22
- **OpenF1 dependency:** Race `session_result.position`

### 4.3 Sprint Position Points
- **Input:** `driver_results.sprint_pos` (from OpenF1 `/session_result`)
- **Formula:** `22 - (pos - 1)` for pos 1–22
- **OpenF1 dependency:** Sprint `session_result.position`
- **Condition:** Only calculated when `races.has_sprint = true`

### 4.4 Overtake Points ("Takes")
- **Inputs:** `driver_results.quali_pos`, `driver_results.race_pos` (both from OpenF1)
- **Formula:** `max(0, quali_pos - race_pos) * 3`
- **OpenF1 dependency:** Qualifying position + Race position (both from `/session_result`)
- **Note:** We use grid-to-finish delta, NOT the `/overtakes` endpoint. The overtakes endpoint tracks physical passes which don't map cleanly to our scoring model.

### 4.5 Improvement Points ("I.P.")
- **Inputs:**
  - `driver_results.race_pos` (from OpenF1, current race)
  - 8-race rolling average finish position (**derived internally** from historical `driver_results`)
- **Formula:** Lookup table based on `floor(rolling_avg) - race_pos` (see LEAGUE_MECHANICS.md §5)
- **OpenF1 dependency:** Current race position only. Rolling average is calculated from our own stored results.

### 4.6 Beating Teammate Points ("B.T.")
- **Inputs:**
  - `driver_results.race_pos` for the driver
  - `driver_results.race_pos` for teammate(s) — identified by shared `constructor_id`
- **Formula:** Margin brackets: 1–3 pos = 2 pts, 4–7 = 5, 8–12 = 8, 13+ = 12
- **OpenF1 dependency:** Race positions for all drivers. Teammate identification from `drivers.team_name`.

### 4.7 Completion Points ("Comp")
- **Inputs:**
  - `driver_results.laps_completed` (from OpenF1 `/session_result.number_of_laps`)
  - `races.total_laps` (from race leader's `/session_result.number_of_laps`)
- **Formula:** +3 pts at each of 25%, 50%, 75%, 90% of total laps
- **OpenF1 dependency:** `session_result.number_of_laps` for both driver and race leader

### 4.8 Constructor Qualifying Points
- **Inputs:** Each constructor's two drivers' `quali_pos` values
- **Derivation:** Average the two drivers' qualifying positions, rank all constructors by average, assign constructor qualifying position 1–10
- **Formula:** `30 - (constructor_quali_pos - 1)` for pos 1–18
- **OpenF1 dependency:** Individual driver qualifying positions from `/session_result`
- **Note:** Constructor positions are NOT directly available from OpenF1 — must be derived.

### 4.9 Constructor Race Points
- **Inputs:** Each constructor's two drivers' `race_pos` values
- **Derivation:** Average the two drivers' race positions, rank all constructors, assign constructor race position
- **Formula:** `60 - 2 * (constructor_race_pos - 1)` for pos 1–22
- **OpenF1 dependency:** Individual driver race positions from `/session_result`

---

## 5. Salary Adjustment — Data Source Mapping

Post-scoring, admin triggers salary recalculation.

- **Input:** Total fantasy points per element for the race (from `driver_scores` / `constructor_scores` — **internal data**)
- **Process:** Rank all drivers by total event points, rank all constructors separately
- **Lookup:** Compare current salary vs. default salary at earned rank (hardcoded tables)
- **No additional OpenF1 data needed** — salary adjustment is purely internal calculation on top of scored data.

---

## 6. Data NOT Available from OpenF1

These fields must be maintained internally or hardcoded:

| Data | Source | Notes |
|---|---|---|
| Driver/constructor salaries | `server/data/salaries_2025.py` | Hardcoded initial values, adjusted per race by scoring engine |
| Total race laps (pre-race) | Hardcode per circuit OR leave null until race results ingested | Could maintain a `circuit_laps` lookup table |
| 8-race rolling average | Calculated from `driver_results` table | Recalculated after each race |
| Constructor positions | Derived from driver positions | Average two drivers' positions, rank among constructors |
| Fantasy points / scores | Calculated by scoring engine | Stored in `driver_scores`, `constructor_scores`, `fantasy_scores` |
| Salary history | Internal tracking | `salary_history` table records before/after per race |
| Contract data | User actions | Signing, releasing, cooldowns |
| League adoption % | Internal query | Count of users with element / active users |
| DNF ratio (historical) | Could seed from OpenF1 2023+ data | Query historical `driver_results` for DNF counts |

---

## 7. OpenF1 Endpoint Summary — Grouped by App Function

### Used in Season Setup (run once)
| Endpoint | Purpose |
|---|---|
| `GET /drivers?session_key=latest` | Seed driver roster |
| `GET /meetings?year={year}` | Seed race calendar |
| `GET /sessions?meeting_key={key}` | Get session details per race weekend |

### Used in Results Ingestion (run per race weekend)
| Endpoint | Purpose |
|---|---|
| `GET /sessions?meeting_key={key}` | Find session_keys for quali/sprint/race |
| `GET /session_result?session_key={key}` | Qualifying results |
| `GET /session_result?session_key={key}` | Sprint results (if applicable) |
| `GET /session_result?session_key={key}` | Race results (positions, laps, DNF) |

### Not Used (available but unnecessary for MVP)
| Endpoint | Why Skipped |
|---|---|
| `/overtakes` | We calculate position-gained from quali→race delta instead |
| `/laps` | `session_result.number_of_laps` is sufficient for completion points |
| `/car_data` | Telemetry not needed for fantasy scoring |
| `/location` | Car coordinates not needed |
| `/pit` | Pit strategy not scored |
| `/stints` | Tire data not scored |
| `/team_radio` | Not needed for scoring |
| `/weather` | Not needed for scoring |
| `/race_control` | Flags/incidents not scored |
| `/intervals` | Real-time gaps not needed (post-session results suffice) |
| `/position` | Real-time position tracking — not needed when using final `session_result` |
| `/starting_grid` | Qualifying results give us grid position already |
| `/championship_drivers` | Could use for initial salary ranking, but we hardcode instead |
| `/championship_teams` | Same — hardcoded |

---

## 8. API Call Budget per Race Weekend

Estimating OpenF1 API calls for a single race weekend ingestion:

| Step | Calls | Endpoint |
|---|---|---|
| Find sessions | 1 | `/sessions?meeting_key={key}` |
| Qualifying results | 1 | `/session_result?session_key={quali_key}` |
| Sprint results | 0–1 | `/session_result?session_key={sprint_key}` (only sprint weekends) |
| Race results | 1 | `/session_result?session_key={race_key}` |
| **Total per weekend** | **3–4 calls** | |

At 3 req/s rate limit, a full race weekend ingestion completes in ~2 seconds. Season setup (meetings + sessions for ~24 races) takes ~25 calls, completing in under 10 seconds.
