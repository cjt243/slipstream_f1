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

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Frontend | React (Vite) | Fast dev, Claude-friendly, mobile-responsive |
| Backend | FastAPI + SQLAlchemy | Async Python backend, native Pydantic, auto OpenAPI docs |
| Database | Turso (LibSQL/SQLite) | Free tier, edge-ready, simple schema |
| Hosting | DigitalOcean App Platform | Simple GitHub deploy, affordable |
| Styling | Tailwind CSS | Utility-first, great for mobile layouts |
| Auth | Resend (magic links) | Free tier (3k emails/mo), no passwords |
| F1 Data | OpenF1 API | Free, no auth for historical data, 3 req/s |
| Migrations | Alembic | SQLAlchemy-native schema versioning |

---

## Project Structure
```text (planned — not yet created)
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
│   ├── services/            # Business logic (scoring, contracts, OpenF1, email)
│   ├── data/                # Static seed data (salaries, circuit laps)
│   ├── middleware/          # Auth, error handling
│   ├── dependencies.py      # FastAPI Depends() helpers (get_db, get_current_user)
│   ├── app.py               # Entry point (FastAPI app, router registration)
│   ├── cli.py               # CLI commands (seed, ingest, etc.)
│   └── pyproject.toml       # Python dependencies
│
├── CLAUDE.md                # This file
├── PLAN.md                  # MVP build plan with issue breakdown
├── DATA_SOURCES.md          # OpenF1 API endpoint mapping
├── LEAGUE_MECHANICS.md      # Full scoring rules & game mechanics
├── slipstream-style-guide-v1.jsx  # UI design reference
├── .env.example             # Required env vars (TODO: create this file)
└── package.json             # Client scripts (dev, build)
```

---

## Game Rules & Scoring

See [LEAGUE_MECHANICS.md](LEAGUE_MECHANICS.md) for complete scoring rules, contract mechanics, team composition (5 drivers + 1 constructor), and salary adjustment algorithm.
See [DATA_SOURCES.md](DATA_SOURCES.md) for OpenF1 API endpoint mapping to app features.


---

## Features — Phased Roadmap

### Phase 1 — MVP (build first)
- [ ] User auth (magic links)
- [ ] Driver + constructor roster (seeded from static data)
- [ ] Contract signing UI (budget-constrained, 1–5 race contracts)
- [ ] Race weekend scoring engine
- [ ] Leaderboard per race + season total
- [ ] Default league seeded at setup (single-league for now)

### Phase 2 — Enhancements
- [ ] Live score updates during race weekends (immediately post-session)
- [ ] A deeper focus on each weekend - a dedicated "Race" view that focuses on qualifying stats, team lineups, and a Race weekend "winner" - similar to how fantasy football is very week to week focused
- [ ] Notifications related to deadlines for lineup locking, star drivers
- [ ] Minimum points threshold for teams that forget to set their lineup

### Phase 3 — Polish
- [ ] Animated score reveals post-race
- [ ] Potentially a post-weekend graphic that shows how fantasy teams trended throughout the weekend events by total points scored (line chart that accumulates points by fantasy team)
- [ ] Weekly team move summaries once lineups lock

---

## Database Schema (Initial)
```sql
-- Core entities
CREATE TABLE users ( ... );                -- id, email, username, is_admin
CREATE TABLE leagues ( ... );              -- id, name, invite_code, owner_id
CREATE TABLE league_members ( ... );       -- league_id, user_id, bank_balance

-- F1 reference data
CREATE TABLE drivers ( ... );              -- id, name, constructor_id, salary, season
CREATE TABLE constructors ( ... );         -- id, name, salary, season
CREATE TABLE races ( ... );                -- id, season, round, name, total_laps, has_sprint, lockdown_at

-- Contracts (replaces team_selections)
CREATE TABLE contracts ( ... );            -- id, user_id, league_id, element_type, element_id,
                                           -- race_start, contract_length, signed_salary, released_early

-- Results (separate tables for driver & constructor, with full detail)
CREATE TABLE driver_results ( ... );       -- race_id, driver_id, quali_pos, sprint_pos, race_pos,
                                           -- laps_completed, dnf
CREATE TABLE constructor_results ( ... );  -- race_id, constructor_id, quali_pos, race_pos

-- Scoring (broken down by category per element per race)
CREATE TABLE driver_scores ( ... );        -- race_id, driver_id, quali_pts, sprint_pts, race_pts,
                                           -- overtake_pts, improvement_pts, teammate_pts, completion_pts
CREATE TABLE constructor_scores ( ... );   -- race_id, constructor_id, quali_pts, race_pts

-- Fantasy scores (per user per league per race)
CREATE TABLE fantasy_scores ( ... );       -- user_id, league_id, race_id, total_points

-- Salary history (track fluctuations for team value calc)
CREATE TABLE salary_history ( ... );       -- element_type, element_id, race_id, salary_before, salary_after
```

