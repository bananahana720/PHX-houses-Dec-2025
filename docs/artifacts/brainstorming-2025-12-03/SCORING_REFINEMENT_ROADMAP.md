# Scoring & Filtering Refinement Roadmap

**Strategic Guide for Buy-Box Evolution**
**Date**: 2025-12-03

---

## QUICK START: The 3 Biggest Opportunities

### #1: KILL-SWITCH FLEXIBILITY TIERS (HIGH ROI, QUICK IMPACT)
**Impact**: Could pass 20-30% more properties for Phase 2 evaluation
**Effort**: 1-2 weeks
**Why Now**: Current all-or-nothing approach may filter too aggressively

**Current State**:
```
HARD (instant FAIL):
  - HOA > $0 (absolutely no HOA allowed)
  - Beds < 4 (must be ≥4)
  - Baths < 2 (must be ≥2)

SOFT (severity accumulated):
  - Sewer ≠ city (2.5 severity)
  - Year ≥ 2024 (2.0 severity)
  - Garage < 2 (1.5 severity)
  - Lot < 7k or > 15k sqft (1.0 severity)
```

**Proposal: Flexibility Tier System**
```python
CRITICAL (instant FAIL, never flex):
  - Beds < 4 (space non-negotiable)
  - Baths < 2 (same)

FIRM (strong preference, limited flex):
  - HOA ≤ $150/mo OK, else severity 0.0-2.0 graduated
  - Sewer: City ideal, septic with good inspector cert, severity 0.5
  - Garage: 2 ideal (0 severity), 1.5-car acceptable (0.5 severity), 1-car FAIL (3.0 severity)

SOFT (preference, high tolerance):
  - Lot: 7k-15k ideal, 5k-7k acceptable (0.25 severity), 15k-25k acceptable (0.25 severity)
  - Year: Pre-2024 ideal, 2023 OK (0 severity), 2024 needs inspection (1.0 severity)
```

**Implementation Steps**:
1. Add `FlexibilityTier` enum to kill-switch system
2. Recalibrate severity weights per tier
3. Update criteria definitions with graduated thresholds
4. Test on existing portfolio - measure pass rate change
5. Document buyer intent assumptions per tier

**File Changes Needed**:
- `src/phx_home_analysis/services/kill_switch/constants.py` - Add tier definitions, new severity weights
- `scripts/lib/kill_switch.py` - Update evaluation logic for graduated thresholds
- `CLAUDE.md` (project root) - Document flexibility tier philosophy

---

### #2: SECTION-LEVEL SCORE BREAKDOWN (QUICK WIN, HIGH CLARITY)
**Impact**: Dramatically improves interpretability
**Effort**: 1 day
**Why Now**: Properties scored but results don't explain what drives score

**Current State**:
```
Property: 4209 W Wahalla Ln, Glendale, AZ 85301
Price: $475,000
Beds/Baths: 4/2.5
Score: 415 points
Tier: Contender
Verdict: PASS
```

