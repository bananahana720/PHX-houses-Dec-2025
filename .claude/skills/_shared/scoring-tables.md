---
name: _shared/scoring-tables
description: Single source of truth for PHX Houses scoring system. All score ranges, multipliers, tier thresholds, and kill-switch criteria consolidated here. Other skill files reference this file rather than duplicating.
allowed-tools: Read
---

# PHX Houses Scoring Reference (Canonical)

**This is the authoritative source for all scoring information.** Other skill files should reference this file, not duplicate these tables.

Last updated: 2025-12-01

---

## Quick Reference

| Metric | Value |
|--------|-------|
| **Maximum Score** | 600 points |
| **Sections** | 3 (A, B, C) |
| **Section A: Location** | 230 pts |
| **Section B: Lot/Systems** | 180 pts |
| **Section C: Interior** | 190 pts |
| **Tier Thresholds** | 480 / 360 |
| **Kill-Switch Criteria** | 3 HARD + 4 SOFT |

---

## Tier Classification

| Tier | Score Range | Percentage | Action |
|------|-------------|------------|--------|
| **UNICORN** | >480 | >80% | Schedule immediately |
| **CONTENDER** | 360-480 | 60-80% | Strong candidate |
| **PASS** | <360 | <60% | Monitor for price drops |
| **FAILED** | Any | Kill-switch fail | Disqualified |

---

## Section A: Location (230 pts max)

**Definition:** Property location quality based on schools, noise, safety, amenities, and sun orientation.

### Categories and Multipliers

| Category | Max | Multiplier | Field | Scoring Notes |
|----------|-----|------------|-------|---------------|
| **School Rating** | 50 | 5x | `school_rating` (1-10) | GreatSchools rating |
| **Quietness** | 40 | 4x | `distance_to_highway_miles` | Further = better |
| **Safety** | 50 | 5x | `safety_neighborhood_score` (1-10) | Crime stats inverse |
| **Grocery** | 30 | 3x | `distance_to_grocery_miles` | Closer = better |
| **Parks** | 30 | 3x | `parks_walkability_score` (1-10) | Proximity score |
| **Orientation** | 30 | - | `orientation` (N/S/E/W) | AZ-specific sun exposure |

**Formula:** `Points = raw_score * multiplier` (capped at max)

### Orientation Scoring (AZ-Specific)

Critical for Arizona due to extreme heat exposure affecting cooling costs.

| Direction | Points | Reason | Cooling Impact |
|-----------|--------|--------|-----------------|
| **North** | 30 | Minimal direct sun | Lowest cooling costs |
| **NE/NW** | 25 | Near-optimal | Low-moderate cooling |
| **East** | 20 | Morning sun only | Moderate cooling |
| **South** | 10 | Moderate all-day exposure | Higher cooling costs |
| **SE/SW** | 5 | Near-worst | High cooling costs |
| **West** | 0 | Brutal afternoon sun | Highest cooling costs |

**Note:** West-facing = $100-200/mo additional cooling costs in summer.

---

## Section B: Lot/Systems (180 pts max)

**Definition:** Property systems condition and lot quality based on roof age, lot size, plumbing era, pool condition, and cost efficiency.

### Categories and Multipliers

| Category | Max | Multiplier | Field | Scoring Notes |
|----------|-----|------------|-------|---------------|
| **Roof** | 50 | 5x | `roof_age` | Newer = higher (invert age) |
| **Backyard** | 40 | 4x | `lot_sqft` | Lot usability and size |
| **Plumbing** | 40 | 4x | `year_built` | Newer = higher (invert age) |
| **Pool** | 20 | 2x | `pool_equipment_age` | If has_pool; else fixed 20 |
| **Cost Efficiency** | 30 | 3x | `cost_efficiency_score` (1-10) | Price/value ratio |

### Roof Age Scoring

Roof lifespan in Arizona: 10-15 years (vs 20+ in northern climates).

| Age (years) | Raw Score (1-10) | Points | Replacement Likely? |
|-------------|------------------|--------|---------------------|
| 0-5 | 10 | 50 | No |
| 6-10 | 8 | 40 | Not yet |
| 11-15 | 6 | 30 | Within 5 years |
| 16-20 | 4 | 20 | Likely soon |
| 21+ | 2 | 10 | Imminent ($8-15k) |

**Derivation:** If `roof_age` unknown, derive from `year_built`: `age = 2025 - year_built` (assume original roof).

