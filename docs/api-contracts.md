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

### GET /drivers
Response `200`:
```json
{
  "drivers": [
    {
      "id": 1,
      "name": "Max Verstappen",
      "driver_number": 1,
      "constructor_id": 3,
      "constructor_name": "Red Bull Racing",
      "constructor_color": "#3671C6",
      "salary": 30000000,
      "season": 2025
    }
  ]
}
```

### GET /constructors
Response `200`:
```json
{
  "constructors": [
    { "id": 3, "name": "Red Bull Racing", "color": "#3671C6", "salary": 28000000, "season": 2025 }
  ]
}
```

### GET /races
`status` is one of `upcoming` | `lockdown` | `completed`. `next_race` is the id
of the soonest non-completed race (or `null`).

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
      "lockdown_at": "2025-03-02T15:00:00Z",
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
  "lockdown_at": "2025-03-02T15:00:00Z",
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
Per-driver scoring breakdown for a race (see LEAGUE_MECHANICS.md §3–8).

Response `200`:
```json
{
  "race_id": 1,
  "scores": [
    {
      "driver_id": 1,
      "driver_name": "Max Verstappen",
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
Response `200`:
```json
{
  "race_id": 1,
  "scores": [
    { "constructor_id": 3, "constructor_name": "Red Bull Racing", "quali_pts": 40, "race_pts": 80, "total_pts": 120 }
  ]
}
```

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

### POST /admin/results
Ingest results for a race from OpenF1, then run scoring.

Request:
```json
{ "race_id": 1 }
```
Response `200`:
```json
{ "race_id": 1, "drivers_scored": 20, "constructors_scored": 10, "users_scored": 8 }
```

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