**Proposed Output**:
```
Property: 4209 W Wahalla Ln, Glendale, AZ 85301
Price: $475,000 | Beds/Baths: 4/2.5 | Score: 415/600 (69%) | Tier: Contender

SCORE BREAKDOWN:
  Section A (Location & Environment): 185/250 pts (74%)
    ✓ Schools: 42/42 (Excellent - Rating 10)
    ◐ Safety: 30/47 (Moderate - Crime index 65)
    ◑ Quietness: 5/30 (Noisy - 0.3mi to freeway)
    ✓ Grocery Proximity: 23/23 (Walking distance)
    ✓ Parks/Walkability: 22/23 (Very walkable)
    ✓ Orientation: 25/25 (North-facing, excellent cooling)
    ◐ Flood Risk: 18/23 (500-year zone, no insurance needed)
    - Walk/Transit: 20/22 (Somewhat walkable)

  Section B (Lot & Systems): 95/170 pts (56%) ← DRAG ON SCORE
    ◑ Roof: 20/45 (Fair condition - 15 years old)
    ◑ Backyard: 20/35 (Small - ~1,500 sqft usable)
    ◑ Plumbing/Electrical: 28/35 (Modern - built 2002)
    ✓ Pool: 20/20 (Equipment excellent - 3 years old)
    ✓ Cost: 35/35 (Very affordable - $3,200/mo estimated)

  Section C (Interior & Features): 135/180 pts (75%)
    ✓ Kitchen: 35/40 (Great layout - island, open to living)
    ✓ Master Suite: 32/35 (Excellent - walk-in closet, dual sinks)
    ✓ Natural Light: 28/30 (Abundant windows, vaulted ceilings)
    ✓ High Ceilings: 25/25 (9-10ft throughout, vaulted living)
    ◐ Fireplace: 10/20 (Decorative, not gas)
    - Laundry: 5/20 (Garage only, no dedicated room)

KEY INSIGHTS:
  • Strong location (74%) with excellent schools and safety
  • Weak systems (56%) - Roof aging, backyard small
  • Strong interior (75%) - Well-designed living spaces
  • Likely improvement area: New roof would add +8 points (→ 423, still Contender)
  • Comparable properties (4 bed, $475k): Score range 380-450 (you're 77th percentile)
```

**Implementation Steps**:
1. Update `ScoreBreakdown` dataclass to include section totals + percentages
2. Modify scoring service to track section scores (not just total)
3. Update deal sheet renderer to display section breakdown + insights
4. Add percentile calculation (requires full portfolio scoring)
5. Create visual indicator (✓/◐/◑/- for quality tiers)

**File Changes Needed**:
- `src/phx_home_analysis/domain/value_objects.py` - Enhance `ScoreBreakdown` with sections
- `src/phx_home_analysis/services/scoring/scorer.py` - Track section totals
- `scripts/deal_sheets/renderer.py` - Render section breakdown
- `docs/VISUALIZATIONS_GUIDE.md` - Document new output format

---

### #3: FOUNDATION + STRUCTURAL ASSESSMENT (MEDIUM EFFORT, HIGH IMPACT)
**Impact**: Completes "bones over cosmetics" philosophy
**Effort**: 2-3 weeks
**Why Now**: Current system grades roof/HVAC/plumbing but misses foundation (most expensive to fix)

**Current State**:
```
Systems Section (170 pts) includes:
  - Roof condition (45 pts)
  - Backyard utility (35 pts)
  - Plumbing/Electrical (35 pts)
  - Pool condition (20 pts)
  - Cost efficiency (35 pts)

MISSING: Foundation/structural health
```

**Proposal: Foundation Assessment Criteria**

**New Criterion**: Foundation & Structural Integrity (40 pts, Section B)
```
Score mapping (0-10 scale, converted to 40pts):
  10 pts: New construction or recent repair, no visible issues
  8 pts: Post-1990 slab, minimal hairline cracks only
  6 pts: Pre-1990 slab, minor settled areas, small patches
  4 pts: Pre-1980 slab, visible cracks >1/4", uneven floors in spots
  2 pts: Very old slab, major cracks, significant settling, water stains
  0 pts: Foundation failure evident, major water intrusion

Assessment via Phase 2 Image-Assessor:
  - Visible cracks in photos (exterior foundation, garage)
  - Settled/uneven areas in interior floor photos
  - Water stains in basement/crawlspace (if visible)
  - Gap issues between door frames and wall
  - Foundation age estimation from listing/year_built
```

**Severity Implications**:
```
Foundation condition score < 4 could become kill-switch soft criterion:
  - Foundation assessment (2.0 severity if score < 4)
  - Becomes MEDIUM flexibility tier: "Requires inspection, may add $5k-20k cost"
```

