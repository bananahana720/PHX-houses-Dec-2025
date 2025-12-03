# Market-Alpha: Financial Baseline Research Report

**Report Date:** December 2024
**Research Agent:** Claude Opus 4.5
**Project:** PHX Houses Analysis Pipeline

---

## Executive Summary

This research report establishes critical financial baselines for first-time homebuyer analysis in the Phoenix metropolitan area. Key findings include:

1. **Mortgage Rates:** Arizona's 30-year fixed rates (~6.19-6.44%) are marginally below the national average (~6.31%), with 2024 seeing a volatile range of 6.08% to 7.22%.

2. **HOA Reality Check:** With 31.1% of Arizona homes in HOAs (5th highest nationally) and average fees of $448/month (2nd highest nationally), a strict $0 HOA requirement eliminates significant inventory but remains achievable in Phoenix with ~1,600-2,800 listings available.

3. **Commute Costs:** AAA's 2024 data shows driving costs range from 59.24 cents/mile (small sedan) to $1.10/mile (half-ton pickup), with Phoenix-specific factors including lower rust but accelerated battery/AC wear.

---

## MKT-01: Current Phoenix Mortgage Rates

### Current Rate Snapshot (December 2024)

| Metric | Arizona | National | Difference |
|--------|---------|----------|------------|
| 30-Year Fixed | 6.19% | 6.31% | -0.12% (AZ lower) |
| 15-Year Fixed | 5.38% | N/A | - |

**[High Confidence]** - Based on Zillow, Bankrate, and Freddie Mac data.

### 6-Month Trend (July-December 2024)

| Period | Rate | Event |
|--------|------|-------|
| May 2, 2024 | **7.22%** | 2024 Peak |
| September 26, 2024 | **6.08%** | 2024 Low (post-Fed cut) |
| October 2024 | 6.43% | Monthly average |
| November 7, 2024 | 6.79% | Post-election volatility |
| Late November 2024 | 6.81% | End of month |
| December 1, 2024 | 6.19% | Current AZ rate |

**[High Confidence]** - Freddie Mac Primary Mortgage Market Survey data.

### Federal Reserve Context

The Federal Reserve cut rates three times in 2024:
- **September 2024:** First cut in 4 years (0.50%)
- **November 2024:** Second cut (0.25%)
- **December 2024:** Third cut (0.25%)

Despite these cuts, mortgage rates did not sustain decreases due to bond market dynamics and inflation expectations. The Fed funds rate ended 2024 at 4.25%-4.50%.

**[High Confidence]**

### 2025 Outlook

Experts forecast rates remaining between **6% and 7%** throughout 2025, though economic uncertainty could cause more dramatic movements.

**[Medium Confidence]** - Expert forecasts vary.

### Arizona-Specific Programs

First-time buyers in Phoenix/Maricopa County have access to:
- **Home Plus Program:** 30-year fixed-rate loan + up to 4% down payment assistance
- **Arizona Is Home:** Similar structure with competitive rates
- **Home in Five (Maricopa County):** Down payment assistance with competitive rates

**[High Confidence]**

---

## MKT-02: First-Time Buyer HOA Tolerance

### Phoenix HOA Landscape

| Metric | Value | Source |
|--------|-------|--------|
| % of AZ homes in HOA | **31.1%** | Phoenix Agent Magazine |
| National HOA rank | **5th highest** | Foundation for Community Association Research |
| Average monthly fee (AZ) | **$448** | DoorLoop/iPropertyManagement |
| National HOA rank (fees) | **2nd highest** | DoorLoop (behind Missouri at $469) |
| National median fee | $135 | U.S. Census Bureau |

**[High Confidence]**

### Is $0 HOA Realistic?

**Assessment: YES, but with reduced inventory**

| Data Point | Finding |
|------------|---------|
| Non-HOA listings in Phoenix | 1,599-2,782 homes available |
| Median price (non-HOA) | ~$470,000-$499,000 |
| Average days on market | 64-73 days |
| % of new construction with HOA | **80%** |
| % of existing homes with HOA | **38%** |

**Key Insight:** Non-HOA homes exist primarily in older neighborhoods. New construction in Arizona is overwhelmingly HOA-governed (80%). A $0 HOA requirement is **not** overly restrictive if targeting existing homes, but eliminates most new construction.

**[High Confidence]**

### Buyer Preferences on HOAs

