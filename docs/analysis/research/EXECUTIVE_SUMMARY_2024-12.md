# Executive Research Summary: PHX Houses Analysis Pipeline

**Report Date:** December 2024
**Synthesis Agent:** Claude Opus 4.5
**Research Campaign:** 9 Domain Reports (Market x3, Domain x3, Technical x3)
**Purpose:** Strategic intelligence for first-time homebuyer property analysis in Phoenix metropolitan area

---

## 1. Strategic Overview

### What This Research Campaign Discovered

This comprehensive research campaign validated, refined, and expanded the PHX Houses Analysis Pipeline through systematic investigation across three domains:

**Market Intelligence:** Confirmed the Phoenix metro housing market remains accessible for first-time buyers despite 54.6% appreciation since 2020. The $0 HOA requirement is well-supported by data (70% buyer preference, $448/month average fees). A critical finding emerged: **solar leases represent a significant hidden liability** (3-8% value reduction) affecting 75% of Phoenix solar installations.

**Domain Intelligence:** Arizona's extreme climate reduces building system lifespans by 20-40% versus national averages. HVAC units last 8-15 years (not 20+), requiring scoring recalibration. The 2023 groundwater moratorium has created a **two-tier property market** - properties in Designated Assured Water Supply (DAWS) areas have secure long-term value, while outlying areas face development restrictions and uncertainty.

**Technical Intelligence:** The pipeline's current technical architecture (nodriver + curl_cffi + residential proxies) aligns well with Q4 2024 anti-bot requirements. Multiple free government APIs are available for integration (FEMA NFHL for flood zones, Maricopa County Assessor, Phoenix Open Data for crime). Task queue architecture (RQ) is appropriate for current scale.

### Key Themes Across All Three Domains

| Theme | Finding | Confidence | Pipeline Impact |
|-------|---------|------------|-----------------|
| **Arizona Climate Premium** | 20-40% accelerated system degradation | High | Recalibrate HVAC/roof scoring |
| **Solar Lease Liability** | 75% leased, 3-8% value loss | High | Add as kill-switch criterion |
| **Water Security Bifurcation** | DAWS vs non-DAWS creates two markets | High | Add location-based warning |
| **HOA Avoidance Validated** | 70% buyer preference, $448 avg fee | High | Maintain $0 requirement |
| **4-Bedroom Not Restrictive** | 32% market share, multigenerational trend | High | Maintain 4+ requirement |
| **Pool Cost Burden** | $250-400/month comprehensive | Medium | Add to cost projections |
| **Septic Risk Undervalued** | 10%+ failure rate in AZ | High | Elevate sewer preference |

### Overall Confidence Assessment

| Domain | Reports | High Confidence | Medium Confidence | Low Confidence |
|--------|---------|-----------------|-------------------|----------------|
| Market | 3 | 85% of findings | 12% | 3% |
| Regulatory/Domain | 3 | 78% of findings | 18% | 4% |
| Technical | 3 | 72% of findings | 23% | 5% |
| **Weighted Average** | **9** | **78%** | **18%** | **4%** |

**Assessment:** The research campaign achieved strong data quality. Low-confidence items primarily relate to future predictions (rate forecasts, appreciation projections) and unpublished pricing (enterprise API costs).

---

## 2. Market Intelligence Summary

### Phoenix Real Estate Market Position for First-Time Buyers

**Current Market State (December 2024):**

| Metric | Value | Trend | Source |
|--------|-------|-------|--------|
| Median Home Price | $453,000 | +54.6% since Jan 2020 | Zillow |
| 30-Year Fixed Rate (AZ) | 6.19% | Below national avg (6.31%) | Freddie Mac |
| Non-HOA Inventory | 1,600-2,800 listings | Adequate | Redfin/Zillow |
| Days on Market (Non-HOA) | 64-73 days | Normal | MLS Data |
| Population Growth | +80,000 in 2024 | Sustained | City of Phoenix |
| Job Growth | +52,400 YTD (2.2%) | Above national (1.3%) | Economic Indicators |

**Market Accessibility:** Phoenix remains accessible for first-time buyers seeking non-HOA properties. The $0 HOA requirement reduces inventory by ~31% but adequate listings exist, primarily in established neighborhoods with existing homes.