**New Section B Structure (245 pts total, up from 170):
```
SYSTEMS & STRUCTURE (245 pts)
  - Roof Condition (45 pts)
  - Foundation/Structural (40 pts) ← NEW
  - Plumbing/Electrical (35 pts)
  - Backyard Utility (35 pts)
  - Pool Condition (20 pts)
  - Cost Efficiency (35 pts)
  - HVAC Condition (20 pts) ← OPTIONAL, not yet captured

This rebalances total score from 600 to 645 pts, requires tier recalibration
OR keep 600 by adjusting existing criteria allocations
```

**Implementation Steps**:
1. Define foundation assessment rubric (5-point scale)
2. Add foundation_assessment_score field to Property entity
3. Create FoundationAssessmentScorer strategy
4. Update image-assessor Phase 2 rubric with foundation guidance
5. Add kill-switch soft criterion for major foundation issues (optional)
6. Recalibrate tier boundaries if adding 40pts to Section B

**Subtask: HVAC Assessment (Optional but Aligned)**
Similar to foundation:
```
HVAC Condition (20 pts):
  10 pts: New/recent replacement (0-5 years)
  8 pts: Good condition (5-10 years)
  6 pts: Fair condition (10-15 years) ← AZ average lifespan
  3 pts: Aging (15-20 years), major service history
  0 pts: Replacement imminent (>20 years)

Data source: Year_built inference + Phase 2 visual (compressor age if visible)
```

**File Changes Needed**:
- `src/phx_home_analysis/domain/entities.py` - Add foundation_assessment_score, hvac_condition_score
- `src/phx_home_analysis/services/scoring/strategies/systems.py` - Add FoundationAssessmentScorer, HVACScorer
- `.claude/agents/image-assessor.md` - Update Phase 2 rubric with foundation guidance
- `src/phx_home_analysis/config/scoring_weights.py` - Add foundation + hvac weights (or recalibrate existing)

---

## MEDIUM-TERM INITIATIVES (2-4 Weeks)

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

## STRATEGIC INITIATIVES (1+ Months)

### #7: ZONING & DEVELOPMENT RISK LAYER (Phase 0.5)
**Impact**: Adds missing "Growth/zoning" dimension from vision
**Effort**: 3-4 weeks
**Why Now**: Vision explicitly mentions zoning; current system doesn't capture it

**Proposal**:
```
NEW PHASE 0.5 ENRICHMENT: Zoning & Development Risk
Data sources:
  1. Maricopa County zoning shapefile (GIS data)
  2. City comprehensive plans + future land use maps
  3. County development pipeline (upcoming zoning changes)
  4. School district expansion plans
  5. Commercial/industrial proximity risk

New Criteria (25 pts, add to Section A):
  - Current zoning appropriateness (5 pts)
    * Single-family residential: 5 pts (what you want)
    * Planned residential: 4 pts (will be rezoned)
    * Mixed-use: 3 pts (commercial may come)
    * Commercial/industrial nearby: 1 pt (noise/traffic risk)

  - Zoning change risk (10 pts)
    * Stable (no planned changes): 10 pts
    * Potential upzoning (multi-family planned in 5yr): 5 pts (value play)
    * Likely zoning change (city plan shows commercial): 2 pts (risk)

  - School district growth (10 pts)
    * Stable/declining enrollment: 10 pts
    * Moderate growth (5-10% in 5yr): 8 pts
    * Rapid growth (>15% in 5yr): 5 pts (quality dilution risk)

New Section A: 275 pts total (up from 250)

This requires:
  - County GIS data integration
  - Reverse geocoding to zoning district
  - City comprehensive plan parsing
  - School enrollment projections
```

**Implementation Steps**:
1. Acquire Maricopa County zoning GIS shapefile
2. Set up GIS reverse geocoding (property coords → zoning district)
3. Create ZoningScorer strategy
4. Integrate school district growth data (from GreatSchools or Census)
5. Create risk scoring model (low/medium/high)
6. Add to Phase 0.5 enrichment pipeline

**File Changes Needed**:
- `src/phx_home_analysis/services/location_data/zoning.py` ← NEW
- `src/phx_home_analysis/services/scoring/strategies/location.py` - Add ZoningScorer
- `src/phx_home_analysis/config/scoring_weights.py` - Add zoning weights
- `scripts/extract_zoning_data.py` ← NEW script

