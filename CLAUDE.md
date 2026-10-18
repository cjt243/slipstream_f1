# CLAUDE.md — F1 Fantasy League App

This file is the source of truth for Claude when working on this project. Read it at the start of every session.

---

## Project Overview

We are building an F1 Fantasy League web application — a mobile-first, responsive web app. The goal is a clean, fast, cheap-to-run product with great UX and deep fantasy F1 features.

**Core principles:**
- Simplicity over cleverness
- Mobile-first UI
- Low operational cost (free tiers where possible)
- Build incrementally — one feature at a time
- Build robust regression testing

---

## Current Status (as of Oct 18, 2026)

- **Phase 1 MVP is complete and live** at https://slipstreamf1.vercel.app (API docs at `/api/docs`).
- The league plays the **2026 season** (`SEASON=2026`) and joins it at round 18 (US GP, lockdown Sat Oct 24
  21:00 UTC). Rounds 1–17 were ingested and scored, and salaries were replayed through all 17 so they reflect the
  season so far. League points start at round 18; earlier races have driver/constructor scores only.
- Production has 2 real users (`Sad_Charlie` — the owner, user id 1, admin — and `FakeMikeGross`), neither with a
  contract yet, plus six `Sim_*` league members (ids 3–8) holding 33 round-18 contracts, created outside this repo.
- Race weekends run hands-off via the autopilot workflow (see CI/CD). The first real end-to-end run of fantasy
  scoring, contract settlement and the leaderboard happens after the US GP (Oct 25).
- Phase 2 is complete. Next up: Phase 3 (below).

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | React (Vite) | Fast dev, Claude-friendly, mobile-responsive |
| Backend | FastAPI + SQLAlchemy | Async Python backend, native Pydantic, auto OpenAPI docs |
| Database | Turso (LibSQL/SQLite) | Free tier, edge-ready, simple schema |
| Hosting | Vercel (multi-service: `client` + `server`) | Free Hobby tier, GitHub deploys, preview URL per PR |
| Styling | Tailwind CSS | Utility-first, great for mobile layouts |
| Auth | Resend (magic links) | Free tier (3k emails/mo), no passwords |
| F1 Data | OpenF1 API | Free, no auth for historical data, 3 req/s |
| Migrations | Alembic | SQLAlchemy-native schema versioning |

---

## Project Structure
```text
/
├── client/                  # React frontend (Vite)
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Route-level page components
│   │   ├── hooks/           # Custom React hooks
│   │   ├── lib/             # API calls, utilities
│   │   └── main.jsx
│   ├── index.html
│   └── vite.config.js
│
├── server/                  # FastAPI backend
│   ├── routes/              # API route handlers (APIRouter)
│   ├── models/              # SQLAlchemy ORM models
│   │   └── enums.py         # All shared Enum types (ElementType, etc.)
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Business logic: auth, email, openf1, seed, roster, races, results
│   │                        # (ingestion), scoring (pure rules), salary, contracts, fantasy, weekend,
│   │                        # notifications (lineup reminders), race_weekend (weekend view)
│   ├── data/                # salaries.py: default salary tables + season-start rankings
│   ├── tests/               # pytest suite (conftest.py, test_*.py per service/route)
│   ├── dependencies.py      # get_db, get_current_user, get_admin_user, get_optional_user
│   ├── app.py               # Entry point (FastAPI app, router registration)
│   ├── cli.py               # CLI: seed, ingest-results, ingest-season, adjust-salaries, autopilot, create-admin
│   └── pyproject.toml       # Python dependencies
│
├── .github/workflows/       # ci.yml (tests + prod migrate), autopilot.yml (race weekends), ops.yml (manual CLI)
├── docs/api-contracts.md    # Exact request/response shapes for every endpoint — keep in sync with routes
├── CLAUDE.md                # This file
├── PLAN.md                  # MVP build plan with issue breakdown
├── DATA_SOURCES.md          # OpenF1 API endpoint mapping
├── LEAGUE_MECHANICS.md      # Full scoring rules & game mechanics
├── slipstream-style-guide-v1.jsx  # UI design reference
├── vercel.json              # Vercel services + routing (/api/* → server, rest → client)
└── .env.example             # Env vars with local-dev defaults
```

