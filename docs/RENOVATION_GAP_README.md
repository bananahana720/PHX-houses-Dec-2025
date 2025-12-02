# Renovation Gap Analysis - Phoenix Homes

## Overview

This analysis calculates the **True Cost** (move-in ready price) for each property by adding estimated renovation and repair costs to list prices. All estimates are Arizona-specific, accounting for harsh climate conditions that reduce equipment lifespan.

## Key Findings

### Summary Statistics (23 PASSING properties)

- **Average Renovation Estimate**: $35,957
- **Range**: $12,000 - $42,000
- **Properties with >$20k Renovation**: 24 out of 33 total (72.7%)

### Cost Components (Average per PASSING property)

1. **Kitchen Updates**: $12,391 (34.5%) - 82.6% of properties need updates
2. **Roof Replacement**: $7,652 (21.3%) - 95.7% have unknown age (contingency)
3. **Plumbing/Electrical**: $7,304 (20.3%) - 56.5% built pre-1980 need major work
4. **Pool Equipment**: $4,783 (13.3%) - 95.7% have unknown age (contingency)
5. **HVAC Replacement**: $3,826 (10.6%) - 95.7% have unknown age (contingency)

### Top 3 Best True Value Properties (PASSING only)

#### 1. 16814 N 31st Ave, Phoenix, AZ 85053
- **Rank**: #22 | **Tier**: Contender | **Score**: 361.0
- **List Price**: $400,000
- **True Cost**: $442,000 (+10.5%)
- **Breakdown**: Roof $8k + HVAC $4k + Pool $5k + Plumbing $10k + Kitchen $15k = **$42k**

#### 2. 4417 W Sandra Cir, Glendale, AZ 85308
- **Rank**: #9 | **Tier**: Contender | **Score**: 370.0
- **List Price**: $415,000
- **True Cost**: $457,000 (+10.1%)
- **Breakdown**: Roof $8k + HVAC $4k + Pool $5k + Plumbing $10k + Kitchen $15k = **$42k**

#### 3. 5522 W Carol Ave, Glendale, AZ 85302
- **Rank**: #25 | **Tier**: Contender | **Score**: 354.5
- **List Price**: $442,000
- **True Cost**: $484,000 (+9.5%)
- **Breakdown**: Roof $8k + HVAC $4k + Pool $5k + Plumbing $10k + Kitchen $15k = **$42k**

## Arizona-Specific Cost Estimation Rules

### Roof (Tile/Shingle Replacement)
- **Age unknown**: $8,000 (contingency)
- **Age < 10 years**: $0 (no work needed)
- **Age 10-15 years**: $5,000 (minor repairs)
- **Age 15-20 years**: $10,000 (partial replacement)
- **Age > 20 years**: $18,000 (full replacement)

### HVAC (Central Air + Heat)
Arizona's extreme heat shortens HVAC lifespan to 12-15 years (vs 20+ elsewhere)

- **Age unknown**: $4,000 (contingency)
- **Age < 8 years**: $0 (no work needed)
- **Age 8-12 years**: $3,000 (potential repairs)
- **Age > 12 years**: $8,000 (replacement needed)

### Pool Equipment
If property has a pool:

- **Age unknown**: $5,000 (contingency)
- **Age < 5 years**: $0 (no work needed)
- **Age 5-10 years**: $3,000 (pump/filter replacement)
- **Age > 10 years**: $8,000 (full equipment overhaul)

### Plumbing/Electrical (by Build Year)
- **Built 2000+**: $0 (modern systems)
- **Built 1990-1999**: $2,000 (potential updates)
- **Built 1980-1989**: $5,000 (inspection/updates likely)
- **Built < 1980**: $10,000 (galvanized pipes, old wiring)

### Kitchen Updates
Only for older homes with neutral interior scores (default 95.0):

- **Built < 1990 AND score_interior = 95**: $15,000 (full update needed)
- **Otherwise**: $0 (modern or already updated)

## Files Generated

### 1. `renovation_gap_report.csv`
Detailed cost breakdown for all properties:
- List price, renovation costs by component
- Total renovation estimate
- True cost (list + renovation)
- Price delta percentage

### 2. `renovation_gap_report.html`
Interactive sortable table with:
- Color coding: Green (<5%), Yellow (5-10%), Red (>10%) price delta
- Bold border highlighting "Best True Value" property
- Summary statistics dashboard
- Click column headers to sort

### 3. `renovation_gap.py`
Python script that generates the reports. Can be re-run anytime with updated data.

## How to Use

### Run Full Analysis
```bash
python renovation_gap.py
```

### View Best Values
```bash
python show_best_values.py
```

### View Cost Breakdown
```bash
python cost_breakdown_analysis.py
```

### Open HTML Report
```bash
# Windows
start renovation_gap_report.html

# Mac/Linux
open renovation_gap_report.html
```

## Insights

### Data Quality Issues
- **95.7%** of properties lack roof/HVAC/pool age data
- Contingency costs ($8k roof, $4k HVAC, $5k pool) apply to most properties
- This adds ~$17k baseline to nearly all estimates

### Recommendations
1. **Prioritize inspections** for properties with high renovation estimates (>$30k)
2. **Request equipment ages** from sellers before making offers
3. **Budget for unknowns** - actual costs may vary ±30% from estimates
4. **Consider true cost** when comparing properties, not just list price

### Age Distribution Insights
- **56.5%** of PASSING properties built pre-1980 (need major plumbing/electrical work)
- **82.6%** need kitchen updates (built pre-1990 with neutral scores)
- Only **1 property** has known roof/HVAC ages (8426 E Lincoln Dr, Scottsdale)

## Next Steps

1. **Request Age Documentation**: For top candidates, ask sellers for:
   - Roof installation/replacement date
   - HVAC installation date and service records
   - Pool equipment age (pump, filter, heater)

2. **Professional Inspections**: Schedule comprehensive inspections for:
   - Roof condition assessment
   - HVAC performance testing
   - Plumbing/electrical systems (especially pre-1980 homes)
   - Pool equipment functionality

3. **Refine Estimates**: Update `enrichment_data.json` with actual ages and re-run analysis

4. **Negotiate**: Use renovation estimates to justify lower offers or request seller credits

## Notes

- All cost estimates are conservative mid-range values for Phoenix metro area
- Actual costs may vary based on:
  - Specific materials/brands chosen
  - Contractor rates
  - Permit requirements
  - Unexpected issues discovered during work
- This analysis does NOT include:
  - Cosmetic updates (paint, flooring, landscaping)
  - Major structural repairs
  - Foundation issues
  - Termite/pest remediation
  - Window/door replacements
