# Slipstream F1 Fantasy League — MVP Build Plan

## Context

Building a Phase 1 MVP for an F1 Fantasy League app (Grid Rivals clone). The repo currently has only documentation (CLAUDE.md, LEAGUE_MECHANICS.md), a style guide JSX reference, and a Turso/SQLAlchemy spike. No server or client code exists yet.

**Goal:** Break the MVP into modular, parallelizable issues so two devs (one backend-focused, one frontend-focused) can work independently with minimal blocking.

**Key enabler:** A shared API contract document defined upfront lets both sides code against agreed interfaces. Frontend uses mock data until backend is ready.

---

## Issue Dependency Graph

```
TIER 0 — Bootstrapping (parallel, do first)
  0A [BE Scaffold]     0B [FE Scaffold]     0C [API Contracts]

TIER 1 — Core Data + Shell (parallel after Tier 0)
  1A [DB Models] ←0A       1C [App Shell + Routing] ←0B
  1B [OpenF1 Service] ←1A  1D [Roster UI] ←0B,0C

TIER 2 — Feature Verticals (parallel pairs, BE/FE independent)
  2A [Auth BE] ←1A              → 2B [Auth FE] ←1C,0C
  2C [Contracts BE] ←1A,1B     → 2D [Contracts FE] ←1C,1D,0C
  2E [Races BE] ←1A,1B         → 2F [Races FE] ←1C,0C

TIER 3 — Scoring + Leaderboard (after results exist)
  3A [Scoring Engine] ←2C,1B   → 3C [Scores FE] ←2F,0C
  3B [Salary Adjust] ←3A       → (no separate FE issue)
  3D [Leaderboard BE] ←3A      → 3E [Leaderboard FE] ←1C,0C

TIER 4 — Integration
  4A [E2E Integration] ←all
  4B [Admin CLI] ←3A,3B
```

**Suggested backend track:** 0A → 0C → 1A → 1B → 2A → 2C → 2E → 3A → 3B → 3D → 4B
**Suggested frontend track:** 0B → 1C → 1D → 2B → 2D → 2F → 3C → 3E → 4A
*(Either dev can pick up any issue — these tracks just minimize blocking)*

---

## TIER 0: Bootstrapping

### 0A: Backend Scaffold
**Files:** `server/pyproject.toml`, `server/app.py`, `server/models/__init__.py`, `server/models/base.py`, `.env.example`

- Init `server/` with Flask, flask-cors, flask-jwt-extended, sqlalchemy>=2.0, sqlalchemy-libsql, resend, python-dotenv
- App factory in `app.py`: CORS, JWT, blueprint registration stubs
- SQLAlchemy engine factory reading `TURSO_DATABASE_URL` with local SQLite fallback
- `GET /api/health` returns `{"status": "ok"}`
- `uv run flask run --port 3001` works

**Reuse:** Engine creation pattern from `spike/turso_sqlalchemy/test_connection.py`

### 0B: Frontend Scaffold
**Files:** `client/vite.config.js`, `client/src/lib/tokens.js`, `client/src/lib/api.js`, `client/src/components/ui/*.jsx`

- Vite + React + Tailwind CSS v4
- Extract design tokens from `slipstream-style-guide-v1.jsx`: colors (`C` object), fonts (`FONT` object)
- Extract shared UI components: `Card`, `Pill`, `Mono`, `StatRow`, `Label`, `ToggleGroup`
- Google Fonts: Barlow, Barlow Condensed, Space Mono
- `api.js` fetch wrapper: prepends `VITE_API_URL`, attaches JWT from localStorage, handles 401 redirect
- Vite proxy `/api` → `localhost:3001`
- Placeholder dark-themed page renders

### 0C: Shared API Contract Document
**File:** `docs/api-contracts.md`

Define exact JSON request/response shapes for all Phase 1 endpoints. Both devs code against this. Includes:
- Auth: register, login (verify magic link), me
- Data: drivers, constructors, races, races/:id
- Contracts: list, sign, release
- Scores: driver scores, constructor scores per race
- Leaderboard: season, per-race
- Admin: ingest results, salary adjust
- Standard error format: `{"error": "message"}`

