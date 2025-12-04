# Phase 1: Kill-Switch Consolidation (CRITICAL)

### Problem Statement

Kill-switch criteria are defined in **3 separate locations** with different implementations:

1. `scripts/phx_home_analyzer.py` lines 83-91 - Dict with lambdas
2. `scripts/deal_sheets.py` lines 15-51 - Dict with lambdas (pandas-based)
3. `src/.../services/kill_switch/criteria.py` - Class-based (canonical)

**Impact:** Criteria changes require 3 synchronization points. The service layer has robust class-based implementation, but scripts bypass it.

### Solution

Modify scripts to import and use the canonical `KillSwitchFilter` from the service layer.

### Implementation Steps

#### Step 1.1: Update phx_home_analyzer.py

**Before:**
```python
KILL_SWITCH_CRITERIA = {
    "hoa": {"check": lambda p: p.hoa_fee == 0 or p.hoa_fee is None, ...},
    "sewer": {"check": lambda p: p.sewer_type == "city" or p.sewer_type is None, ...},
    # ... 5 more criteria
}

def apply_kill_switch(prop: Property) -> Property:
    failures = []
    for name, criteria in KILL_SWITCH_CRITERIA.items():
        if not criteria["check"](prop):
            failures.append(f"{name}: {criteria['desc']}")
    prop.kill_switch_failures = failures
    prop.kill_switch_passed = len(failures) == 0
    return prop
```

**After:**
```python
# Remove KILL_SWITCH_CRITERIA dict entirely
# Remove apply_kill_switch function

# Import canonical service
from src.phx_home_analysis.services.kill_switch import KillSwitchFilter

# Use in pipeline
def main():
    filter_service = KillSwitchFilter()
    passed, failed = filter_service.filter_properties(properties)
```

#### Step 1.2: Update deal_sheets.py

**Before:**
```python
KILL_SWITCH_CRITERIA = {
    'HOA': {'field': 'hoa_fee', 'check': lambda val: val == 0 or pd.isna(val), ...},
    # ... more criteria
}

for name, criteria in KILL_SWITCH_CRITERIA.items():
    field = criteria['field']
    value = row[field] if field in row and not pd.isna(row[field]) else None
    # ... evaluation logic
```

**After:**
```python
from src.phx_home_analysis.services.kill_switch import KillSwitchFilter
from src.phx_home_analysis.domain.entities import Property

# Convert DataFrame rows to Property entities
# Use KillSwitchFilter.evaluate() for consistent results
```

### Files Modified

- `scripts/phx_home_analyzer.py` - Remove duplicate criteria
- `scripts/deal_sheets.py` - Remove duplicate criteria
- No changes needed to service layer (already canonical)

### Testing Strategy

1. Run existing unit tests: `pytest tests/unit/test_kill_switch.py`
2. Verify script outputs match pre-refactor results
3. Add integration test comparing old vs new results

---