**Warning Sign:** 86.9% of Phoenix-area homes reportedly lost value between November 2024 and October 2025, indicating potential market correction. However, this conflicts with other sources showing 3-5% appreciation, suggesting measurement methodology differences.

### Financial Baseline Validation

| Factor | Research Finding | Current System | Recommendation |
|--------|------------------|----------------|----------------|
| **Mortgage Rate** | 6.19% AZ, 6.31% national | Not directly scored | Use for affordability calculations |
| **HOA Costs** | $448/month average (2nd highest nationally) | $0 HARD kill | VALIDATED - maintain |
| **Commute Cost** | 65-70 cents/mile (IRS basis) | Used in cost efficiency | Update to 70 cents/mile |
| **Pool Ownership** | $250-400/month comprehensive | Not fully modeled | ADD $300/month cost factor |
| **Solar Lease** | -3% to -8% home value | Not in system | ADD as HARD kill-switch |
| **Owned Solar** | +4.1% to +6.9% home value | Not scored | ADD +5 pts bonus |

### Pool Economics Deep Dive

**Annual Cost Breakdown (Phoenix):**

| Category | DIY | Professional | Full Service |
|----------|-----|--------------|--------------|
| Service/Maintenance | $996 | $1,500 | $2,400 |
| Electricity | $360 | $720 | $1,200 |
| Water (evaporation) | $240 | $420 | $600 |
| Chemicals | $240 | $400 | $660 |
| Equipment Reserve | $300 | $600 | $1,200 |
| **Annual Total** | **$2,136** | **$3,640** | **$6,060** |
| **Monthly Equivalent** | **$178** | **$303** | **$505** |

**Arizona Advantage:** No winterization costs ($450+ savings vs. northern climates).

**Scoring Impact:** Properties with pools should have $300-400/month added to cost efficiency calculations.

### Solar Lease Crisis

**Critical Finding:** Solar leases represent a major hidden liability in the Phoenix market.

| Factor | Leased Solar | Owned Solar |
|--------|--------------|-------------|
| Home Value Impact | -3% to -8% | +4.1% to +6.9% |
| Monthly Cost | $100-200+ (escalating) | $0 (after payoff) |
| Federal Tax Credit | Company keeps (30%) | Homeowner claims |
| Transfer Process | Complex, buyer credit required | Simple |
| Phoenix Prevalence | **75%** of installations | 25% |

**Escalator Risk:** Most solar leases include 2-3% annual payment increases over 20-25 year terms. Example: $100/month starting payment becomes $203/month by year 20.

**Industry Instability:** 100+ solar companies have gone bankrupt since 2023, including SunPower (2024), creating warranty and service uncertainty.

**Recommendation:** Add solar lease as HARD kill-switch due to:
- Direct 3-8% value reduction
- Transfer complications (buyer must pass credit check)
- Escalating payment burden
- Industry bankruptcy risk
- No appraisal value inclusion

### Buyer Demographic Insights

**First-Time Buyer Profile (2024):**
- Average age: **38 years old** (oldest on record since 1981)
- Typical home purchased: 3 bedrooms, 2 bathrooms, 1,900 sq ft
- 17% purchased multigenerational homes (all-time high)
- 40% of millennials plan to stay 16+ years ("forever home" trend)

**4-Bedroom Demand Validation:**
- 32.4% of new construction is 4-bedroom
- Multigenerational housing at all-time high supports larger home demand
- Arizona household size (2.51) above national average
- West South Central region has 46.7% 4+ bedroom share (highest)

**Conclusion:** The 4+ bedroom requirement is NOT overly restrictive for Phoenix market.

### Market Timing Considerations

**Appreciation by Area (5-Year):**

| Area | 5-Year Appreciation | Affordability | Risk Level |
|------|---------------------|---------------|------------|
| Tolleson | 74.5% | Good | Low |
| Buckeye | 69.9% | Best | Medium (water) |
| Maricopa | 68.8% | Best | Low |
| Queen Creek | ~100% | Moderate | Medium (water) |
| Gilbert | 139.5% (10-year) | Moderate | Low |
| Chandler | 139.5% (10-year) | Moderate | Low |

**Buyer's Market Areas (July 2024):** Surprise, Goodyear, Cave Creek - shifted to buyer-favorable conditions.

**Hot Markets:** Desert Ridge (+27.2% 2022-2023), North Scottsdale, Arcadia.

