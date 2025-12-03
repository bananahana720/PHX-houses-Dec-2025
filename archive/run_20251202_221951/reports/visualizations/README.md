# Phoenix Home Analysis - Interactive Visualizations
**Generated:** December 1, 2025 | **Data Last Updated:** December 1, 2025

This directory contains interactive HTML visualizations for analyzing Phoenix-area home listings against buyer criteria.

---

## Files Overview

### 1. value_spotter.html (4.6 MB)
**Interactive Scatter Plot: Price vs. Score**

Identifies undervalued properties by comparing total score (Y-axis) against price (X-axis).

#### Key Features:
- **X-Axis:** Total Score (0-500 points)
- **Y-Axis:** Price ($400k-$850k range)
- **Point Size/Color:** Lot size (7,000-15,000 sqft)
- **Point Markers:**
  - Circles = PASS (meets all kill-switch criteria)
  - X marks = FAIL (see hover for reason)
- **Value Zone:** Green shaded area (bottom-right: high score, low price)
- **Top Picks:** Gold star annotations highlighting the 3 best value properties
- **Reference Lines:** Median price and score for context

#### Interactive Features:
- Hover over any point to see full property details
- Click legend items to toggle PASS/FAIL properties
- Zoom in/out using scroll or buttons
- Pan across the chart
- Download as PNG using camera icon

#### How to Use:
Look for properties in the **green value zone** (bottom-right quadrant):
- High scores (350+)
- Low prices (<$550k)
- This combination = best value for money

---

### 2. radar_comparison.html (4.6 MB)
**5-Dimensional Radar Comparison of Top 3 Properties**

Compare the top 3 ranked properties across 5 key dimensions.

