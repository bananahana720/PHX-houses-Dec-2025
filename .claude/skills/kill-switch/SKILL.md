---
name: kill-switch
description: Evaluate buyer kill-switch criteria with weighted severity threshold. HARD criteria (HOA=$0, beds>=4, baths>=2) cause instant fail. SOFT criteria (sewer, garage, lot, year) accumulate severity scores - threshold >=3.0 fails, 1.5-3.0 warns. Use when filtering properties, validating purchases, or checking buyer requirements.
allowed-tools: Read, Bash(python:*)
---

# Kill Switch Evaluation Skill

Evaluate buyer criteria using a two-tier weighted severity threshold system.

## Quick Reference

```
HARD Criteria (instant fail):
  - HOA ≠ $0 → FAIL
  - beds < 4  → FAIL
  - baths < 2 → FAIL

SOFT Criteria (severity accumulates):
  - sewer ≠ city    → +2.5
  - year ≥ 2024     → +2.0
  - garage < 2      → +1.5
  - lot not 7k-15k  → +1.0

Verdict:
  severity >= 3.0  → FAIL
  severity >= 1.5  → WARNING
  severity < 1.5   → PASS
```

## Severity Weights Rationale

| Criterion | Weight | Why |
|-----------|--------|-----|
| Sewer | 2.5 | Septic = $10k+ failure risk, ongoing maintenance |
| Year Built | 2.0 | New builds = builder markup, warranty issues |
| Garage | 1.5 | Security/storage convenience, resale factor |
| Lot Size | 1.0 | Minor preference, less critical than structure |

**Design:** Single SOFT failure survivable (max 2.5 < 3.0), two significant failures = review/exclude.

## Canonical Implementation

```python
from scripts.lib.kill_switch import (
    evaluate_kill_switches,      # Returns (verdict, severity, failures, results)
    KillSwitchVerdict,           # PASS, WARNING, FAIL
    HARD_CRITERIA,               # {"hoa", "beds", "baths"}
    SOFT_SEVERITY_WEIGHTS,       # {"sewer": 2.5, "garage": 1.5, ...}
    SEVERITY_FAIL_THRESHOLD,     # 3.0
    SEVERITY_WARNING_THRESHOLD,  # 1.5
)

verdict, severity, failures, results = evaluate_kill_switches(property_dict)

if verdict == KillSwitchVerdict.FAIL:
    print(f"Excluded: {failures}")
elif verdict == KillSwitchVerdict.WARNING:
    print(f"Needs review (severity {severity})")
```

## Constants (Single Source of Truth)

```python
from src.phx_home_analysis.config.constants import (
    SEVERITY_FAIL_THRESHOLD,        # 3.0
    SEVERITY_WARNING_THRESHOLD,     # 1.5
    SEVERITY_WEIGHT_SEWER,          # 2.5
    SEVERITY_WEIGHT_YEAR_BUILT,     # 2.0
    SEVERITY_WEIGHT_GARAGE,         # 1.5
    SEVERITY_WEIGHT_LOT_SIZE,       # 1.0
)
```

## Null Handling

| Field | If Null | Result | Flag |
|-------|---------|--------|------|
| hoa_fee | PASS | Assume no HOA | Yellow |
| sewer_type | PASS | Cannot verify | Yellow |
| garage_spaces | PASS | Cannot verify | Yellow |
| beds, baths | Evaluated | 0 if missing | Green/Red |

**Yellow = UNKNOWN status, verify before final decision.**

## Decision Logic

```
1. Check HARD criteria first
   Any fail? → STOP, return FAIL

2. Calculate SOFT severity
   Sum weights of all failing SOFT criteria

3. Apply threshold
   ≥3.0 → FAIL
   ≥1.5 → WARNING
   <1.5 → PASS
```

## Example Outcomes

| Scenario | HARD | SOFT Severity | Verdict |
|----------|------|---------------|---------|
| HOA = $150 | FAIL | N/A | **FAIL** |
| Septic + 1-car garage | PASS | 4.0 | **FAIL** |
| 1-car garage only | PASS | 1.5 | WARNING |
| Lot = 6,500 sqft only | PASS | 1.0 | PASS |

## Integration Pattern

```python
def process_property(address: str) -> dict:
    prop = get_property(address)
    verdict, severity, failures, _ = evaluate_kill_switches(prop)

    if verdict == KillSwitchVerdict.FAIL:
        return {"status": "failed", "tier": "FAILED", "failures": failures}

    if verdict == KillSwitchVerdict.WARNING:
        prop["needs_review"] = True
        prop["review_reason"] = f"Severity {severity}: {failures}"

    # Continue with scoring...
```

## Best Practices

1. **Check early** - Apply before expensive operations (images, scoring)
2. **Use canonical module** - `scripts/lib/kill_switch.py`
3. **Track severity** - Store scores for buyer transparency
4. **County first** - Use Phase 0 data for authoritative lot/year/garage
5. **Review WARNINGs** - Properties with 1.5-2.99 need buyer input
