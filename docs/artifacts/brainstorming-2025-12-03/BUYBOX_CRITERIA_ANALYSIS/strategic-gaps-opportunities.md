# STRATEGIC GAPS & OPPORTUNITIES

### Priority 1: MAJOR VISION-IMPLEMENTATION GAPS

1. **Zoning & Growth Risk Assessment** (HIGH IMPACT)
   - Vision explicitly mentions zoning and growth
   - Not implemented in current system
   - Would require: Maricopa County zoning layer (GIS data), future development pipeline
   - Recommendation: Add as Phase 0.5 enrichment using ArcGIS public data

2. **Foundation & Structural Integrity** (HIGH IMPACT)
   - Vision emphasizes "bones over cosmetics"
   - Roof/HVAC/plumbing captured, but foundation missing
   - Only addressable via Phase 2 visual inspection + expert assessment
   - Recommendation: Add foundation scoring criteria to image-assessor rubric

3. **Energy Efficiency & Low-Water Landscaping** (MEDIUM IMPACT)
   - Climate dimension underdeveloped
   - Solar systems captured as cost, not efficiency asset
   - Xeriscape preference not modeled
   - Recommendation: Add solar offset calculation, xeriscape scoring

4. **Commute Cost Monetization** (MEDIUM IMPACT)
   - Commute minutes captured but not $ impact on affordability
   - Currently: Distance embedded in location score, cost not deducted
   - Recommendation: Calculate daily commute cost ($0.50-0.70/mile round trip), integrate into cost_efficiency

### Priority 2: INTERPRETABILITY ENHANCEMENTS

1. **Section-Level Breakdowns** (Quick win)
   - Report scores by section (A/B/C) to show category strength
   - Currently: Total score only, no decomposition

2. **Decision Rubrics for Visual Scoring** (Medium effort)
   - Kitchen layout: Define what 10/10 vs 5/10 vs 0/10 looks like
   - Master suite: Break down bedroom size, closet, bathroom separately
   - Would improve consistency across image-assessor agents

3. **Percentile Ranking** (Quick win)
   - Show property in context: "Top 18% of 450 properties analyzed"
   - Add to deal sheet reports

4. **What-If Analysis** (Medium effort)
   - "If roof replaced, score increases by +8 points"
   - "If solar added, monthly cost drops $180, score +5 points"

### Priority 3: MISSING RESALE FACTORS

1. **Garage Quality** (Not just count)
   - 2-car min enforced, but quality not scored
   - Climate-controlled? Direct entry from house? Finished vs raw?

2. **Patio/Outdoor Living Detail** (Partially captured)
   - Backyard utility as raw sqft, but patio coverage/shade not distinguished
   - Pool presence scored, but resort-style vs maintenance burden not

3. **Storage Capacity** (Minimal)
   - Laundry area only, no attic/basement assessment
   - Important for families, not currently weighted

4. **Street Parking Quality** (Not captured)
   - Kill-switch enforces ≥2-car garage, but street parking safety not scored
   - Matters for visitor/overflow scenarios

---
