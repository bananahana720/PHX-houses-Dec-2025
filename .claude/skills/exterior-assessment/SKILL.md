---
name: exterior-assessment
description: Assess exterior property condition from photos including roof, pool equipment, HVAC units, foundation/stucco, and backyard utility. Apply Arizona-specific aging factors (HVAC 10-15yr, tile roof 30-40yr). Use when analyzing exterior photos, estimating component ages, scoring Phase 2 exterior condition, or determining repair budgets.
allowed-tools: Read
---

# Exterior Assessment Skill

Systematic visual assessment protocols for exterior property features in Arizona.

## Quick Scoring Reference

### Roof (Tile)

| Age | Visual Indicators | Score |
|-----|-------------------|-------|
| 0-5 yrs | Uniform color, sharp edges | 9-10 |
| 6-15 yrs | Slight fading, edges intact | 7-8 |
| 16-25 yrs | Noticeable fading, worn edges | 5-6 |
| 26+ yrs | Cracks, missing tiles | 1-4 |

### HVAC Unit

| Age | Visual Indicators | Score |
|-----|-------------------|-------|
| 0-5 yrs | Modern, pristine paint | 9-10 |
| 6-10 yrs | Slight fading, minor wear | 7-8 |
| 11-15 yrs | Rust spots, dust on coils | 5-6 |
| 16+ yrs | Significant rust, heavy contamination | 1-4 |

**Arizona lifespan**: 10-15 years (national: 15-20)

### Pool Equipment

| Age | Visual Indicators |
|-----|-------------------|
| 0-3 yrs | Crisp labels, no rust, digital controls |
| 4-7 yrs | UV-faded labels, minor rust |
| 8-12 yrs | Illegible labels, moderate rust |
| 13+ yrs | Missing labels, heavy rust, obsolete |

**Arizona factor**: Apply +20% aging (110-120F accelerates wear)

## Photo Priority

1. Aerial/Drone - roof, layout, orientation
2. Front Exterior - roof, foundation
3. Rear Exterior - backyard, patio, HVAC
4. Pool Equipment Pad - all components

## Output Schema

```yaml
exterior_assessment:
  roof: {type, age_estimate, score, budget_impact}
  pool_equipment: {age_estimate, score, budget_impact}
  hvac_unit: {age_estimate, score, refrigerant_type, budget_impact}
  foundation: {condition, score, critical_issues[]}
  backyard_utility: {score, covered_patio, pool_impact}
```

## Reference Files

| File | Content |
|------|---------|
| `protocols.md` | Detailed protocols for each component |

**Load detail:** `Read .claude/skills/exterior-assessment/protocols.md`

## Best Practices

1. Analyze multiple photos per category
2. Apply Arizona aging factors to all estimates
3. Note photo limitations in confidence
4. Cross-reference home age to validate
5. Distinguish critical vs cosmetic issues
