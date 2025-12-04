# Code Architecture References

### 16. Current Kill-Switch Implementation

**File:** `scripts/lib/kill_switch.py`
**Lines:** 365
**Status:** TO BE MODIFIED in Wave 1

**Key Functions:**
- `evaluate_kill_switches()` (lines 203-248): Main evaluation logic
- `apply_kill_switch()` (lines 251-266): Property update wrapper
- `evaluate_kill_switches_for_display()` (lines 300-352): UI-friendly results
- `KILL_SWITCH_CRITERIA` dict (lines 152-195): Criterion definitions

**Modification Points:**
- Add `evaluate_kill_switches_weighted()` function
- Update `KILL_SWITCH_CRITERIA` with type (HARD/SOFT) and severity
- Maintain backward compatibility in existing functions

---

### 17. Current Scoring Weights

**File:** `src/phx_home_analysis/config/scoring_weights.py`
**Lines:** 319
**Status:** TO BE MODIFIED in Wave 2

**Current Weights:**
- Section A: 250 pts (lines 193-199)
- Section B: 160 pts (lines 201-205)
- Section C: 190 pts (lines 207-214)

**Modification Points:**
- Line 198: quietness 50→40
- Line 197: supermarket_proximity 40→30
- Line 205: pool_condition 30→20
- Line 205+: ADD cost_efficiency 40 (new field)

**Properties to Update:**
- `section_b_max` (line 259-267): 160→180
- `total_possible_score` (line 217-244): Verify still 600

---

### 18. Current Scoring Strategies

**File:** `src/phx_home_analysis/services/scoring/strategies/systems.py`
**Lines:** 253
**Status:** TO BE MODIFIED in Wave 2

**Existing Strategies:**
- RoofConditionScorer (lines 19-77)
- BackyardUtilityScorer (lines 79-127)
- PlumbingElectricalScorer (lines 129-188)
- PoolConditionScorer (lines 190-253)

**Addition Point:**
- Add CostEfficiencyScorer class (after line 253)
- Follows same pattern as existing scorers
- Integrates with CostEstimator for monthly cost data

---

### 19. Property Entity Structure

**File:** `src/phx_home_analysis/domain/entities.py`
**Lines:** 372
**Status:** TO BE MODIFIED in Waves 2, 5

**Key Sections:**
- Property dataclass (lines 15-336): Main entity
- Computed properties (lines 113-312): Derived values
- EnrichmentData (lines 339-372): DTO for JSON

**Modification Points (Wave 2):**
- Line 73+: Add `monthly_cost_estimate: Optional[MonthlyCostEstimate]`

**Modification Points (Wave 5):**
- Line 73+: Add `field_lineage: dict[str, FieldLineage]`
- Line 74+: Add `quality_score: Optional[float]`

---
