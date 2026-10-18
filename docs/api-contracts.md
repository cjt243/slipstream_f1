# Slipstream F1 — API Contracts (Phase 1)

The agreed JSON request/response shapes for every Phase 1 endpoint. Backend
implements these exactly; frontend codes against them.

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
Active drivers (the current entry list) ordered by driver number. `code` is
the 3-letter abbreviation (may be `null`). `salary_change` is the element's
most recent post-race adjustment (`null` before any). Constructors have it too.

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
      "salary_change": -400000,
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
    { "id": 3, "name": "McLaren", "color": "#F47600", "salary": 30000000, "salary_change": 1200000, "season": 2026 }
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

Money model (settle on release): signing moves the element's current salary
from cash into the contract. When the contract ends — early release or expiry
after its last race — the element's *current, post-race* salary comes back as
cash (less a 3% penalty on early release). Salary moves in between change team
value, not cash. `team_value = bank_balance + contract_value`.

Timing: changes apply to the **current race** (first race not yet completed)
and are only allowed before its lockdown. A contract covers rounds
`race_start … last_round`. Releasing before the contract's first race locks is
a free cancellation (`cancellable: true`). After any departure the element is
in **cooldown** for the next race (one-race interval).

### GET /contracts
The user's team for the current race.

Response `200`:
```json
{
  "contracts": [
    {
      "id": 10,
      "element_type": "driver",
      "element_id": 1,
      "element_name": "Max Verstappen",
      "element_color": "#4781D7",
      "constructor_name": "Red Bull Racing",
      "signed_salary": 32000000,
      "current_salary": 32000000,
      "race_start": 18,
      "contract_length": 3,
      "last_round": 20,
      "races_remaining": 3,
      "cancellable": true
    }
  ],
  "bank_balance": 68000000,
  "contract_value": 32000000,
  "team_value": 100000000,
  "current_race": { "id": 18, "round": 18, "name": "United States Grand Prix",
                    "lockdown_at": "2026-10-24T21:00:00Z", "locked": false, "races_left": 6 },
  "cooldown": [ { "element_type": "driver", "element_id": 7 } ],
  "star_driver_id": 15,
  "star_max_salary": 18000000
}
```
`current_race` is `null` once the season is over. `star_driver_id` is the
current race's star pick (or `null`); only drivers earning less than
`star_max_salary` can be the star.

### POST /contracts
Sign a driver or constructor for the current race onward.

Request:
```json
{ "element_type": "driver", "element_id": 1, "contract_length": 3 }
```
Response `201`: the created contract (same shape as a `contracts[]` item).

Errors:
- `400` length not 1–5 or longer than the races left, roster full (5 drivers /
  1 constructor), driver not on the current grid, lockdown active, season over.
- `402` not enough cash.
- `404` unknown driver/constructor.
- `409` already on your team, or in cooldown.

### PUT /contracts/star
Make one of your drivers the star for the current race: their points count
double that weekend. Must be on your team for the current race and earn less
than £18M (`star_max_salary`). Replaces any earlier pick; pick again each race.
Releasing the star driver clears the pick.

Request: `{ "driver_id": 15 }` → Response `200`: `{ "star_driver_id": 15 }`

Errors: `400` not on your team, salary £18M or more, lockdown active, season
over; `403` not a league member; `404` unknown driver.

### DELETE /contracts/star
Clear the current race's star pick. Response `200`: `{ "star_driver_id": null }`.
Errors: `400` lockdown active.

### DELETE /contracts/{id}
Release a contract on your team. Before its first race locks: full refund, no
penalty, no cooldown. Afterwards: 3% penalty on the current salary, the rest
returned to cash, cooldown for the next race.

Response `200`:
```json
{ "released": true, "penalty": 960000, "refund": 31040000, "bank_balance": 99040000 }
```
Errors: `400` lockdown active; `404` not your contract / not on your team.

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

Public; with a valid token, `is_current_user` flags the viewer's row. A team's
points for a race are the summed fantasy points of every element under
contract for that round. Equal points share a rank (1, 2, 2, 4).

### GET /leaderboard
Season standings for every league member (members without points show 0).
`team_value` = cash + current salaries under contract. `races` lists races
with fantasy points, for the per-race selector.

Response `200`:
```json
{
  "standings": [
    {
      "rank": 1,
      "user_id": 1,
      "username": "speedy",
      "total_points": 1240,
      "team_value": 101500000,
      "bank_balance": 12000000,
      "is_current_user": true
    }
  ],
  "races": [ { "id": 18, "round": 18, "name": "United States Grand Prix" } ]
}
```

