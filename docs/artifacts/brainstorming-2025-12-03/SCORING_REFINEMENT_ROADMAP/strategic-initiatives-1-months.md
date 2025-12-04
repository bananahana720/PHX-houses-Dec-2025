# STRATEGIC INITIATIVES (1+ Months)

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
