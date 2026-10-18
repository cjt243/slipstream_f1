# Slipstream F1 — API Contracts (Phase 1)

The agreed JSON request/response shapes for every Phase 1 endpoint. Backend
implements these exactly; frontend codes against them (with mock data matching
these shapes until the backend lands).

## Conventions

- Base URL: `/api`. All examples omit the prefix.
- Auth: `Authorization: Bearer <jwt>` header. Protected endpoints return `401`
  when missing/invalid.
- Single-league design: every endpoint is implicitly scoped to the default
  league. No `league_id` in any path or body.
- **Money is integers (whole pounds).** `100000000` == £100,000,000 (£100M).
  No sub-pound amounts ever arise (salaries are £100k-granular). The client
  formats for display.
- Timestamps are ISO-8601 UTC strings, e.g. `"2025-03-16T15:00:00Z"`.
- IDs are integers unless noted.
- Standard error shape (any non-2xx):
  ```json
  { "error": "Human-readable message" }
  ```

---

## Auth

### POST /auth/register
Send a magic link. Always returns `200` regardless of whether the email exists
(no account enumeration). Creates the user (and enrols them in the default
league with a £100M balance) if new.

Request:
```json
{ "email": "user@example.com", "username": "speedy" }
```
Response `200`:
```json
{ "message": "If that email is valid, a magic link has been sent." }
```
The username is only used when creating a new account; an existing account's
username is never changed by this endpoint. When registration is closed
(`REGISTRATION_OPEN` false, the default), unknown emails get the same `200`
but no account is created and no email is sent.

Errors: `422` invalid email or blank username (e.g. `{"error": "email: Enter a valid email address"}`);
`502` the email provider failed.

The emailed link is `<FRONTEND_URL>/auth/verify?token=<raw token>`, valid for
15 minutes and single-use.

### POST /auth/verify
Exchange a magic-link token for a JWT. Token is single-use.

Request:
```json
{ "token": "raw-magic-token-from-email-link" }
```
Response `200`:
```json
{ "token": "<jwt>", "user": { "id": 1, "email": "user@example.com", "username": "speedy", "is_admin": false } }
```
Errors: `401` invalid/expired/used token.