### GET /leaderboard/{race_id}
Single-race standings.

Response `200`:
```json
{
  "race_id": 18,
  "standings": [
    { "rank": 1, "user_id": 1, "username": "speedy", "race_points": 502, "is_current_user": true }
  ]
}
```
Errors: `404` unknown race.

---

## Weekend

### GET /weekend/{race_id}
One race weekend: every team's lineup and points, the weekend winner, and the
qualifying order. Public; send a token to see your own lineup before lockdown
and to have `is_current_user` set. Before lockdown only the viewer's lineup is
returned (`hidden_lineups` counts the rest) and `picked_by` is `null`.

Response `200`:
```json
{
  "race": { "...": "same shape as GET /races/{id}" },
  "locked": true,
  "scored": true,
  "final": true,
  "winners": [ { "...": "lineup, as below" } ],
  "lineups": [
    {
      "user_id": 2, "username": "FakeMikeGross", "is_current_user": true,
      "rank": 1, "points": 935,
      "elements": [
        { "element_type": "driver", "element_id": 9, "name": "Charles Leclerc", "code": "LEC",
          "color": "#E80020", "constructor_name": "Ferrari", "points": 166,
          "quali_pos": 1, "race_pos": 1, "is_star": false },
        { "element_type": "constructor", "element_id": 8, "name": "Ferrari", "code": null,
          "color": "#E80020", "constructor_name": null, "points": 137,
          "quali_pos": null, "race_pos": null, "is_star": false }
      ]
    }
  ],
  "hidden_lineups": 0,
  "qualifying": [
    { "driver_id": 9, "driver_name": "Charles Leclerc", "code": "LEC", "constructor_name": "Ferrari",
      "constructor_color": "#E80020", "quali_pos": 1, "quali_pts": 50, "picked_by": 3 }
  ]
}
```
- `lineups` covers every league member (an empty `elements` list = no team that
  weekend), ranked by points once scored (ties share a rank), else by name.
  `rank`/`points` are `null` until the race is scored.
- `scored`: some points are in — live after qualifying/sprint. `final`: the
  race result is in and scored. Live points rank the lineups but don't crown
  a winner.
- `winners`: the top-ranked lineup(s) with a team, once `final`; else `[]`.
- `is_star`: the owner's star driver; its `points` are already doubled.
- `qualifying` is `[]` until qualifying results are ingested.

Errors: `404` unknown race.

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

Also (re)computes every team's fantasy points for the race.

Before the race result is out, it scores whatever qualifying/sprint results
OpenF1 has instead (`live: true`) — the race stays in `lockdown`, not
`completed`, until its race result is stored.

Request:
```json
{ "race_id": 1 }
```
Response `200`:
```json
{ "race_id": 1, "drivers_scored": 22, "constructors_scored": 11, "live": false }
```
Errors: `404` unknown race, `409` OpenF1 has no results for any of its sessions yet.

### POST /admin/salary-adjust
Apply a scored race's salary adjustments (LEAGUE_MECHANICS.md §12) and record
them in `salary_history`. Each race is adjusted once, in round order. Salary
moves change team value, not bank balances (settle-on-release model).

Request:
```json
{ "race_id": 1 }
```
Response `200`:
```json
{ "race_id": 1, "adjustments": 33 }
```
Contracts whose last round was this race are then settled (the element's
post-race salary is paid back to the owner's cash), and any team worth less
than £100M has its cash topped up to the floor (LEAGUE_MECHANICS.md §6.3).

Errors: `404` unknown race; `409` not scored yet, already adjusted, or an
earlier round still needs adjusting.

### POST /admin/reminders
Email every member whose team for the current race is incomplete (fewer than
5 drivers or no constructor), if its lockdown is within the next 24h. Each
member is reminded at most once per race; the scheduled autopilot calls the
same service every two hours, so this is for testing or an early nudge.
A reminder is recorded only once Resend accepts it: `logged` (no
`RESEND_API_KEY`) and `failed` members are retried on the next run.

Response `200`:
```json
{ "race_id": 18, "race_name": "United States Grand Prix", "due": true,
  "sent": ["FakeMikeGross"], "logged": [], "failed": [] }
```
`due` is `false` (and nothing is sent) outside the 24h window; `race_id` and
`race_name` are `null` once the season is over.
