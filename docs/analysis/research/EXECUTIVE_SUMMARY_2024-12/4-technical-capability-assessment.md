# 4. Technical Capability Assessment

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
