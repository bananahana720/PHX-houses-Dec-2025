# KILL-SWITCH STRATEGY CRITIQUE

### Current Approach: Binary All-or-Nothing

**Philosophy**: NO compromise on 3 hard criteria (HOA, beds, baths), graduated penalties on soft criteria

**Strengths**:
- Clear buyer intent signaling (firm on HOA, space requirements)
- Prevents wasting time on obviously unsuitable properties
- Severity threshold captures "death by 1000 cuts" pattern

**Weaknesses**:
- HOA=$0 absolute (what if $150/mo excellent community?)
- Beds=4 absolute (what if 3+1 office perfectly fits buyer lifestyle?)
- Severity math is additive (sewer + year = 4.5 both equally bad?)
- Missing compound risk factors (old roof + old HVAC = higher risk than sum)

### Recommended Refinement: Add Flexibility Tiers

```python
# Current: HARD (instant fail) vs SOFT (severity weighted)
# Proposed: HARD, MEDIUM, SOFT with weighted flexibility

class KillSwitchTier(Enum):
    HARD = 0      # Non-negotiable (beds, baths)
    MEDIUM = 1    # Firm but evaluable (HOA ≤$200 OK, sewer ≥risk score, garage ≥1)
    SOFT = 2      # Preference with tolerance (lot size ±20%, year ±5yr)
```

**Example Recalibration**:
- HOA: MEDIUM tier - Allow up to $200/mo, severity 0.0-2.5 graduated
- Sewer: HARD → MEDIUM - City preferred but septic with inspector cert OK, severity 1.0
- Garage: HARD → MEDIUM - 2+ car ideal, 1.5-car acceptable, 1-car FAIL
- Lot: SOFT → MEDIUM - 7k-15k ideal, 5k-7k or 15k-20k acceptable, severity 0.5-1.5

**Impact**: Would likely pass 15-30% more properties for detailed evaluation

---
