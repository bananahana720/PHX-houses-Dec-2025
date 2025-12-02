---
name: scoring
description: Calculate property scores using the 600-point weighted scoring system with cost efficiency (Location 230pts, Systems 180pts, Interior 190pts). Use when scoring properties, understanding tier assignments, or analyzing score breakdowns.
allowed-tools: Read, Bash(python:*)
---

# Property Scoring Skill

Expert at calculating and analyzing property scores using the PHX homes 600-point scoring system.

## Scoring System Overview

**Maximum Score: 600 points**

| Section | Points | Categories |
|---------|--------|------------|
| **A: Location** | 230 | Schools, Noise, Safety, Grocery, Parks, Orientation |
| **B: Lot/Systems** | 180 | Roof, Backyard, Plumbing, Pool, Cost Efficiency |
| **C: Interior** | 190 | Kitchen, Master, Light, Ceilings, Fireplace, Laundry, Aesthetics |

## Tier Classification

| Tier | Score Range | Percentage | Action |
|------|-------------|------------|--------|
| **UNICORN** | >480 | >80% | Schedule immediately |
| **CONTENDER** | 360-480 | 60-80% | Strong candidate |
| **PASS** | <360 | <60% | Monitor for price drops |
| **FAILED** | Any | Kill-switch fail | Disqualified |

## Section A: Location (230 pts)

| Category | Max | Multiplier | Field | Change |
|----------|-----|------------|-------|--------|
| School Rating | 50 | 5x | `school_rating` (1-10) | - |
| Quietness | 40 | 4x | `distance_to_highway_miles` | -10 |
| Safety | 50 | 5x | `safety_neighborhood_score` (1-10) | - |
| Grocery | 30 | 3x | `distance_to_grocery_miles` | -10 |
| Parks | 30 | 3x | `parks_walkability_score` (1-10) | - |
| Orientation | 30 | - | `orientation` (N/S/E/W) | - |

### Orientation Scoring (AZ-specific)

| Direction | Points | Reason |
|-----------|--------|--------|
| North | 30 | Minimal direct sun, lowest cooling |
| East | 20 | Morning sun only |
| South | 10 | Moderate exposure |
| West | 0 | High cooling costs |
| NE/NW | 25 | Near-optimal |
| SE/SW | 5 | Near-worst |

## Section B: Lot/Systems (180 pts)

| Category | Max | Multiplier | Field | Change |
|----------|-----|------------|-------|--------|
| Roof | 40 | 4x | `roof_age` (invert: newer = higher) | -10 |
| Backyard | 40 | 4x | `lot_sqft` + usability | - |
| Plumbing | 40 | 4x | `year_built` (invert: newer = higher) | - |
| Pool | 20 | 2x | `pool_equipment_age` (if has_pool) | -10 |
| **Cost Efficiency** | **40** | **4x** | `monthly_cost` | **NEW** |

### Roof Age Scoring

| Age | Score | Points (max 40) |
|-----|-------|-----------------|
| 0-5 years | 10 | 40 |
| 6-10 years | 8 | 32 |
| 11-15 years | 6 | 24 |
| 16-20 years | 4 | 16 |
| 21+ years | 2 | 8 |

### Cost Efficiency Scoring (NEW)

The CostEfficiencyScorer rewards properties with lower monthly ownership costs.

**Formula:**
```python
base_score = max(0, 10 - ((monthly_cost - 3000) / 200))
cost_efficiency_points = base_score * 4  # Multiplier of 4x
```

**Score Breakdown:**

| Monthly Cost | Base Score | Points (4x) |
|--------------|------------|-------------|
| $3,000/mo | 10.0 | 40 |
| $3,200/mo | 9.0 | 36 |
| $3,400/mo | 8.0 | 32 |
| $3,600/mo | 7.0 | 28 |
| $3,800/mo | 6.0 | 24 |
| $4,000/mo | 5.0 | 20 |
| $4,200/mo | 4.0 | 16 |
| $4,400/mo | 3.0 | 12 |
| $4,600/mo | 2.0 | 8 |
| $4,800/mo | 1.0 | 4 |
| $5,000+/mo | 0.0 | 0 |

