# Phase 0: County Data

**Prerequisites:** None (first phase)

**Pre-execution check:**
```python
prereq = check_phase_prerequisites(0, state, enrichment)
# Always proceeds (phase 0 has no prerequisites)
```

**Execution:**
```bash
# Single
python scripts/extract_county_data.py --address "{ADDRESS}" --update-only

# Batch
python scripts/extract_county_data.py --all --update-only
```

**Fields**: lot_sqft, year_built, garage_spaces, has_pool, livable_sqft

**Post-execution validation:**
```python
required_fields = ["lot_sqft", "year_built", "garage_spaces"]
for field in required_fields:
    if enrichment.get(field) is None:
        log_warning(f"Phase 0 missing {field} - will use defaults")
```

**Early kill-switch check:**
```python
from scripts.lib.kill_switch import evaluate_kill_switches, KillSwitchVerdict

verdict, severity, failures, results = evaluate_kill_switches(enrichment)
if verdict == KillSwitchVerdict.FAIL:
    # Still complete Phase 0, but mark property as FAILED
    update_property_tier("FAILED", reason=failures)
    # In strict mode, stop here
    # In default mode, continue for data collection but skip scoring
elif verdict == KillSwitchVerdict.WARNING:
    # Still viable but needs review
    log_warning(f"Kill-switch warnings: {failures}")
# else: PASS - continue normally
```

**Checkpoint**: `phase0_county = "complete"`