| Survey Finding | Percentage | Source |
|----------------|------------|--------|
| Would prefer non-HOA in future | **70%** | Frontdoor 2024 Survey |
| Would not recommend HOA home | **63%** | Frontdoor 2024 Survey |
| Dislike their current HOA | **57%** | Rocket Mortgage 2023 |
| Feel HOA has too much power | **30%+** | Rocket Mortgage 2023 |
| Think HOA is fairly priced | **63%** | LendingTree 2024 |
| Think HOA is too expensive | **35%** | LendingTree 2024 |
| Experienced fee increases | **51%** | Frontdoor 2024 |

**[High Confidence]** - Multiple corroborating surveys.

### What HOA Fees Typically Cover in Phoenix

Based on Arizona HOA law and management resources:

**Standard Services:**
- Common area landscaping and maintenance
- Community pool maintenance and insurance
- Clubhouse/recreation center upkeep
- Walking trail maintenance
- Exterior lighting and irrigation
- Trash removal (sometimes)
- Master insurance policy

**Common Amenities:**
- Swimming pools
- Parks and green spaces
- Sports courts (tennis, pickleball)
- Dog parks
- Fitness centers
- Clubhouses

**[High Confidence]**

### Fee Distribution Analysis (National 2024)

| Monthly Fee Range | % of Households |
|-------------------|-----------------|
| Less than $50 | 26% (~5.6M homes) |
| $50-$500 | ~61% |
| Over $500 | 14% (~3M homes) |

**[High Confidence]** - U.S. Census Bureau 2024 data.

### Recommendation for PHX Houses System

**Current Setting:** $0 HOA (hard kill-switch)

**Assessment:** This is **appropriate** given:
1. 70% of surveyed buyers would prefer non-HOA
2. Arizona has 2nd-highest fees nationally ($448 avg)
3. Adequate non-HOA inventory exists (~2,000+ listings)
4. Fee increases are common (51% reported increases)
5. First-time buyers are particularly cost-sensitive

**Alternative Consideration:** If inventory becomes too restrictive, a tiered approach could be considered:
- $0-$50/month: Minor (1.0 severity)
- $51-$100/month: Moderate (2.0 severity)
- $101+/month: Significant (2.5+ severity)

**[Medium Confidence]** - Recommendation based on research synthesis.

---

## MKT-06: Commute Cost Per Mile

### AAA Your Driving Costs 2024 - Official Data

**Methodology:** 5-year ownership period, 75,000 total miles (15,000/year average)

#### Cost Per Mile by Vehicle Type

| Vehicle Category | Cost/Mile | Annual Cost (15K mi) | Examples |
|-----------------|-----------|---------------------|----------|
| Small Sedan | **59.24 cents** | $8,886 | Civic, Corolla, Elantra |
| Hybrid | **66.07 cents** | $9,911 | Various hybrid models |
| Subcompact SUV | **67.51 cents** | $10,127 | HR-V, Kona, Crosstrek |
| Medium Sedan | **70.38 cents** | $10,557 | Camry, Accord, Altima |
| Compact SUV | **71.04 cents** | $10,656 | RAV4, CR-V, Rogue |
| Mid-size Pickup | **82.44 cents** | $12,366 | Various mid-size trucks |
| Medium SUV | **83.84 cents** | $12,576 | Explorer, Highlander |
| Half-Ton Pickup | **$1.10** | $16,500 | Full-size trucks |

**[High Confidence]** - Official AAA 2024 data.

#### Cost Component Breakdown

| Component | Rate/Cost | Notes |
|-----------|-----------|-------|
| Maintenance, Repair & Tires | **10.13 cents/mile** | Includes extended warranty, replacement tires |
| Fuel | ~15 cents/mile | Based on $3.999/gallon (May 2024 average) |
| License, Registration & Taxes | **$815/year** | National average |
| Insurance | Varies by vehicle | Pickups lowest, sedans moderate |
| Depreciation | Largest component | Varies significantly by vehicle type |
| Finance | Based on 5-yr loan | 15% down, national avg rate |

**[High Confidence]**

### Phoenix-Specific Vehicle Factors

**Accelerated Wear (Negative):**
| Component | Impact | Cost Implication |
|-----------|--------|------------------|
| Battery | 30-50% shorter lifespan | Replace 1-2 years earlier ($150-$300) |
| A/C System | Runs 6+ months/year at high load | Annual service recommended (~$150) |
| Tires | Hot asphalt increases wear | May need replacement 10-15% sooner |
| Rubber seals/hoses | Dry rot from heat | More frequent replacement |
| Engine oil | Breaks down faster | More frequent changes (recommend severe schedule) |
| Interior | Dashboard/upholstery degradation | Cosmetic, affects resale |