---

## 3. Regulatory & Domain Intelligence Summary

### Arizona-Specific Factors Confirmed/Updated

**Building System Lifespan Adjustments:**

| System | National Average | Arizona Lifespan | Reduction | Scoring Impact |
|--------|------------------|------------------|-----------|----------------|
| HVAC/AC | 15-20 years | **8-15 years** | 20-40% | Major recalibration needed |
| Asphalt Roof | 20-30 years | **12-25 years** | 17-30% | Moderate recalibration |
| Tile Roof (tiles) | 50-100 years | 50-100 years | None | No change |
| Tile Roof (underlayment) | 20-30 years | **12-20 years** | 33-40% | Add as scoring factor |
| Pool Equipment | 10-15 years | **8-12 years** | 20% | Add equipment age factor |

**Critical HVAC Insight:** A 10-year-old HVAC unit in Phoenix has done the equivalent work of a 15-year-old system in moderate climates due to 30-40% more runtime hours. The "$5,000 Rule" applies: multiply age x repair cost; if >$5,000, replace.

**HVAC Replacement Costs (2024 Phoenix):**
- Central AC only: $6,000-$12,500
- Full HVAC system: $11,000-$26,000
- High-efficiency (18+ SEER): $15,000-$26,000

### Legal/Regulatory Landscape

**HOA Disclosure (A.R.S. Section 33-1806):**
- Seller must provide disclosures within 10 days
- Maximum disclosure fee: $550 total
- Civil penalty for violations: Up to $1,200
- Buyer acknowledgment required

**Solar Lease Regulations (A.R.S. Section 44-1763):**
- Extensive disclosure requirements
- 3+ business day rescission right
- Arizona Association of REALTORS revising solar addendum (November 2025)

**New Construction Warranty:**
- Implied warranty of workmanship cannot be waived (Zambrano v. M & RC, 2022)
- 8-year statute of repose for latent defects
- 90-day pre-litigation notice required
- ROC complaints valid for 2 years

**Septic Inspection Requirements:**
- Mandatory inspection within 6 months prior to sale
- Tank must be pumped or certified at transfer
- $50 transfer fee per parcel
- Notice of Transfer required within 15 days

### Infrastructure Considerations

**Water Security (Critical 2023 Update):**

The 2023 groundwater moratorium created a definitive two-tier market:

| Tier | Status | Cities | Water Security | Recommendation |
|------|--------|--------|----------------|----------------|
| **Tier 1: Secure** | DAWS | Phoenix, Mesa, Chandler, Gilbert, Scottsdale, Tempe, Glendale, Peoria, Goodyear, Avondale | 100-year assured | PASS |
| **Tier 2: At Risk** | Non-DAWS | Buckeye, Queen Creek (SE), San Tan Valley (parts) | Groundwater dependent | WARNING |

**EPCOR West Valley:** Received first new DAWS designation in 25 years (October 2025), enabling 60,000 new homes.

**City of Phoenix Water Portfolio:**
- ~60% Salt/Verde Rivers
- ~40% Colorado River (CAP)
- ~2% groundwater

**Septic vs. Sewer:**

| Factor | City Sewer | Septic System |
|--------|------------|---------------|
| Annual Cost | $360-720 | $400-950+ |
| Failure Risk | Minimal | **10%+** |
| Pre-sale Inspection | Not required | **Mandatory** |
| Replacement Cost | N/A | $6,000-$50,000 |
| Arizona Soil Issues | None | Caliche, clay, drainage problems |

**Recommendation:** Maintain sewer preference as SOFT kill-switch with severity 2.5.

### Foundation Considerations

**Standard Types:**
- Slab-on-Grade: Most common
- Post-Tension Slab: Common in newer homes, expansive soil areas

**Warning Signs:**
- Stair-step cracks in masonry (HIGH severity)
- Horizontal cracks in stem wall (HIGH severity)
- Sticking doors/windows (MEDIUM severity)
- Sloping floors (HIGH severity)

**Repair Costs:** $4,000-$15,000 for stabilization; $2,000-$3,000 per helical pier.

---

## 4. Technical Capability Assessment

### Data Sources Now Available

**Government APIs (Free):**

