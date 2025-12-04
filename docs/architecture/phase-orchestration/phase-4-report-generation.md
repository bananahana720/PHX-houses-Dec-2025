# Phase 4: Report Generation

**Prerequisites:**
- Phase 3 must be complete

**Pre-execution check:**
```python
prereq = check_phase_prerequisites(4, state, enrichment)

if not prereq["can_proceed"]:
    handle_prerequisite_failure(prereq, strict_mode)
    return
```

**Execution:**
```bash
python -m scripts.deal_sheets --property "{ADDRESS}"
```

Generate markdown summary with tier, scores, strengths, concerns, and recommendation.

**Checkpoint**: `phase4_report = "complete"`
