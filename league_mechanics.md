# GridRival Fantasy Racing — Comprehensive Scoring & Mechanics Reference
> Optimized for LLM coding agents. All point values, rules, and conditions are stated explicitly and completely.

---

## 1. GAME OVERVIEW

**Game Type:** Contracts-based fantasy racing league (distinct from traditional weekly pick'em fantasy)

**Objective:** Build the highest-scoring team of drivers (and one constructor in F1) using a fixed budget. Accumulate the most fantasy points by season end to win your league.

**Starting Budget:** $100,000,000 (fantasy cash)

**Roster Size:**
- F1: 5 drivers + 1 constructor (6 total "elements")

**"Element"** = umbrella term for any driver, rider, or racing constructor/team on your roster

**Season Structure:** Points accumulate across all race events. League standings are based on total cumulative points.

---

## 2. TERMINOLOGY / GLOSSARY

| Term | Definition |
|------|-----------|
| **Element** | A Driver/Rider OR a Racing Constructor/Team |
| **Rolling Average** | Average of the 8 most recent previous events for a given statistic |
| **Team Value** | Bank Balance + combined current salary value of all signed elements |
| **Bank Balance** | Available cash to sign new elements. Changes only when signing or releasing elements |
| **Salary** | The cost of each element. Fluctuates race-to-race based on performance |
| **Lockdown** | The period before an event when no team changes are allowed |
| **Takes** | Abbreviation for Overtake Points |
| **I.P.** | Abbreviation for Improvement Points |
| **B.T.** or **W.B.** | Abbreviation for Beating Teammate Points (also "best on team") |
| **Comp** | Abbreviation for Race Completion Points |
| **Value Index** | Ratio of rolling average fantasy points to salary. Higher = better value per dollar |
| **League Adoption** | % of active league players who have a specific driver/constructor signed |
| **DNF Ratio** | Number of DNFs divided by number of events competed in (historical, all seasons) |

### Value Index Detail
- Formula: rolling average fantasy points ÷ salary
- Higher number = more points generated per dollar of salary
- Used to identify undervalued or overvalued elements

### League Adoption Detail
- Shows what % of other players in your league have signed a specific element
- "Inactive" players are excluded (defined as: team scored 0 points for 2 consecutive events)
- Diverging from common picks can create competitive advantage

---

## 3. SCORING SYSTEM — DRIVERS

Driver scoring has five independent point categories per race weekend. Points from all categories are summed for the driver's total event score.

---

### 3.1 Qualifying Finish Position Points

Awarded based on where the driver finishes in qualifying.

| Position | Points |
|----------|--------|
| 1st | 50 |
| 2nd | 48 |
| 3rd | 46 |
| 4th | 44 |
| 5th | 42 |
| 6th | 40 |
| 7th | 38 |
| 8th | 36 |
| 9th | 34 |
| 10th | 32 |
| 11th | 30 |
| 12th | 28 |
| 13th | 26 |
| 14th | 24 |
| 15th | 22 |
| 16th | 20 |
| 17th | 18 |
| 18th | 16 |
| 19th | 14 |
| 20th | 12 |
| 21st | 10 |
| 22nd | 8 |

**Pattern:** 1st = 50 pts, decrements by 2 per position down to 22nd (8 pts).

---

### 3.2 Race Finish Position Points

Awarded based on where the driver finishes the main race.

| Position | Points |
|----------|--------|
| 1st | 100 |
| 2nd | 97 |
| 3rd | 94 |
| 4th | 91 |
| 5th | 88 |
| 6th | 85 |
| 7th | 82 |
| 8th | 79 |
| 9th | 76 |
| 10th | 73 |
| 11th | 70 |
| 12th | 67 |
| 13th | 64 |
| 14th | 61 |
| 15th | 58 |
| 16th | 55 |
| 17th | 52 |
| 18th | 49 |
| 19th | 46 |
| 20th | 43 |
| 21st | 40 |
| 22nd | 37 |

**Pattern:** 1st = 100 pts, decrements by 3 per position down to 22nd (37 pts).

---

### 3.3 Sprint Finish Position Points

Awarded based on where the driver finishes in a Sprint race (where applicable).

| Position | Points |
|----------|--------|
| 1st | 22 |
| 2nd | 21 |
| 3rd | 20 |
| 4th | 19 |
| 5th | 18 |
| 6th | 17 |
| 7th | 16 |
| 8th | 15 |
| 9th | 14 |
| 10th | 13 |
| 11th | 12 |
| 12th | 11 |
| 13th | 10 |
| 14th | 9 |
| 15th | 8 |
| 16th | 7 |
| 17th | 6 |
| 18th | 5 |
| 19th | 4 |
| 20th | 3 |
| 21st | 2 (implied by pattern) |
| 22nd | 1 (implied by pattern) |

**Pattern:** 1st = 22 pts, decrements by 1 per position. Only applies at race weekends that include a Sprint event.

---

### 3.4 Overtake Points ("Takes")

Awarded for net positions gained during the main race.

**Rule:** Calculated as (Qualifying Position) − (Race Finish Position). Uses **qualifying position**, NOT grid start position.

- Only net positive gains are rewarded (no penalty for losing positions)
- Rate: **+3 points per position gained**

**Examples:**
- Qualified P10, finished P5 → gained 5 positions → 5 × 3 = **15 overtake points**
- Qualified P3, finished P1 → gained 2 positions → 2 × 3 = **6 overtake points**
- Qualified P5, finished P8 → lost positions → **0 overtake points** (no negative)

---

### 3.5 Improvement Points ("I.P.")

Awarded when a driver finishes better than their 8-race rolling average finish position.

**Rule:** If (Driver's 8-race average rank) − (Current race finish position) ≥ 2, improvement points are awarded.

| Positions Improved vs. 8-Race Average | Points |
|---------------------------------------|--------|
| 1 | 0 |
| 2 | 2 |
| 3 | 4 |
| 4 | 6 |
| 5 | 9 |
| 6 | 12 |
| 7 | 16 |
| 8 | 20 |
| 9 | 25 |
| 10 | 30 |
| 11 | 30 |
| 12 | 30 |
| 13 | 30 |
| 14 | 30 |
| 15 | 30 |
| 16 | 30 |
| 17 | 30 |
| 18 | 30 |
| 19 | 30 |
| 20 | 30 |
| 21 | 30 |
| 22 | 30 |

**Notes:**
- Maximum improvement points = 30 (capped at 10+ positions improved)
- Improving by exactly 1 position = 0 points (threshold is 2+)
- The 8-race average is recalculated after each event

**Example from app:** Driver ranked 7th by 8-race average, finishes 3rd → improved by 4 positions → **6 improvement points**

---

### 3.6 Beating Teammate Points ("B.T." / "W.B.")

Awarded to the driver who finishes ahead of their teammate(s) in the same real-world constructor.

**Rule:** Awarded based on the margin of positions by which the driver beats their teammate in the race finish.

| Win Margin (Positions Ahead of Teammate) | Points |
|------------------------------------------|--------|
| 1–3 positions | 2 |
| 4–7 positions | 5 |
| 8–12 positions | 8 |
| 13+ positions | 12 |

**Notes:**
- Points go to the driver who finishes **ahead** of their teammate
- The losing teammate receives 0 points in this category
- Applies to real-world teammate pairings within the same constructor

---

### 3.7 Completion Points ("Comp")

Awarded incrementally as a driver completes race distance milestones.

| Race Completion Milestone | Points Awarded |
|---------------------------|----------------|
| 25% of race distance | 3 |
| 50% of race distance | 3 |
| 75% of race distance | 3 |
| 90% of race distance | 3 |

**Total possible completion points:** 12 (if driver completes 90%+ of the race)

**Calculation method:** GridRival divides total lap count by each percentage and rounds down to the nearest lap.

**Example:** 78-lap race → 75% milestone = lap 58 (78 × 0.75 = 58.5, rounded down to 58)

**DNF Implication:** A driver who DNFs early collects only the milestones they completed before retiring.

---

## 4. MAXIMUM POSSIBLE POINTS PER EVENT (Driver)

For a race weekend **with a Sprint**:

| Category | Maximum Points |
|----------|---------------|
| Qualifying Position (P1) | 50 |
| Sprint Position (P1) | 22 |
| Race Position (P1) | 100 |
| Overtake Points (max realistic ~18 positions × 3) | ~54 |
| Improvement Points (cap) | 30 |
| Beating Teammate (13+ positions ahead) | 12 |
| Completion (all 4 milestones) | 12 |
| **Theoretical Maximum** | **~280** |

For a race weekend **without a Sprint**, subtract up to 22 Sprint points.

---

## 5. CONTRACT MECHANICS

### 5.1 How Contracts Work

- When adding an element to your roster, you choose a **contract length** (number of races)
- **Default minimum:** 1 race
- **Default maximum:** 5 races
- Once a contract expires, the element is automatically **released** from your team
- You must then sign new elements to fill the vacant spots

### 5.2 Lockdown

- The game enters **Lockdown** before each event at a series-specific time
- After Lockdown: no team changes permitted
- Elements saved to your team at Lockdown are considered "signed" for the number of races selected
- Early release after Lockdown is possible but incurs a penalty (see 5.3)

### 5.3 Early Release Penalty

- You may release an element before their contract expires
- **Penalty:** 3% of the element's **current salary** is deducted from your bank balance
- Example: Driver valued at $20,000,000 → early release costs $600,000

### 5.4 One-Race-Interval Rule

- After any element leaves your team (contract expiry OR early release), you **cannot re-sign that element for one race**
- This applies universally regardless of the reason for release

---

## 6. SALARY & TEAM VALUE MECHANICS

### 6.1 Element Salaries

- Salaries are **dynamic** — they fluctuate race-to-race
- Salary movement is based on the element's rank after each event (ranked by fantasy points earned)
- Higher performance → salary increases; lower performance → salary decreases

### 6.2 Salary Gains/Losses While Under Contract

- If an element's salary **increases** while on your team: you **pocket the gain** (added to bank balance)
- If an element's salary **decreases** while on your team: the loss is also reflected in your bank balance
- This creates a trading/portfolio dimension — holding a driver who rises in value generates extra cash

### 6.3 Team Value Floor

- Each player maintains a **minimum team value of $100,000,000**
- This floor prevents a player from losing so much value that recovery is impossible
- The floor applies to total team value (bank balance + signed element values combined)

### 6.4 Bank Balance vs. Team Value

- **Bank Balance:** Cash available to sign elements. Only changes when signing/releasing
- **Team Value:** Bank Balance + current salary of all signed elements. Fluctuates every event
- These are two distinct figures shown separately in the app

---

## 7. KEY STRATEGIC CONCEPTS

### 7.1 Rolling Average (8-Race Window)

- Used in: Improvement Points calculation, Value Index, and general performance metrics
- Represents average across the **8 most recent** events
- Newly signed elements with fewer than 8 events use available history

### 7.2 Value Index

- Formula: (Rolling Avg Fantasy Points) ÷ (Current Salary)
- Higher = more efficient (more points per dollar)
- Key metric for identifying undervalued drivers and optimizing budget allocation

### 7.3 League Adoption

- Shows % of active players in your specific league who have each element signed
- Low adoption + high performance = potential competitive edge
- "Inactive" = scored 0 points in 2 consecutive events (excluded from adoption %)

### 7.4 DNF Ratio

- Historical metric: (Total DNFs) ÷ (Total Events Competed In)
- Based on all historical data in GridRival's database (multi-season)
- Useful for assessing reliability/risk when choosing elements

---

## 8. SCORING CATEGORY SUMMARY TABLE

| Category | Trigger | Max Points | Notes |
|----------|---------|-----------|-------|
| Qualifying Position | Quali result | 50 | P1=50, -2 per position |
| Sprint Position | Sprint result | 22 | P1=22, -1 per position |
| Race Position | Race result | 100 | P1=100, -3 per position |
| Overtake Points | Positions gained in race vs. quali | Uncapped* | +3 per position gained |
| Improvement Points | Outperformed 8-race avg | 30 | 0 pts for 1-pos improvement |
| Beating Teammate | Beat real-world teammate in race | 12 | Based on margin |
| Completion | Race distance milestones | 12 | 3 pts each at 25/50/75/90% |

*Overtake points are technically uncapped but practically bounded by field size (~21 max positions in F1)

---

## 9. DATA STRUCTURES FOR IMPLEMENTATION

### Driver Score Object (per event)
```
{
  driver_id: string,
  event_id: string,
  qualifying_position: int (1–22),
  sprint_position: int | null,
  race_position: int (1–22),
  race_completion_pct: float (0.0–1.0),
  teammate_race_positions: int[],
  rolling_avg_finish: float,  // 8-race average finish position rank
  
  // Calculated scores
  qualifying_points: int,
  sprint_points: int,
  race_position_points: int,
  overtake_points: int,       // (qualifying_position - race_position) * 3, min 0
  improvement_points: int,    // based on positions improved vs rolling_avg_finish
  beating_teammate_points: int,
  completion_points: int,
  total_event_points: int
}
```

### Overtake Points Logic
```python
def calculate_overtake_points(qualifying_pos, race_finish_pos):
    positions_gained = qualifying_pos - race_finish_pos
    if positions_gained <= 0:
        return 0
    return positions_gained * 3
```

### Improvement Points Logic
```python
IMPROVEMENT_TABLE = {
    1: 0, 2: 2, 3: 4, 4: 6, 5: 9,
    6: 12, 7: 16, 8: 20, 9: 25
}
def calculate_improvement_points(rolling_avg_rank, race_finish_pos):
    # Lower finish position number = better result
    positions_improved = round(rolling_avg_rank) - race_finish_pos
    if positions_improved <= 0:
        return 0
    if positions_improved >= 10:
        return 30
    return IMPROVEMENT_TABLE[positions_improved]
```

### Beating Teammate Points Logic
```python
def calculate_beating_teammate_points(driver_pos, teammate_positions):
    # Find best (lowest) teammate position
    best_teammate = min(teammate_positions)
    margin = best_teammate - driver_pos  # positive = driver is ahead
    if margin <= 0:
        return 0
    elif margin <= 3:
        return 2
    elif margin <= 7:
        return 5
    elif margin <= 12:
        return 8
    else:  # 13+
        return 12
```

### Completion Points Logic
```python
def calculate_completion_points(laps_completed, total_laps):
    milestones = [0.25, 0.50, 0.75, 0.90]
    points = 0
    for pct in milestones:
        milestone_lap = int(total_laps * pct)  # floor division
        if laps_completed >= milestone_lap:
            points += 3
    return points
```

---

## 10. NOTES & EDGE CASES

- **Qualifying-based overtakes, not grid position:** If a driver takes a grid penalty and starts further back than they qualified, overtake points are still calculated from their qualifying position.
- **Improvement points use rounded rolling average:** The 8-race average is compared as a rank (position number); when the average is fractional, the comparison still yields a whole-number "positions improved" value.
- **Completion milestones are independent:** A driver earns each milestone point as they pass it. A DNF at lap 60 of 78 earns the 25%, 50%, and 75% milestones (3+3+3 = 9 pts) but not the 90% milestone.
- **Salary changes are real-time during contract:** The gain/loss in salary value is reflected in your bank balance as it occurs during the season, not just at contract end.
- **Team value floor ($100M) is a floor on total team value**, not on bank balance alone.
- **One-Race-Interval Rule applies after ANY departure** — voluntary release or contract expiry.