**Reduced Wear (Positive):**
| Component | Impact | Cost Savings |
|-----------|--------|--------------|
| Body rust | Virtually none (low humidity) | Significant long-term savings |
| Undercarriage corrosion | No road salt | Extended component life |
| Brake rotors | Less moisture-related wear | Longer service intervals |

**[Medium Confidence]** - Based on Arizona automotive specialist insights, not quantified studies.

#### Phoenix-Adjusted Cost Estimate

**Baseline (AAA National):** 59.24-71.04 cents/mile (sedan to compact SUV range)

**Phoenix Adjustment:** +5-10% for accelerated A/C and battery wear

**Recommended PHX Rate:** **62-78 cents/mile** depending on vehicle type

**[Medium Confidence]** - Extrapolated from qualitative data.

### Phoenix Fuel Costs 2024

| Period | Phoenix Price | National Context |
|--------|---------------|------------------|
| January 2024 | ~$3.27/gallon | Post-holiday baseline |
| April 2024 | $4.27/gallon | 65 cents above national avg |
| September 2024 | $3.40/gallon | Summer decline |
| December 2024 | $3.08/gallon | Year-end low |

**2024 Average:** Approximately **$3.50/gallon** (slightly above national)

**[High Confidence]** - GasBuddy and EIA data.

### IRS Standard Mileage Rate (Reference)

| Year | Business Rate | Notes |
|------|---------------|-------|
| 2024 | **67 cents/mile** | Used for tax deductions |
| 2025 | **70 cents/mile** | 3-cent increase |

**Note:** IRS rate is a reasonable proxy for actual vehicle costs but may underestimate for Phoenix due to climate factors.

**[High Confidence]**

### Phoenix Commute Context

| Metric | Value | Source |
|--------|-------|--------|
| Average commute time | 26 minutes | National average |
| Average 6-mile drive time | 10.4 minutes | TomTom 2024 |
| Rush hour time lost annually | 31 hours | TomTom 2024 |
| National traffic ranking | 69th slowest (of 93) | TomTom 2024 |
| Average daily travel (national) | 42 miles | Replica data |

Phoenix has **better than average** traffic conditions compared to similar-sized metros.

**[High Confidence]**

---

## Data Tables Summary

### Quick Reference: Key Numbers

| Metric | Value | Confidence |
|--------|-------|------------|
| AZ 30-yr fixed rate | 6.19% | High |
| National 30-yr fixed rate | 6.31% | High |
| AZ homes in HOA | 31.1% | High |
| Average AZ HOA fee | $448/month | High |
| Non-HOA listings (Phoenix) | ~2,000+ | Medium |
| Small sedan cost/mile | 59.24 cents | High |
| Compact SUV cost/mile | 71.04 cents | High |
| Phoenix gas (Dec 2024) | $3.08/gallon | High |
| IRS 2024 mileage rate | 67 cents/mile | High |

### Scoring System Impact Assessment

| Research Item | Current PHX System | Recommendation |
|---------------|-------------------|----------------|
| Mortgage Rates | Not directly scored | Use for cost efficiency calculations |
| HOA Kill-Switch ($0) | HARD fail | **Maintain** - well-supported by buyer preferences |
| Commute Costs | Used in cost efficiency | Update to 65-70 cents/mile baseline |

---

## Recommendations for PHX Houses System

### 1. Mortgage Rate Integration
- Current Arizona rates (~6.19%) should be used for monthly payment calculations
- Consider flagging properties when rates exceed 7% threshold
- Factor in down payment assistance programs for first-time buyer scoring

### 2. HOA Policy Validation
**CONFIRM: $0 HOA as HARD kill-switch is appropriate**
- Strongly supported by buyer preference data (70% would avoid)
- Adequate inventory exists in Phoenix market
- High average fees ($448) make any HOA a significant cost burden

### 3. Commute Cost Updates
**Current system should use:**
- **Primary baseline:** 67 cents/mile (IRS 2024 rate)
- **Conservative baseline:** 70 cents/mile (2025 IRS rate, accounts for Phoenix factors)
- **Vehicle-specific:** Reference AAA table for detailed analysis

### 4. Data Refresh Schedule
| Data Point | Refresh Frequency | Source |
|------------|------------------|--------|
| Mortgage rates | Weekly | Freddie Mac PMMS |
| Gas prices | Monthly | GasBuddy/EIA |
| HOA statistics | Annually | Census Bureau |
| Driving costs | Annually | AAA Your Driving Costs |

