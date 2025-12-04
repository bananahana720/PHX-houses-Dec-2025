# RECOMMENDED REFINEMENTS

### PHASE A: Quick Wins (1-2 weeks)

1. **Add Section Breakdown Reporting**
   ```python
   # Current: Property(score=415, tier="Contender")
   # Enhanced: Property(
   #   score=415, tier="Contender",
   #   section_a_score=185, section_b_score=95, section_c_score=135,
   #   section_a_pct=0.74, section_b_pct=0.56, section_c_pct=0.75
   # )
   ```

2. **Add Percentile Ranking**
   ```python
   # Requires: Scoring of all portfolio properties
   # Output: "Top 18% of 450 properties (score 415)"
   ```

3. **Improve Kill-Switch Messaging**
   ```python
   # Current: failures=["garage: Minimum 2-car garage (1-car) [severity +1.5]"]
   # Better: "Property has 1-car garage (need 2+) - SOFT criterion, severity 1.5/3.0"
   ```

### PHASE B: Medium Effort (2-4 weeks)

1. **Add Commute Cost to Affordability**
   - Calculate daily commute cost based on distance + fuel/transit
   - Deduct from monthly budget for true affordability score
   - Impact: May change Tier for properties with >60 min commute

2. **Create Visual Scoring Rubrics**
   - Define 5-point scales for Kitchen, Master, Natural Light, etc.
   - Train image-assessor agents on consistent criteria
   - Example: Kitchen 5/5 = Island + open to living room, modern appliances, +2000 sqft view
   - Reduces default neutral scoring dependency

3. **Add Foundation Assessment Criteria**
   - Phase 2 image-assessor evaluates: Visible cracks, settled areas, water stains
   - Score 0-10 for foundation condition
   - Integrate into systems section (roof/HVAC/plumbing/electrical/foundation)

### PHASE C: Strategic Vision Alignment (4-8 weeks)

1. **Zoning & Development Risk Layer**
   - Add Phase 0.5 enrichment: Maricopa County zoning + future dev pipeline
   - Score based on: Current zoning fit, planned upzoning, school expansions
   - Add 25pts location section (push Section A to 275pts)

2. **Energy Efficiency Modeling**
   - Calculate annual kWh use (sqft × climate × orientation × efficiency factor)
   - Model solar offset if present (not as cost, as production benefit)
   - Score energy efficiency as separate criterion (25pts, Section B)
   - Affects: Cost efficiency calculation, resale appeal

3. **Commute & Lifestyle Cost Integration**
   - Monetize commute: $/mo = distance × 2 × 0.65 $/mi
   - Integrate into cost_efficiency calculation
   - Recalculate budget tiers with true all-in cost
   - May shift tier boundaries based on commute realities

4. **Decision Support Tools**
   - What-If scenarios: "If roof replaced" → score change
   - Offer timing: Days on market + price trend integration
   - Comparable analysis: "Score 415 puts you in top 25% for $475k price point"
   - Risk dashboard: Foundation + HVAC + Roof + Electrical health status

---
