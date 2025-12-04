# Integration Points

### External APIs
| API | Purpose | Authentication | Rate Limit |
|-----|---------|----------------|------------|
| Maricopa County Assessor | Lot size, year built, garage, pool | Bearer token | ~1 req/sec |
| GreatSchools | School ratings (1-10) | API key | 1000 req/day |
| Google Maps | Geocoding, distances, orientation | API key | Pay-as-you-go |
| FEMA Flood | Flood zone classification | None (public) | Unknown |
| WalkScore | Walk/Transit/Bike Scores | API key | 5000 req/day |

### Web Scraping
| Site | Method | Detection | Data |
|------|--------|-----------|------|
| Zillow | nodriver (stealth) | PerimeterX | Images, price, details |
| Redfin | nodriver (stealth) | Cloudflare | Images, listing data |
| Realtor.com | Playwright | Minimal | Listing details |

---
