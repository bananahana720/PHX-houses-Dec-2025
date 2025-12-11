# ScoreBreakdown Schema Documentation

## Overview

The `ScoreBreakdown` value object aggregates property scores across three main dimensions (Location, Systems, Interior) following the 605-point scoring system. This document defines the schema, constraints, and serialization format for data layer persistence and reporting integration.

**Source:** `src/phx_home_analysis/domain/value_objects.py:138-276`

---

## 605-Point System Summary

| Section | Name | Max Points | Percentage |
|---------|------|------------|------------|
| A | Location & Environment | 250 pts | 41.3% |
| B | Lot & Systems | 175 pts | 28.9% |
| C | Interior & Features | 180 pts | 29.8% |
| **Total** | | **605 pts** | **100%** |

---

## Score Value Object

Each individual criterion is represented by a `Score` value object.

### Score Fields

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `criterion` | `str` | Required | Human-readable criterion name |
| `base_score` | `float` | 0.0 - 10.0 | Raw assessment score |
| `weight` | `float` | >= 0 | Maximum possible points for this criterion |
| `note` | `str \| None` | Optional | Additional context or explanation |

### Score Computed Properties

| Property | Formula | Description |
|----------|---------|-------------|
| `weighted_score` | `(base_score / 10.0) * weight` | Points earned |
| `max_possible` | `weight` | Maximum achievable points |
| `percentage` | `(weighted_score / weight) * 100` | Score as percentage |

### Score Example

```json
{
  "criterion": "School District Rating",
  "base_score": 8.5,
  "weight": 42.0,
  "note": "Paradise Valley Unified - GreatSchools 8.5/10",
  "weighted_score": 35.7,
  "max_possible": 42.0,
  "percentage": 85.0
}
```

---

## ScoreBreakdown Value Object

### ScoreBreakdown Fields

| Field | Type | Description |
|-------|------|-------------|
| `location_scores` | `list[Score]` | Section A scores (max 250 pts) |
| `systems_scores` | `list[Score]` | Section B scores (max 175 pts) |
| `interior_scores` | `list[Score]` | Section C scores (max 180 pts) |

### ScoreBreakdown Constants and Access Patterns

ScoreBreakdown provides two ways to access section maximums:

**Class-level constants (static):** `ScoreBreakdown.SECTION_A_MAX`
**Instance properties (dynamic):** `breakdown.section_a_max`

Both return identical values. Use class constants for type annotations or
static calculations; use instance properties when chaining with computed totals.

| Class Constant | Instance Property | Value | Description |
|----------------|-------------------|-------|-------------|
| `SECTION_A_MAX` | `section_a_max` | 250 | Location & Environment maximum |
| `SECTION_B_MAX` | `section_b_max` | 175 | Lot & Systems maximum |
| `SECTION_C_MAX` | `section_c_max` | 180 | Interior & Features maximum |
| `TOTAL_MAX` | `total_max` | 605 | Total maximum score |

### ScoreBreakdown Computed Properties

| Property | Type | Description |
|----------|------|-------------|
| `location_total` | `float` | Sum of location weighted scores |
| `systems_total` | `float` | Sum of systems weighted scores |
| `interior_total` | `float` | Sum of interior weighted scores |
| `total_score` | `float` | Sum of all section totals |
| `location_percentage` | `float` | Location score as % of 250 |
| `systems_percentage` | `float` | Systems score as % of 175 |
| `interior_percentage` | `float` | Interior score as % of 180 |
| `total_percentage` | `float` | Total score as % of 605 |

---

## Section A: Location & Environment (250 pts)

9 criteria affecting property location desirability.

| Criterion | Weight | Description |
|-----------|--------|-------------|
| School District Rating | 42 pts | GreatSchools rating (0-10) |
| Noise Level / Quietness | 30 pts | HowLoud API / highway proximity |
| Crime Index / Safety | 47 pts | Neighborhood safety score |
| Supermarket Proximity | 23 pts | Distance to nearest grocery |
| Parks & Walkability | 23 pts | Walk Score / park access |
| Sun Orientation | 25 pts | N=25, NE/NW=20, E/SE=15, S/SW=10, W=0 |
| Flood Risk | 23 pts | FEMA flood zone rating |
| Walk/Transit Score | 22 pts | Combined walkability + transit |
| Air Quality | 15 pts | EPA AirNow AQI score |