| API | Authentication | Data Available | Integration Priority |
|-----|---------------|----------------|---------------------|
| **FEMA NFHL** | None required | Flood zone by coordinates | HIGH - Add to Phase 0 |
| **Maricopa County Assessor** | Free API key | Parcel, ownership, valuations | EXISTING - Expand fields |
| **FBI Crime Data Explorer** | Free API key | Crime statistics by city | MEDIUM - Supplemental |
| **Phoenix Open Data** | None | Crime data (address-level) | HIGH - Phase 1 |
| **EIA Energy** | Free API key | Consumption statistics | LOW - Estimation only |

**Third-Party APIs:**

| Service | Free Tier | Integration Value |
|---------|-----------|-------------------|
| **WalkScore** | 5,000 calls/day | HIGH - Location scoring |
| **CrimeOMeter** | 10 calls/month | LOW - Too restrictive |
| **UtilityAPI** | Contact for pricing | MEDIUM - APS actual data |

### Scraping Infrastructure Recommendations

**Current Stack (Validated):**
- nodriver: Stealth headless browser (successor to undetected-chromedriver)
- curl_cffi: TLS fingerprint spoofing for API calls
- Residential proxies: Required for Zillow/Redfin

**Anti-Bot Landscape (Q4 2024):**

| Site | Protection | Difficulty | Best Approach |
|------|------------|------------|---------------|
| Zillow | HUMAN Security (PerimeterX) | HIGH | nodriver + residential proxies |
| Redfin | IP rate limiting + CAPTCHA | MEDIUM | curl_cffi + proxies |
| Realtor.com | Moderate | MEDIUM | Playwright MCP acceptable |

**Proxy Provider Recommendation:**

| Use Case | Provider | Cost | Rationale |
|----------|----------|------|-----------|
| Development | IPRoyal | $7/GB (non-expiring) | Budget, flexibility |
| Production | Smartproxy/Decodo | $3-5/GB | Best value, 99.86% success |
| Enterprise | Oxylabs | $5-15/GB | Real estate-specific tools |

### Integration Opportunities

**Immediate (Low Effort, High Value):**
1. FEMA NFHL flood zone lookup (2-4 hours)
2. WalkScore API integration (2-4 hours)
3. Phoenix Open Data crime feed (4-8 hours)

**Medium-Term:**
1. Expand Maricopa Assessor fields (lot features, pool details)
2. Add septic system detection via county database
3. Water service area verification

**Task Queue Assessment:**
- **Current Scale:** ~500-1,000 tasks per analysis run
- **Recommendation:** RQ is appropriate
- **Migration Trigger:** Queue latency >30 seconds consistently, or >10,000 tasks/minute

---

## 5. Kill-Switch Criteria Validation

### Current Criteria Assessment

| Criterion | Type | Current Setting | Research Finding | Recommendation |
|-----------|------|-----------------|------------------|----------------|
| **HOA** | HARD | $0 required | 70% buyer preference, $448 avg, adequate non-HOA inventory | **MAINTAIN** |
| **Bedrooms** | HARD | 4+ required | 32% market share, multigenerational trend supports | **MAINTAIN** |
| **Bathrooms** | HARD | 2+ required | Standard requirement, 2.32 avg in Phoenix | **MAINTAIN** |
| **Sewer** | SOFT | City preferred | 10%+ septic failure rate, $6k-50k replacement | **MAINTAIN** (severity 2.5) |
| **Year Built** | SOFT | <2024 preferred | Strong implied warranty protection (Zambrano ruling) | **MAINTAIN** (severity 2.0) |
| **Garage** | SOFT | 2+ spaces | Standard for Arizona market | **MAINTAIN** (severity 1.5) |
| **Lot Size** | SOFT | 7k-15k sqft | Zoning research confirms appropriate range | **MAINTAIN** (severity 1.0) |

### Recommended NEW Kill-Switch Criteria

**1. Solar Lease - HARD Kill-Switch**

| Attribute | Value |
|-----------|-------|
| Type | HARD |
| Condition | Solar lease or PPA present |
| Rationale | 3-8% home value reduction, transfer complications, 100+ bankruptcies |
| Implementation | Check listing data, county records, seller disclosure |

**2. Flood Zone (SFHA) - HARD Kill-Switch**

