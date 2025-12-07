---
name: block-hardcoded-values
enabled: true
event: file
conditions:
  - field: file_path
    operator: regex_match
    pattern: src/phx_home_analysis/(services|application|domain)/.*\.py$
  - field: new_text
    operator: regex_match
    pattern: (?:=\s*["']?(UNICORN|CONTENDER|PASS)["']?|[=<>]\s*(605|484|363|250|175|180|230)|threshold\s*=\s*\d+|score\s*[<>=]+\s*\d{2,3})
action: block
---

## 🛑 Hardcoded Business Value Blocked

**You attempted to add a hardcoded business rule value to production code.**

### Detected Antipatterns
| Pattern | Issue | Use Instead |
|---------|-------|-------------|
| `"UNICORN"` | String literal | `ScoringTier.UNICORN` enum |
| `= 605` | Max score literal | `SCORING_CONSTANTS.MAX_SCORE` |
| `>= 484` | Tier threshold | `TIER_THRESHOLDS["UNICORN"]` |
| `threshold = 8000` | Kill-switch value | `HARD_CRITERIA["lot_size"]` |

### Why This Is Blocked (Antipattern Detection)
Per validation wave findings:
- **Magic numbers** make code hard to maintain
- **Threshold drift** occurs when values change in one place but not others
- **Kill-switch criteria** are authoritative in `constants.py`
- **Scoring weights** are defined in `scoring_config.yaml`

### Correct Approach

**For tier constants:**
```python
from phx_home_analysis.domain.enums import ScoringTier

if tier == ScoringTier.UNICORN:
    ...
```

**For scoring thresholds:**
```python
from phx_home_analysis.services.scoring.constants import TIER_THRESHOLDS, MAX_SCORE

if score >= TIER_THRESHOLDS["UNICORN"]:  # 484
    return ScoringTier.UNICORN
```

**For kill-switch criteria:**
```python
from phx_home_analysis.services.kill_switch.constants import HARD_CRITERIA

if lot_sqft < HARD_CRITERIA["lot_size_min"]:  # 8000
    return KillSwitchResult.FAIL
```

### Reference Files
- Scoring constants: `src/phx_home_analysis/services/scoring/constants.py`
- Kill-switch criteria: `src/phx_home_analysis/services/kill_switch/constants.py`
- Tier thresholds: Per ADR-07, 605 max, 484 Unicorn, 363 Contender

**Extract all magic numbers to named constants before proceeding.**