**Section A Total: 42 + 30 + 47 + 23 + 23 + 25 + 23 + 22 + 15 = 250 pts**

---

## Section B: Lot & Systems (175 pts)

6 criteria affecting property systems and infrastructure.

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Roof Condition/Age | 45 pts | Roof age and condition |
| Backyard Utility | 35 pts | Backyard usability rating |
| Plumbing/Electrical | 35 pts | HVAC, plumbing age/condition |
| Pool Condition | 20 pts | Pool equipment age (if applicable) |
| Cost Efficiency | 35 pts | Monthly cost relative to $4000 target |
| Solar Status | 5 pts | OWNED=5, NONE=2.5, LEASED=0 |

**Section B Total: 45 + 35 + 35 + 20 + 35 + 5 = 175 pts**

---

## Section C: Interior & Features (180 pts)

7 criteria affecting interior quality and features.

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Kitchen Layout | 40 pts | Kitchen design and functionality |
| Master Suite | 35 pts | Master bedroom quality |
| Natural Light | 30 pts | Window placement and light |
| High Ceilings | 25 pts | Ceiling height rating |
| Fireplace | 20 pts | Fireplace presence (yes/no) |
| Laundry Area | 20 pts | Laundry room quality |
| Aesthetics | 10 pts | Overall visual appeal |

**Section C Total: 40 + 35 + 30 + 25 + 20 + 20 + 10 = 180 pts**

---

## Tier Thresholds

Properties are classified into tiers based on total score:

| Tier | Score Range | Percentage | Description |
|------|-------------|------------|-------------|
| **Unicorn** | >= 484 pts | >= 80% | Top-tier property, rare find |
| **Contender** | 363-483 pts | 60-79% | Strong candidate, worth pursuing |
| **Pass** | < 363 pts | < 60% | Meets minimum criteria |
| **Failed** | N/A | N/A | Kill-switch failure (any score) |

### Tier Calculation Rules

1. If `kill_switch_passed == False`, tier is **FAILED** regardless of score
2. If `total_score >= 484`, tier is **UNICORN**
3. If `total_score >= 363`, tier is **CONTENDER**
4. Otherwise, tier is **PASS**

---

## Validation Rules

### Score Constraints

```python
# Score validation
if not 0 <= base_score <= 10:
    raise ValueError(f"base_score must be 0-10, got {base_score}")
if weight < 0:
    raise ValueError(f"weight must be non-negative, got {weight}")
```

### ScoreBreakdown Invariants

1. **Score lists may be empty** - Results in 0 total for that section
2. **Individual scores must be valid** - All Score constraints apply
3. **Weighted scores cannot exceed weight** - `weighted_score <= weight`
4. **Section totals bounded by max** - Practical limit from strategy weights

### Data Layer Persistence Rules

When storing ScoreBreakdown in `enrichment_data.json`:

1. Store as serialized JSON object (see format below)
2. Include timestamp of scoring calculation
3. Include scorer version for reproducibility
4. Retain individual criterion scores for audit trail

---

## JSON Serialization Format

### Full ScoreBreakdown Serialization

```json
{
  "score_breakdown": {
    "location": {
      "total": 187.5,
      "max": 250,
      "percentage": 75.0,
      "scores": [
        {
          "criterion": "School District Rating",
          "base_score": 8.5,
          "weight": 42.0,
          "weighted_score": 35.7,
          "percentage": 85.0,
          "note": null
        },
        {
          "criterion": "Crime Index",
          "base_score": 7.0,
          "weight": 47.0,
          "weighted_score": 32.9,
          "percentage": 70.0,
          "note": null
        }
        // ... remaining 7 location criteria
      ]
    },
    "systems": {
      "total": 131.25,
      "max": 175,
      "percentage": 75.0,
      "scores": [
        {
          "criterion": "Roof Condition/Age",
          "base_score": 8.0,
          "weight": 45.0,
          "weighted_score": 36.0,
          "percentage": 80.0,
          "note": "5-year-old tile roof"
        }
        // ... remaining 5 systems criteria
      ]
    },
    "interior": {
      "total": 135.0,
      "max": 180,
      "percentage": 75.0,
      "scores": [
        {
          "criterion": "Kitchen Layout",
          "base_score": 7.5,
          "weight": 40.0,
          "weighted_score": 30.0,
          "percentage": 75.0,
          "note": null
        }
        // ... remaining 6 interior criteria
      ]
    },
    "total": 453.75,
    "max": 605,
    "percentage": 75.0,
    "tier": "Contender",
    "scored_at": "2025-12-10T14:30:00Z",
    "scorer_version": "1.0.0"
  }
}
```