**Monthly Cost Components:**
- Mortgage payment (P&I)
- Property taxes
- Insurance
- HOA fees (if any, though kill-switch excludes HOA)
- Estimated utilities
- Pool maintenance (if applicable)

## Section C: Interior (190 pts)

| Category | Max | Multiplier | Field |
|----------|-----|------------|-------|
| Kitchen | 40 | 4x | `kitchen_layout_score` (1-10) |
| Master Suite | 40 | 4x | `master_suite_score` (1-10) |
| Natural Light | 30 | 3x | `natural_light_score` (1-10) |
| High Ceilings | 30 | 3x | `high_ceilings_score` (1-10) |
| Fireplace | 20 | 2x | `fireplace_score` (1-10) |
| Laundry | 20 | 2x | `laundry_area_score` (1-10) |
| Aesthetics | 10 | 1x | `aesthetics_score` (1-10) |

## Tier Classification Service

**Location:** `src/phx_home_analysis/services/classification/tier_classifier.py`

```python
from phx_home_analysis.services.classification import TierClassifier

classifier = TierClassifier()
tier = classifier.classify(property)  # Returns Tier enum
properties = classifier.classify_batch(properties)  # Batch classification
```

**Thresholds:** (from `config/constants.py`)
- UNICORN: >480 pts
- CONTENDER: 360-480 pts
- PASS: <360 pts

## Centralized Constants

**Location:** `src/phx_home_analysis/config/constants.py`

All scoring thresholds and weights are centralized:

```python
from src.phx_home_analysis.config.constants import (
    TIER_UNICORN_MIN,      # 480
    TIER_CONTENDER_MIN,    # 360
    MAX_POSSIBLE_SCORE,    # 600

    # Section totals
    SCORE_SECTION_A_TOTAL,         # 230 (Location)
    SCORE_SECTION_B_TOTAL,         # 180 (Lot/Systems)
    SCORE_SECTION_C_TOTAL,         # 190 (Interior)
)
```

Individual criterion maximums are also defined:

```python
from src.phx_home_analysis.config.constants import (
    # Section A: Location (230 pts)
    SCORE_SECTION_A_SCHOOL_DISTRICT,        # 50
    SCORE_SECTION_A_QUIETNESS,              # 40
    SCORE_SECTION_A_SAFETY,                 # 50
    SCORE_SECTION_A_SUPERMARKET_PROXIMITY,  # 30
    SCORE_SECTION_A_PARKS_WALKABILITY,      # 30
    SCORE_SECTION_A_SUN_ORIENTATION,        # 30

    # Section B: Lot/Systems (180 pts)
    SCORE_SECTION_B_ROOF_CONDITION,         # 50
    SCORE_SECTION_B_BACKYARD_UTILITY,       # 40
    SCORE_SECTION_B_PLUMBING_ELECTRICAL,    # 40
    SCORE_SECTION_B_POOL_CONDITION,         # 20
    SCORE_SECTION_B_COST_EFFICIENCY,        # 30

    # Section C: Interior (190 pts)
    SCORE_SECTION_C_KITCHEN_LAYOUT,         # 40
    SCORE_SECTION_C_MASTER_SUITE,           # 40
    SCORE_SECTION_C_NATURAL_LIGHT,          # 30
    SCORE_SECTION_C_HIGH_CEILINGS,          # 30
    SCORE_SECTION_C_FIREPLACE,              # 20
    SCORE_SECTION_C_LAUNDRY_AREA,           # 20
    SCORE_SECTION_C_AESTHETICS,             # 10
)
```

**Note:** These constants are the **single source of truth** - both CLI and service layers import from here.

## Using the Canonical Scorer

```python
# Use project's canonical scorer
from src.phx_home_analysis.services.scoring import PropertyScorer

scorer = PropertyScorer()
score_breakdown = scorer.score(property_obj)

# Access results
print(f"Total: {score_breakdown.total_score}/600")
print(f"Location: {score_breakdown.location_total}/230")
print(f"Systems: {score_breakdown.systems_total}/180")
print(f"Interior: {score_breakdown.interior_total}/190")
```

