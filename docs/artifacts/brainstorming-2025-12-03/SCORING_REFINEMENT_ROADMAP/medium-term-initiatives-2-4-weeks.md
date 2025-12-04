# MEDIUM-TERM INITIATIVES (2-4 Weeks)

### #4: COMMUTE COST MONETIZATION
**Impact**: Transforms "distance" into real affordability metric
**Effort**: 1-2 weeks
**Why Now**: Current system captures distance but not $ impact on monthly budget

**Current State**:
```
Cost Efficiency Calculation (35 pts):
  Monthly cost = Mortgage + Tax + Insurance + HOA + Utilities + Pool + Solar lease
  Commute distance: Captured in location score only (highway distance)
  Commute cost: NOT calculated, not deducted from affordability budget
```

**Proposal**:
```python
# Add commute cost factor to monthly cost calculation

COMMUTE_COST_MODEL:
  - One-way distance: From property to work address (user input)
  - Round-trip daily cost: distance * 2 * 0.65 $/mile (fuel + maintenance)
  - Monthly commute cost: daily * 22 working days

Examples:
  5 mi commute:   5*2*0.65*22 = $143/mo
  10 mi commute: 10*2*0.65*22 = $286/mo
  30 mi commute: 30*2*0.65*22 = $858/mo

Updated Monthly Cost Calculation:
  Total = Mortgage + Tax + Insurance + HOA + Utilities + Pool + Solar + COMMUTE

New Tiers:
  $3,000/mo or less → 35 pts (very affordable, includes all costs)
  $3,500/mo → 25.7 pts
  $4,000/mo → 17.5 pts (at budget)
  $4,500/mo → 8.2 pts (stretching)
  $5,000+/mo → 0 pts (exceeds target)
```

**Impact Example**:
```
Property A (close to work):
  Mortgage: $2,200
  Taxes/Ins/HOA/Utils: $600
  Pool: $200
  Commute (5mi): $143
  Total: $3,143 → 35 pts, VERY AFFORDABLE

Property B (far from work):
  Mortgage: $2,000 (cheaper house, farther out)
  Taxes/Ins/HOA/Utils: $550
  Pool: $200
  Commute (30mi): $858
  Total: $3,608 → 24 pts, AFFORDABLE (but lower score)

Even though Property B is cheaper purchase price, true cost is 15% higher
```

**Implementation Steps**:
1. Add work_address field to BuyerProfile or as input parameter
2. Geocode work_address to lat/lon
3. Calculate distance from property to work (Google Maps API or haversine)
4. Add commute_monthly_cost field to Property entity
5. Update cost_efficiency calculation to include commute_cost
6. Recalibrate cost_efficiency tier thresholds (will increase all costs by ~$100-500/mo)
7. Add to deal sheet reports for transparency

**File Changes Needed**:
- `src/phx_home_analysis/config/constants.py` - Add COMMUTE_COST_PER_MILE, COMMUTE_WORKING_DAYS
- `src/phx_home_analysis/domain/entities.py` - Add commute_distance_miles, commute_monthly_cost
- `src/phx_home_analysis/services/scoring/strategies/cost_efficiency.py` - Update calculation
- `scripts/phx_home_analyzer.py` - Accept work_address as parameter
- `scripts/deal_sheets/renderer.py` - Display commute cost breakdown

---

### #5: VISUAL SCORING RUBRICS FOR CONSISTENCY
**Impact**: Eliminates default neutral scoring, improves inter-agent consistency
**Effort**: 1-2 weeks
**Why Now**: Phase 2 image-assessor defaults to neutral (5-10 pts) when rubric is vague

**Current State**:
```python
# From scoring_weights.py:
"Kitchen Layout (40 pts max):
    Open concept vs closed
    Island/counter space
    Modern appliances
    Pantry size
    Natural light
  Scoring: 0-40 scale, default 20 (neutral)"
```

**Problem**: Image-assessor agent has no clear criteria for "what is 20/40 vs 35/40?"

**Proposal: Detailed 5-Point Rubrics**

```markdown
# KITCHEN LAYOUT (40 pts max) - 5-Point Rubric

## 5/5 (40 pts) - Ideal Kitchen
- Island with counter seating or bar
- Open concept to living/dining area
- Modern appliances (stainless steel, convection)
- Pantry (walk-in preferred) or extensive cabinetry
- Abundant natural light (multiple windows or skylights)
- Modern finishes (quartz or granite counters)
- Examples: Open concept with island + bar, window over sink, walk-in pantry, recent appliances

## 4/5 (32 pts) - Very Good Kitchen
- Open concept OR island (not both)
- Good counter space (not abundant)
- Mix of modern/older appliances (some original)
- Standard pantry or generous cabinetry
- Good natural light (couple windows)
- Adequate finishes (laminate OK if clean)
- Examples: Open to living room, island no seating, decent counter space, older appliances work

## 3/5 (24 pts) - Decent Kitchen
- Somewhat open (galley with adjacent living area) OR small island
- Adequate counter space
- Older appliances (pre-2010) but functional
- Limited pantry, modest cabinetry
- Minimal natural light (one or two windows)
- Dated finishes (2000s style)
- Examples: Galley kitchen, limited counter, older appliances, one window, basic cabinets

## 2/5 (16 pts) - Below Average Kitchen
- Closed galley layout (not open)
- Limited counter space, cramped
- Very old appliances (pre-2000)
- No pantry, very limited storage
- No natural light (interior kitchen)
- Dated finishes (1980s-90s style)
- Examples: Closed galley, tight counter, very old appliances, no pantry, dark

## 1/5 (8 pts) - Poor Kitchen
- Closed galley, very cramped
- Minimal counter space
- Non-functional appliances, missing major appliances
- No storage, minimal cabinetry
- No natural light
- Poor condition (needs renovation)
- Examples: Tiny closed kitchen, broken appliances, no counter space, falling apart
```