### Compact Serialization (Summary Only)

For lightweight storage or API responses:

```json
{
  "score_summary": {
    "location": { "score": 187.5, "max": 250, "pct": 75.0 },
    "systems": { "score": 131.25, "max": 175, "pct": 75.0 },
    "interior": { "score": 135.0, "max": 180, "pct": 75.0 },
    "total": { "score": 453.75, "max": 605, "pct": 75.0 },
    "tier": "Contender"
  }
}
```

---

## Python Usage Examples

### Creating ScoreBreakdown

```python
from src.phx_home_analysis.domain.value_objects import Score, ScoreBreakdown

# Create individual scores
school_score = Score(
    criterion="School District Rating",
    base_score=8.5,
    weight=42.0,
    note="Paradise Valley Unified"
)

# Create breakdown
breakdown = ScoreBreakdown(
    location_scores=[school_score, ...],  # 9 location scores
    systems_scores=[...],                   # 6 systems scores
    interior_scores=[...],                  # 7 interior scores
)

# Access computed properties
print(f"Total: {breakdown.total_score}/605 ({breakdown.total_percentage:.1f}%)")
print(f"Location: {breakdown.location_total}/250")
print(f"Systems: {breakdown.systems_total}/175")
print(f"Interior: {breakdown.interior_total}/180")
```

### Serializing to Dict

```python
def score_to_dict(score: Score) -> dict:
    """Convert Score to serializable dict."""
    return {
        "criterion": score.criterion,
        "base_score": round(score.base_score, 1),
        "weight": score.weight,
        "weighted_score": round(score.weighted_score, 1),
        "percentage": round(score.percentage, 1),
        "note": score.note,
    }

def breakdown_to_dict(breakdown: ScoreBreakdown) -> dict:
    """Convert ScoreBreakdown to serializable dict."""
    return {
        "location": {
            "total": round(breakdown.location_total, 1),
            "max": breakdown.SECTION_A_MAX,
            "percentage": round(breakdown.location_percentage, 1),
            "scores": [score_to_dict(s) for s in breakdown.location_scores],
        },
        "systems": {
            "total": round(breakdown.systems_total, 1),
            "max": breakdown.SECTION_B_MAX,
            "percentage": round(breakdown.systems_percentage, 1),
            "scores": [score_to_dict(s) for s in breakdown.systems_scores],
        },
        "interior": {
            "total": round(breakdown.interior_total, 1),
            "max": breakdown.SECTION_C_MAX,
            "percentage": round(breakdown.interior_percentage, 1),
            "scores": [score_to_dict(s) for s in breakdown.interior_scores],
        },
        "total": round(breakdown.total_score, 1),
        "max": breakdown.TOTAL_MAX,
        "percentage": round(breakdown.total_percentage, 1),
    }
```

---

## Integration Points

### Kill-Switch to Scoring

- **Input**: `Property` with `kill_switch_passed` flag
- **Gate**: Only properties with `kill_switch_passed=True` receive full scoring
- **Failed properties**: Get `tier=FAILED`, score may still be calculated for informational purposes

### Scoring to Reporting

- **Output**: `ScoreBreakdown` value object
- **Consumer**: `DealSheetReporter`, `ConsoleReporter`, `HtmlReporter`
- **Format**: Use `to_dict()` serialization for template rendering

---

## References

- **Value Object Source**: `src/phx_home_analysis/domain/value_objects.py:138-276`
- **Scoring Weights Config**: `src/phx_home_analysis/config/scoring_weights.py`
- **Tier Thresholds**: `src/phx_home_analysis/config/scoring_weights.py:TierThresholds`
- **Scorer Implementation**: `src/phx_home_analysis/services/scoring/scorer.py`
- **Strategy Implementations**: `src/phx_home_analysis/services/scoring/strategies/`

---

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-10 | Initial schema documentation created for E4.S0 | Claude Opus 4.5 |