---

## Game Rules & Scoring

See [LEAGUE_MECHANICS.md](LEAGUE_MECHANICS.md) for complete scoring rules, contract mechanics, team composition (5 drivers + 1 constructor), and salary adjustment algorithm.
See [DATA_SOURCES.md](DATA_SOURCES.md) for OpenF1 API endpoint mapping to app features.

### League decisions (where the rules were silent or contradictory)
- **Money — settle on release** (owner's decision): signing moves the element's current salary out of cash; when a
  contract ends (expiry or early release) the element's *post-race* salary comes back as cash. Salary moves in
  between only change team value. `team value = cash + current salaries under contract`. Bank balances are never
  adjusted mid-contract.
- **Timing:** team changes apply to the *current race* (first race not yet completed) and are blocked from lockdown
  (start of the first competitive session — Sprint Qualifying on sprint weekends) until the race is scored.
  Releases are blocked during lockdown too.
- **Release:** before a contract's first race locks it is a free cancellation (full refund, row deleted, no
  cooldown); afterwards 3% of the current salary, plus a one-race cooldown. Expiry also starts the cooldown.
- **Constructor rank** per session = average position of its drivers; ties → better best driver.
- **Unclassified drivers** are placed after the classified ones (most laps first), then DSQ/DNS; they score
  position points for that place.
- **Stand-in drivers** are created by ingestion at the floor salary and stay inactive (unsignable) unless they
  are on the current entry list at the next seed.
- **Starting salaries** (manual per §12.5): the previous season's final championship order read against the
  default tables (`server/data/salaries.py`, keyed by driver code / team name — numbers change between seasons).
- **Results timing:** a race is processed 4h after its start; later penalties can be re-scored via
  `POST /api/admin/results`, but salaries are not re-adjusted. Once a weekend locks, qualifying/sprint are
  scored live (driver_results rows with `race_pos` null). A race is **completed** only when its race result is
  stored (`race_pos` set) — that, not "any results", drives race status, the current race and salary adjustment.