---

### #8: ENERGY EFFICIENCY MODELING
**Impact**: Quantifies climate/power usage dimension of vision
**Effort**: 2-3 weeks
**Why Now**: Climate factors underdeveloped; solar currently treated as cost liability only

**Proposal**:
```python
ENERGY EFFICIENCY MODULE:

1. Annual kWh Projection:
   - Base: sqft * 12 * 0.8 kWh/sqft/month (Phoenix baseline)
   - Adjustment by orientation:
     * North-facing: 0.85x (best, minimal sun exposure)
     * East-facing: 0.90x
     * South-facing: 1.0x (neutral)
     * West-facing: 1.15x (worst, afternoon sun)
   - Adjustment by age/efficiency:
     * Pre-1980: 1.2x (no insulation, old systems)
     * 1980-2000: 1.1x (basic insulation)
     * 2000-2010: 1.0x (modern standards)
     * 2010+: 0.9x (energy code compliance)
   - Pool impact: +50 kWh/month (pump, heater in summer)

   Example:
   2,000 sqft home, west-facing, 2005 construction, no pool
   Baseline: 2000 * 12 * 0.8 = 19,200 kWh/yr
   West-facing adjustment: 19,200 * 1.15 = 22,080 kWh/yr
   Modern construction adjustment: 22,080 * 1.0 = 22,080 kWh/yr (no change)
   Annual kWh: ~22,000 kWh/yr

2. Solar Offset Calculation (if solar lease or owned):
   - 5 kW system produces: ~6,500-7,000 kWh/yr in Phoenix
   - Net kWh after solar: 22,000 - 6,500 = 15,500 kWh/yr
   - Annual savings: (22,000 - 15,500) * $0.145 = ~$945/yr

3. Total Annual Energy Cost:
   Electricity: 22,000 kWh * $0.145/kWh = $3,190/yr = $266/mo
   With solar: 15,500 kWh * $0.145/kWh = $2,248/yr = $187/mo
   Net solar benefit: -$145/mo (lease cost) + $79/mo (savings) = -$66/mo (actually costs more!)

4. NEW ENERGY EFFICIENCY SCORE (25 pts, Section A or B):
   Scoring based on kWh/sqft/yr ratio:

   Excellent (<8 kWh/sqft/yr): 25 pts
     Examples: New construction, north-facing, good insulation

   Good (8-10 kWh/sqft/yr): 20 pts
     Examples: 2000+ construction, moderate orientation

   Moderate (10-12 kWh/sqft/yr): 15 pts
     Examples: 1990-2000 construction, mixed orientation

   Fair (12-14 kWh/sqft/yr): 10 pts
     Examples: 1980-1990 construction, west-facing

   Poor (>14 kWh/sqft/yr): 5 pts
     Examples: Pre-1980, poor insulation, west-facing
```

**Implementation Steps**:
1. Create EnergyEfficiencyScorer strategy
2. Add constants for kWh baseline, orientation multipliers, age efficiency factors
3. Integrate solar production calculation (if present)
4. Add energy_efficiency_score to Property entity
5. Update cost_efficiency calculation with actual energy cost (not flat estimate)
6. Add energy breakdown to deal sheet reports

**File Changes Needed**:
- `src/phx_home_analysis/services/scoring/strategies/location.py` - Add EnergyEfficiencyScorer
- `src/phx_home_analysis/config/constants.py` - Add energy model constants
- `src/phx_home_analysis/domain/entities.py` - Add estimated_annual_kwh, solar_annual_kwh_offset
- `scripts/deal_sheets/renderer.py` - Show energy cost breakdown

---

### #9: DECISION SUPPORT DASHBOARD
**Impact**: Transforms static scores into actionable insights
**Effort**: 4-6 weeks
**Why Now**: Scores are opaque; no guidance on offer timing, risk, or improvement priorities