See LEAGUE_MECHANICS.md for full scoring rules, contract mechanics, and salary adjustment algorithm.
Single-league design: a default league is seeded at setup. Schema retains league_id FKs for future multi-league support.

---

## API Design

Base URL: `/api`
Single-league design: all endpoints implicitly scoped to the default league.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Send magic link to email (creates user if new) |
| POST | `/auth/login` | Verify magic link token, returns JWT |
| GET | `/auth/me` | Current user profile + bank balance |
| GET | `/drivers` | Current season drivers + salaries |
| GET | `/constructors` | Current season constructors + salaries |
| GET | `/races` | Season race schedule |
| GET | `/races/<id>` | Race detail (laps, sprint, lockdown time) |
| POST | `/contracts` | Sign element (driver/constructor) with contract length |
| DELETE | `/contracts/<id>` | Early release (applies 3% penalty) |
| GET | `/contracts` | Get user's active contracts |
| GET | `/scores/<race_id>/drivers` | Driver scoring breakdown for a race |
| GET | `/scores/<race_id>/constructors` | Constructor scoring breakdown for a race |
| GET | `/leaderboard` | Season standings (with team values) |
| GET | `/leaderboard/<race_id>` | Single race standings |
| POST | `/admin/results` | Submit race results (admin only) |
| POST | `/admin/salary-adjust` | Trigger post-race salary recalc (admin only) |

---

## Environment Variables
```
APP_PORT=3001
SECRET_KEY=your_secret_here
TURSO_DATABASE_URL=libsql://your-db.turso.io  # omit locally to use SQLite fallback
TURSO_AUTH_TOKEN=your_token_here               # omit locally

RESEND_API_KEY=re_your_key_here
FRONTEND_URL=http://localhost:5173

VITE_API_URL=http://localhost:3001/api
```

---

## Environment Isolation

Three environments — each uses a different database and cannot touch the others:

| | Local Dev | Tests | Production |
|---|---|---|---|
| DB | `dev.db` (SQLite file) | in-memory SQLite | Turso (libSQL) |
| `TURSO_DATABASE_URL` | unset | not used | set in DO App Platform |
| Migrations | `alembic upgrade head` | applied in pytest fixture | `alembic upgrade head` on deploy |

### Engine factory rules
- If `TURSO_DATABASE_URL` is set → connect to Turso with `TURSO_AUTH_TOKEN`
- If unset → fall back to `sqlite:///./dev.db` (local dev only)
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

## Development Workflow

### Quick Start
```bash
# Backend (FastAPI)
cd server && uv run alembic upgrade head   # apply migrations to dev.db
cd server && uv run uvicorn app:app --port 3001 --reload

# Run tests
cd server && uv run pytest

# Frontend (React/Vite)
cd client && npm install && npm run dev
```

1. Claude reads this file at the start of every session
2. Pick one feature from the Phase 1 checklist
3. Build it end-to-end: model → API route → React component
4. Test manually, then move to the next feature
5. Never over-engineer — if it works simply, ship it

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
- Name DB query functions descriptively: `get_user_leagues()`, `lock_team_selection()`

### React / Frontend
- Functional components + hooks only
- Tailwind for all styling — no custom CSS unless unavoidable
- Keep components small and single-purpose

---

## Notes for Claude

- Always read this file before writing any code in a session
- Backend is FastAPI — use `APIRouter`, Pydantic schemas, and `Depends()` throughout; no Flask patterns
- SQLAlchemy + Turso spike passed (see `spike/turso_sqlalchemy/`) — local libSQL works, remote Turso untested; async SQLAlchemy not yet validated with sqlalchemy-libsql, start sync
- When completing a Phase 1 feature, check it off the roadmap above
- If the schema changes, update the schema section here too
- Prefer editing existing files over creating new ones
- Ask before making architectural changes not described here
