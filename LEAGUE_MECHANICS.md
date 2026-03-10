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

---

## 11. CONSTRUCTOR SCORING (F1 Only)

Constructors are scored separately from drivers. A constructor slot on your team earns points based on the constructor's aggregate qualifying and race performance. Constructor scoring uses different (lower) point scales than driver scoring.

### 11.1 Constructor Qualifying Points

Awarded based on the constructor's combined qualifying result (best of their two drivers, or aggregate — exact aggregation method not specified in screenshots, but position shown is a single ranked position 1st–18th+).

| Position | Points |
|----------|--------|
| 1st | 30 |
| 2nd | 29 |
| 3rd | 28 |
| 4th | 27 |
| 5th | 26 |
| 6th | 25 |
| 7th | 24 |
| 8th | 23 |
| 9th | 22 |
| 10th | 21 |
| 11th | 20 |
| 12th | 19 |
| 13th | 18 |
| 14th | 17 |
| 15th | 16 |
| 16th | 15 |
| 17th | 14 |
| 18th | 13 |

**Pattern:** 1st = 30 pts, decrements by 1 per position.

### 11.2 Constructor Race Points

Awarded based on the constructor's combined race result position.

| Position | Points |
|----------|--------|
| 1st | 60 |
| 2nd | 58 |
| 3rd | 56 |
| 4th | 54 |
| 5th | 52 |
| 6th | 50 |
| 7th | 48 |
| 8th | 46 |
| 9th | 44 |
| 10th | 42 |
| 11th | 40 |
| 12th | 38 |
| 13th | 36 |
| 14th | 34 |
| 15th | 32 |
| 16th | 30 |
| 17th | 28 |
| 18th | 26 |
| 19th | 24 |
| 20th | 22 |
| 21st | 20 |
| 22nd | 18 |

**Pattern:** 1st = 60 pts, decrements by 2 per position down to 22nd (18 pts).

### 11.3 Constructor vs. Driver Scoring Comparison

| Category | Driver Max | Constructor Max |
|----------|-----------|----------------|
| Qualifying | 50 (P1) | 30 (P1) |
| Race | 100 (P1) | 60 (P1) |
| Sprint | 22 (P1) | N/A (not shown) |
| Overtake Points | Yes (+3/pos) | N/A |
| Improvement Points | Yes (up to 30) | N/A |
| Beating Teammate | Yes (up to 12) | N/A |
| Completion | Yes (up to 12) | N/A |

Constructors score only on qualifying and race finish position. They do not earn Overtake, Improvement, Beating Teammate, or Completion points.

---

## 12. SALARY ADJUSTMENT ALGORITHM (Detailed)

This section documents the exact mechanics by which element salaries change after each race event. Salaries are denominated in £ (GBP) in the app, regardless of the fantasy budget denomination used in leagues.

### 12.1 Three-Step Salary Adjustment Process

**Step 1: Rank elements by fantasy points earned in the event**
After each event, all elements (drivers separately, constructors separately) are ranked by the total fantasy points they earned during that event. Rank 1 = highest scorer.

**Step 2: Calculate base salary variation**
Look up the element's new rank in the Default Salary Table (see sections 12.3 and 12.4). The base salary variation = (Default Salary at new rank) − (Element's current salary before the race).

- Positive variation = element performed better than their current salary implies → salary should increase
- Negative variation = element performed worse → salary should decrease

**Step 3: Apply adjustment formula**
```
adjustment = floor(base_salary_variation / 4, nearest_100k)
new_salary = current_salary + adjustment
```

Constraints:
- **Driver maximum adjustment:** ±£2,000,000 per event
- **Constructor maximum adjustment:** ±£3,000,000 per event
- **Minimum adjustment (both):** ±£100,000 (i.e., if |base_variation / 4| < £100k, still move by £100k in the correct direction)
- Rounding: round **down** to the nearest £100,000

### 12.2 Worked Example (from app)

| Step | Value |
|------|-------|
| 1. Driver salary before the race | £15,800,000 |
| 2. Driver's fantasy rank for the race | 8th |
| 3. Default salary for 8th rank (from table) | £22,800,000 |
| 4. Base salary variation (step 3 − step 1) | +£7,000,000 |
| 5. Adjustment = £7.0M ÷ 4 (rounded down to nearest £100k) | +£1,700,000 |
| 6. New salary after the race | £17,500,000 |

### 12.3 Default Driver Salary Table

Used as the reference point in Step 2 of salary adjustment. Rank is determined by fantasy points earned in the event.