**Proposal**:
```
INTERACTIVE HTML DASHBOARD (per property):

1. OVERVIEW CARD
   │ Property: 4209 W Wahalla Ln, Glendale, AZ 85301
   │ Price: $475,000 | Beds: 4 | Baths: 2.5 | Sqft: 2,150
   │ Score: 415/600 (69%) | Tier: Contender | Ranking: 77th percentile
   │ Kill-Switch: PASS (no failures)
   │ Comparable Properties: 450 analyzed, 346 in price range $450-500k

2. STRENGTHS & WEAKNESSES ANALYSIS
   Strengths (Pull Score Up):
     ✓ Excellent Schools (42/42) - Top-rated school district
     ✓ Strong Interior (135/180) - Well-designed kitchen, master suite
     ✓ North-facing orientation (25/25) - Minimal cooling costs
     ✓ Very Affordable (35/35) - Monthly cost $3,200 (below target)

   Weaknesses (Pull Score Down):
     ✗ Aging Roof (20/45) - 15 years old, consider replacement
     ✗ Small Backyard (20/35) - Limited outdoor space (~1,500 sqft usable)
     ✗ Noisy Location (5/30) - Very close to freeway (0.3mi), traffic noise

3. INVESTMENT OPPORTUNITY ANALYSIS
   What improvements would matter most?

   Rank | Improvement | Cost | Score Impact | ROI | Recommendation
   1    | Replace Roof | $8,000 | +25 (→440) | Strong | Do before offer
   2    | Landscaping (noise barrier) | $3,000 | +5 (→420) | Marginal | Nice-to-have
   3    | Patio/Pavers | $5,000 | +8 (→423) | Marginal | Consider for resale

4. RISK ASSESSMENT
   Condition Health Score: 7/10 (Moderate)

   Roof: 15 years old (AZ avg lifespan 12yr) → HIGH PRIORITY
     Remaining life: ~3-5 years
     Replacement cost: $8,000
     Action: Request recent inspection report before offer

   HVAC: 18 years old (AZ avg lifespan 12yr) → HIGH PRIORITY
     Remaining life: 1-2 years max
     Replacement cost: $8,000
     Action: Plan $8k reserve in next 18 months

   Plumbing/Electrical: Good (2002 construction)

   Foundation: No visible issues (North-facing, no settling)

   Overall Risk: MODERATE (roof + HVAC approaching EOL)
   Action: Include roof + HVAC replacement in inspection/offer

5. MARKET POSITIONING
   Score Distribution (450 properties analyzed):

   Unicorn (>480):      45 properties (10%)
   Contender (360-480): 210 properties (47%)
   Pass (<360):         195 properties (43%)

   Your property (415): 77th percentile (better than 77% of market)

   In $450-500k price range (346 properties):
     Average score: 385 (you're +30 above average)
     Best score: 520 (Unicorn)
     Worst score: 280 (barely passed)

   Comparable properties (4bed, $475k ±$25k):
     Score range: 380-450
     Your rank: 3rd best of 8 similar properties

6. OFFER STRATEGY
   Market Condition: Moderate (47% properties are Contender tier)
   Your Competitiveness: STRONG (top tier in category)

   Recommended Offer: $470,000 - $480,000
     Reasoning: Property slightly above average for price, roof work needed
     Contingency: Professional home inspection with roof assessment
     Repair Request: $8,000 credit for roof replacement or $8k reduction

   Backup Options (if outbid):
     • Property #2 (415 W Central Ave): Score 420, $480k (slightly better, costs more)
     • Property #5 (6245 N 43rd Ave): Score 410, $465k (similar score, cheaper, farther out)
     • Property #7 (Ahwatukee area): Score 425, $495k (better score, much higher cost)

7. TIMELINE SIGNALS
   Days on Market: 32 days (moderate activity)
   Price History: Listed at $485k, now $475k (10k reduction after 30 days)
   Market Signal: Seller motivated, likely room for negotiation

   Recommendation: FAVORABLE TIMING
     - Seller showing flexibility (price reduction)
     - Not getting immediate offers (32 days without sale)
     - Winter market (generally slower)
     Action: Strong offer in $470-480k range likely accepted
```