---

## TIER 1: Core Data + Shell

### 1A: Database Schema — All Models
**Files:** `server/models/user.py`, `league.py`, `driver.py`, `constructor.py`, `race.py`, `contract.py`, `results.py`, `scores.py`, `salary_history.py`, `init_db.py`

- All 13 models using SQLAlchemy 2.0 DeclarativeBase with `Mapped[]` annotations
- Models: User (includes `is_admin` bool flag), League, LeagueMember, Driver, Constructor, Race, Contract, DriverResult, ConstructorResult, DriverScore, ConstructorScore, FantasyScore, SalaryHistory
- Relationships: User↔League (M2M via LeagueMember), Driver→Constructor, Contract FKs
- Contract model: element_type (driver/constructor), element_id, race_start, contract_length, signed_salary, released_early, released_at_race
- `init_db.py`: creates all tables, seeds default league
- All monetary values as integers (pennies)

**Reuse:** DeclarativeBase pattern from `spike/turso_sqlalchemy/test_connection.py`

### 1B: OpenF1 Data Ingestion Service
**Files:** `server/services/openf1.py`, `server/services/seed.py`
**Depends on:** 1A

- `openf1.py` functions:
  - `fetch_drivers(season)` → `/v1/drivers?session_key=latest`, dedupe by driver_number
  - `fetch_constructors(season)` → derived from unique team_name in driver data
  - `fetch_races(season)` → `/v1/meetings?year=` + `/v1/sessions?year=` for details, identify sprints
  - `fetch_race_results(session_key)` → `/v1/session_result`, `/v1/laps`, overtake data
- Rate limiting: max 3 req/s
- `seed.py`: orchestrates initial seeding — constructors, drivers with hardcoded initial salaries (static table ranked by 2025 standings, defined in `server/data/salaries_2025.py`), races with lockdown times from session start times
- `server/data/salaries_2025.py`: static dict mapping driver/constructor IDs to initial salary values per the default salary table in LEAGUE_MECHANICS.md

### 1C: App Shell + Routing
**Files:** `client/src/App.jsx`, `components/layout/Header.jsx`, `layout/BottomNav.jsx`, `context/AuthContext.jsx`, `components/ProtectedRoute.jsx`, page stubs
**Depends on:** 0B

- React Router v6: `/login`, `/auth/verify`, `/team`, `/races`, `/race/:id`, `/leaderboard`
- Sticky header: logo, "SLIPSTREAM", race week indicator
- Bottom tab nav (mobile-first): Team, Races, Leaderboard
- AuthContext: JWT in localStorage, `user`, `login()`, `logout()`, `isAuthenticated`
- ProtectedRoute wrapper → redirect to `/login`
- All pages are placeholder Cards

### 1D: Driver + Constructor Roster UI
**Files:** `client/src/components/roster/DriverCard.jsx`, `ConstructorCard.jsx`, `hooks/useDrivers.js`, `hooks/useConstructors.js`, `lib/mockData.js`
**Depends on:** 0B, 0C

- Drivers/Constructors toggle (ToggleGroup)
- Card per element: name, constructor badge (team color), salary in Mono font
- Sort: by salary, by name. Search/filter input
- Responsive: 1 col mobile, 2 col tablet
- Mock data matching API contract shapes, hooks fall back to mocks

---

## TIER 2: Feature Verticals

### 2A: Auth — Magic Link Backend
**Files:** `server/routes/auth.py`, `server/services/email.py`
**Depends on:** 1A

- `POST /api/auth/register` — create user + username, send magic link via Resend
- `POST /api/auth/login` — verify magic link token (15-min expiry), return 7-day JWT + user
- `GET /api/auth/me` — current user with bank_balance, team_value
- Magic link: random token stored hashed in DB with expiry
- Resend sends link to `{FRONTEND_URL}/auth/verify?token={token}`
- New users auto-added to default league with £100M bank balance
- Dev mode: if no `RESEND_API_KEY`, log magic link to console