| Fantasy Rank | Default Salary |
|-------------|---------------|
| 1st | £34,000,000 |
| 2nd | £32,400,000 |
| 3rd | £30,800,000 |
| 4th | £29,200,000 |
| 5th | £27,600,000 |
| 6th | £26,000,000 |
| 7th | £24,400,000 |
| 8th | £22,800,000 |
| 9th | £21,200,000 |
| 10th | £19,600,000 |
| 11th | £18,000,000 |
| 12th | £16,400,000 |
| 13th | £14,800,000 |
| 14th | £13,200,000 |
| 15th | £11,600,000 |
| 16th | £10,000,000 |
| 17th | £8,400,000 |
| 18th | £6,800,000 |
| 19th | £5,200,000 |
| 20th | £3,600,000 |
| 21st | £2,000,000 |
| 22nd | £400,000 |

**Pattern:** 1st = £34M, decrements by £1,600,000 per rank. 22nd = £400,000 (floor).

### 12.4 Default Constructor Salary Table

| Fantasy Rank | Default Salary |
|-------------|---------------|
| 1st | £30,000,000 |
| 2nd | £27,400,000 |
| 3rd | £24,800,000 |
| 4th | £22,200,000 |
| 5th | £19,600,000 |
| 6th | £17,000,000 |
| 7th | £14,400,000 |
| 8th | £11,800,000 |
| 9th | £9,200,000 |
| 10th | £6,600,000 |
| 11th | £4,000,000 |

**Pattern:** 1st = £30M, decrements by £2,600,000 per rank. 11th (last constructor) = £4,000,000.

### 12.5 Season-Start Salaries

- All elements begin the season with a **manually calculated starting salary**
- Based on: prior season's performance + pre-season testing results + projected performance
- Starting salaries are NOT generated by the default salary table formula — they are set by GridRival staff

### 12.6 Salary Adjustment Pseudocode

```python
DRIVER_DEFAULT_SALARY = {
    1: 34_000_000, 2: 32_400_000, 3: 30_800_000, 4: 29_200_000,
    5: 27_600_000, 6: 26_000_000, 7: 24_400_000, 8: 22_800_000,
    9: 21_200_000, 10: 19_600_000, 11: 18_000_000, 12: 16_400_000,
    13: 14_800_000, 14: 13_200_000, 15: 11_600_000, 16: 10_000_000,
    17: 8_400_000, 18: 6_800_000, 19: 5_200_000, 20: 3_600_000,
    21: 2_000_000, 22: 400_000
}

CONSTRUCTOR_DEFAULT_SALARY = {
    1: 30_000_000, 2: 27_400_000, 3: 24_800_000, 4: 22_200_000,
    5: 19_600_000, 6: 17_000_000, 7: 14_400_000, 8: 11_800_000,
    9: 9_200_000, 10: 6_600_000, 11: 4_000_000
}

def calculate_salary_adjustment(current_salary, fantasy_rank, element_type='driver'):
    salary_table = DRIVER_DEFAULT_SALARY if element_type == 'driver' else CONSTRUCTOR_DEFAULT_SALARY
    max_adjustment = 2_000_000 if element_type == 'driver' else 3_000_000
    min_adjustment = 100_000

    default_salary = salary_table[fantasy_rank]
    base_variation = default_salary - current_salary

    # Divide by 4, round down to nearest 100k
    raw_adjustment = base_variation / 4
    adjustment = int(raw_adjustment / 100_000) * 100_000  # floor to nearest 100k

    # Apply cap
    if abs(adjustment) > max_adjustment:
        adjustment = max_adjustment if adjustment > 0 else -max_adjustment

    # Apply floor (minimum movement if any change is warranted)
    if adjustment == 0 and base_variation != 0:
        adjustment = min_adjustment if base_variation > 0 else -min_adjustment

    return current_salary + adjustment
```

---

## 13. UPDATED SCORING SUMMARY TABLE (All Element Types)

| Category | Drivers | Constructors |
|----------|---------|-------------|
| Qualifying Position | P1=50, -2/pos to P22=8 | P1=30, -1/pos to P18=13 |
| Race Position | P1=100, -3/pos to P22=37 | P1=60, -2/pos to P22=18 |
| Sprint Position | P1=22, -1/pos | N/A |
| Overtake Points | +3 per position gained vs. quali | N/A |
| Improvement Points | 0–30 based on vs. 8-race avg | N/A |
| Beating Teammate | 2/5/8/12 based on margin | N/A |
| Completion | 3 pts each at 25/50/75/90% | N/A |
| Salary Adjustment Cap | ±£2M per event | ±£3M per event |
| Salary Adjustment Min | ±£100k per event | ±£100k per event |
