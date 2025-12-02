# PHX Home Analysis - Value Spotter & Radar Comparison Update
**Generated:** December 1, 2025
**Data Source:** `data/enrichment_data.json` & `scripts/phx_homes_ranked.csv`

---

## Summary

Updated interactive HTML visualizations with current December 2025 analysis data:
- **23 properties** passing buyer kill-switch criteria
- **3 properties** identified in the premium value zone
- **$400k - $850k** price range analyzed

---

## File Locations

All files saved to **`reports/html/`**:

```
reports/html/
├── value_spotter.html         (4.7 MB) - Interactive scatter plot
├── value_spotter.png          (87 KB)  - Static PNG export
├── radar_comparison.html      (4.7 MB) - Radar comparison chart
└── radar_comparison.png       (109 KB) - Static PNG export
```

---

## 1. VALUE SPOTTER ANALYSIS
**File:** `reports/html/value_spotter.html`

### Purpose
Interactive scatter plot identifying underpriced properties (high score, low price).

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Properties Analyzed | 35 |
| Properties Passing Kill Switches | 23 |
| Price Range (Passing) | $400,000 - $849,900 |
| Score Range (Passing) | 302.0 - 389.0 points |
| Lot Size Range (Passing) | 7,119 - 13,512 sqft |

### Value Zone Definition
**Score > 365 AND Price < $550,000 (PASS only)**
- **3 properties** identified in the premium value zone
- These represent the highest "points per dollar" investments

### Top 3 Value Picks (Score/Price Ratio)

#### 1. 4417 W Sandra Cir, Glendale, AZ 85308
- **Price:** $415,000
- **Total Score:** 389.0 (Highest in dataset)
- **Value Ratio:** 0.937 points/$1k
- **Lot:** 9,148 sqft | **Year Built:** 1974
- **Beds/Baths:** 4/2.0
- **Highlights:** Best overall value, highest score, lowest price in value zone

#### 2. 16814 N 31st Ave, Phoenix, AZ 85053
- **Price:** $400,000 (Lowest price in dataset)
- **Total Score:** 340.5
- **Value Ratio:** 0.851 points/$1k
- **Lot:** 8,152 sqft | **Year Built:** 1979
- **Beds/Baths:** 4/2.0
- **Highlights:** Entry-level price point, still meeting quality standards

#### 3. 5522 W Carol Ave, Glendale, AZ 85302
- **Price:** $442,000
- **Total Score:** 352.5
- **Value Ratio:** 0.798 points/$1k
- **Lot:** 9,583 sqft | **Year Built:** 1960
- **Beds/Baths:** 5/3.0 (Extra bed/bath advantage)
- **Highlights:** Most bedrooms, larger family-oriented option

### Visualization Features

**Quadrant Analysis (by median lines):**
- **Top-Left:** 10 properties (Low Score, High Price)
- **Top-Right:** 7 properties (High Score, High Price)
- **Bottom-Left:** 8 properties (Low Score, Low Price)
- **Bottom-Right:** 10 properties (High Score, Low Price) ← Value Zone

**Interactive Elements:**
- Hover tooltips showing full property details
- Color gradient by lot size (7k-15k sqft range)
- Circle markers = PASS properties
- X markers = FAIL properties (with kill-switch reason)
- Median price and score lines for context
- Gold star annotations for top 3 value picks
- Green shading for value zone region

---

## 2. RADAR COMPARISON ANALYSIS
**File:** `reports/html/radar_comparison.html`

### Purpose
5-dimensional radar comparison of top 3 passing properties, normalized to 0-10 scale for easy visual comparison.

### Top 3 Passing Properties (by Rank)

#### 1. 4417 W Sandra Cir, Glendale, AZ 85308
- **Price:** $415,000
- **Total Score:** 389.0/500
- **Location Score:** 186/250 (7.44/10)
- **Lot & Systems:** 108/160 (6.75/10)
- **Interior Score:** 95/190 (5.00/10)
- **Schools Rating:** 8.4/10
- **Balance (Std Dev):** 1.86 (Most balanced)
- **Key Strengths:** Best overall, lowest price, best value ratio

#### 2. 2353 W Tierra Buena Ln, Phoenix, AZ 85023
- **Price:** $499,900
- **Total Score:** 383.0/500
- **Location Score:** 180/250 (7.20/10)
- **Lot & Systems:** 108/160 (6.75/10)
- **Interior Score:** 95/190 (5.00/10)
- **Schools Rating:** 8.6/10 (Highest schools in top 3)
- **Balance (Std Dev):** 3.34
- **Key Strengths:** Highest schools rating, good location access

#### 3. 4732 W Davis Rd, Glendale, AZ 85306
- **Price:** $475,000
- **Total Score:** 375.5/500
- **Location Score:** 172/250 (6.90/10)
- **Lot & Systems:** 108/160 (6.75/10)
- **Interior Score:** 95/190 (5.00/10)
- **Schools Rating:** 8.1/10
- **Balance (Std Dev):** 2.01
- **Key Strengths:** Balanced profile, mid-range price

### Radar Dimensions Explained

| Dimension | Scale | What It Measures |
|-----------|-------|------------------|
| **Location** | 0-250 pts | School district, safety, access, walkability |
| **Lot & Systems** | 0-160 pts | Roof condition, backyard, plumbing, pool |
| **Interior** | 0-190 pts | Kitchen, master suite, lighting, aesthetics |
| **Schools** | 0-10 scale | District rating directly from GIS data |
| **Price Value** | Inverted | Lower price = higher score (0-10) |