### 2B: Auth — Magic Link Frontend
**Files:** `client/src/pages/LoginPage.jsx`, `pages/VerifyPage.jsx`, update `AuthContext.jsx`
**Depends on:** 1C, 0C

- Login page: email + username input, "Send Magic Link" button, success/error states
- Verify page at `/auth/verify`: reads token from URL, calls login endpoint, stores JWT, redirects to `/team`
- Styled per design system: dark bg, speed cyan accents, Barlow font

### 2C: Contract Signing — Backend
**Files:** `server/routes/contracts.py`, `server/services/contracts.py`
**Depends on:** 1A, 1B

- `POST /api/contracts` with validations: budget check, no duplicate, length 1-5, cooldown check, roster limits (5 drivers + 1 constructor), lockdown check
- `GET /api/contracts` — active contracts with current salary, races remaining
- `DELETE /api/contracts/<id>` — early release: 3% penalty, refund salary minus penalty, record release race for cooldown
- Contract expiry on read: `race_start + contract_length <= current_round`
- All business logic in `services/contracts.py`

### 2D: Contract Signing — Frontend (Team Page)
**Files:** `client/src/pages/TeamPage.jsx`, `components/team/RosterSlot.jsx`, `team/ContractCard.jsx`, `team/SigningModal.jsx`, `hooks/useContracts.js`
**Depends on:** 1C, 1D, 0C

- Team page: bank balance, team value bar, 5 driver slots + 1 constructor slot
- Filled slots: name, contract progress, salary, release button with penalty preview
- Empty slots: "Sign Driver/Constructor" opens signing modal
- Signing modal: available elements list, contract length selector (1-5), budget impact preview
- Disabled states for: already signed, cooldown, over budget
- Early release: confirmation dialog with penalty amount

### 2E: Race Schedule — Backend
**Files:** `server/routes/races.py`, `server/services/races.py`
**Depends on:** 1A, 1B

- `GET /api/races` — all races for season, ordered by round, with status (upcoming/lockdown/completed)
- `GET /api/races/<id>` — full detail including lockdown active, results available, has_sprint
- `next_race` convenience field on list endpoint

### 2F: Race Schedule — Frontend
**Files:** `client/src/pages/RacesPage.jsx`, `pages/RaceDetailPage.jsx`, `components/race/RaceCard.jsx`, `components/race/LockdownTimer.jsx`, `hooks/useRaces.js`
**Depends on:** 1C, 0C

- Race list: round, name, circuit, date, status badge, lockdown countdown
- Next race highlighted with speed cyan border
- Race detail: header, lockdown timer, tabs (Schedule, Results placeholder, Your Team)

---

## TIER 3: Scoring + Leaderboard

### 3A: Scoring Engine — Backend
**Files:** `server/services/scoring.py`, `server/services/results_ingestion.py`, `server/routes/admin.py`
**Depends on:** 2C, 1B

- `POST /api/admin/results` (admin-only, checks `user.is_admin`): fetch quali/race/sprint results from OpenF1, populate driver_results + constructor_results, run scoring
- `scoring.py` — `calculate_driver_scores(race_id)`:
  - Qualifying: `50 - 2*(pos-1)`
  - Race: `100 - 3*(pos-1)`
  - Sprint: `22 - (pos-1)` (sprint weekends only)
  - Overtakes: `max(0, quali_pos - race_pos) * 3`
  - Improvement: vs 8-race rolling avg, lookup table
  - Teammate: find by constructor, margin brackets (2/5/8/12)
  - Completion: +3 at 25/50/75/90% laps
- `calculate_constructor_scores(race_id)`: avg driver positions ranked among constructors, quali + race points
- Populate fantasy_scores per user based on active contracts
- All scoring functions pure/testable

**Reference:** LEAGUE_MECHANICS.md sections 3-8 for exact scoring tables

