---
name: image-assessment
description: Analyze property photos for Phase 2 interior scoring (Section C, 190 pts max). Score kitchen layout, master suite, natural light, ceilings, fireplace, laundry, and aesthetics using 1-10 scale with era-adjusted baselines. Use when analyzing property images, scoring interior quality from photos, assessing room conditions, or determining UAD quality/condition ratings from visual inspection.
allowed-tools: Read, Bash(python:*)
---

## Tool Rules

- File reading: `Read` tool ONLY (not bash cat)
- Directory listing: `Glob` tool ONLY (not bash ls)
- Content search: `Grep` tool ONLY (not bash grep)

## Section C Scoring (190 pts max)

| Category | Max | Multiplier | Key Indicators |
|----------|-----|------------|----------------|
| Kitchen | 40 | 4x | Layout, counters, appliances, cabinets |
| Master Suite | 40 | 4x | Size, closet, en-suite, windows |
| Natural Light | 30 | 3x | Window count, skylights, brightness |
| High Ceilings | 30 | 3x | Height, vaulted, coffered |
| Fireplace | 20 | 2x | Presence, type, condition |
| Laundry | 20 | 2x | Dedicated room, hookups, storage |
| Aesthetics | 10 | 1x | Overall appeal, updates, style |

## 5-Step Analysis Protocol

For each image, complete:

1. **Observe**: List objects, materials, colors, dimensions, light quality
2. **Era Context**: Compare vs year_built baseline (see Era Table below)
3. **Condition**: Note wear, damage, updates, maintenance level
4. **Score**: Assign 1-10 with reasoning (adjustments from baseline)
5. **Confidence**: HIGH/MEDIUM/LOW based on photo coverage/quality

### Era Baseline Table

| Era | Kitchen Baseline | Master Baseline | Ceilings |
|-----|------------------|-----------------|----------|
| Pre-1980 | Galley, oak, tile counters | 11x12, reach-in closet | 8ft |
| 1980-1999 | L/U-shape, Corian/laminate | 12x14, walk-in emerging | Some vaulted |
| 2000-2010 | Open plan, granite, island | 14x16, dual vanity | 9ft standard |
| 2010+ | Full open, quartz, waterfall | Large + sitting area | 10ft+ |

**Scoring adjustments**: +1-2 if exceeds era, -1-2 if below era baseline.

## Finding Images

### Address Folder Lookup (CRITICAL)

```python
lookup = json.load(open("data/property_images/metadata/address_folder_lookup.json"))
mapping = lookup.get("mappings", {}).get(target_address)
folder = mapping["path"] if mapping else f"data/property_images/processed/{hashlib.md5(target_address.lower().encode()).hexdigest()[:8]}/"
```

### List Images

Use **Glob** tool: `pattern="*.png", path="{folder}"`

## Scoring Rubrics (1-10 Scale)

| Category | 9-10 | 7-8 | 5-6 | 3-4 | 1-2 |
|----------|------|-----|-----|-----|-----|
| Kitchen | Open, quartz, island, stainless | Modern, good counters, updated | Functional, dated, laminate | Galley, very dated | Major reno needed |
| Master | Large, walk-in, luxury en-suite | Good size, updated bath | Average, basic closet | Small, minimal closet | Cramped, no en-suite |
| Light | Many windows, skylights | Good windows, bright | Average, some dark | Limited windows | Very poor, dark |
| Ceilings | 10ft+ or vaulted | 9ft throughout | Standard 8ft | Low, cramped | <8ft |
| Fireplace | Gas, modern focal point | Wood, well-maintained | Decorative/older | Non-functional | N/A (score 0) |
| Laundry | Dedicated room + sink | Good area + shelving | Hallway, adequate | Garage, cramped | No dedicated space |
| Aesthetics | Modern, designer | Clean, neutral, updated | Average, some dated | 80s/90s throughout | Major cosmetic needed |

**Key visual cues**: Layout type, counter material, appliance age/finish, cabinet condition, closet type, window count, ceiling height relative to doors.

## Condition Flags

| Priority | Deduct | Note | Add |
|----------|--------|------|-----|
| High | Water damage, cracks, mold, foundation issues, knob-and-tube | - | - |
| Medium | - | Popcorn ceilings, brass fixtures, worn carpet, peeling paint | - |
| Positive | - | - | Recent renovation, high-end appliances, built-ins, premium flooring |

## Roof Age Estimation (from aerial photos)

| Visual | Age |
|--------|-----|
| Uniform color, crisp edges | 0-5 yrs |
| Slight fading | 5-15 yrs |
| Noticeable fading/discoloration | 15-25 yrs |
| Wear, missing pieces | 25+ yrs |

If no roof images: Add to `data/research_tasks.json` for follow-up.

## Output Format

See `src/phx_home_analysis/validation/schemas.py` for full schema. Key fields:

```
scores: {kitchen_layout, master_suite, natural_light, high_ceilings, fireplace, laundry_area, aesthetics}
total_interior_score: (weighted sum, 190 max)
confidence: high|medium|low
condition_issues: [{severity, issue, location}]
positive_features: [string]
```

## Confidence Levels

| Level | Photo Coverage | Implications |
|-------|----------------|--------------|
| HIGH | 6+/7 categories, good quality, multi-angle | Reliable for tier assignment |
| MEDIUM | 4-5 categories, single photos, minor quality issues | Flag uncertain categories |
| LOW | <4 categories, poor quality, missing kitchen/master | Verify in person, use 5.0 default |

**Low confidence rule**: Default 5.0 for missing categories; document reason; do not penalize otherwise strong properties.

## UAD Mapping

| Score | UAD Condition | UAD Quality | Description |
|-------|---------------|-------------|-------------|
| 9-10 | C1-C2 | Q1-Q2 | New/Excellent |
| 7-8 | C2-C3 | Q3 | Good |
| 5-6 | C3-C4 | Q4 | Average |
| 3-4 | C4-C5 | Q5 | Fair |
| 1-2 | C5-C6 | Q6 | Poor |

**Update status**: Not Updated (>20 yrs), Updated (<20 yrs), Remodeled (structural changes).

## Related Skills

- **inspection-standards**: UAD/ASHI terminology
- **exterior-assessment**: Roof, pool, HVAC protocols
- **arizona-context-lite**: Phoenix era calibration

## Best Practices

1. Check folder lookup first (hash may differ)
2. View ALL images, not just first few
3. Note missing rooms in output
4. Watch for staging hiding issues
5. Always use year_built for era context
6. Create research tasks for missing data