| Attribute | Value |
|-----------|-------|
| Type | HARD |
| Condition | FEMA zones A, AE, AH, AO, VE (SFHA_TF = True) |
| Rationale | Mandatory flood insurance ($1,500-3,000/year), resale limitations |
| Implementation | FEMA NFHL API query by coordinates |

**3. Water Service Area - SOFT Kill-Switch (NEW)**

| Attribute | Value |
|-----------|-------|
| Type | SOFT |
| Severity | 2.0 |
| Condition | Property outside DAWS service area |
| Rationale | 2023 groundwater moratorium, development restrictions, long-term value risk |
| Implementation | Verify against ADWR designated provider list |

**4. Septic System Age - SOFT Kill-Switch Enhancement**

| Attribute | Value |
|-----------|-------|
| Type | SOFT |
| Severity | 2.5 (base) + 1.0 (if >20 years old) |
| Condition | Septic system present (verified via county database) |
| Rationale | 10%+ failure rate, $6k-50k replacement, mandatory pre-sale inspection |
| Implementation | Query Maricopa County septic database |

### Updated Kill-Switch Summary Table

| Type | Criterion | Requirement | Severity | Source |
|------|-----------|-------------|----------|--------|
| **HARD** | HOA | Must be $0 | Instant fail | Market-Alpha |
| **HARD** | Bedrooms | Must be 4+ | Instant fail | Market-Gamma |
| **HARD** | Bathrooms | Must be 2+ | Instant fail | Baseline |
| **HARD** | Solar Lease | Must be NONE or OWNED | Instant fail | Market-Beta, Domain-Beta |
| **HARD** | Flood Zone | Must NOT be SFHA (A/AE/AH/AO/VE) | Instant fail | Tech-Alpha |
| SOFT | Sewer | City preferred | 2.5 | Domain-Gamma |
| SOFT | Water Service | DAWS preferred | 2.0 | Domain-Gamma |
| SOFT | Year Built | <2024 preferred | 2.0 | Domain-Beta |
| SOFT | Garage | 2+ spaces | 1.5 | Baseline |
| SOFT | Lot Size | 7k-15k sqft | 1.0 | Baseline |

**Verdict Logic:** FAIL if any HARD fails OR severity sum >= 3.0 | WARNING if 1.5-3.0 | PASS if <1.5

---

## 6. Scoring System Implications

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

## 7. Strategic Recommendations

### Top 5 Immediate Actions (This Week)

| Priority | Action | Effort | Impact | Dependencies |
|----------|--------|--------|--------|--------------|
| **1** | Add solar lease as HARD kill-switch | 2 hours | CRITICAL | Update kill_switch.py, constants.py |
| **2** | Integrate FEMA NFHL flood zone API | 4 hours | HIGH | New script: extract_flood_zone.py |
| **3** | Recalibrate HVAC scoring for Arizona lifespan | 2 hours | HIGH | Update scoring_weights.py |
| **4** | Add pool cost factor to cost efficiency | 2 hours | MEDIUM | Update cost calculations |
| **5** | Add water service area verification | 4 hours | MEDIUM | ADWR DAWS list integration |

### Top 5 Medium-Term Improvements (This Month)

| Priority | Action | Effort | Impact | Dependencies |
|----------|--------|--------|--------|--------------|
| **1** | Integrate WalkScore API | 8 hours | HIGH | API key, scoring integration |
| **2** | Add Phoenix crime data integration | 8 hours | MEDIUM | Data pipeline, scoring integration |
| **3** | Implement foundation assessment factor | 16 hours | MEDIUM | Visual assessment rubric |
| **4** | Add septic system detection | 8 hours | MEDIUM | County database query |
| **5** | Implement owned solar bonus scoring | 4 hours | LOW | Detection logic |

### Risk Factors to Monitor

**Market Risks:**

| Risk | Probability | Impact | Monitoring Action |
|------|-------------|--------|-------------------|
| Interest rate spike >7.5% | Medium | High | Weekly Freddie Mac PMMS check |
| Phoenix market correction | Medium | Medium | Monthly Zillow HPI tracking |
| HOA inventory squeeze | Low | Medium | Quarterly listing count check |
| Solar company bankruptcies | High | Medium | Track major provider status |

**Technical Risks:**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| nodriver detection (~6 months) | High | High | Budget for commercial scraping solution |
| Zillow/Redfin ToS enforcement | Medium | Critical | Maintain commercial data provider backup |
| Proxy IP reputation degradation | Medium | Medium | Rotate providers, premium tiers |
| API rate limit changes | Low | Low | Implement adaptive throttling |

