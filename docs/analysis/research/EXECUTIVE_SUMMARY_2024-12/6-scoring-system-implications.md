# 6. Scoring System Implications

### Assumptions Requiring Update

**HVAC Age Scoring (Section B - Systems):**

| Current Assumption | Research Finding | Recommended Update |
|--------------------|------------------|-------------------|
| 20+ year HVAC lifespan | 8-15 years in Arizona | Recalibrate to 12-year midpoint |
| Linear depreciation | Accelerated degradation >8 years | Apply exponential penalty after 8 years |
| Same as national | 30-40% more runtime | Increase age penalty by 30% |

**Proposed HVAC Scoring:**
- 0-5 years: Full points (30/30)
- 6-10 years: Moderate deduction (20/30)
- 11-15 years: Significant deduction (10/30)
- 15+ years: Major deduction + replacement flag (0/30)

**Roof Age Scoring (Section B - Systems):**

| Current | Update |
|---------|--------|
| Tile roof = long lifespan | Add underlayment age factor (12-20 years) |
| Shingle roof standard | Arizona lifespan: 12-25 years (not 20-30) |

**Pool Factor (Section C - Interior/Exterior or Cost Efficiency):**

| Factor | Monthly Addition | Scoring Impact |
|--------|------------------|----------------|
| Pool present | +$300-400/month | Add to cost efficiency calculation |
| Pool equipment >8 years | +$1,500 near-term expense | Flag in deal sheet |
| Pool heater >12 years | +$3,000 near-term expense | Flag in deal sheet |

### New Data Sources to Incorporate

| Data Source | Field(s) | Scoring Integration |
|-------------|----------|---------------------|
| FEMA NFHL API | flood_zone, sfha | Section A - Location (kill-switch) |
| WalkScore API | walk_score, transit_score, bike_score | Section A - Location (+0-20 pts) |
| Phoenix Open Data | crime_incidents, crime_rate | Section A - Location (safety score) |
| County Assessor | year_built, HVAC_age (if available) | Section B - Systems |
| Listing Data | solar_type (owned/leased/none) | Kill-switch + bonus |

**Proposed WalkScore Integration:**

| Walk Score | Points | Description |
|------------|--------|-------------|
| 90-100 | +20 | Walker's Paradise |
| 70-89 | +15 | Very Walkable |
| 50-69 | +10 | Somewhat Walkable |
| 25-49 | +5 | Car-Dependent |
| 0-24 | +0 | Almost All Errands Require a Car |

**Proposed Solar Scoring:**

| Condition | Points | Kill-Switch |
|-----------|--------|-------------|
| Owned solar (no encumbrance) | +5 | No |
| No solar | 0 | No |
| Solar loan | 0 | No (INFO only) |
| Solar lease/PPA | -5 | **HARD FAIL** |

### Calibration Recommendations

**1. Section A (Location) - 230 points max:**
- Add flood zone verification (kill-switch only, no points)
- Add walkability score (+0-20 points, reallocate from other location factors)
- Add water service area factor (kill-switch warning for non-DAWS)

**2. Section B (Systems) - 180 points max:**
- Recalibrate HVAC age curve for Arizona 10-15 year lifespan
- Add roof underlayment age factor for tile roofs
- Add foundation assessment factor (+0-15 points)

**3. Section C (Interior) - 190 points max:**
- Integrate pool equipment age into assessment
- Add owned solar bonus (+5 points)

**4. Cost Efficiency Module:**
- Add pool ownership cost: $300/month baseline
- Update commute cost: 70 cents/mile (2025 IRS rate)
- Add water/sewer differential: $50-100/month for septic maintenance budget

---