### CostEfficiencyScorer Usage

```python
from src.phx_home_analysis.services.scoring import CostEfficiencyScorer

cost_scorer = CostEfficiencyScorer()

# Score a property's cost efficiency
monthly_cost = 3500  # $3,500/month total cost
score = cost_scorer.score(monthly_cost)
# Returns: 7.5 base score -> 30 points (7.5 * 4)

# Or with property dict
property_data = {"monthly_cost": 3500}
score = cost_scorer.score_property(property_data)
```

## CLI Scoring

```bash
# Score all properties
python scripts/analyze.py

# Score single property
python scripts/analyze.py --single "123 Main St, Phoenix, AZ 85001"

# Verbose output
python scripts/analyze.py --verbose
```

## Score Calculation Example

```python
def calculate_manual_score(prop: dict) -> dict:
    """Calculate score breakdown manually for understanding."""
    scores = {
        "location": {
            "school": (prop.get("school_rating") or 5) * 5,  # Max 50
            "quietness": min(10, (prop.get("distance_to_highway_miles") or 0.5) * 10) * 4,  # Max 40
            "safety": (prop.get("safety_neighborhood_score") or 5) * 5,  # Max 50
            "grocery": min(10, 10 - (prop.get("distance_to_grocery_miles") or 1) * 2) * 3,  # Max 30
            "parks": (prop.get("parks_walkability_score") or 5) * 3,  # Max 30
            "orientation": score_orientation(prop.get("orientation")),  # Max 30
        },
        "systems": {
            "roof": score_age(prop.get("roof_age"), max_good=5, max_score=40),
            "backyard": score_lot(prop.get("lot_sqft"), max_score=40),
            "plumbing": score_age(2024 - (prop.get("year_built") or 1990), max_good=10, max_score=40),
            "pool": score_pool(prop.get("has_pool"), prop.get("pool_equipment_age"), max_score=20),
            "cost_efficiency": score_cost_efficiency(prop.get("monthly_cost")),  # Max 40, NEW
        },
        "interior": {
            "kitchen": (prop.get("kitchen_layout_score") or 5) * 4,
            "master": (prop.get("master_suite_score") or 5) * 4,
            "light": (prop.get("natural_light_score") or 5) * 3,
            "ceilings": (prop.get("high_ceilings_score") or 5) * 3,
            "fireplace": (prop.get("fireplace_score") or 5) * 2,
            "laundry": (prop.get("laundry_area_score") or 5) * 2,
            "aesthetics": (prop.get("aesthetics_score") or 5) * 1,
        }
    }

    totals = {
        "location_total": sum(scores["location"].values()),  # Max 230
        "systems_total": sum(scores["systems"].values()),    # Max 180
        "interior_total": sum(scores["interior"].values()),  # Max 190
    }
    totals["total_score"] = sum(totals.values())  # Max 600

    return {**scores, **totals}


def score_cost_efficiency(monthly_cost: float) -> float:
    """Score cost efficiency (max 40 points)."""
    if monthly_cost is None:
        return 20  # Default to middle score (5 * 4)
    base_score = max(0, 10 - ((monthly_cost - 3000) / 200))
    return min(40, base_score * 4)
```

## Default Values

When fields are null, scoring uses defaults of 5/10 (neutral):

```python
DEFAULTS = {
    "school_rating": 5.0,
    "safety_neighborhood_score": 5,
    "parks_walkability_score": 5,
    "kitchen_layout_score": 5,
    "master_suite_score": 5,
    "natural_light_score": 5,
    "high_ceilings_score": 5,
    "fireplace_score": 5,
    "laundry_area_score": 5,
    "aesthetics_score": 5,
    "monthly_cost": 4000,  # Default assumes $4k/mo (middle of target range)
}
```

## Value Ratio Calculation

For comparing properties by value:

```python
def value_ratio(score: float, price: int) -> float:
    """Calculate points per $1,000 spent."""
    return score / (price / 1000)

# Higher ratio = better value
# Example: 400 pts / $450k = 0.89 pts/$1k
```

## Weight Change Summary (Wave 2)