**Implementation Steps**:
1. Create dashboard HTML template (Jinja2 or similar)
2. Implement comparison analytics (percentile, comparable properties)
3. Build improvement scenario renderer (what-if results)
4. Create risk assessment module (Condition Health Score)
5. Integrate market positioning analysis
6. Add offer strategy recommendation logic
7. Create dashboard generator script
8. Host on local server for viewing

**File Changes Needed**:
- `scripts/generate_dashboard.py` ← NEW script
- `scripts/dashboard_renderer.py` ← NEW module
- `docs/templates/dashboard.html` ← NEW template
- `src/phx_home_analysis/services/analysis/comparables.py` ← NEW module
- `src/phx_home_analysis/services/analysis/market_positioning.py` ← NEW module
- `src/phx_home_analysis/services/analysis/offer_strategy.py` ← NEW module

---

## IMPLEMENTATION PRIORITY MATRIX

```
           EFFORT
      Low      Medium     High
H    #2       #1          #5
I    #6       #4          #7
G    (Quick   (Score      #8
H    Wins)    Breakdown)  #3
              #9
    (Visual
    Rubrics)
                          #9
                        (Dashboard)

                        (Zoning)
                        (Energy)
```

**Recommended Execution Order**:

**Sprint 1 (2 weeks)**:
- #2: Section Breakdown Reporting (Quick impact, high clarity)
- #1: Kill-Switch Flexibility Tiers (High ROI, improves pass rate)

**Sprint 2 (2 weeks)**:
- #5: Visual Scoring Rubrics (High quality, prep for Phase 2)
- #4: Commute Cost Integration (High accuracy improvement)

**Sprint 3 (2-3 weeks)**:
- #3: Foundation + HVAC Assessment (Complete "bones" philosophy)
- #6: What-If Scenario Calculator (Decision support)

**Sprint 4+ (Ongoing)**:
- #7: Zoning & Growth Risk (Strategic alignment)
- #8: Energy Efficiency Modeling (Climate dimension)
- #9: Decision Support Dashboard (Full implementation)

---

## SUCCESS METRICS

### Quick Wins (#1, #2, #5, #6)
- [ ] Section-level breakdowns appear in all deal sheets
- [ ] Section breakdowns match total score (A + B + C = total)
- [ ] Kill-switch pass rate increases by 15-25% with flexibility tiers
- [ ] Visual scoring rubrics adopted by image-assessor agents
- [ ] What-if scenarios calculated for top 50 properties

### Medium-term (#3, #4)
- [ ] Commute cost integrated, monthly budgets recalculated
- [ ] Properties with 30+ min commute show $400+ higher monthly cost
- [ ] Foundation assessment appears on 100% of Phase 2 evaluations
- [ ] Foundation assessment scores correlate with visual inspection notes

### Strategic (#7, #8, #9)
- [ ] Zoning data available for 100% of properties
- [ ] Energy efficiency scores improve cost_efficiency accuracy (< 5% variance)
- [ ] Dashboard provides actionable insights for top 50 properties
- [ ] Offer strategy recommendations generated from dashboard data

---

## CONCLUSION

The PHX Houses project has a **solid foundation** (kill-switch + 600-point scoring) and is ready for focused refinement. The 9 initiatives above address the major vision-implementation gaps while building toward a **comprehensive decision support platform**.

**Key Takeaway**: Start with #1-2 (kill-switch flexibility + section breakdowns) for quick wins that improve both coverage and clarity. Follow with #3-6 (foundation, commute, rubrics, what-if) to close major capability gaps. Reserve #7-9 (zoning, energy, dashboard) for next quarter as strategic, high-effort efforts.

The system can go from **80% vision alignment → 95%+ alignment** with disciplined, prioritized effort over the next 2-3 months.

