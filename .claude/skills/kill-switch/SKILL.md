---
name: kill-switch
description: Evaluate buyer kill-switch criteria with weighted severity threshold system. HARD criteria (HOA, beds, baths) cause instant failure. SOFT criteria (sewer, garage, lot, year) accumulate severity scores. Use when filtering properties, validating purchases, or checking buyer requirements.
allowed-tools: Read, Bash(python:*)
---

# Kill Switch Evaluation Skill

Expert at evaluating buyer criteria using a two-tier weighted severity threshold system that distinguishes between non-negotiable requirements (HARD) and flexible preferences (SOFT).

## Severity Threshold System Overview

The kill-switch system uses a **weighted severity model** instead of simple pass/fail:

```
                    +------------------+
                    |   Property Data  |
                    +--------+---------+
                             |
              +--------------+--------------+
              |                             |
     +--------v--------+           +--------v--------+
     |  HARD Criteria  |           |  SOFT Criteria  |
     |  (instant fail) |           | (severity sum)  |
     +-----------------+           +--------+--------+
              |                             |
       Any failure?                  Sum weights
              |                             |
        +-----v-----+              +--------v--------+
        |   FAIL    |              | severity score  |
        +-----------+              +--------+--------+
                                            |
                          +-----------------+-----------------+
                          |                 |                 |
                    >= 3.0            1.5 - 2.99           < 1.5
                          |                 |                 |
                    +-----v-----+     +-----v-----+     +-----v-----+
                    |   FAIL    |     |  WARNING  |     |   PASS    |
                    +-----------+     +-----------+     +-----------+
```

## HARD Criteria (Instant Fail)

Any single HARD failure immediately disqualifies the property, regardless of all other criteria.

| Criterion | Field | Requirement | Rationale |
|-----------|-------|-------------|-----------|
| **HOA** | `hoa_fee` | Must be $0 or None | Buyer is firm - no governance/assessments |
| **Beds** | `beds` | Must be >= 4 | Core space requirement, non-negotiable |
| **Baths** | `baths` | Must be >= 2 | Core space requirement, non-negotiable |

**Why HARD?** These represent buyer deal-breakers that cannot be compensated by other property strengths.

## SOFT Criteria (Weighted Severity)

SOFT failures accumulate a severity score. The total determines the verdict.

| Criterion | Field | Requirement | Severity Weight | Rationale |
|-----------|-------|-------------|-----------------|-----------|
| **Sewer** | `sewer_type` | Must be "city" | **2.5** | Infrastructure risk - septic maintenance/failure |
| **Year Built** | `year_built` | Must be < 2024 | **2.0** | New build avoidance - warranty issues, builder markup |
| **Garage** | `garage_spaces` | Must be >= 2 | **1.5** | Convenience factor - vehicle security, storage |
| **Lot Size** | `lot_sqft` | 7,000-15,000 sqft | **1.0** | Minor preference - yard space flexibility |

**Maximum possible SOFT severity:** 7.0 (all four fail)

## Verdict Logic

```python
def determine_verdict(has_hard_failure: bool, severity_score: float) -> str:
    if has_hard_failure:
        return "FAIL"           # Instant fail, severity irrelevant
    if severity_score >= 3.0:
        return "FAIL"           # Threshold exceeded
    if severity_score >= 1.5:
        return "WARNING"        # Approaching limit, buyer review needed
    return "PASS"               # Acceptable
```

| Condition | Verdict | Action |
|-----------|---------|--------|
| Any HARD failure | **FAIL** | Auto-exclude, no further processing |
| severity >= 3.0 | **FAIL** | Threshold exceeded, auto-exclude |
| 1.5 <= severity < 3.0 | **WARNING** | Flag for buyer review |
| severity < 1.5 | **PASS** | Proceed with scoring |

## Example Outcomes

### Example 1: Clean Pass
```json
{"hoa_fee": 0, "beds": 4, "baths": 2.5, "sewer_type": "city",
 "garage_spaces": 2, "lot_sqft": 9000, "year_built": 2010}
```
- HARD: All pass
- SOFT: All pass (severity = 0.0)
- **Verdict: PASS**

### Example 2: Single SOFT Failure (Pass)
```json
{"hoa_fee": 0, "beds": 4, "baths": 2, "sewer_type": "city",
 "garage_spaces": 1, "lot_sqft": 10000, "year_built": 2015}
```
- HARD: All pass
- SOFT: Garage fails (1-car < 2), severity = **1.5**
- **Verdict: WARNING** (1.5 >= threshold but < 3.0)

### Example 3: Multiple SOFT Failures (Fail)
```json
{"hoa_fee": 0, "beds": 4, "baths": 2, "sewer_type": "septic",
 "garage_spaces": 1, "lot_sqft": 8000, "year_built": 2018}
```
- HARD: All pass
- SOFT: Sewer (2.5) + Garage (1.5) = severity **4.0**
- **Verdict: FAIL** (4.0 >= 3.0 threshold)

