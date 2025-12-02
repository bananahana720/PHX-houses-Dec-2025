---
name: arizona-context-lite
description: Lightweight AZ context for image assessment - pool/HVAC age estimation and era calibration only. Use instead of full arizona-context when only visual scoring context is needed.
allowed-tools: Read
---

# Arizona Context (Lite)

Minimal Arizona-specific context for image assessment agents.

**When to use this vs full arizona-context:**
- Use **lite** for: Image assessment, era calibration, pool/HVAC visual estimation
- Use **full** for: Full property evaluation, solar analysis, orientation scoring, cost analysis

## Pool Equipment Age Estimation

When assessing pool condition from photos:

### Visual Indicators

| Indicator | Estimated Age | Condition |
|-----------|---------------|-----------|
| Clean housing, digital controls, new-looking | 0-5 years | Excellent |
| Some weathering, older controls | 5-10 years | Good |
| Visible rust, worn housing | 10-15 years | Fair |
| Heavy corrosion, outdated equipment | 15+ years | Poor |

### Scoring by Equipment Age

```python
def score_pool_equipment(has_pool: bool, equipment_age: int | None) -> tuple[int, str]:
    """Score pool based on equipment age (Section B: max 30 pts).

    Returns:
        (score_1_to_10, notes) tuple
    """
    if not has_pool:
        return 10, "No pool (lower maintenance burden)"

    if equipment_age is None:
        return 5, "Pool present, equipment age unknown - verify in person"

    if equipment_age <= 5:
        return 10, f"Pool with newer equipment ({equipment_age}yr)"
    elif equipment_age <= 10:
        return 7, f"Pool equipment moderate age ({equipment_age}yr)"
    elif equipment_age <= 15:
        return 4, f"Pool equipment aging ({equipment_age}yr) - budget $3-5k"
    else:
        return 2, f"Pool equipment old ({equipment_age}yr) - budget $8-15k"
```

## HVAC Age Estimation

When HVAC age is unknown, estimate from year_built:

### Arizona HVAC Lifespan

| Component | National Avg | Arizona Avg | Notes |
|-----------|--------------|-------------|-------|
| AC unit | 15-20 years | 10-15 years | Extreme heat reduces lifespan |

### Estimation Logic

```python
def estimate_hvac_age(year_built: int) -> tuple[int, str]:
    """Estimate HVAC age from year_built.

    Assumes: AZ HVAC typically replaced every 12-15 years.
    Returns (estimated_age, confidence_level)
    """
    current_year = 2025
    building_age = current_year - year_built

    if building_age <= 15:
        # Likely original equipment
        return building_age, "low"
    elif building_age <= 30:
        # Likely one replacement (assume at ~15yr mark)
        return building_age - 15, "low"
    else:
        # Multiple replacements - high uncertainty
        return building_age % 15, "very_low"
```

### Visual HVAC Indicators (from photos)

| Visible Feature | Indicates |
|-----------------|-----------|
| Digital thermostat, modern AC unit visible, clean housing | < 10 years |
| Older thermostat style, weathered unit, some discoloration | 10-15 years |
| Very old controls, rust visible, deteriorating housing | 15+ years |

## Era Calibration for Visual Scoring

Adjust expectations based on construction era. Properties meeting era baseline score at baseline; upgrades score above, deficiencies score below.

### Kitchen Baseline by Era

| Era | Baseline Score | Typical Features |
|-----|----------------|------------------|
| Pre-1980 | 4/10 | Galley layout, tile counters, limited storage |
| 1980-1999 | 5/10 | Oak cabinets, Corian counters, decent layout |
| 2000-2010 | 6/10 | Granite, stainless steel, open concept emerging |
| 2010+ | 7/10 | Quartz, modern appliances, large islands |

### Master Bedroom Baseline by Era

| Era | Baseline Score | Typical Features |
|-----|----------------|------------------|
| Pre-1980 | 3/10 | Small, reach-in closet, shared bathroom |
| 1980-1999 | 5/10 | Medium, walk-in closet emerging, ensuite |
| 2000-2010 | 6/10 | Large, walk-in closet standard, spa bathroom |
| 2010+ | 8/10 | Large, double walk-in, luxury finishes |

### Light / Ceilings Baseline by Era

| Era | Baseline Score | Typical Features |
|-----|----------------|------------------|
| Pre-1980 | 4/10 | Few windows, textured ceilings, popcorn common |
| 1980-1999 | 5/10 | Adequate windows, textured/flat mix |
| 2000-2010 | 6/10 | Good windows, mostly flat ceilings |
| 2010+ | 7/10 | Large windows, flat ceilings, high ceilings |

### Aesthetics Baseline by Era

| Era | Baseline Score | Notes |
|-----|----------------|-------|
| Pre-1980 | 4/10 | Dated OK; assess cleanliness, paint |
| 1980-1999 | 5/10 | Era-typical; neutral |
| 2000-2010 | 6/10 | Modern baseline expected |
| 2010+ | 7/10 | Contemporary standard |

**Scoring Rule:** Start with era baseline, then adjust based on property condition:
- Well-maintained/updated for era = +1 to +2
- Average for era = baseline
- Neglected/dated for era = -1 to -3

## Quick Reference

- **Pool**: No pool = 10/10, new equipment (0-5yr) = 10/10, moderate (5-10yr) = 7/10, old (15+yr) = 2/10
- **HVAC**: Estimate from year_built if unknown, flag confidence as "low" for inspection priority
- **Era Calibration**: Pre-1980 = dated acceptable, 1980-1999 = era-typical, 2000+ = modern baseline expected
