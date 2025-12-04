# Phase 4: Unify Scoring Functions (MEDIUM)

### Problem Statement

`scripts/phx_home_analyzer.py` contains 17 scoring functions (lines 113-265) that duplicate logic in `src/.../services/scoring/strategies/*.py`.

### Solution

Remove scoring functions from script, use canonical `PropertyScorer` service.

### Implementation

Replace in `phx_home_analyzer.py`:

```python
# Remove all score_* functions (lines 113-265)
# Remove calculate_weighted_score function (lines 267-319)

# Add import
from src.phx_home_analysis.services.scoring import PropertyScorer

# In main():
scorer = PropertyScorer()
for prop in properties:
    scorer.score(prop)
```

---