### Example 4: HARD Failure Trumps All
```json
{"hoa_fee": 150, "beds": 5, "baths": 3, "sewer_type": "city",
 "garage_spaces": 3, "lot_sqft": 10000, "year_built": 2008}
```
- HARD: HOA fails ($150 > 0)
- SOFT: All pass (irrelevant)
- **Verdict: FAIL** (HARD failure = instant fail)

### Example 5: Borderline WARNING
```json
{"hoa_fee": 0, "beds": 4, "baths": 2, "sewer_type": "city",
 "garage_spaces": 2, "lot_sqft": 6500, "year_built": 2015}
```
- HARD: All pass
- SOFT: Lot size fails (6,500 < 7,000), severity = **1.0**
- **Verdict: PASS** (1.0 < 1.5 warning threshold)

## Centralized Constants

**Primary Location:** `src/phx_home_analysis/config/constants.py`
**Secondary Location:** `src/phx_home_analysis/services/kill_switch/constants.py`

All severity thresholds and weights are centralized in the config module and re-exported via the service layer:

```python
from src.phx_home_analysis.config.constants import (
    SEVERITY_FAIL_THRESHOLD,        # 3.0
    SEVERITY_WARNING_THRESHOLD,     # 1.5
    SEVERITY_WEIGHT_SEWER,          # 2.5
    SEVERITY_WEIGHT_YEAR_BUILT,     # 2.0
    SEVERITY_WEIGHT_GARAGE,         # 1.5
    SEVERITY_WEIGHT_LOT_SIZE,       # 1.0
)

from src.phx_home_analysis.services.kill_switch.constants import (
    KillSwitchVerdict,              # PASS, WARNING, FAIL
    SOFT_SEVERITY_WEIGHTS,          # dict: {"sewer": 2.5, "garage": 1.5, ...}
    HARD_CRITERIA,                  # set: {"hoa", "beds", "baths"}
)
```

**Note:** These constants are the **single source of truth** - both CLI (`scripts/lib/kill_switch.py`) and service layers import from here.

## Architecture (Consolidated)

**Canonical Source:** `src/phx_home_analysis/config/constants.py`
- Contains: Severity thresholds and weights (imported by all layers)

**Service Wrapper:** `src/phx_home_analysis/services/kill_switch/constants.py`
- Re-exports config constants + `KillSwitchVerdict`, `SOFT_SEVERITY_WEIGHTS`, `HARD_CRITERIA`
- Provides both scripts/lib and service layer naming conventions

**Service Layer:** `src/phx_home_analysis/services/kill_switch/filter.py`
- `KillSwitchFilter` class for programmatic use

**CLI Layer:** `scripts/lib/kill_switch.py`
- Thin facade importing from service constants
- `evaluate_kill_switches()` for script usage

**Note:** Both layers now import from shared constants (DRY consolidated)

## Canonical Implementation

Use the project's canonical kill-switch module:

```python
from scripts.lib.kill_switch import (
    # Core evaluation function (new API)
    evaluate_kill_switches,      # Returns (verdict, severity, failures, results)

    # Verdict enum
    KillSwitchVerdict,           # PASS, WARNING, FAIL

    # Configuration constants
    HARD_CRITERIA,               # {"hoa", "beds", "baths"}
    SOFT_SEVERITY_WEIGHTS,       # {"sewer": 2.5, "garage": 1.5, ...}
    SEVERITY_FAIL_THRESHOLD,     # 3.0
    SEVERITY_WARNING_THRESHOLD,  # 1.5

    # Legacy compatibility
    evaluate_kill_switches_legacy,  # Returns (bool, failures, results)
    apply_kill_switch,              # Mutates Property dataclass

    # Display helpers
    evaluate_kill_switches_for_display,  # For deal sheets/UI
    KILL_SWITCH_DISPLAY_NAMES,           # Title-case names
)
```

### New API: evaluate_kill_switches()

```python
from scripts.lib.kill_switch import evaluate_kill_switches, KillSwitchVerdict

# Evaluate a property
verdict, severity, failures, results = evaluate_kill_switches(property_dict)

# Check verdict
if verdict == KillSwitchVerdict.FAIL:
    print(f"Property excluded: {failures}")
elif verdict == KillSwitchVerdict.WARNING:
    print(f"Needs review (severity {severity}): {failures}")
else:
    print("Property passed all criteria")

# Inspect individual results
for result in results:
    print(f"{result.name}: {'PASS' if result.passed else 'FAIL'}")
    if not result.passed and not result.is_hard:
        print(f"  Severity weight: +{result.severity_weight}")
```

### Legacy API: evaluate_kill_switches_legacy()

For backward compatibility with existing code:

```python
from scripts.lib.kill_switch import evaluate_kill_switches_legacy

# Returns old-style tuple (WARNING maps to passed=True)
passed, failures, results = evaluate_kill_switches_legacy(property_dict)

if not passed:
    print(f"Kill switch failures: {failures}")
```

### Apply to Property Dataclass

```python
from scripts.lib.kill_switch import apply_kill_switch

# Mutates property in-place
prop = apply_kill_switch(prop)

# Check results
print(prop.kill_switch_passed)    # True if PASS or WARNING
print(prop.kill_switch_failures)  # List of failure messages

# New fields (if property has them)
print(prop.kill_switch_verdict)   # "PASS", "WARNING", or "FAIL"
print(prop.kill_switch_severity)  # float severity score
```

### Display-Friendly Evaluation

```python
from scripts.lib.kill_switch import evaluate_kill_switches_for_display

# Get display-ready results for deal sheets
results = evaluate_kill_switches_for_display(property_dict)

# Each criterion has display metadata
for name, data in results.items():
    if name == "_summary":
        continue  # Summary is separate
    print(f"{name}: {data['label']} ({data['color']})")
    print(f"  Value: {data['description']}")
    print(f"  HARD: {data['is_hard']}, Weight: {data['severity_weight']}")

# Access summary
summary = results["_summary"]
print(f"Verdict: {summary['verdict']}, Severity: {summary['severity_score']}")
```

## Unknown/Null Handling

| Field | If Null/NaN | Result | Display Color |
|-------|-------------|--------|---------------|
| `hoa_fee` | PASS | Assume no HOA unless stated | Yellow |
| `sewer_type` | PASS | Cannot verify, proceed with caution | Yellow |
| `garage_spaces` | PASS | Cannot verify, proceed with caution | Yellow |
| `lot_sqft` | PASS | Cannot verify, proceed with caution | Yellow |
| `year_built` | PASS | Cannot verify, proceed with caution | Yellow |
| `beds` | Evaluated | Required field - 0 if missing | Green/Red |
| `baths` | Evaluated | Required field - 0 if missing | Green/Red |

**Important:** Yellow (UNKNOWN) status indicates data that should be verified before final decision.

## Integration with Scoring Pipeline

### Early Exit Pattern

```python
def process_property(address: str) -> dict:
    """Process property with early exit on kill-switch failure."""
    prop = get_property(address)

    verdict, severity, failures, _ = evaluate_kill_switches(prop)

    if verdict == KillSwitchVerdict.FAIL:
        return {
            "address": address,
            "status": "failed",
            "tier": "FAILED",
            "kill_switch_failures": failures,
            "kill_switch_severity": severity,
            "next_steps": []  # No further processing needed
        }

    if verdict == KillSwitchVerdict.WARNING:
        # Continue but flag for review
        prop["needs_review"] = True
        prop["review_reason"] = f"Kill-switch severity {severity}: {failures}"

    # Continue with scoring...
```

### Tier Assignment

```python
def assign_tier(score: float, verdict: KillSwitchVerdict) -> str:
    """Assign tier based on score and kill-switch verdict."""
    if verdict == KillSwitchVerdict.FAIL:
        return "FAILED"  # Regardless of score

    # WARNING properties can still tier normally but are flagged
    if score > 480:
        return "UNICORN"
    elif score >= 360:
        return "CONTENDER"
    else:
        return "PASS"
```

## County Data Verification

After Phase 0 (county data extraction), verify SOFT criteria with authoritative data:

```python
def verify_soft_criteria_with_county(prop: dict) -> tuple[float, list[str]]:
    """Check SOFT kill-switches using county-verified data.

    County API provides authoritative values for:
    - lot_sqft (weight 1.0)
    - year_built (weight 2.0)
    - garage_spaces (weight 1.5)

    NOT from county (requires manual research):
    - sewer_type (weight 2.5)
    """
    severity = 0.0
    issues = []

    # Lot size (county data, weight 1.0)
    lot = prop.get("lot_sqft")
    if lot is not None:
        if lot < 7000:
            severity += 1.0
            issues.append(f"lot_size: {lot:,} sqft < 7,000 [+1.0]")
        elif lot > 15000:
            severity += 1.0
            issues.append(f"lot_size: {lot:,} sqft > 15,000 [+1.0]")

    # Year built (county data, weight 2.0)
    year = prop.get("year_built")
    if year is not None and year >= 2024:
        severity += 2.0
        issues.append(f"year_built: {year} >= 2024 (new build) [+2.0]")

    # Garage (county data, weight 1.5)
    garage = prop.get("garage_spaces")
    if garage is not None and garage < 2:
        severity += 1.5
        issues.append(f"garage: {garage}-car < 2 [+1.5]")

    return severity, issues
```

## Summary Report Format