**Apply Same Structure To**:
- Master Suite (35 pts) - Bedroom size, closet quality, bathroom finishes
- Natural Light (30 pts) - Window count/size, skylights, room brightness
- High Ceilings (25 pts) - Vaulted, 10ft+, 9ft, 8ft standard
- Fireplace (20 pts) - Gas, wood-burning, decorative, none
- Laundry Area (20 pts) - Dedicated room upstairs, any floor, closet, garage
- Aesthetics (10 pts) - Curb appeal, finishes, modern vs dated

**Implementation Steps**:
1. Create detailed rubric document (100-150 lines)
2. Update `.claude/agents/image-assessor.md` with rubric in Phase 2 instructions
3. Add rubric reference to scoring_weights.py docstrings
4. Train image-assessor agents with example images + expected scores
5. Add "reasoning" field to Phase 2 output (explain score choice per rubric)
6. Review first 10-20 scored properties for consistency
7. Iterate rubric if inter-agent variance > 10%

**File Changes Needed**:
- `docs/artifacts/IMAGE_SCORING_RUBRICS.md` ← NEW file (detailed rubrics)
- `.claude/agents/image-assessor.md` - Reference rubrics in Phase 2 instruction set
- `src/phx_home_analysis/config/scoring_weights.py` - Link to detailed rubrics

---

### #6: WHAT-IF SCENARIO CALCULATOR
**Impact**: Decision support tool ("If I fix X, score becomes Y")
**Effort**: 2-3 weeks
**Why Now**: Score of 415 is opaque without counterfactual understanding

**Proposal**:
```python
# Create PropertyScenarios service

property.scenario("Replace Roof")
  # Current: Roof score = 20/45 (15 yrs old, fair condition)
  # New: Roof score = 45/45 (0 yrs old, new)
  # Change: +25 pts
  # New Total Score: 415 + 25 = 440 (still Contender)
  # Cost estimate: $8,000 (from HVAC_REPLACEMENT_COST constant)
  # ROI: Improve score by 25 pts for $8k investment

property.scenario("Replace HVAC")
  # New criterion: HVAC in acceptable range (10-15 yrs)
  # Current: HVAC is 18 years (aging, not scored yet)
  # Scenario: New HVAC (0 yrs)
  # Score impact: +6 pts (if HVAC becomes 20-pt criterion)
  # Cost: $8,000
  # Benefit: Lower energy bills (~$100/mo savings)

property.scenario("Install Solar")
  # Current: No solar (cost efficiency $3,200/mo baseline)
  # With 5kW solar: Reduces kWh usage by ~65%
  # New utility cost: $1,800/mo (vs $2,000)
  # Solar lease: $150/mo
  # Net: Save $50/mo, add $150/mo debt, net -$100/mo (not great)
  # NOTE: This reveals solar lease might not be good value!

property.scenario("Fix Foundation Cracks")
  # Current: Foundation score = 4/10 (visible cracks)
  # New: Foundation score = 8/10 (repaired)
  # Score impact: +16 pts
  # Cost: $5,000-$25,000 (depends on severity)
  # Recommendation: Get inspector estimate before offer
```

**Implementation Steps**:
1. Create PropertyScenarios service in `src/phx_home_analysis/services/`
2. Map each criterion to renovation cost estimate (from constants)
3. Implement scenario calculator for each criterion:
   - Roof replacement → new roof_age = 0
   - HVAC replacement → new hvac_age = 0
   - Foundation repair → new foundation_score = 8
   - Solar installation → new solar_lease = $150, recalc utilities
4. Add to deal sheet as "Score Optimization" section
5. Create CLI: `python scripts/property_scenarios.py --address "ADDR"`

**File Changes Needed**:
- `src/phx_home_analysis/services/scenarios.py` ← NEW file
- `src/phx_home_analysis/config/constants.py` - Add renovation cost estimates (roof, HVAC, foundation, solar)
- `scripts/property_scenarios.py` ← NEW script
- `scripts/deal_sheets/renderer.py` - Add scenarios section to deal sheet

---
