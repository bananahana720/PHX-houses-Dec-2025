# Phase 3: Synthesis & Scoring

**Prerequisites:**
- Phase 0 must be complete
- Phase 0.5 should be complete (cost estimation for CostEfficiencyScorer)
- At least one Phase 1 task must be complete

**Pre-execution check:**
```python
prereq = check_phase_prerequisites(3, state, enrichment)

if not prereq["can_proceed"]:
    handle_prerequisite_failure(prereq, strict_mode)
    return

for warning in prereq["warnings"]:
    log_warning(f"Phase 3: {warning}")
```

**Use existing scripts**:

```bash
python scripts/analyze.py
```

**Scoring Components:**
- **PropertyScorer**: 600-point weighted scoring (Location, Systems, Interior)
- **CostEfficiencyScorer**: Evaluates monthly_cost vs quality score ratio
  - Uses `monthly_cost` from Phase 0.5
  - Flags properties exceeding $4k/month budget
  - Identifies value opportunities (high score, low cost)

**Tier Assignment** (600-point scale):
- UNICORN: >480 pts (80%+)
- CONTENDER: 360-480 pts (60-80%)
- PASS: <360 pts (<60%)
- FAILED: Kill-switch failure

**Checkpoint**: `phase3_synthesis`, move to `completed_properties`
