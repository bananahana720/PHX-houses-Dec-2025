# PHX Houses Scoring Quick Reference Card

**Canonical Source:** `.claude/skills/_shared/scoring-tables.md`

---

## Scoring System at a Glance

| Tier | Score | Action |
|------|-------|--------|
| UNICORN | >480 (>80%) | Schedule immediately |
| CONTENDER | 360-480 (60-80%) | Strong candidate |
| PASS | <360 (<60%) | Monitor for price drops |
| FAILED | Any | Kill-switch fail - Disqualified |

**Total: 600 points across 3 sections**

---

## Section A: Location (250 pts max)

| Category | Max | Multiplier | Source |
|----------|-----|------------|--------|
| School Rating | 50 | 5x | GreatSchools |
| Quietness | 50 | 5x | Distance to highway |
| Safety | 50 | 5x | Crime stats |
| Grocery | 40 | 4x | Distance to grocery |
| Parks | 30 | 3x | Walkability score |
| **Orientation** | **30** | **Fixed** | **Satellite view** |

### Orientation Scoring (AZ-Specific)
- North: 30 pts (lowest cooling costs)
- NE/NW: 25 pts
- East: 20 pts
- South: 10 pts
- SE/SW: 5 pts
- West: 0 pts (highest cooling, $100-200/mo extra)

---

## Section B: Lot/Systems (160 pts max)

| Category | Max | Based On | Notes |
|----------|-----|----------|-------|
| Roof | 50 | Age | 0-5 yrs=50pts, 21+yrs=10pts |
| Backyard | 40 | Lot sqft | Usability score |
| Plumbing | 40 | Year built | Era-based quality |
| Pool | 30 | Equipment age | 0-5yrs=30pts, no pool=30pts |

### AZ Context
- Roof lifespan: 10-15 years (vs 20+ elsewhere)
- Pool costs: $100-150/mo service, $3-15k equipment
- HVAC: 10-15 year lifespan, dual-zone preferred

---

## Section C: Interior (190 pts max)

| Category | Max | Multiplier | Scoring |
|----------|-----|------------|---------|
| Kitchen | 40 | 4x | 1-10 scale |
| Master Suite | 40 | 4x | 1-10 scale |
| Natural Light | 30 | 3x | 1-10 scale |
| High Ceilings | 30 | 3x | 1-10 scale |
| Fireplace | 20 | 2x | 1-10 scale |
| Laundry | 20 | 2x | 1-10 scale |
| Aesthetics | 10 | 1x | 1-10 scale |

### Visual Score Interpretation
- 9-10: Exceptional (modern, high-end)
- 7-8: Good (updated, move-in ready)
- 5-6: Average (era-appropriate)
- 3-4: Below average (dated, needs work)
- 1-2: Poor (major renovation needed)

---

## Kill-Switch Criteria (ALL Must Pass)

Properties failing ANY criterion are automatically disqualified.

| Criterion | Requirement | Data Source | Strictness |
|-----------|-------------|-------------|-----------|
| HOA | $0/mo | Listing | STRICT |
| Sewer | City only | Manual research | STRICT |
| Garage | 2+ car | County/Listing | STRICT |
| Bedrooms | 4+ | Listing | STRICT |
| Bathrooms | 2+ | Listing | STRICT |
| Lot Size | 7,000-15,000 sqft | County | STRICT |
| Year Built | Pre-2024 | County | STRICT |

**Note:** No carports - garage only. Carport = FAIL for "2-car garage" requirement.

---

## Default Values

Use 5.0 (neutral/average) when data is missing:

| Category | Default | When OK |
|----------|---------|---------|
| school_rating | 5.0 | No GreatSchools data |
| safety_score | 5.0 | No crime stats |
| parks_score | 5.0 | No park proximity data |
| kitchen_score | 5.0 | No kitchen photos |
| master_score | 5.0 | No master photos |
| All Section C | 5.0 | Insufficient photos |

**Rule:** Never default kill-switch criteria. Flag for research if missing.