#### Properties Compared:
1. **4417 W Sandra Cir, Glendale, AZ** - $354,000 (Rank #1)
2. **2353 W Tierra Buena Ln, Phoenix, AZ** - $499,900 (Rank #2)
3. **4732 W Davis Rd, Glendale, AZ** - $475,000 (Rank #4)

#### 5 Radar Dimensions (all normalized 0-10):
- **Location:** School quality, safety, walkability, amenities (max 250 pts → 10)
- **Lot & Systems:** Roof, HVAC, plumbing, pool condition (max 160 pts → 10)
- **Interior:** Kitchen, master suite, lighting, finishes (max 190 pts → 10)
- **Schools:** District rating directly (already 0-10 scale)
- **Price Value:** Inverted pricing (lower price = higher score, 0-10)

#### Interactive Features:
- Hover over axes to see exact scores
- Click legend to toggle properties on/off
- Overlapping semi-transparent fills show comparative strengths
- Analysis box below chart with key insights

#### How to Interpret:
- **Large coverage area** = well-rounded property
- **Peaks in certain directions** = specialized strengths
- **Balanced shapes** = consistent quality across dimensions

---

## Data Summary

### Dataset Composition
- **Total Properties:** 35
- **Passing Kill-Switches:** 23 (65.7%)
- **Failing Kill-Switches:** 12

### Buyer Kill-Switch Criteria (must pass ALL)
- NO HOA fees
- City sewer (not septic)
- 2+ car garage
- 4+ beds, 2+ baths
- Lot: 7,000-15,000 sqft
- Built before 2024 (no new construction)

### Value Zone Properties
**Score > 365 AND Price < $550,000 (PASS only)**
- 3 properties meet these ultra-competitive criteria
- These represent the absolute best value opportunities

### Top Value Picks
| Rank | Address | Price | Score | Ratio |
|------|---------|-------|-------|-------|
| 1 | 4417 W Sandra Cir, Glendale | $415k | 389.0 | 0.937 pts/$1k |
| 2 | 16814 N 31st Ave, Phoenix | $400k | 340.5 | 0.851 pts/$1k |
| 3 | 5522 W Carol Ave, Glendale | $442k | 352.5 | 0.798 pts/$1k |

---

## Scoring System

### Total Score: 600 Points Maximum

#### Section A: Location (250 pts)
- School district quality: 50 pts
- Neighborhood safety: 50 pts
- Quiet/low-traffic area: 50 pts
- Grocery store proximity: 40 pts
- Parks & recreation: 30 pts
- Sun exposure/orientation: 30 pts

#### Section B: Lot & Systems (160 pts)
- Roof condition/age: 50 pts
- Backyard potential: 40 pts
- Plumbing system: 40 pts
- Pool status/condition: 30 pts

#### Section C: Interior (190 pts)
- Kitchen quality: 40 pts
- Master suite: 40 pts
- Natural lighting: 30 pts
- Ceiling height/quality: 30 pts
- Fireplace presence: 20 pts
- Laundry arrangement: 20 pts
- Aesthetic appeal: 10 pts

### Tier Classification
- **Unicorn:** 480+ points (exceptional, rare)
- **Contender:** 360-480 points (strong candidates)
- **Pass:** 300-360 points (acceptable fallback)

---

## How to Use These Visualizations

### For Finding Opportunities
1. **Start with Value Spotter**
   - Look for points in the green value zone
   - Check top 3 gold-starred properties
   - Hover to see details

2. **Deep Dive with Radar**
   - Compare the top 3 across all dimensions
   - Identify which property best matches YOUR priorities
   - See detailed score breakdowns

### For Decision Making
1. **Identify candidates** → Value Spotter
2. **Compare finalists** → Radar Comparison
3. **Review specific details** → Hover tooltips
4. **Next step** → Schedule inspections for top picks

### Data Interpretation

#### Value Ratio (Points/$1,000)
- Higher = better value (more points per dollar spent)
- Top pick: 0.937 is excellent (1 point per $1,066 spent)
- Useful for: Budget-conscious buyers

#### Radar Balance
- Balanced shape = consistent quality across all areas
- Peaked shape = specialized strengths/weaknesses
- Use to identify: Properties with your desired focus

#### Location Scores
- 7.4+/10 = excellent neighborhood
- 7.0-7.4 = very good area
- 6.5-7.0 = good area
- <6.5 = acceptable but less developed

---

## Technical Details

### Data Sources
- **Scoring:** Multi-criteria analysis of listing data, county records, and research
- **Properties:** Phoenix metro area listings, December 2025
- **Scoring Date:** December 1, 2025

### Browser Compatibility
- Works in all modern browsers (Chrome, Firefox, Safari, Edge)
- No plugins required
- Fully self-contained (data embedded in HTML)
- Works offline (no internet needed)

### File Sizes
- value_spotter.html: 4.6 MB (includes all plot data)
- radar_comparison.html: 4.6 MB (includes all property data)

### Technology Stack
- **Visualization:** Plotly.js (interactive charts)
- **Data:** Embedded JSON arrays
- **Styling:** Plotly built-in themes

---

## Key Insights

### The Clear Winner: 4417 W Sandra Cir, Glendale, AZ 85308

**Why it stands out:**
- Highest score (389.0) among all passing properties
- Lowest price ($354,000) in value zone
- Best value ratio (0.937 pts/$1k)
- Excellent location (7.44/10)
- Strong schools (8.4/10)
- Meets all buyer criteria comfortably

**Recommendation:** Schedule inspection immediately if interested

### Market Characteristics
- **Value Leaders:** West Valley (Glendale, Peoria) offers best value
- **Premium Areas:** Scottsdale/East Valley command price premiums
- **Interior Consistency:** All scoring properties show strong interior standards
- **Lot Availability:** Larger lots (>10k sqft) are premium amenities

### Buyer Alignment
- All 23 passing properties meet strict buyer criteria
- 3 properties offer exceptional value (>365 score, <$550k)
- Most cluster around $450k-$550k price range
- Age range 1957-1997 shows solid age diversity

---

## Next Steps

1. **Review both visualizations** to identify candidates
2. **Schedule inspections** for top 3-5 value picks
3. **Verify details** in person (especially interior condition)
4. **Run numbers** on financing options for finalists
5. **Make offer** on the best match for your criteria

---

## Questions About the Data?

- **Scoring methodology:** See `docs/artifacts/VALUE_SPOTTER_RADAR_UPDATE.md`
- **Kill-switch criteria:** See `CLAUDE.md` in project root
- **Full property list:** See `scripts/phx_homes_ranked.csv`
- **Enrichment data:** See `scripts/enrichment_data.json`

---

**Last Updated:** December 1, 2025 at 12:11 UTC
**Data Snapshot:** 35 properties analyzed, 23 passing, 3 in value zone