### 3B: Salary Adjustment Engine — Backend
**Files:** `server/services/salary.py`, extend `server/routes/admin.py`
**Depends on:** 3A

- `POST /api/admin/salary-adjust`: rank elements by race points, apply adjustment formula from LEAGUE_MECHANICS.md Section 12
- Formula: `floor(variation / 4, nearest_100k)`, capped ±2M driver / ±3M constructor, floor ±100K
- Update driver/constructor salary, record in salary_history
- Adjust bank_balance for users with active contracts on affected elements
- Team value floor: top up bank if team value drops below £100M

### 3C: Scores Display — Frontend
**Files:** `client/src/components/scores/DriverScoreCard.jsx`, `scores/ConstructorScoreCard.jsx`, `scores/UserRaceSummary.jsx`, `hooks/useScores.js`
**Depends on:** 2F, 0C

- Race detail "Results" tab: driver scores table (sortable by total), expandable category breakdown
- Color coding per category: gold=race pos, cyan=quali, purple=sprint/improvement, orange=overtakes, green=completion
- Constructor scores table (simpler)
- "Your Drivers" section: how user's contracted drivers scored, subtotal
- User's total fantasy score for this race

### 3D: Leaderboard — Backend
**Files:** `server/routes/leaderboard.py`, `server/services/leaderboard.py`
**Depends on:** 3A

- `GET /api/leaderboard` — season standings: aggregate fantasy_scores, include team value + bank balance, ranked
- `GET /api/leaderboard/<race_id>` — single race standings
- Handle ties, include current user highlight

### 3E: Leaderboard — Frontend
**Files:** `client/src/pages/LeaderboardPage.jsx`, `components/leaderboard/StandingsTable.jsx`, `hooks/useLeaderboard.js`
**Depends on:** 1C, 0C

- Toggle: Season vs per-race (dropdown selector)
- Season view: rank, username, total points (Mono), team value
- Current user row highlighted (speed cyan), P1 row gold
- Per-race view: rank, username, race points

---

## TIER 4: Integration + Admin

### 4A: End-to-End Integration
**Depends on:** All above

- Connect FE to real BE, remove mock data fallbacks
- Test full flow: register → magic link → login → view drivers → sign contracts → view results → leaderboard
- API error handling: 401 redirect, 400/409 display, 500 generic
- Seed script populates 2025 season from OpenF1

### 4B: Admin CLI
**Files:** `server/cli.py`, update `server/app.py`
**Depends on:** 3A, 3B

- `uv run flask seed` — seed DB with 2025 data from OpenF1 + default league
- `uv run flask ingest-results --race-id <id>` — results + scoring
- `uv run flask adjust-salaries --race-id <id>` — salary recalc
- `uv run flask create-admin --email <email>` — mark user as admin

---

## Key Design Decisions
- **Salaries**: Hardcoded in `server/data/salaries_2025.py` (not derived from OpenF1). OpenF1 provides driver/constructor/race data; we assign fantasy salaries ourselves.
- **Admin**: Simple `is_admin` boolean on User model. Admin endpoints check this. Set via `uv run flask create-admin --email`.
- **Dev assignment**: Issues are self-contained — either dev can pick up any issue. Suggested tracks minimize blocking but aren't mandatory.

## Verification Plan

1. **Backend smoke test:** `uv run flask run --port 3001`, hit `/api/health`
2. **Seed test:** `uv run flask seed`, verify drivers/constructors/races populated
3. **Auth flow:** Register → check console for magic link (dev mode) → verify → get JWT → hit `/api/auth/me`
4. **Contract flow:** Sign 5 drivers + 1 constructor, verify budget deducted, release one with penalty
5. **Scoring flow:** `uv run flask ingest-results --race-id 1`, verify scores calculated, fantasy_scores populated
6. **Salary flow:** `uv run flask adjust-salaries --race-id 1`, verify salary_history records
7. **Leaderboard:** Multiple users with contracts, verify ranking after scoring
8. **Frontend E2E:** Full user journey through all pages on mobile viewport