### Plumbing/Electrical (Year Built)

| Era | Raw Score (1-10) | Points | Considerations |
|-----|------------------|--------|-----------------|
| 2010+ | 10 | 40 | Modern code, likely updated |
| 2000-2009 | 8 | 32 | Generally adequate |
| 1990-1999 | 7 | 28 | May need selective updates |
| 1980-1989 | 6 | 24 | Likely updated once |
| 1970-1979 | 5 | 20 | Possibly original |
| Pre-1970 | 4 | 16 | May require major updates |

### Pool Scoring

**If no pool:** Fixed score = 20 pts (20/20 = lower maintenance cost).

**If has pool:** Score based on equipment age.

| Equipment Age (years) | Raw Score (1-10) | Points | Condition | Budget Needed |
|--------|------------------|--------|-----------|-----------------|
| No pool | 10 | 20 | N/A | N/A |
| 0-5 | 10 | 20 | New equipment | None |
| 5-10 | 7 | 14 | Moderate | $1-3k minor |
| 10-15 | 4 | 8 | Aging | $3-8k replacement |
| 15+ | 2 | 4 | Failing | $8-15k+ replacement |

**AZ Pool Costs:**
- Monthly service: $100-150
- Equipment replacement: $3k-15k
- Monthly energy: $50-100

### Cost Efficiency Scoring

Evaluates price relative to property value, market conditions, and comparable sales.

| Raw Score (1-10) | Points | Interpretation |
|------------------|--------|----------------|
| 9-10 | 27-30 | Exceptional value - below market |
| 7-8 | 21-24 | Good value - fair price |
| 5-6 | 15-18 | Average - market price |
| 3-4 | 9-12 | Below average - slightly overpriced |
| 1-2 | 3-6 | Poor value - significantly overpriced |

**Factors Considered:**
- Price per square foot vs area average
- Days on market (longer = potential negotiation)
- Price reductions history
- Condition relative to asking price
- Comparable recent sales

---

## Section C: Interior (190 pts max)

**Definition:** Interior quality based on visual assessment of kitchen, master, natural light, ceilings, fireplace, laundry, and overall aesthetics.

### Categories and Multipliers

| Category | Max | Multiplier | Field | Visual Indicators |
|----------|-----|------------|-------|-------------------|
| **Kitchen** | 40 | 4x | `kitchen_layout_score` (1-10) | Layout, counters, appliances |
| **Master Suite** | 40 | 4x | `master_suite_score` (1-10) | Size, closet, en-suite |
| **Natural Light** | 30 | 3x | `natural_light_score` (1-10) | Windows, skylights |
| **High Ceilings** | 30 | 3x | `high_ceilings_score` (1-10) | Height, vaulted |
| **Fireplace** | 20 | 2x | `fireplace_score` (1-10) | Presence, type, condition |
| **Laundry** | 20 | 2x | `laundry_area_score` (1-10) | Dedicated room, hookups |
| **Aesthetics** | 10 | 1x | `aesthetics_score` (1-10) | Overall appeal, updates |

**Source:** Section C scores determined via visual analysis of property photos (Phase 2: Image Assessment).

### Section C Score Interpretation Scale

| Raw Score | Interpretation | Typical Examples |
|-----------|----------------|------------------|
| 9-10 | Exceptional | Modern renovation, high-end finishes |
| 7-8 | Good | Updated, functional, move-in ready |
| 5-6 | Average | Era-appropriate, some dated elements |
| 3-4 | Below Average | Dated, needs updates |
| 1-2 | Poor | Major renovation required |

### Kitchen Layout Rubric (1-10)

| Score | Indicators | Condition |
|-------|------------|-----------|
| 9-10 | Open concept, quartz/granite counters, stainless appliances, ample storage, island | Exceptional |
| 7-8 | Modern layout, good counters, updated appliances, decent storage | Good |
| 5-6 | Functional but dated, laminate counters, older appliances | Average |
| 3-4 | Galley layout, very dated, limited storage | Below Average |
| 1-2 | Major renovation needed, non-functional | Poor |

### Master Suite Rubric (1-10)

| Score | Indicators | Condition |
|-------|------------|-----------|
| 9-10 | Large room, walk-in closet, luxury en-suite with dual vanity | Exceptional |
| 7-8 | Good size, adequate closet, updated bathroom | Good |
| 5-6 | Average size, basic closet, standard bath | Average |
| 3-4 | Small room, minimal closet | Below Average |
| 1-2 | Cramped, no en-suite or walk-in | Poor |

