# Integration Architecture

### External API Integrations

| API | Purpose | Auth | Rate Limit | Client |
|-----|---------|------|------------|--------|
| Maricopa County Assessor | Lot, year, garage, pool, sewer | Bearer token | ~1 req/sec | `services/county_data/` |
| GreatSchools | School ratings (1-10) | API key | 1000/day free | `services/schools/` |
| Google Maps | Geocoding, distances, satellite | API key | Pay-as-you-go | Map analyzer agent |
| FEMA NFHL | Flood zone classification | None (public) | N/A | `services/flood_data/` |
| WalkScore | Walk/Transit/Bike scores | API key | 5000/day free | `services/walkscore/` |
| EPA AirNow | Air quality index | API key | 500/hour | `services/air_quality/` |

### Browser Automation Stack

```
┌────────────────────────────────────────────────────────┐
│                    EXTRACTION TARGET                    │
├────────────────────────────────────────────────────────┤
│                Zillow      Redfin      Realtor.com     │
│               (PerimeterX) (Cloudflare)  (Minimal)     │
└─────────────────────────────────────────────────────────┘
                    │            │            │
                    ▼            ▼            ▼
┌────────────────────────────────────────────────────────┐
│                    STEALTH LAYER                        │
├────────────────────────────────────────────────────────┤
│  nodriver (Primary)    curl-cffi (HTTP)    Playwright  │
│  - Stealth Chrome      - Browser TLS       - Fallback  │
│  - PerimeterX bypass   - Fingerprints      - MCP tool  │
│  - Human behavior sim  - Fast requests     - Less      │
│                                              stealth   │
└────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│                    PROXY LAYER                          │
├────────────────────────────────────────────────────────┤
│  Residential Proxy Rotation                            │
│  - IP rotation to avoid blocking                       │
│  - Chrome proxy extension for auth                     │
│  - $10-30/month budget                                 │
└────────────────────────────────────────────────────────┘
```

### API Cost Estimation

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Claude API (Haiku) | ~2M tokens | $0.50-$2 |
| Claude API (Sonnet - vision) | ~1M tokens + images | $15-30 |
| Google Maps API | ~500 requests | $5-10 |
| Residential Proxies | ~10GB | $10-30 |
| **TOTAL** | | **$30-72** |

---