**Regulatory Risks:**

| Risk | Probability | Impact | Monitoring Action |
|------|-------------|--------|-------------------|
| Arizona water restrictions expansion | Medium | High | Track ADWR announcements |
| HOA law changes (fee caps, etc.) | Low | Low | Annual legislative review |
| Solar lease transfer law changes | Medium | Low | November 2025 AAR form release |

---

## 8. Research Gaps Remaining

### Questions Not Fully Answered

**Market Intelligence:**
1. Exact percentage of Phoenix sales that are 4-bedroom (no MLS data found)
2. Precise zip code-level 5-year appreciation (requires premium MLS subscription)
3. Non-HOA vs HOA price differential (anecdotal only)
4. First-time buyer market share in Phoenix specifically

**Domain Intelligence:**
1. Home warranty claim rates for Arizona (HVAC/roof failure frequency)
2. Post-tension slab failure rates vs. standard slabs
3. Solar panel installation impact on roof underlayment lifespan
4. Ground water level changes affecting expansive soil behavior

**Technical Intelligence:**
1. Actual permit API availability timeline (Accela/Maricopa)
2. SRP energy data access options (no public API found)
3. Long-term success rates for stealth scraping tools (6-12 month horizon)
4. NFIP claims history accessibility by address

### Recommended Follow-Up Research

**High Priority:**

| Topic | Research Question | Method | Timeline |
|-------|-------------------|--------|----------|
| MLS Data Access | Can we obtain 4-bedroom sales percentage? | Contact Phoenix REALTORS | 2 weeks |
| Permit History | When will Maricopa enable Accela API? | Contact county | 1 week |
| Insurance Data | Roof/HVAC claim rates in Arizona? | Industry contacts | 4 weeks |

**Medium Priority:**

| Topic | Research Question | Method |
|-------|-------------------|--------|
| Energy Usage | SRP actual usage data access options | Contact SRP, UtilityAPI |
| Foundation | Post-tension slab performance data | Academic literature search |
| Solar Degradation | Panel efficiency loss rate in Arizona | Manufacturer data |

**Low Priority:**

| Topic | Research Question | Method |
|-------|-------------------|--------|
| Appreciation Forecast | 2025-2026 Phoenix appreciation prediction | Economic modeling |
| Builder Quality | Which builders have most ROC complaints? | ROC database analysis |
| School District Impact | Quantified impact on property values | Academic research |

---

## Appendix A: Research Report Index

| Report ID | Title | Key Findings | Confidence |
|-----------|-------|--------------|------------|
| Market-Alpha | Financial Baseline | HOA validated, mortgage rates, commute costs | High |
| Market-Beta | Pool & Solar Economics | Solar lease liability, pool costs | High |
| Market-Gamma | Demographics & Appreciation | 4-bed validated, appreciation data | High |
| Domain-Alpha | Building Systems | HVAC/roof lifespan recalibration | High |
| Domain-Beta | Regulations | HOA disclosure, solar transfer, warranties | High |
| Domain-Gamma | Land & Infrastructure | Septic risk, water security, zoning | High |
| Tech-Alpha | Government APIs | FEMA NFHL, Assessor API | High |
| Tech-Beta | Data APIs | Crime, WalkScore, Energy | High |
| Tech-Gamma | Scraping Infrastructure | Anti-bot, proxies, task queues | High |

## Appendix B: Source Summary

**Total Unique Sources Cited:** 150+

**Source Categories:**
- Government/Official: 45%
- Industry Publications: 25%
- Academic/Research: 10%
- News/Media: 12%
- Community/Forum: 8%

**Data Freshness:**
- 2024 data: 85%
- 2023 data: 12%
- Pre-2023: 3%

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | December 2024 | Claude Opus 4.5 | Initial synthesis of 9 research reports |

**Next Review:** June 2025 (before summer selling season)

**Distribution:** PHX Houses Analysis Pipeline development team

---

*This executive summary synthesizes findings from 9 domain-specific research reports conducted December 2024. For detailed findings and source citations, refer to individual reports in `docs/analysis/research/`.*

*Generated by Claude Opus 4.5 for PHX Houses Analysis Pipeline*
