---
name: scoring
description: Calculate property scores using the 605-point weighted system (Location 250pts, Systems 175pts, Interior 180pts). Tier thresholds are UNICORN >=484, CONTENDER 363-483, PASS <363. Use when scoring properties, understanding tier assignments, analyzing score breakdowns, or running the scoring pipeline.
allowed-tools: Read, Bash(python:*)
---

# Property Scoring Skill

Calculate property scores using the PHX homes 605-point weighted scoring system.

## Quick Reference

| Metric | Value |
|--------|-------|
| **Max Score** | 605 points |
| **Section A: Location** | 250 pts (schools, safety, orientation) |
| **Section B: Systems** | 175 pts (roof, plumbing, cost efficiency) |
| **Section C: Interior** | 180 pts (kitchen, master, light) |

### Tier Classification

| Tier | Score | Action |
|------|-------|--------|
| **UNICORN** | >=484 (>=80%) | Schedule immediately |
| **CONTENDER** | 363-483 (60-80%) | Strong candidate |
| **PASS** | <363 (<60%) | Monitor for price drops |
| **FAILED** | Any | Kill-switch fail |

## Helper Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `scripts/analyze.py` | Run scoring pipeline | `python scripts/analyze.py` |
| `scripts/analyze.py --single "123 Main"` | Score single property | Address match |
| `scripts/analyze.py --verbose` | Detailed output | Debug scoring |

## Service Layer

```python
from src.phx_home_analysis.services.scoring import PropertyScorer
from src.phx_home_analysis.services.classification import TierClassifier

scorer = PropertyScorer()
breakdown = scorer.score(property_obj)
print(f"Total: {breakdown.total_score}/605")

classifier = TierClassifier()
tier = classifier.classify(property)  # Returns Tier enum
```

## Constants (Single Source of Truth)

```python
from src.phx_home_analysis.config.constants import (
    TIER_UNICORN_MIN,      # 484
    TIER_CONTENDER_MIN,    # 363
    MAX_POSSIBLE_SCORE,    # 605
)
```

## Default Values

When fields are null, scoring uses **5/10 (neutral)**:

| Criterion | Default | Impact |
|-----------|---------|--------|
| school_rating | 5.0 | 25/50 pts |
| safety_score | 5.0 | 25/50 pts |
| monthly_cost | $4,000 | 20/40 pts |
| All interior scores | 5.0 | 50% of max |

**Flag properties with >5 defaulted criteria as LOW_DATA_QUALITY.**

## Reference Shards

| Shard | WHAT | WHEN |
|-------|------|------|
| `../_shared/scoring-tables.md` | Complete scoring tables, multipliers, orientation points | Detailed criterion breakdown |

**To load detail:** `Read .claude/skills/_shared/scoring-tables.md`

## Sanity Check Protocol

After calculating, verify:
1. **Section sums**: A + B + C = Total
2. **Maximum bounds**: Each criterion ≤ its max
3. **Tier match**: Score → correct tier
4. **Default count**: Flag if >5 criteria defaulted

## Cost Efficiency Scoring (Section B)

```python
# Formula: base_score = max(0, 10 - ((monthly_cost - 3000) / 200))
# Points = base_score * 4 (max 40 pts)

# Monthly Cost → Points
# $3,000 → 40 pts (optimal)
# $4,000 → 20 pts (neutral)
# $5,000 → 0 pts (expensive)
```

## Best Practices

1. **Check kill-switch first** - Don't score disqualified properties
2. **Use canonical scorer** - `PropertyScorer` from services layer
3. **Handle nulls** - Use 5/10 defaults, track which are defaulted
4. **Re-score after updates** - Run analyze.py after enrichment changes
5. **Reference _shared** - Don't duplicate scoring tables