### Natural Light Rubric (1-10)

| Score | Indicators | Condition |
|-------|------------|-----------|
| 9-10 | Many large windows, skylights, glass doors, bright throughout | Exceptional |
| 7-8 | Good window count, bright main rooms | Good |
| 5-6 | Average lighting, some dark areas | Average |
| 3-4 | Limited windows, darker rooms | Below Average |
| 1-2 | Very poor natural light, basement-like | Poor |

### High Ceilings Rubric (1-10)

| Score | Indicators | Condition |
|-------|------------|-----------|
| 9-10 | 10ft+ or vaulted/cathedral ceilings | Exceptional |
| 7-8 | 9ft ceilings throughout | Good |
| 5-6 | Standard 8ft ceilings | Average |
| 3-4 | Low ceilings, some cramped areas | Below Average |
| 1-2 | Very low ceilings (<8ft) | Poor |

### Fireplace Rubric (1-10)

| Score | Indicators | Condition |
|-------|------------|-----------|
| 9-10 | Gas fireplace, modern styling, focal point | Exceptional |
| 7-8 | Wood-burning, well-maintained surround | Good |
| 5-6 | Decorative or older gas unit | Average |
| 3-4 | Non-functional or very dated | Below Average |
| 0 | No fireplace present | None |

### Laundry Area Rubric (1-10)

| Score | Indicators | Condition |
|-------|------------|-----------|
| 9-10 | Dedicated laundry room with storage, sink | Exceptional |
| 7-8 | Good-sized laundry area, shelving | Good |
| 5-6 | Hallway laundry, adequate space | Average |
| 3-4 | Garage laundry or cramped | Below Average |
| 1-2 | No dedicated space, poor setup | Poor |

### Aesthetics Rubric (1-10)

| Score | Indicators | Condition |
|-------|------------|-----------|
| 9-10 | Modern, move-in ready, designer touches | Exceptional |
| 7-8 | Clean, neutral, recently updated | Good |
| 5-6 | Average, some dated elements | Average |
| 3-4 | Dated 80s/90s style throughout | Below Average |
| 1-2 | Major cosmetic work needed | Poor |

---

## Kill-Switch Criteria

Kill-switches are divided into HARD (instant fail) and SOFT (severity-weighted) criteria.

### HARD Criteria (Instant Fail)

Any HARD failure immediately disqualifies the property - no exceptions.

| Criterion | Requirement | Field | Fail Condition |
|-----------|-------------|-------|----------------|
| **HOA** | Must be $0 | `hoa_fee` | `hoa_fee > 0` |
| **Bedrooms** | Must be >= 4 | `beds` | `beds < 4` |
| **Bathrooms** | Must be >= 2 | `baths` | `baths < 2` |

### SOFT Criteria (Severity Weighted)

SOFT failures accumulate severity. Total severity determines verdict.

| Criterion | Requirement | Field | Fail Condition | Severity Weight |
|-----------|-------------|-------|----------------|-----------------|
| **Sewer** | Must be "city" | `sewer_type` | `sewer_type == "septic"` | 2.5 |
| **Year Built** | Must be < 2024 | `year_built` | `year_built >= 2024` | 2.0 |
| **Garage** | Must be >= 2 | `garage_spaces` | `garage_spaces < 2` | 1.5 |
| **Lot Size** | 7k-15k sqft | `lot_sqft` | `lot_sqft < 7000 OR lot_sqft > 15000` | 1.0 |

### Verdict Logic

```
IF any HARD failure:
    verdict = FAIL (instant)
ELSE:
    total_severity = sum(failed_soft_criteria.severity_weight)

    IF total_severity >= 3.0:
        verdict = FAIL
    ELIF total_severity >= 1.5:
        verdict = WARNING
    ELSE:
        verdict = PASS
```

| Severity Total | Verdict | Action |
|----------------|---------|--------|
| Any HARD fail | FAIL | Property disqualified |
| >= 3.0 | FAIL | Too many soft issues |
| 1.5 - 2.99 | WARNING | Proceed with caution |
| < 1.5 | PASS | Meets buyer criteria |

### Evaluation Priority Order

Evaluate in this order (stops at first HARD fail for efficiency):