| Section | Old | New | Delta |
|---------|-----|-----|-------|
| **A: Location** | 250 | 230 | -20 |
| **B: Systems** | 160 | 180 | +20 |
| **C: Interior** | 190 | 190 | 0 |
| **Total** | 600 | 600 | 0 |

### Individual Criterion Changes

| Criterion | Old Max | New Max | Change |
|-----------|---------|---------|--------|
| Quietness | 50 | 40 | -10 |
| Grocery | 40 | 30 | -10 |
| Roof | 50 | 40 | -10 |
| Pool | 30 | 20 | -10 |
| **Cost Efficiency** | - | **40** | **+40** |

**Rationale:** Cost efficiency is critical for first-time buyers with a $4k/month budget ceiling. The rebalancing shifts 20 points from location convenience factors (quietness, grocery proximity) and systems condition factors (roof age, pool) to directly reward affordability.

## Best Practices

1. **Use canonical scorer** - `src/phx_home_analysis/services/scoring/PropertyScorer`
2. **Check kill-switch first** - Don't score disqualified properties
3. **Handle nulls** - Use neutral defaults (5/10) for missing data
4. **Track confidence** - Note which scores are defaults vs actual data
5. **Re-score after updates** - Run analyze.py after enrichment changes
6. **Include monthly costs** - Cost efficiency requires accurate monthly cost estimates

---

## Score Sanity Check Protocol

After calculating scores, verify with these checks:

### Mandatory Validation Checks

```
1. SECTION TOTALS
   - Sum(Section A criteria) = Section A total?
   - Sum(Section B criteria) = Section B total?
   - Sum(Section C criteria) = Section C total?

2. OVERALL TOTAL
   - Section A + Section B + Section C = Total?
   - Total <= 600?

3. MAXIMUM BOUNDS
   For each criterion: actual_score <= max_score?
   - Section A: School<=50, Quietness<=40, Safety<=50, Grocery<=30, Parks<=30, Sun<=30
   - Section B: Roof<=40, Backyard<=40, Plumbing<=40, Pool<=20, CostEfficiency<=40
   - Section C: Kitchen<=40, Master<=40, Light<=30, Ceilings<=30, Fireplace<=20, Laundry<=20, Aesthetics<=10

4. TIER CLASSIFICATION
   - Score >480 -> UNICORN?
   - Score 360-480 -> CONTENDER?
   - Score <360 -> PASS?
   - Kill-switch failed -> FAILED (regardless of score)?

5. DATA QUALITY FLAGS
   - Count criteria using default (5.0) -> flag if >5 defaults
   - Section score = 0 -> check if extraction failed
   - Kill-switch FAIL but being scored -> error
```

### Validation Result Format

```
PASS: [check name] - [confirmation]
FAIL: [check name] - [specific error]
WARN: [check name] - [potential issue]
```

### Integration Code

