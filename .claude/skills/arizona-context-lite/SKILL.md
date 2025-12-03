---
name: arizona-context-lite
description: Lightweight AZ context for image assessment - pool/HVAC age estimation and era calibration only. Use instead of full arizona-context when only visual scoring context is needed.
allowed-tools: Read
---

# Arizona Context Lite (Image Assessment)

Minimal Arizona-specific context for visual property assessment. For full context including solar leases, pool economics, and commute analysis, use the `arizona-context` skill.

## 1. Era Calibration Table

Use visual indicators to estimate construction era and detect updates:

| Era | Years | Visual Indicators |
|-----|-------|-------------------|
| **Pre-1980** | Before 1980 | Smaller windows, flat roofs, dated fixtures, carports instead of garages |
| **1980s** | 1980-1989 | Arched doorways, mirrored walls, brass fixtures, step-down living rooms |
| **1990s** | 1990-1999 | Vaulted ceilings, plant shelves, oak cabinets, ceiling fans everywhere |
| **2000s** | 2000-2009 | Open floor plans, granite counters, earth tones, maple cabinets |
| **2010s** | 2010-2019 | Gray/white palette, shaker cabinets, stainless appliances, quartz counters |
| **2020s** | 2020+ | Smart home features, waterfall islands, matte black fixtures, clean lines |

### Era Mismatch Scoring

When visual era differs from year_built by 15+ years:
- **Updated kitchen/baths**: +5 pts for modern finishes in older home
- **Dated throughout**: -5 pts, flag renovation budget needed
- **Mixed updates**: Score based on most visible areas (kitchen, main living)

## 2. Arizona HVAC Lifespan

Arizona heat significantly reduces equipment lifespan compared to national averages:

| Component | National Avg | Arizona Avg | Budget When Due |
|-----------|--------------|-------------|-----------------|
| **HVAC** | 15-20 years | 10-15 years | $8,000-15,000 |
| **Water Heater** | 12-15 years | 8-12 years | $1,500-3,000 |
| **Roof (tile)** | 40-50 years | 25-40 years | $10,000-25,000 |
| **Roof (shingle)** | 20-25 years | 15-20 years | $8,000-15,000 |

### HVAC Visual Age Assessment

| Visual Condition | Estimated Age | Score Impact |
|------------------|---------------|--------------|
| Clean housing, modern controls, no rust | 0-5 years | Full points |
| Minor weathering, some discoloration | 5-10 years | -2 pts |
| Visible rust, dated controls | 10-15 years | -5 pts |
| Heavy rust, deteriorated housing | 15+ years | -10 pts (budget $8-15k) |

## 3. Pool Condition Indicators

| Indicator | Good | Fair | Poor |
|-----------|------|------|------|
| **Tile line** | Clean, intact | Some staining | Cracked, missing |
| **Deck/Coping** | Level, no cracks | Minor cracks | Major damage, trip hazards |
| **Interior Surface** | Smooth, even color | Minor staining | Exposed aggregate |
| **Equipment** | <10 years, clean | 10-15 years, weathered | >15 years, rusted |
| **Water Clarity** | Crystal clear | Slightly cloudy | Green, murky |

### Pool Equipment Age from Photos

| Visual Cue | Estimated Age | Budget |
|------------|---------------|--------|
| Variable speed pump, automation | 0-5 years | None |
| Single speed pump, basic filter | 5-10 years | $3-5k soon |
| Visible rust, old salt cell | 10+ years | $8-15k imminent |

## 4. Orientation Impact

Determine orientation from exterior photos showing sun exposure patterns:

| Facing | Score | Reason |
|--------|-------|--------|
| **North** | 30 pts | Best - minimal sun exposure on facade |
| **East** | 20 pts | Good - morning sun only |
| **South** | 10 pts | Fair - manageable with overhangs |
| **West** | 0 pts | Worst - intense afternoon heat, highest cooling bills |

### Orientation Clues in Exterior Photos

- **Shadow direction**: Morning photos show east-facing, afternoon show west-facing
- **Fading/damage**: West-facing facades show most UV damage to paint/stucco
- **Landscaping**: Desert plants on west side = owner mitigation attempt
- **Covered areas**: West-facing patios typically have full shade structures

---

## Quick Reference Card

```
ARIZONA LIFESPAN PENALTIES
==========================
HVAC 12+ years:       Budget $8-15k replacement
Pool equip 10+ years: Budget $5-10k replacement
Roof 25+ years:       Budget $10-25k

ORIENTATION SCORING
===================
North = 30 pts (best)
East  = 20 pts
South = 10 pts
West  = 0 pts (worst)

ERA BASELINE EXPECTATIONS
=========================
Pre-1980:  Dated fixtures acceptable, assess maintenance
1980-1999: Oak/brass era-typical, neutral baseline
2000-2009: Granite/earth-tones expected
2010+:     Modern finishes expected (gray/white/quartz)
```