1. **HOA Fee** - HARD: Financial dealbreaker
2. **Beds** - HARD: Space requirement
3. **Baths** - HARD: Space requirement
4. **Sewer** - SOFT (2.5): Infrastructure constraint
5. **Year Built** - SOFT (2.0): Eliminates new builds
6. **Garage** - SOFT (1.5): Structural feature
7. **Lot Size** - SOFT (1.0): Size constraint

### Unknown/Null Handling

When data is missing or null:

| Field | If Null | Action | Color |
|-------|---------|--------|-------|
| `hoa_fee` | PASS | Assume no HOA unless stated | GREEN |
| `sewer_type` | PASS (flag) | Cannot verify, proceed with caution | YELLOW |
| `garage_spaces` | PASS (flag) | Cannot verify, proceed with caution | YELLOW |
| `beds` | Check listing | Required field, don't assume | RED |
| `baths` | Check listing | Required field, don't assume | RED |
| `lot_sqft` | PASS (flag) | Cannot verify, proceed with caution | YELLOW |
| `year_built` | PASS (flag) | Cannot verify, proceed with caution | YELLOW |

**Rule:** Never default kill-switch criteria. Flag for research if missing critical data.

---

## Default Values

When data is missing from all sources, use these defaults for **non-critical** criteria only:

| Field | Default | Confidence | Use Case |
|-------|---------|------------|----------|
| `school_rating` | 5.0 | LOW | If GreatSchools data unavailable |
| `safety_neighborhood_score` | 5.0 | LOW | If crime stats unavailable |
| `parks_walkability_score` | 5.0 | LOW | If park proximity unmapped |
| `cost_efficiency_score` | 5.0 | LOW | If market data unavailable |
| `kitchen_layout_score` | 5.0 | LOW | If no kitchen photos available |
| `master_suite_score` | 5.0 | LOW | If no master photos available |
| `natural_light_score` | 5.0 | LOW | If insufficient light photos |
| `high_ceilings_score` | 5.0 | LOW | If ceiling height unclear |
| `fireplace_score` | 5.0 | LOW | If fireplace not visible |
| `laundry_area_score` | 5.0 | LOW | If laundry area not shown |
| `aesthetics_score` | 5.0 | LOW | If staging obscures finishes |

**Important:**
- Default = 5/10 (perfectly average = 5 * multiplier = mid-range points)
- Never default kill-switch criteria
- Flag properties with >5 defaults for manual review
- Document which fields used defaults in metadata

---

## Score Calculation Reference

### Manual Calculation Example

```
Property: 123 Main St, Phoenix, AZ 85001

SECTION A: LOCATION (230 max)
  School Rating:    7/10 × 5 = 35 pts
  Quietness:        6/10 × 4 = 24 pts
  Safety:           8/10 × 5 = 40 pts
  Grocery:          7/10 × 3 = 21 pts
  Parks:            6/10 × 3 = 18 pts
  Orientation:      North = 30 pts
  ────────────────────────────────────
  Section A Total: 168/230 pts

SECTION B: LOT/SYSTEMS (180 max)
  Roof (8 yrs):     6/10 × 5 = 30 pts
  Backyard:         7/10 × 4 = 28 pts
  Plumbing (2005):  8/10 × 4 = 32 pts
  Pool (no pool):   10/10 × 2 = 20 pts
  Cost Efficiency:  7/10 × 3 = 21 pts
  ────────────────────────────────────
  Section B Total: 131/180 pts

SECTION C: INTERIOR (190 max)
  Kitchen:          7/10 × 4 = 28 pts
  Master Suite:     8/10 × 4 = 32 pts
  Natural Light:    6/10 × 3 = 18 pts
  High Ceilings:    5/10 × 3 = 15 pts
  Fireplace:        6/10 × 2 = 12 pts
  Laundry:          7/10 × 2 = 14 pts
  Aesthetics:       6/10 × 1 = 6 pts
  ────────────────────────────────────
  Section C Total: 125/190 pts

GRAND TOTAL: 168 + 131 + 125 = 424/600 pts
Percentage: 424 / 600 = 71%
Tier: CONTENDER (360-480)
```

### Python Reference Implementation