```python
def validate_score(score_data: dict) -> dict:
    """Validate score calculation for errors."""
    errors, warnings = [], []

    # Check section totals with new maximums
    section_a_max = 230
    section_b_max = 180
    section_c_max = 190

    section_a = sum([score_data.get(f, 0) for f in [
        'school_score', 'quietness_score', 'safety_score',
        'grocery_score', 'parks_score', 'sun_score'
    ]])
    if abs(score_data.get('section_a_total', 0) - section_a) > 0.01:
        errors.append(f"Section A mismatch: {score_data.get('section_a_total')} != {section_a}")

    section_b = sum([score_data.get(f, 0) for f in [
        'roof_score', 'backyard_score', 'plumbing_score',
        'pool_score', 'cost_efficiency_score'
    ]])
    if abs(score_data.get('section_b_total', 0) - section_b) > 0.01:
        errors.append(f"Section B mismatch: {score_data.get('section_b_total')} != {section_b}")

    # Check total <= 600
    if score_data.get('total_score', 0) > 600:
        errors.append(f"Total exceeds max: {score_data.get('total_score')} > 600")

    # Validate individual criterion bounds (updated)
    bounds = {
        'school_score': 50, 'quietness_score': 40, 'safety_score': 50,
        'grocery_score': 30, 'parks_score': 30, 'sun_score': 30,
        'roof_score': 40, 'backyard_score': 40, 'plumbing_score': 40,
        'pool_score': 20, 'cost_efficiency_score': 40,
        'kitchen_score': 40, 'master_score': 40, 'light_score': 30,
        'ceilings_score': 30, 'fireplace_score': 20, 'laundry_score': 20,
        'aesthetics_score': 10
    }
    for field, max_val in bounds.items():
        if score_data.get(field, 0) > max_val:
            errors.append(f"{field} exceeds max: {score_data.get(field)} > {max_val}")

    # Check tier classification
    total = score_data.get('total_score', 0)
    expected_tier = "UNICORN" if total > 480 else "CONTENDER" if total >= 360 else "PASS"
    if score_data.get('tier') != expected_tier:
        errors.append(f"Tier mismatch: {score_data.get('tier')} should be {expected_tier}")

    # Count defaults (warning only)
    default_count = sum(1 for k, v in score_data.items() if k.endswith('_score') and v == 5.0)
    if default_count > 5:
        warnings.append(f"High default count: {default_count} fields using 5.0")

    # Check cost efficiency is populated
    if 'cost_efficiency_score' not in score_data:
        warnings.append("Cost efficiency score missing - ensure monthly_cost is calculated")

    return {'valid': len(errors) == 0, 'errors': errors, 'warnings': warnings}
```

---

## Default Value Decision Tree

When data is missing, follow this logic to determine scoring strategy:

### Decision Flow

```
Missing data for criterion?
|
|-> Is data EXTRACTABLE from sources?
|   |-> County API has it? -> Extract (authoritative)
|   |-> Listing has it? -> Extract (reliable)
|   |-> No source available? -> Continue to derivation
|
|-> Is data DERIVABLE from other fields?
|   |-> High confidence derivation? -> Derive and score
|   |   Example: roof_age = 2025 - year_built (if no roof replacement)
|   |-> Low confidence? -> Use default 5.0 with caveat
|
|-> Is data VISIBLE in photos?
|   |-> Clear photos available? -> Score from image assessment
|   |-> Photos insufficient? -> Use default 5.0, flag "PHOTO_INSUFFICIENT"
|
|-> Use DEFAULT or flag RESEARCH
    |-> Non-critical criterion? -> Default 5.0, document
    |-> Critical criterion? -> Flag "REQUIRES_RESEARCH", don't default
```

### Criterion-Specific Rules

| Criterion | Strategy | Default OK? | Notes |
|-----------|----------|-------------|-------|
| school_rating | Extract (GreatSchools) | Last resort | Location data should be extractable |
| safety_score | Extract (crime stats) | Last resort | Research if not found |
| orientation | Derive (satellite) | **Never** | Critical for AZ, must research |
| roof_age | Derive (year_built) | Yes | Assume original roof if unknown |
| plumbing | Derive (year_built) | Yes | Era-based estimation OK |
| kitchen_score | Photo analysis | If no photos | Visual criterion |
| master_score | Photo analysis | If no photos | Visual criterion |
| monthly_cost | Calculate (mortgage+taxes+ins) | Yes | Use estimate if unknowns |

### When to Use Defaults (5.0)

**Use default when:**
- Non-critical criterion AND no data source available
- Photo analysis attempted but photos insufficient
- Derived value has low confidence

**Never default when:**
- Criterion is critical (orientation, school for Section A)
- Data should be extractable (location-based metrics)
- Property flagged for thorough analysis (Unicorn candidate)

### Track Default Usage

```python
score_metadata = {
    "defaults_used": [
        {"criterion": "fireplace_score", "reason": "no_photos", "impact": 10}
    ],
    "derived_values": [
        {"criterion": "roof_age", "method": "year_built - 2025", "confidence": "medium"},
        {"criterion": "monthly_cost", "method": "mortgage_calculator", "confidence": "high"}
    ],
    "data_quality": 0.85  # 85% from actual data
}
```

### Flag Properties with High Default Count

```python
if len(defaults_used) > 5:
    property['flags'].append("LOW_DATA_QUALITY")
    property['confidence'] = "low"
```
