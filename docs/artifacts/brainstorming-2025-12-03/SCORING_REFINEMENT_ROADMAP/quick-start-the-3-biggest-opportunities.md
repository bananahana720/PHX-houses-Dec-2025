# QUICK START: The 3 Biggest Opportunities

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