```python
def calculate_section_total(scores: dict, section: str) -> int:
    """Calculate section total from raw scores (1-10)."""
    multipliers = {
        "A": {
            "school_rating": 5,
            "distance_to_highway": 4,  # Quietness
            "safety_neighborhood": 5,
            "distance_to_grocery": 3,
            "parks_walkability": 3,
            "orientation": 1  # Special handling below
        },
        "B": {
            "roof_age": 5,
            "backyard_lot": 4,
            "plumbing_year": 4,
            "pool_equipment": 2,
            "cost_efficiency": 3
        },
        "C": {
            "kitchen_layout": 4,
            "master_suite": 4,
            "natural_light": 3,
            "high_ceilings": 3,
            "fireplace": 2,
            "laundry_area": 2,
            "aesthetics": 1
        }
    }

    total = 0
    for key, multiplier in multipliers[section].items():
        raw_score = scores.get(key, 5.0)  # Default 5.0 if missing

        # Special case: orientation (fixed points, not multiplied)
        if key == "orientation" and section == "A":
            total += get_orientation_points(scores.get("orientation"))
        else:
            # Standard: raw_score * multiplier
            points = min(raw_score * multiplier, 10 * multiplier)  # Cap at max
            total += points

    return total


def assign_tier(total_score: float, kill_switch_passed: bool) -> str:
    """Assign tier based on score and kill-switch status."""
    if not kill_switch_passed:
        return "FAILED"
    elif total_score > 480:
        return "UNICORN"
    elif total_score >= 360:
        return "CONTENDER"
    else:
        return "PASS"
```

---

## Score Validation Protocol

After calculating scores, verify with these checks:

### Mandatory Validation Checks

```
1. SECTION TOTALS
   ✓ Sum(Section A criteria) = Section A total?
   ✓ Sum(Section B criteria) = Section B total?
   ✓ Sum(Section C criteria) = Section C total?

2. OVERALL TOTAL
   ✓ Section A + Section B + Section C = Total?
   ✓ Total ≤ 600?

3. MAXIMUM BOUNDS
   ✓ Section A: School≤50, Quietness≤40, Safety≤50, Grocery≤30, Parks≤30, Orientation≤30
   ✓ Section B: Roof≤50, Backyard≤40, Plumbing≤40, Pool≤20, CostEfficiency≤30
   ✓ Section C: Kitchen≤40, Master≤40, Light≤30, Ceilings≤30, Fireplace≤20, Laundry≤20, Aesthetics≤10

4. TIER CLASSIFICATION
   ✓ Score >480 → UNICORN?
   ✓ Score 360-480 → CONTENDER?
   ✓ Score <360 → PASS?
   ✓ Kill-switch failed → FAILED (regardless of score)?

5. DATA QUALITY FLAGS
   ⚠ Count criteria using default (5.0) → flag if >5 defaults
   ⚠ Section score = 0 → check if extraction failed
   ⚠ Kill-switch FAIL but being scored → ERROR
```

---

## Usage from Other Files

Other skill files should reference this file rather than duplicating tables:

```markdown
## Scoring Reference

See `.claude/skills/_shared/scoring-tables.md` for complete scoring tables, definitions, rubrics, and calculation formulas.

Quick reference:
- Section A: 230 pts (Location: schools, quietness, safety, grocery, parks, orientation)
- Section B: 180 pts (Lot/Systems: roof, backyard, plumbing, pool, cost efficiency)
- Section C: 190 pts (Interior: kitchen, master, light, ceilings, fireplace, laundry, aesthetics)
- Total: 600 pts
- Tiers: UNICORN (>480), CONTENDER (360-480), PASS (<360), FAILED (kill-switch)
- Kill-Switches: 3 HARD (instant fail) + 4 SOFT (severity-weighted)
```

---

## File Relationships

| File | Purpose | References This File For |
|------|---------|--------------------------|
| `.claude/skills/scoring/SKILL.md` | Scoring system operations | Tier thresholds, default values |
| `.claude/skills/image-assessment/SKILL.md` | Section C visual scoring | Section C rubrics & interpretation |
| `.claude/skills/kill-switch/SKILL.md` | Kill-switch evaluation | Kill-switch criteria table & logic |
| `.claude/skills/arizona-context/SKILL.md` | AZ-specific factors | Orientation scoring (sun impact) |
| `.claude/AGENT_CONTEXT.md` | Quick reference | Tier table, kill-switch summary |

---

**Last Updated:** 2025-12-01
**Status:** Canonical - Single Source of Truth
**Maintenance:** Keep synchronized across all references