### GET /auth/me  (protected)
Response `200`:
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "speedy",
  "is_admin": false,
  "bank_balance": 100000000
}
```

---

## Reference Data

Reference data is for the league's current season (`SEASON` setting, default
2026). Both lists are public (no auth) and empty until the season is seeded.

### GET /drivers
Ordered by driver number. `code` is the 3-letter abbreviation (may be `null`).

Response `200`:
```json
{
  "drivers": [
    {
      "id": 1,
      "name": "Lando Norris",
      "code": "NOR",
      "driver_number": 1,
      "constructor_id": 3,
      "constructor_name": "McLaren",
      "constructor_color": "#F47600",
      "salary": 34000000,
      "season": 2026
    }
  ]
}
```

### GET /constructors
Ordered by name.

Response `200`:
```json
{
  "constructors": [
    { "id": 3, "name": "McLaren", "color": "#F47600", "salary": 30000000, "season": 2026 }
  ]
}
```

### GET /races
`status` is one of `upcoming` (before lockdown) | `lockdown` (from the first
competitive session until results are in) | `completed` (results ingested).
`next_race` is the id of the first non-completed race by round (or `null`).
`lockdown_at` / `race_start_at` may be `null` if OpenF1 has no session times.

Response `200`:
```json
{
  "next_race": 2,
  "races": [
    {
      "id": 1,
      "season": 2025,
      "round": 1,
      "name": "Bahrain Grand Prix",
      "circuit": "Bahrain International Circuit",
      "total_laps": 57,
      "has_sprint": false,
      "lockdown_at": "2025-03-01T15:00:00Z",
      "race_start_at": "2025-03-02T15:00:00Z",
      "status": "completed"
    }
  ]
}
```

### GET /races/{id}
Response `200`:
```json
{
  "id": 1,
  "season": 2025,
  "round": 1,
  "name": "Bahrain Grand Prix",
  "circuit": "Bahrain International Circuit",
  "total_laps": 57,
  "has_sprint": false,
  "lockdown_at": "2025-03-01T15:00:00Z",
  "race_start_at": "2025-03-02T15:00:00Z",
  "status": "completed",
  "lockdown_active": false,
  "results_available": true
}
```
Errors: `404` unknown race.

---

## Contracts  (all protected)

### GET /contracts
Active contracts for the current user. `element_type` is `driver` |
`constructor`.

Response `200`:
```json
{
  "contracts": [
    {
      "id": 10,
      "element_type": "driver",
      "element_id": 1,
      "element_name": "Max Verstappen",
      "signed_salary": 30000000,
      "current_salary": 31000000,
      "race_start": 1,
      "contract_length": 3,
      "races_remaining": 2
    }
  ],
  "bank_balance": 70000000,
  "team_value": 31000000
}
```

### POST /contracts
Sign a driver or constructor.

Request:
```json
{ "element_type": "driver", "element_id": 1, "contract_length": 3 }
```
Response `201`: the created contract object (same shape as a `contracts[]` item).

Errors:
- `400` invalid length (must be 1–5), roster full (max 5 drivers / 1 constructor), past lockdown.
- `409` already under contract, or in post-release cooldown.
- `402` insufficient bank balance.

### DELETE /contracts/{id}
Early release. Applies a 3% penalty on the current salary; refunds the
remainder to the bank and starts a cooldown.

Response `200`:
```json
{ "released": true, "penalty": 930000, "refund": 30070000, "bank_balance": 100070000 }
```
Errors: `404` not the user's contract / unknown.

---

## Scores

### GET /scores/{race_id}/drivers
Per-driver scoring breakdown for a race (see LEAGUE_MECHANICS.md §3–8), highest
total first. Public. Positions are the order ingestion assigned (unclassified
drivers follow the classified ones); `constructor_*` is the team the driver
raced for at this event.

Response `200`:
```json
{
  "race_id": 1,
  "scores": [
    {
      "driver_id": 1,
      "driver_name": "Max Verstappen",
      "code": "VER",
      "constructor_name": "Red Bull Racing",
      "constructor_color": "#4781D7",
      "quali_pos": 1,
      "sprint_pos": null,
      "race_pos": 1,
      "dnf": false,
      "quali_pts": 50,
      "race_pts": 100,
      "sprint_pts": 0,
      "overtake_pts": 0,
      "improvement_pts": 5,
      "teammate_pts": 8,
      "completion_pts": 12,
      "total_pts": 175
    }
  ]
}
```
Errors: `404` race unknown, `409` results not yet available.

### GET /scores/{race_id}/constructors
Teams are ranked by the average position of their drivers in each session
(ties → better best driver); `quali_rank`/`race_rank` are those ranks.

Response `200`:
```json
{
  "race_id": 1,
  "scores": [
    { "constructor_id": 3, "constructor_name": "Red Bull Racing", "constructor_color": "#4781D7",
      "quali_rank": 1, "race_rank": 2, "quali_pts": 30, "race_pts": 58, "total_pts": 88 }
  ]
}
```
Errors (both): `404` race unknown, `409` results not yet available.

---

## Leaderboard

### GET /leaderboard
Season standings, ranked. `is_current_user` flags the requesting user's row.

Response `200`:
```json
{
  "standings": [
    {
      "rank": 1,
      "user_id": 1,
      "username": "speedy",
      "total_points": 1240,
      "team_value": 95000000,
      "bank_balance": 12000000,
      "is_current_user": true
    }
  ]
}
```

### GET /leaderboard/{race_id}
Single-race standings.

Response `200`:
```json
{
  "race_id": 1,
  "standings": [
    { "rank": 1, "user_id": 1, "username": "speedy", "race_points": 175, "is_current_user": true }
  ]
}
```

---

## Admin  (protected, admin only — else `403`)

### POST /admin/seed
Seed or refresh a season's races, constructors and drivers from OpenF1, and
make sure the default league exists. Idempotent: existing salaries are never
changed. `season` defaults to the server's `SEASON`.

Request:
```json
{ "season": 2026 }
```
Response `200`:
```json
{ "season": 2026, "constructors": 11, "drivers": 22, "races": 23, "league": "Slipstream League" }
```

### POST /admin/results
Ingest results for a race from OpenF1, then run scoring. Safe to re-run (e.g.
after a post-race penalty). Ingest races in round order — improvement points
use the earlier rounds' finishes.

Request:
```json
{ "race_id": 1 }
```
Response `200`:
```json
{ "race_id": 1, "drivers_scored": 22, "constructors_scored": 11 }
```
Errors: `404` unknown race, `409` OpenF1 has no results for it yet.

### POST /admin/salary-adjust
Recompute salaries after a race (LEAGUE_MECHANICS.md §12).

Request:
```json
{ "race_id": 1 }
```
Response `200`:
```json
{ "race_id": 1, "adjustments": 30 }
```
