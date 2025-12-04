# What This System Does

### Core Functionality

1. **Multi-Source Data Integration**
   - Imports listing data from CSV (Zillow/Redfin exports)
   - Enriches with Maricopa County Assessor API data
   - Extracts images from listing sites using stealth automation
   - Integrates geographic data (schools, crime, flood zones, walkability)
   - Performs visual analysis of property images for interior quality assessment

2. **Kill-Switch Filtering** (Pass/Fail/Warning)
   - **Hard Criteria (Instant Fail):**
     - HOA fee > $0
     - Bedrooms < 4
     - Bathrooms < 2
   - **Soft Criteria (Severity Accumulation, threshold ≥3.0 fails):**
     - Septic system (not city sewer): +2.5 severity
     - Year built ≥2024: +2.0 severity
     - Garage < 2 spaces: +1.5 severity
     - Lot size outside 7k-15k sqft: +1.0 severity

3. **600-Point Weighted Scoring**
   - **Section A: Location & Environment (250 pts)**
     - School district (42pts), Quietness (30pts), Crime index (47pts)
     - Supermarket proximity (23pts), Parks/walkability (23pts)
     - Sun orientation (25pts), Flood risk (23pts), Walk/transit (22pts), Air quality (15pts)
   - **Section B: Lot & Systems (170 pts)**
     - Roof condition (45pts), Backyard utility (35pts)
     - Plumbing/electrical (35pts), Pool condition (20pts), Cost efficiency (35pts)
   - **Section C: Interior & Features (180 pts)**
     - Kitchen layout (40pts), Master suite (35pts), Natural light (30pts)
     - High ceilings (25pts), Fireplace (20pts), Laundry (20pts), Aesthetics (10pts)

4. **Tier Classification**
   - **Unicorn:** >480 points (80%+) - Exceptional properties
   - **Contender:** 360-480 points (60-80%) - Strong candidates
   - **Pass:** <360 points (<60%) - Meets minimums only

5. **Multi-Agent AI Pipeline**
   - Phase 0: County Assessor API data extraction
   - Phase 1: listing-browser (Haiku) + map-analyzer (Haiku) run in parallel
   - Phase 2: image-assessor (Sonnet) for visual scoring (requires Phase 1 complete)
   - Phase 3: Synthesis - scoring, tier assignment, kill-switch verdict
   - Phase 4: Report generation - deal sheets, visualizations, rankings