- **Team-value floor** top-ups go into cash.
- **Star driver** (modelled on GridRival's talent driver): before lockdown each user may pick one of their drivers
  earning **under £18M** (`STAR_MAX_SALARY`, current salary) as the current race's star; its points count double
  in fantasy scoring. Picked per race (no carry-over); releasing that driver clears the pick.
- **Forgotten-lineup floor** (owner's number, to revisit once league averages are known): once a race is final,
  a member whose team was incomplete or empty that round scores at least `LINEUP_FLOOR` = 600, capped at the
  lowest complete team's score so skipping never beats playing. No complete team that race → no floor (keeps
  pre-league rounds clean). Applied in `score_fantasy`; flagged by `fantasy_scores.floor_applied`.


---

## Features — Phased Roadmap

### Phase 1 — MVP (build first)
- [x] User auth (magic links)
- [x] Driver + constructor roster (seeded from static data)
- [x] Contract signing UI (budget-constrained, 1–5 race contracts)
- [x] Race weekend scoring engine
- [x] Leaderboard per race + season total
- [x] Default league seeded at setup (single-league for now)
- [x] Scheduled race-weekend processing (autopilot) — added beyond the original plan

### Phase 2 — Enhancements
- [x] Live score updates during race weekends (immediately post-session)
  (qualifying/sprint scored as soon as OpenF1 has them; autopilot runs hourly Fri–Sun)
- [x] A deeper focus on each weekend - a dedicated "Race" view that focuses on qualifying stats, team lineups, and a Race weekend "winner" - similar to how fantasy football is very week to week focused
  (Weekend tab, `GET /weekend/{race_id}`; other teams' lineups are revealed at lockdown)
- [x] Notifications related to deadlines for lineup locking, star drivers
  - [x] Lineup reminder email in the 24h before lockdown to members with an incomplete team (autopilot +
    `POST /admin/reminders`)
  - [x] Star driver: one driver under £18M per race scores double (`PUT/DELETE /contracts/star`)
- [x] Minimum points threshold for teams that forget to set their lineup
  (600, capped at the lowest complete team; `fantasy_scores.floor_applied`)

### Phase 3 — Polish
- [ ] Animated score reveals post-race
- [ ] Potentially a post-weekend graphic that shows how fantasy teams trended throughout the weekend events by total points scored (line chart that accumulates points by fantasy team)
- [x] Weekly team move summaries once lineups lock
  (Weekend tab → Moves: signings, releases/expiries and star pick per team; `moves` on `GET /weekend/{race_id}`)

---

## Database Schema
```sql
-- Core entities
CREATE TABLE users ( ... );                -- id, email, username, is_admin
CREATE TABLE magic_tokens ( ... );         -- id, user_id, token_hash, expires_at (deleted on use)
CREATE TABLE leagues ( ... );              -- id, name, invite_code, owner_id
CREATE TABLE league_members ( ... );       -- league_id, user_id, bank_balance

-- F1 reference data
CREATE TABLE drivers ( ... );              -- id, name, code, driver_number, constructor_id, salary, season,
                                           -- is_active (on the current grid; only active drivers can be signed)
CREATE TABLE constructors ( ... );         -- id, name, color, salary, season
CREATE TABLE races ( ... );                -- id, season, round, name, circuit, total_laps, has_sprint,
                                           -- lockdown_at, race_start_at, OpenF1 meeting/session keys

-- Contracts (replaces team_selections)
CREATE TABLE contracts ( ... );            -- id, user_id, league_id, element_type, element_id,
                                           -- race_start (round), contract_length, signed_salary, released_early,
                                           -- released_at_race (last round served; drives the cooldown)

-- Results (separate tables for driver & constructor, with full detail)
CREATE TABLE driver_results ( ... );       -- race_id, driver_id, constructor_id (team at that race),
                                           -- quali_pos, sprint_pos, race_pos, laps_completed, dnf
CREATE TABLE constructor_results ( ... );  -- race_id, constructor_id, quali_pos, race_pos

-- Scoring (broken down by category per element per race)
CREATE TABLE driver_scores ( ... );        -- race_id, driver_id, quali_pts, sprint_pts, race_pts,
                                           -- overtake_pts, improvement_pts, teammate_pts, completion_pts, total_pts
CREATE TABLE constructor_scores ( ... );   -- race_id, constructor_id, quali_pts, race_pts, total_pts

-- Fantasy scores (per user per league per race; only for members with a team that race)
CREATE TABLE fantasy_scores ( ... );       -- user_id, league_id, race_id, total_points,
                                           -- floor_applied (incomplete lineup raised to the minimum)

-- Salary history (track fluctuations for team value calc)
CREATE TABLE salary_history ( ... );       -- element_type, element_id, race_id, salary_before, salary_after

-- Star driver pick per user per race (points count double)
CREATE TABLE star_drivers ( ... );         -- user_id, league_id, race_id, driver_id

-- Emails sent per user per race (one per kind, so scheduled jobs never repeat one)
CREATE TABLE notifications ( ... );        -- user_id, race_id, kind (lineup_reminder), sent_at
```

See LEAGUE_MECHANICS.md for full scoring rules, contract mechanics, and salary adjustment algorithm.
Single-league design: a default league is seeded at setup. Schema retains league_id FKs for future multi-league support.

---

## API Design

Base URL: `/api`
Single-league design: all endpoints implicitly scoped to the default league.
Exact shapes and error codes: [docs/api-contracts.md](docs/api-contracts.md) — update it with every route change.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Send magic link to email (creates user if new) |
| POST | `/auth/verify` | Verify magic link token, returns JWT |
| GET | `/auth/me` | Current user profile + bank balance |
| GET | `/drivers` | Current season's active drivers + salaries (+ last salary change) |
| GET | `/constructors` | Current season constructors + salaries (+ last salary change) |
| GET | `/races` | Season schedule with status (upcoming/lockdown/completed) + next race |
| GET | `/races/<id>` | Race detail (laps, sprint, lockdown and race start times) |
| GET | `/contracts` | User's team for the current race, cash/contract/team value, cooldowns |
| POST | `/contracts` | Sign element (driver/constructor) with contract length |
| DELETE | `/contracts/<id>` | Cancel (free, before first race) or early release (3% penalty) |
| PUT/DELETE | `/contracts/star` | Pick / clear the current race's star driver (under £18M, double points) |
| GET | `/scores/<race_id>/drivers` | Driver scoring breakdown for a race |
| GET | `/scores/<race_id>/constructors` | Constructor scoring breakdown for a race |
| GET | `/leaderboard` | Season standings (with team values) |
| GET | `/leaderboard/<race_id>` | Single race standings |
| GET | `/weekend/<race_id>` | Weekend view: lineups + points + moves, winner, qualifying with pick counts |
| POST | `/admin/seed` | Seed/refresh the season from OpenF1 (admin only) |
| POST | `/admin/results` | Ingest + score a race and its fantasy teams from OpenF1; before the race, live quali/sprint (admin only) |
| POST | `/admin/salary-adjust` | Finalize a scored race: salaries, contract settlement, floor (admin only) |
| POST | `/admin/reminders` | Email lineup reminders now if the next lockdown is within 24h (admin only) |

---

## Environment Variables
See `.env.example` for the canonical list. Server vars are loaded via
pydantic-settings (`server/config.py`) from `server/.env`.
```
PORT=3001
SECRET_KEY=your_secret_here
JWT_EXPIRY_DAYS=7
REGISTRATION_OPEN=true                         # default false: only existing users can sign in
SEASON=2026                                    # season the league plays (default 2026)
TURSO_DATABASE_URL=libsql://your-db.turso.io  # omit locally to use SQLite fallback
TURSO_AUTH_TOKEN=your_token_here               # omit locally

RESEND_API_KEY=re_your_key_here                # omit locally to log magic links to console
EMAIL_FROM=Slipstream <onboarding@resend.dev>  # Resend sender; use a verified domain in prod
FRONTEND_URL=http://localhost:5173             # magic-link base URL; set to the prod domain on Vercel

VITE_API_URL=http://localhost:3001/api         # client/.env — leave unset on Vercel (defaults to same-origin /api)
```

Production values (`TURSO_*`, `SECRET_KEY`, `RESEND_API_KEY`, `EMAIL_FROM`, `FRONTEND_URL`) are set in the Vercel project's
environment variables. Empty values count as unset (`env_ignore_empty`), since CI passes missing secrets as `""`. The migration job reads `TURSO_DATABASE_URL` / `TURSO_AUTH_TOKEN` from
GitHub Actions secrets (`production` environment or repo-level).
Registration is **closed in production** (`REGISTRATION_OPEN` unset): only emails already in the
`users` table can request a magic link; unknown emails get the same 200 but nothing is created or sent.
The server refuses to start on Vercel (`VERCEL` env set) while `SECRET_KEY` is the dev default,
so set it for both Production and Preview environments. On Vercel production it also refuses to
start without `TURSO_DATABASE_URL` (the `dev.db` fallback can't be opened there). If
`FRONTEND_URL` is unset on Vercel, magic links use the deployment's own URL
(`VERCEL_BRANCH_URL`, else `VERCEL_URL`), so previews link back to themselves.

---

## Environment Isolation

Three environments — each uses a different database and cannot touch the others:

| | Local Dev | Tests | Production |
|---|---|---|---|
| DB | `dev.db` (SQLite file) | in-memory SQLite | Turso (libSQL) |
| `TURSO_DATABASE_URL` | unset | not used | Vercel env vars + GitHub Actions secret |
| Migrations | `alembic upgrade head` | applied in pytest fixture | `migrate` job in CI on push to `main` |

### Engine factory rules
- If `TURSO_DATABASE_URL` is set → connect to Turso with `TURSO_AUTH_TOKEN`
- If unset → fall back to `sqlite+libsql:///dev.db` (local dev only — same libSQL dialect as Turso for parity)
- If `TURSO_AUTH_TOKEN` is set but `TURSO_DATABASE_URL` is not → raise a clear startup error (misconfiguration guard)

### Test database
- pytest always uses an **in-memory SQLite** DB (`sqlite:///:memory:`) — no env vars needed, no risk of touching dev or prod
- A session-scoped fixture creates the engine and runs all Alembic migrations against it
- Each test function wraps its session in a transaction and rolls back after — fast, clean, no teardown logic
- Fixture lives in `server/tests/conftest.py`

### Gitignore entries required
```
.env
*.db        # dev.db and any local SQLite files
```

### Safeguards — rules Claude must follow
- Never connect to Turso in tests — test fixtures always use `sqlite:///:memory:`
- Never hardcode a DB URL in application code — always read from env
- Never commit `.env` or `*.db` files

---

## CI/CD

### Continuous Integration (GitHub Actions)
- Every PR runs `pytest` against the in-memory SQLite DB, applies migrations to a fresh SQLite DB, and builds the client — no env vars required
- Workflow file: `.github/workflows/ci.yml`
- On push to `main` only, after tests pass, the `migrate` job runs `alembic upgrade head` against production Turso (fails loudly if the Turso secrets are missing)
- CI must pass before merging — never merge a branch with failing tests

### Race autopilot (GitHub Actions)
- `.github/workflows/autopilot.yml` runs `cli.py autopilot` hourly Fri–Sun, every two hours otherwise (and on manual dispatch), against
  production Turso: it refreshes the calendar and grid from OpenF1, then for every race that started 4+ hours ago
  and isn't finalized, in round order: ingest results → score drivers/constructors/fantasy teams → adjust
  salaries → settle expired contracts → apply the £100M team-value floor. A locked weekend whose race isn't
  processed yet gets its qualifying/sprint scored live. Then, in the 24h before the next
  lockdown, it emails members with an incomplete team (once per race). Idempotent; between race weekends it
  only refreshes the calendar.
- Reminder emails from autopilot need `RESEND_API_KEY`, `EMAIL_FROM` and `FRONTEND_URL` as GitHub Actions secrets
  (same values as on Vercel). Without the key they're only logged and not recorded, so `POST /admin/reminders`
  (which runs on Vercel, where the key is set) still sends them.
- Manual overrides: `POST /api/admin/results` re-scores a race (e.g. after a late penalty; salaries aren't
  re-adjusted), `POST /api/admin/salary-adjust` finalizes one.

### Production ops (GitHub Actions)
- `.github/workflows/ops.yml` runs a `server/cli.py` command against production Turso on manual dispatch
  (`command` choice + optional `args`). It applies migrations first and shares the `migrate-production`
  concurrency group, so it never overlaps a migration.
- The Claude GitHub integration can't dispatch workflows, and the libSQL driver can't authenticate from a
  Claude cloud session. So Claude runs production admin jobs through the admin API (`/api/admin/*`, admin JWT)
  instead; `ops.yml` is there for a person to dispatch from the Actions tab.

### Continuous Deployment (Vercel)
- Merges to `main` auto-deploy to production via Vercel's GitHub integration; every PR gets a preview deployment
- `vercel.json` defines two services: `client` (Vite, `index.html` fallback for client routes) and `server` (FastAPI). `/api/*` is rewritten to `server` with the path preserved, so all FastAPI routes (including docs at `/api/docs`) live under `/api`
- Vercel services have no pre-deploy hook — migrations run from the CI `migrate` job instead, **concurrently with the Vercel deploy**, so either may finish first
- Preview deployments must never run migrations or point at the production Turso DB. Today no env vars are set
  for Preview, so a preview's API refuses to start (dev `SECRET_KEY`) — previews only exercise the client build.
  Test full-stack changes locally (see Testing) and verify on production after merge.
- No manual deploys — all production changes go through `main`
- `vercel build` / `vercel dev` run both services locally (needs a Vercel login)

### Rules Claude must follow
- Do not suggest merging a PR if tests are failing
- Migration files must be committed alongside model changes so CI and deploy both pick them up
- Migrations must be backward-compatible with the previously deployed code (additive first: add columns/tables, backfill, and only drop or rename in a later release), because the deploy and the migration run concurrently
- The CI workflow uses `uv` — do not change the test runner or introduce pip-based install steps

---

## Development Workflow

### Quick Start
```bash
# Backend (FastAPI)
cd server && uv run alembic upgrade head   # apply migrations to dev.db
cd server && uv run python cli.py seed     # fetch the season from OpenF1 into dev.db (idempotent)
cd server && uv run uvicorn app:app --port 3001 --reload

# Run tests
cd server && uv run pytest

# Frontend (React/Vite)
cd client && npm install && npm run dev
```

1. Claude reads this file at the start of every session
2. Pick the next roadmap item and write down its success criteria
3. Build it end-to-end: model → migration → service → route → React component, with tests
4. Verify locally: `uv run pytest`, `npm run build`, Playwright against a seeded `dev.db`
5. Open a PR → CI green → merge (Claude may merge its own PRs once CI is green) → wait for the Vercel
   production deploy and CI `migrate` job → re-verify on production → run any data jobs → tick the roadmap
6. Never over-engineer — if it works simply, ship it

---

## Coding Conventions

### Database Migrations (Alembic)

- Alembic is the sole mechanism for schema changes — never use `Base.metadata.create_all()` or `drop_all()` outside of isolated test fixtures
- `alembic upgrade head` applies all pending migrations; safe to run repeatedly (idempotent)
- `alembic revision --autogenerate -m "<description>"` generates a migration after editing a model
- `alembic downgrade -1` rolls back one step — **dev only**, never run in production
- `alembic downgrade base` wipes all tables — **never run this** unless re-seeding a fresh dev DB, and only after explicit confirmation
- Migration files live in `server/alembic/versions/` and are committed to git; never edit an already-applied migration
- Seed scripts (`cli.py seed`) must guard against re-seeding: check for existing rows before inserting, never call `drop_all()` as part of seeding

**SQLite/Turso table rebuilds:** batch mode recreates a table (copy → DROP → rename) for many ALTERs — e.g. adding a
column with a `server_default`. Turso enforces foreign keys, so that DROP would cascade-delete every child row; this
happened once in production (driver_results/driver_scores were wiped). `alembic/env.py` therefore turns
`PRAGMA foreign_keys` off for the duration of a migration, and `tests/test_migrations.py` fills every table at the
base revision, upgrades to head with foreign keys ON, and fails if any rows disappear. When adding a table, add a
seed row for it to that test.

**Safeguards — rules Claude must follow:**
1. Never emit `Base.metadata.drop_all()` or `op.drop_table()` in non-test code without an explicit user instruction
2. Never suggest `alembic downgrade base` unless the user explicitly asks to wipe and re-seed a dev DB
3. Always generate a new revision file for schema changes — never hand-edit an existing migration
4. Seed commands must be idempotent (use `INSERT OR IGNORE` / existence checks, not truncate + re-insert)

### Python / FastAPI
- Routes stay thin — business logic lives in `services/`, DB queries in `models/`
- Use SQLAlchemy 2.0 style (`DeclarativeBase`, session via `Depends(get_db)`)
- All ENUMs defined in `server/models/enums.py` and imported everywhere — never inline string literals for typed fields
- Pydantic schemas in `server/schemas/` for all request bodies and response models — never access `request.json()` directly in routes
- Declare route response types with `response_model=` so OpenAPI docs stay accurate
- Auth and DB session injected via `Depends()` — no global state
- Use `uv run` for all Python execution — never bare `pip` or `python3`
- `server/` is the project root: run backend commands from `server/` with top-level imports (`from models...`, `from services...`) — never a `server.` prefix. pytest resolves this via `pythonpath = ["."]` in pyproject.
- Money is stored as integer **whole pounds** (£100M = `100000000`) — never floats, never pennies.
- Name DB query functions descriptively: `get_user_leagues()`, `lock_team_selection()`

### Service Layer
- Services are **module-level functions** by default — no class wrapper unless the service holds state across calls
- The one exception is `OpenF1Client`: a class because it owns rate-limiter state
- Service functions accept and return **ORM models or primitives** — never Pydantic schemas; services must not import from `schemas/`
- Services never import FastAPI or `HTTPException` — they are pure Python and must be testable without an HTTP context
- Business rule violations raise standard Python exceptions: `ValueError` for invalid input, `PermissionError` for auth violations
- Routes are responsible for schema↔ORM translation and for catching service exceptions and converting them to `HTTPException`

### Error Handling
- Services: raise `ValueError` or `PermissionError` with a human-readable message
- Routes: catch and re-raise as `HTTPException` with the appropriate status code
  - `ValueError` → 400
  - `PermissionError` → 403
  - `None` return from a lookup → 404
  - Where the contract needs other codes, services raise a `ValueError` subclass the route maps explicitly
    (`ContractConflict` → 409, `InsufficientFunds` → 402; `LookupError` → 404). Catch subclasses before `ValueError`.
- Never let ORM or service exceptions propagate unhandled to the client

### Not-Found Pattern
- Service functions return `None` when a record is not found — never raise inside the service
- The calling route checks for `None` and raises `HTTPException(status_code=404)`

### Type Hints
- All function signatures annotated, including return types
- No `Any` unless genuinely unavoidable

### Testing
- Test services directly by passing a `db` session from the in-memory SQLite fixture — not via HTTP
- Test routes via FastAPI `TestClient` for integration coverage
- Never mock the DB — always use the real in-memory SQLite fixture
- Scoring and salary functions must be pure and unit-testable without a DB session where possible
- Verify the frontend renders with Playwright: `uv run --with playwright python <script>` (run `playwright install chromium` once). Start the API (`uv run uvicorn app:app --port 3001`, with a seeded `dev.db`) and the Vite dev server first, and wait for elements — data loads async. In a Claude cloud session Chromium lives in `/opt/pw-browsers`; pass its path as `executable_path`. To test signed-in pages, put a JWT for a local user (`services.auth.create_jwt`) in `localStorage['slipstream_jwt']`.

### React / Frontend
- Functional components + hooks only
- Tailwind for all styling — no custom CSS unless unavoidable
- Keep components small and single-purpose

---

## Notes for Claude

- Always read this file before writing any code in a session
- Backend is FastAPI — use `APIRouter`, Pydantic schemas, and `Depends()` throughout; no Flask patterns
- SQLAlchemy + remote Turso works (production migrations run via CI). The Turso auth token must be passed as the driver's `auth_token` connect arg — `libsql_experimental` ignores `?authToken=` in the URL and sends an empty token. Async SQLAlchemy not yet validated with sqlalchemy-libsql; stay sync
- When completing a roadmap feature, check it off above and update "Current Status"
- If the schema changes, update the schema section here too
- Prefer editing existing files over creating new ones
- Ask before making architectural changes not described here

### Operating production from a Claude cloud session
- **Reads:** the session proxy injects Turso credentials for plain HTTPS, so query production with Turso's HTTP API:
  `POST https://slipstreamf1db-cjt243.aws-us-east-1.turso.io/v2/pipeline` with
  `{"requests":[{"type":"execute","stmt":{"sql":"..."}},{"type":"close"}]}`. Use it to verify, not to
  hand-edit app data.
- **Writes go through the app:** the libSQL driver (SQLAlchemy/Alembic) can't authenticate from the session, and
  the GitHub integration can't dispatch workflows (403). Run data jobs via the admin API with an admin JWT.
- **Signing in as the owner** (the owner approved this for testing): insert a magic token for user id 1 via the
  HTTP API (`token_hash` = SHA-256 of a random raw token, `expires_at` naive UTC ~10 min out), then exchange the
  raw token at `POST /api/auth/verify`. Leave the owner's real data as you found it: cancel test contracts before
  lockdown (free) and confirm 0 contracts / unchanged cash afterwards. Never touch other users' data.
- After a merge, wait for the new deployment *and* the migrate job (`alembic_version` on Turso) before running
  data jobs. Race data must be processed in round order (improvement points and salaries depend on it).

### OpenF1 quirks (handled in `services/openf1.py` / `services/results.py`)
- Limits are 3 req/s **and 30 req/min**; the client throttles both and retries 429s.
- "No results" is a **404** (`{"detail": "No results found."}`) — treated as an empty list.
- Pre-season testing appears as meetings without a Race session; cancelled meetings have `is_cancelled: true`.
  Both are skipped, so rounds count real race weekends only.
- The Sprint has `session_type: "Race"` and Sprint Qualifying `"Qualifying"` — identify sessions by `session_name`.
- `position` can be `null` (unclassified) or a code like `"RT"` in qualifying.
- `full_name` upper-cases the surname; use `first_name` + `last_name`. Driver numbers change between seasons
  (2026: Norris #1, Verstappen #3) — key season-to-season data by 3-letter code.