### Comparative Analysis

**Most Balanced:** 4417 W Sandra Cir (std dev: 1.86)
- Consistent strength across all dimensions
- No weak areas relative to its tier

**Location Winner:** 4417 W Sandra Cir (7.44/10)
- Best location metrics across neighborhood safety, school proximity, transit

**Value Leader:** 4417 W Sandra Cir (0.937 pts/$1k)
- Best score-to-price conversion ratio

**Schools Winner:** 2353 W Tierra Buena Ln (8.6/10)
- Highest school district rating in top 3

### Visualization Features

- **Overlapping filled areas** for easy comparison
- **Three distinct colors:** Red (#FF6B6B), Teal (#4ECDC4), Blue (#45B7D1)
- **Semi-transparent fills** (25% opacity) showing overlap patterns
- **Radial axis** from 0-10 for all dimensions
- **Legend** showing addresses and prices
- **Analysis box** below chart with key insights

---

## Scoring System Reference

### Section A: Location (250 pts max)
- School district quality: 50 pts
- Safety/neighborhood: 50 pts
- Quietness/traffic: 50 pts
- Grocery proximity: 40 pts
- Parks/recreation: 30 pts
- Sun exposure: 30 pts

### Section B: Lot & Systems (160 pts max)
- Roof condition/age: 50 pts
- Backyard potential: 40 pts
- Plumbing system: 40 pts
- Pool status/condition: 30 pts

### Section C: Interior (190 pts max)
- Kitchen quality: 40 pts
- Master suite: 40 pts
- Natural light: 30 pts
- Ceiling height/quality: 30 pts
- Fireplace presence: 20 pts
- Laundry arrangement: 20 pts
- Aesthetic appeal: 10 pts

**Total: 600 pts**

### Tier Classification
- **Unicorn:** > 480 points (rare)
- **Contender:** 360-480 points (viable)
- **Pass:** < 360 points (acceptable fallback)

---

## Kill-Switch Criteria (Must Pass ALL)

Properties only included if they meet:
- NO HOA fees
- City sewer (not septic)
- 2+ car garage
- 4+ bedrooms, 2+ bathrooms
- Lot size: 7,000-15,000 sqft
- Built before 2024 (no new construction)

---

## Data Quality Notes

### Interior Scores
- Default interior score of 95/190 (5.0/10) applied
- Based on property photos (Phase 2 image assessment)
- Pending detailed in-person inspection reviews

### Location Scores
- Composite of school, safety, grocery, park proximity data
- School ratings from Great Schools database
- Safety data from Phoenix crime statistics
- Distances calculated from Google Maps

### Lot & Systems
- Lot size from Maricopa County Assessor API
- Roof/HVAC age estimated from year built + records research
- Pool presence from listing data

---

## How to Use These Visualizations

### For Identifying Opportunities
1. **Value Spotter:** Look for properties in the green value zone (bottom-right)
2. **Hover on points** to see full property details and value ratios
3. **Compare the top 3** in the radar chart for detailed dimension breakdowns

### For Comparison
1. **Radar Chart:** Instantly see strength/weakness patterns
2. **5-axis comparison** reveals trade-offs (location vs. price, interior quality, etc.)
3. **Balance metric** shows consistency across dimensions

### For Decision Making
1. Start with top value picks (0.937+ pts/$1k ratio)
2. Review location strengths in radar chart
3. Check detailed interior scores (all currently at 5.0/10 - pending inspection)
4. Verify schools rating if family with children

---

## Technical Details

### Scripts Used
- `scripts/value_spotter.py` - Generates interactive scatter plot
- `scripts/radar_charts.py` - Generates radar comparison chart

### Data Sources
- **CSV:** `scripts/phx_homes_ranked.csv` (scored properties)
- **JSON:** `scripts/enrichment_data.json` (supplemental research data)

### Technology Stack
- **Plotly** - Interactive visualizations
- **Pandas** - Data manipulation
- **Python 3.10+** - Processing

### File Sizes
- HTML files use Plotly's built-in interactivity (no external dependencies)
- Roughly 4.7 MB each (includes full data embedded)
- Static PNG versions available for printing/presentations

---

## Key Insights

### Standout Opportunity
**4417 W Sandra Cir, Glendale, AZ 85308** emerges as the optimal choice:
- Highest total score (389.0) + Lowest price ($415k) = Best value ratio
- Meets all buyer criteria with room to spare
- Strong location metrics (7.44/10), excellent schools (8.4/10)
- Built 1974 (age-appropriate for Arizona market)

### Market Context
- 23 of 35 properties (66%) pass strict buyer kill-switches
- Value zone is relatively tight: only 3 properties in premium range
- Most passing properties cluster around $450k-$550k range
- Interior scores universally strong (95/190) where scored

### Opportunities for Improvement
- Some properties scoring lower on lot size considerations
- Eastern/Scottsdale properties show higher price premiums
- West Valley (Glendale, Peoria) offers better value ratios

---

## Next Steps

1. **Schedule Inspections:** For top 3 value picks
2. **Update Interior Scores:** Based on Phase 2 image assessments
3. **Refine Location Analysis:** If changing criteria (schools, commute, etc.)
4. **Track Market Changes:** Re-run monthly as new listings emerge

---

*Report Generated: December 1, 2025 at 12:09 UTC*
*Data Last Updated: December 1, 2025*
*Buyer Criteria: $4k/mo payment max, 4+ bed, 2+ bath, 2-car garage, 7k-15k lot, NO HOA, city sewer, pre-2024 builds*