```
KILL SWITCH SUMMARY (Severity Threshold System)
===============================================
Total Properties: 25
Passed (severity < 1.5): 15 (60%)
Warning (1.5 <= severity < 3.0): 5 (20%)
Failed: 5 (20%)

Failure Breakdown:
  HARD Failures:
    - HOA: 2 properties
    - Beds: 1 property

  SOFT Threshold Exceeded (severity >= 3.0):
    - Sewer + Garage: 1 property (severity 4.0)
    - Sewer + Year: 1 property (severity 4.5)

Warning Properties (needs review):
    - 123 Main St: garage only (severity 1.5)
    - 456 Oak Ave: lot_size only (severity 1.0) -- below threshold but flagged

Average Severity (non-failed): 0.8
```

## Best Practices

1. **Check early** - Apply kill-switch before expensive operations (image extraction, scoring)
2. **Use canonical module** - `scripts/lib/kill_switch.py` is single source of truth
3. **Understand thresholds**:
   - FAIL: severity >= 3.0 OR any HARD failure
   - WARNING: 1.5 <= severity < 3.0
   - PASS: severity < 1.5
4. **Track severity** - Store severity scores for buyer transparency
5. **County first** - Use Phase 0 county data for authoritative lot/year/garage checks
6. **Display colors** - Green=pass, Yellow=unknown, Red=fail
7. **Review WARNINGs** - Properties with 1.5-2.99 severity need buyer input

## Severity Weight Rationale

| Criterion | Weight | Why This Weight? |
|-----------|--------|------------------|
| Sewer | 2.5 | Highest: Septic = ongoing maintenance, potential $10k+ failure |
| Year Built | 2.0 | High: New builds have builder markup, warranty claims, unproven quality |
| Garage | 1.5 | Medium: Security/storage convenience, resale factor |
| Lot Size | 1.0 | Low: Preference flexibility, less critical than structure |

**Design principle:** A single SOFT failure should be survivable (max 2.5 < 3.0), but two significant failures should trigger review or exclusion.

---

## Chain-of-Thought Evaluation Process

When evaluating kill-switches, follow this systematic reasoning chain:

### Step 1: Evaluate HARD Criteria First

**Always check HARD criteria before SOFT** - any HARD failure is immediate exclusion:

```
1. HOA fee: Is hoa_fee > 0? -> HARD FAIL
2. Beds: Is beds < 4? -> HARD FAIL
3. Baths: Is baths < 2? -> HARD FAIL
```

If any HARD failure, stop processing and return FAIL.

### Step 2: Calculate SOFT Severity

For each SOFT criterion that fails, add its weight:

```
severity = 0.0
if sewer_type != "city":     severity += 2.5
if year_built >= 2024:       severity += 2.0
if garage_spaces < 2:        severity += 1.5
if lot_sqft not in range:    severity += 1.0
```

### Step 3: Apply Threshold Logic

```
if severity >= 3.0:   verdict = FAIL
elif severity >= 1.5: verdict = WARNING
else:                 verdict = PASS
```

### Step 4: Document Decision

```
**Property:** [Address]
**HARD Status:** PASS/FAIL (specify which failed)
**SOFT Severity:** X.X (breakdown: sewer +2.5, etc.)
**Final Verdict:** PASS/WARNING/FAIL
**Rationale:** [1-2 sentences explaining decision]
```

---

## Edge Case Decision Matrix

| Scenario | HARD | SOFT Severity | Verdict | Notes |
|----------|------|---------------|---------|-------|
| HOA = $1/month | FAIL | N/A | **FAIL** | Any HOA fee = governance exists |
| lot = 6,950 sqft | PASS | +1.0 | PASS | Slightly under, tolerable |
| baths = 1.75 | FAIL | N/A | **FAIL** | 1.75 < 2.0, no rounding |
| 1 garage + 1 carport | PASS | +1.5 | WARNING | Carport != garage |
| septic + 1-car garage | PASS | +4.0 | **FAIL** | 2.5 + 1.5 >= 3.0 |
| year_built = 2024 + lot = 6,000 | PASS | +3.0 | **FAIL** | 2.0 + 1.0 >= 3.0 |
| sewer = "unknown" | PASS | 0 | PASS | Unknown passes with yellow flag |

---

## Migration from Legacy System

If updating code from the old pass/fail system:

```python
# OLD (deprecated)
passed, failures, results = evaluate_kill_switches(data)

# NEW (recommended)
verdict, severity, failures, results = evaluate_kill_switches(data)

# Or use legacy wrapper for minimal changes
passed, failures, results = evaluate_kill_switches_legacy(data)
# Note: WARNING maps to passed=True in legacy mode
```

**Key behavioral change:** Properties that would have failed under the old system may now get WARNING status if their severity is 1.5-2.99. This gives buyers more visibility into borderline properties.
