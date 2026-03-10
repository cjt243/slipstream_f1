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
- [ ] League creation & invite codes
- [ ] Driver + constructor roster (seeded from static data)
- [ ] Team selection UI (budget-constrained picker)
- [ ] Race weekend scoring engine
- [ ] Leaderboard per race + season total

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
CREATE TABLE users (
  id TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  username TEXT UNIQUE NOT NULL,
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE leagues (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  invite_code TEXT UNIQUE NOT NULL,
  owner_id TEXT REFERENCES users(id),
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE league_members (
  league_id TEXT REFERENCES leagues(id),
  user_id TEXT REFERENCES users(id),
  PRIMARY KEY (league_id, user_id)
);

CREATE TABLE drivers (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  team TEXT NOT NULL,
  price INTEGER NOT NULL,
  season INTEGER NOT NULL
);

CREATE TABLE constructors (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  price INTEGER NOT NULL,
  season INTEGER NOT NULL
);

CREATE TABLE team_selections (
  id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  league_id TEXT REFERENCES leagues(id),
  race_id TEXT NOT NULL,
  driver_ids TEXT NOT NULL,      -- JSON array of 5 driver IDs
  constructor_id TEXT REFERENCES constructors(id),
  locked INTEGER DEFAULT 0,      -- 1 = locked after qualifying
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE race_results (
  id TEXT PRIMARY KEY,
  race_id TEXT NOT NULL,
  driver_id TEXT REFERENCES drivers(id),
  position INTEGER,
  fastest_lap INTEGER DEFAULT 0,
  dnf INTEGER DEFAULT 0,
  dotd INTEGER DEFAULT 0,
  overtakes INTEGER DEFAULT 0
);

CREATE TABLE scores (
  id TEXT PRIMARY KEY,
  user_id TEXT REFERENCES users(id),
  league_id TEXT REFERENCES leagues(id),
  race_id TEXT NOT NULL,
  points INTEGER DEFAULT 0
);
```

---

## API Design

Base URL: `/api`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Returns JWT |
| GET | `/leagues` | Get user's leagues |
| POST | `/leagues` | Create a league |
| POST | `/leagues/:id/join` | Join via invite code |
| GET | `/drivers` | Current season drivers |
| GET | `/constructors` | Current season constructors |
| POST | `/selections` | Submit team for a race |
| GET | `/leaderboard/:leagueId` | Season standings |
| GET | `/leaderboard/:leagueId/:raceId` | Single race standings |
| POST | `/admin/results` | Submit race results (admin only) |

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