---

## Data Quality Scoring

When submitting scores, include:

```
Data Quality: [count of authoritative fields] / [total required fields]
Defaults Used: [count]
```

| Quality | Confidence | Action |
|---------|------------|--------|
| >0.85 | HIGH | Proceed to tier assignment |
| 0.70-0.85 | MEDIUM | Flag uncertain fields |
| <0.70 | LOW | Manual review required |

---

## Scoring Calculation Example

```
Property: 123 Main St, Phoenix

SECTION A (Location): 181/250 pts
  School (7): 35 pts
  Quietness (6): 30 pts
  Safety (8): 40 pts
  Grocery (7): 28 pts
  Parks (6): 18 pts
  Orientation (North): 30 pts

SECTION B (Systems): 120/160 pts
  Roof (8yr): 30 pts
  Backyard (7): 28 pts
  Plumbing (2005): 32 pts
  Pool (none): 30 pts

SECTION C (Interior): 125/190 pts
  Kitchen (7): 28 pts
  Master (8): 32 pts
  Light (6): 18 pts
  Ceilings (5): 15 pts
  Fireplace (6): 12 pts
  Laundry (7): 14 pts
  Aesthetics (6): 6 pts

TOTAL: 426/600 (71%)
TIER: CONTENDER
```

---

## Validation Checklist

Before finalizing scores, verify:

- [ ] All section totals sum correctly
- [ ] Total score ≤ 600
- [ ] Each category ≤ max (Kitchen≤40, etc)
- [ ] Tier matches score range (UNICORN if >480, etc)
- [ ] Kill-switch evaluated first
- [ ] Count defaults (flag if >5)
- [ ] No section score = 0
- [ ] No defaults used for kill-switch criteria

---

## Era-Based Visual Anchors

### Pre-1980
- Kitchen baseline: 5-6/10 (small, oak cabinets, tile counters)
- Scoring adjustment: Original +0, Updated counters +1, Full reno +2-3
- Master baseline: 4-5/10 (small, reach-in closet, shared bath)

### 1980-1999
- Kitchen baseline: 5-6/10 (L-shape, raised panels, Corian)
- Scoring adjustment: Oak/Corian +0, Granite +1, Full stainless +1, Reno +2-3
- Master baseline: 5-6/10 (moderate size, walk-in emerging, en-suite)

### 2000+
- Kitchen baseline: 6-7/10 (open, 42" cabinets, granite, stainless)
- Scoring adjustment: Granite/stainless/island +0, Quartz +1, Smart features +1-2
- Master baseline: 6-7/10 (large, walk-in required, dual vanity, 9ft ceilings)

---

## Quick Field Mappings

| Score Category | Data Field | Format |
|---|---|---|
| school_rating | `school_rating` | 1-10 (GreatSchools) |
| quietness | `distance_to_highway_miles` | Float (miles) |
| safety | `safety_neighborhood_score` | 1-10 (crime inverse) |
| grocery | `distance_to_grocery_miles` | Float (miles) |
| parks | `parks_walkability_score` | 1-10 |
| orientation | `orientation` | N/S/E/W/NE/NW/SE/SW |
| roof | `roof_age` | Years (integer) |
| backyard | `lot_sqft` | Square feet |
| plumbing | `year_built` | Year (integer) |
| pool | `pool_equipment_age` | Years or N/A |
| kitchen | `kitchen_layout_score` | 1-10 (from photos) |
| master | `master_suite_score` | 1-10 (from photos) |
| light | `natural_light_score` | 1-10 (from photos) |
| ceilings | `high_ceilings_score` | 1-10 (from photos) |
| fireplace | `fireplace_score` | 1-10 (from photos) |
| laundry | `laundry_area_score` | 1-10 (from photos) |
| aesthetics | `aesthetics_score` | 1-10 (from photos) |

---

**Last Updated:** 2025-12-01
**Source:** `.claude/skills/_shared/scoring-tables.md` (canonical)
