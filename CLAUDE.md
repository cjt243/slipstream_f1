# CLAUDE.md — F1 Fantasy League App

This file is the source of truth for Claude when working on this project. Read it at the start of every session.

---

## Project Overview

We are building an F1 Fantasy League web application — a mobile-first, responsive web app that clones and improves upon [Grid Rivals](https://www.gridrivalsgame.com/). The goal is a clean, fast, cheap-to-run product with better UX and features than Grid Rivals currently offers.

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
| Backend | Flask + SQLAlchemy | Python backend, ORM over Turso via sqlalchemy-libsql |
| Database | Turso (LibSQL/SQLite) | Free tier, edge-ready, simple schema |
| Hosting | DigitalOcean App Platform | Simple GitHub deploy, affordable |
| Styling | Tailwind CSS | Utility-first, great for mobile layouts |

---

## Project Structure
```
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
├── server/                  # Flask backend
│   ├── routes/              # API route handlers (blueprints)
│   ├── models/              # SQLAlchemy models
│   ├── middleware/           # Auth, error handling
│   └── app.py               # Entry point
│
├── CLAUDE.md                # This file
├── .env.example             # Required env vars (no secrets)
└── package.json             # Root scripts (dev, build, deploy)
```

---

## Game Rules & Scoring (Grid Rivals Clone)

We mirror Grid Rivals' [scoring and rules system](LEAGUE_MECHANICS.md)

### Team Composition
- Each player picks **1 constructor** and **5 drivers** per race weekend (on a contract system)
- Budget cap applies — players cannot exceed their team's budget
### Scoring Events (per race weekend)
- Sprint (if applicable)
- Qualifying (only for the main race, not sprint races)
- Race
  
---

## Features — Phased Roadmap

### Phase 1 — MVP (build first)
- [ ] User auth (magic links)
- [ ] Driver + constructor roster (seeded from static data)
- [ ] Contract signing UI (budget-constrained, 1–5 race contracts)
- [ ] Race weekend scoring engine
- [ ] Leaderboard per race + season total
- [ ] Default league seeded at setup (single-league for now)

### Phase 2 — Improvements over Grid Rivals
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
CREATE TABLE users ( ... );                -- id, email, username
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
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Returns JWT |
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
PORT=3001
JWT_SECRET=your_secret_here
TURSO_DATABASE_URL=libsql://your-db.turso.io
TURSO_AUTH_TOKEN=your_token_here

VITE_API_URL=http://localhost:3001/api
```

---

## Development Workflow

1. Claude reads this file at the start of every session
2. Pick one feature from the Phase 1 checklist
3. Build it end-to-end: model → API route → React component
4. Test manually, then move to the next feature
5. Never over-engineer — if it works simply, ship it
6. Always use `uv run` for Python — never use `pip` or `python3` directly

---

## Coding Conventions

- Flask routes stay thin — logic lives in model/query functions
- Use SQLAlchemy 2.0 style (DeclarativeBase, Session context managers)
- React: functional components + hooks only
- Tailwind for all styling — no custom CSS unless unavoidable
- Keep components small and single-purpose
- Name DB query functions descriptively: `getUserLeagues()`, `lockTeamSelection()`
- Use `uv run` for all Python execution — never bare `pip` or `python3`

---

## Notes for Claude

- Always read this file before writing any code in a session
- SQLAlchemy + Turso spike passed (see `spike/turso_sqlalchemy/`) — local libSQL works, remote Turso untested
- When completing a Phase 1 feature, check it off the roadmap above
- If the schema changes, update the schema section here too
- Prefer editing existing files over creating new ones
- Ask before making architectural changes not described here