---

## Sources

### Mortgage Rates (MKT-01)
- [Bankrate - Arizona Mortgage Rates](https://www.bankrate.com/mortgages/mortgage-rates/arizona/)
- [Zillow Home Loans - Arizona](https://www.zillow.com/homeloans/mortgage-rates/arizona/)
- [Freddie Mac PMMS](https://www.freddiemac.com/pmms)
- [Freddie Mac Research - December 2024 Outlook](https://www.freddiemac.com/research/forecast/20241220-us-economy-remains-robust-with-strong-q3-growth)
- [FRED - 30-Year Fixed Rate Mortgage Average](https://fred.stlouisfed.org/series/MORTGAGE30US)
- [Mortgage News Daily - 30-Year Fixed](https://www.mortgagenewsdaily.com/mortgage-rates/30-year-fixed)
- [The Mortgage Reports - Rate History](https://themortgagereports.com/61853/30-year-mortgage-rates-chart)

### HOA Data (MKT-02)
- [Phoenix Agent Magazine - Arizona HOA Statistics](https://phoenixagentmagazine.com/2023/04/21/nearly-one-third-of-arizona-homes-are-part-of-an-hoa-among-the-highest-percentages-in-the-nation/)
- [U.S. Census Bureau - HOA Fees 2024](https://www.census.gov/library/stories/2025/09/condo-hoa-fees.html)
- [AZ Family - Arizona HOA Fees Study](https://www.azfamily.com/2024/02/29/study-shows-arizona-ranks-among-most-expensive-hoas-country/)
- [NAR - 2024 Profile of Home Buyers and Sellers](https://www.nar.realtor/research-and-statistics/research-reports/highlights-from-the-profile-of-home-buyers-and-sellers)
- [LendingTree HOA Survey 2024](https://www.lendingtree.com/home/mortgage/hoa-survey/)
- [Frontdoor - HOA Survey 2024](https://www.frontdoor.com/blog/real-estate/pros-and-cons-of-hoa-what-homeowners-really-think)
- [Rocket Mortgage - Assessing the Association](https://www.rocketmortgage.com/learn/assessing-the-association)
- [CNBC - Rise of HOAs](https://www.cnbc.com/2024/12/02/heres-what-the-rise-of-homeowners-associations-means-for-buyers.html)
- [Redfin - Phoenix No HOA Listings](https://www.redfin.com/city/14240/AZ/Phoenix/amenity/no+hoa+fees)
- [AZ and Associates - HOAs in Phoenix](https://www.azandassociates.com/blog/hoas-in-phoenix-az-what-homebuyers-need-to-know-in-2025/)

### Commute Costs (MKT-06)
- [AAA Your Driving Costs 2024 Fact Sheet](https://newsroom.aaa.com/wp-content/uploads/2024/09/YDC_Fact-Sheet-FINAL-9.2024.pdf)
- [AAA Your Driving Costs 2024 Brochure](https://newsroom.aaa.com/wp-content/uploads/2024/08/YDC-Brochure-FINAL-9.2024.pdf)
- [AAA Newsroom - 2025 Cost Update](https://newsroom.aaa.com/2025/09/aaa-new-vehicle-costs-drop-to-11577/)
- [AAA Driving Costs Calculator](https://www.aaa.com/autorepair/drivingcosts)
- [IRS Standard Mileage Rates](https://www.irs.gov/tax-professionals/standard-mileage-rates)
- [IRS Notice 2024-08](https://www.irs.gov/pub/irs-drop/n-24-08.pdf)

### Phoenix-Specific Data
- [Kelly Clark Automotive - Arizona Heat Effects](https://www.kellyclark.com/how-does-the-heat-affect-my-car/)
- [Arizona Car Sales - Climate Impact on Vehicles](https://www.arizona.cars/blog/the-impact-of-arizonas-climate-on-vehicle-lifespan-what-buyers-should-know/)
- [Axios Phoenix - Gas Prices 2024](https://www.axios.com/local/phoenix/2024/04/22/gas-price-increase)
- [Axios Phoenix - Traffic Ranking](https://www.axios.com/local/phoenix/2025/01/16/phoenix-traffic-rush-hour-ranking)
- [AZMAG - Commute Shed Reports 2024](https://azmag.gov/Portals/0/Maps-Data/Commute-Shed-Reports/Phoenix_Text-only.pdf)
- [TomTom Traffic Index](https://www.tomtom.com/traffic-index/)

---

*Report generated for PHX Houses Analysis Pipeline - December 2024*
