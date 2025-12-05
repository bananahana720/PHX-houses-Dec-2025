# Epic 2: Property Data Acquisition

**Status:** COMPLETE (7/7 stories) | **Completed:** 2025-12-05

**User Value:** Gather complete, authoritative property data from multiple sources (County Assessor, Zillow/Redfin, Google Maps, GreatSchools) to enable comprehensive analysis.

**PRD Coverage:** FR1-6, FR58-62
**Architecture References:** Integration Architecture, Stealth Browser Strategy, API Cost Estimation

---

### E2.S1: Batch Analysis CLI Entry Point

**Priority:** P0 | **Dependencies:** E1.S1, E1.S4 | **FRs:** FR1

**User Story:** As a system user, I want to initiate batch property analysis via a single CLI command, so that I can analyze multiple properties efficiently.

**Acceptance Criteria:** `--all` queues all CSV properties with progress display and ETA. `--test` processes only first 5 properties. `--dry-run` validates input without API calls and shows estimated time. Invalid input lists specific errors with row numbers and blocks processing.

**Technical Notes:** Use argparse. Input: `data/phx_homes.csv`. Flags: `--all`, `--test`, `--resume`, `--strict`, `--dry-run`, `--json`. Progress via `rich` library. ETA: rolling average of last 5 properties.

**Definition of Done:** CLI with all flags | CSV validation | Progress with ETA | Test mode | Dry-run mode

**Implementation Status:** ✅ COMPLETE (2025-12-04) | **Tests:** 37

**Implementation Notes:**
- Added `--json` flag for machine-readable output
- Row-specific CSV validation with error messages
- ETA: rolling average of last 5 properties

---

### E2.S2: Maricopa County Assessor API Integration

**Priority:** P0 | **Dependencies:** E1.S3, E1.S6, E2.S7 | **FRs:** FR2

**User Story:** As a system user, I want to fetch authoritative property data from Maricopa County Assessor, so that I have reliable lot size, year built, and system information.

**Acceptance Criteria:** Retrieves lot_sqft, year_built, garage_spaces, has_pool, sewer_type. Data stored in `county_data` section with 0.95 confidence. Missing properties flagged with "county_data_missing" warning and 0.0 confidence. Rate limit (429) triggers exponential backoff per E1.S6.

**Technical Notes:** API requires Bearer token from `MARICOPA_ASSESSOR_TOKEN`. Rate limit ~1 req/sec. Implement `CountyAssessorClient` in `src/phx_home_analysis/services/county_data/`.

**Definition of Done:** CountyAssessorClient | Field mapping | Provenance metadata | Missing property handling | Mocked integration test

**Implementation Status:** ✅ COMPLETE (2025-12-04) | **Tests:** 25 live tests

**Implementation Notes:**
- PO Box address rejection with ReDoS-safe regex
- SLA adjusted to 300s for realistic batch performance
- Rate limit: 0.5s delay between requests

---

### E2.S3: Zillow/Redfin Listing Extraction

**Priority:** P0 | **Dependencies:** E2.S1, E2.S7 | **FRs:** FR3, FR61, FR62

**User Story:** As a system user, I want to extract listing data from Zillow and Redfin using stealth browsers, so that I have current price, HOA, and property details.

**Acceptance Criteria:** Retrieves price, beds, baths, sqft, hoa_fee, listing_url, images[] stored in `listing_data`. Primary: nodriver (stealth Chrome). Fallback 1: curl-cffi. Fallback 2: Playwright MCP. User-Agent rotated from 20+ signatures with residential proxy and 2-5s random delays. Not found properties flagged with 0.0 confidence.

**Technical Notes:** Primary nodriver for PerimeterX bypass. User-Agent pool in `config/user_agents.txt`. Implement in `scripts/extract_images.py` and `src/phx_home_analysis/services/listing_extraction/`.

**Definition of Done:** nodriver extraction | curl-cffi fallback | Playwright fallback | UA/proxy rotation | Image URL extraction | Mock server integration test

**Implementation Status:** ✅ COMPLETE (2025-12-04) | **Tests:** 18 integration

**Implementation Notes:**
- Primary: nodriver (stealth Chrome) for PerimeterX bypass
- Fallback chain: nodriver → curl-cffi → Playwright MCP
- User-Agent pool: 24 signatures (Chrome/Firefox/Safari/Edge)
- Files created: user_agent_pool.py, playwright_mcp.py

**⚠️ Known Blockers (Live Testing 2025-12-04):**
- **BLOCK-001:** Zillow CAPTCHA (PerimeterX px-captcha) blocking ~67% extractions
- **BLOCK-002:** Redfin CDN 404 errors (session-bound URLs)
- Remediation: zpid URLs, residential proxies, single-session extract+download

---

### E2.S4: Property Image Download and Caching

**Priority:** P0 | **Dependencies:** E2.S3 | **FRs:** FR4

**User Story:** As a system user, I want property images downloaded and cached locally, so that visual assessment can be performed offline.

**Acceptance Criteria (Implemented as Content-Addressed Storage):**
- Images stored in `data/property_images/processed/{hash[:8]}/{hash}.png` (NOT {normalized_address}/)
- Manifest in `image_manifest.json` with lineage: property_hash, created_by_run_id, content_hash
- Failed downloads logged, processing continues (partial success)
- Cache hit via content hash prevents re-downloading
- `--force` flag for re-extraction
- Parallel downloads: httpx async + semaphore (max 5)

**Technical Notes:** Use httpx for async downloads with semaphore (max 5 concurrent). Convert webp/png to jpg for consistency.

**Definition of Done:** Image download with manifest | Cache hit detection | Parallel downloads with rate limiting | Cache cleanup | Unit tests

**Implementation Status:** ✅ COMPLETE (2025-12-05) | **Tests:** 25 unit tests

**Implementation Notes (9 Critical Bug Fixes):**
1. Shared manifest race condition → Run-specific manifests
2. Dual folder naming → Single content_hash system
3. Missing property_hash → Added lineage field
4. Address mismatch → Fixed normalization
5. No run isolation → Added run_id tracking
6. UUID non-determinism → Stable content_hash
7. Race conditions → File locking (file_lock.py)
8. Stale lookup → Atomic manifest updates
9. Missing lineage → Complete provenance tracking

**Files Created:**
- `src/phx_home_analysis/services/image_extraction/file_lock.py`
- `src/phx_home_analysis/services/image_extraction/validators.py`
- `src/phx_home_analysis/services/image_extraction/reconciliation.py`
- `src/phx_home_analysis/validation/image_schemas.py`

---

### E2.S5: Google Maps API Geographic Data

**Priority:** P0 | **Dependencies:** E2.S7 | **FRs:** FR5

**User Story:** As a system user, I want geographic data from Google Maps API, so that I have accurate geocoding, distances, and orientation.

**Acceptance Criteria:** Geocoding returns lat/lng and formatted address, cached to minimize API costs. Distances computed to work location, supermarket, and park. Sun orientation inferred from satellite imagery with scoring: N=25pts, E=18.75pts, S=12.5pts, W=0pts.

**Technical Notes:** APIs: Geocoding, Distance Matrix, Places (nearby search). Key from `GOOGLE_MAPS_API_KEY`. Cache in `data/api_cache/google_maps/` with 7-day TTL. Cost ~$0.05-0.10 per property.

**Definition of Done:** Geocoding with caching | Distance calculations | Orientation determination | API cost tracking | Mocked integration test

**Implementation Status:** ✅ COMPLETE (2025-12-04) | **Tests:** Part of 72 API track

**Implementation Notes:**
- GoogleMapsClient extends APIClient base class
- APIs: Geocoding, Distance Matrix, Places, Static Maps
- Cost tracking: ~$0.05-0.10 per property
- Completed as part of Sprint 2 parallel API track

---

### E2.S6: GreatSchools API School Ratings

**Priority:** P0 | **Dependencies:** E2.S5, E2.S7 | **FRs:** FR6

**User Story:** As a system user, I want school ratings from GreatSchools API, so that I can assess neighborhood education quality.

**Acceptance Criteria:** Elementary, middle, and high school ratings (1-10) with names and distances, cached 30 days. Identifies assigned schools (not just nearby). Fallback to Google Places with 0.5 confidence if unavailable.

**Technical Notes:** Free tier 1000 requests/day. Key from `GREATSCHOOLS_API_KEY`. Composite: (elem*0.3) + (mid*0.3) + (high*0.4). Cache in `data/api_cache/greatschools/`.

**Definition of Done:** GreatSchools client | Assigned school determination | Composite rating | Caching with TTL | Google Places fallback

**Implementation Status:** ✅ COMPLETE (2025-12-04) | **Tests:** Part of 72 API track

**Implementation Notes:**
- SchoolRatingsClient using SchoolDigger API (via RapidAPI)
- Composite: (elem×0.3) + (mid×0.3) + (high×0.4)
- Assigned schools: boundary-based + nearest fallback
- 30-day cache TTL, 1000 req/day quota

---

### E2.S7: API Integration Infrastructure

**Priority:** P0 | **Dependencies:** E1.S6 | **FRs:** FR58, FR59, FR60

**User Story:** As a system user, I want robust API integration with authentication, rate limiting, and caching, so that external data sources are accessed reliably and cost-efficiently.

**Acceptance Criteria:** Credentials from environment variables, never logged. Approaching limits triggers proactive throttling, 429 responses use exponential backoff. Cache checked before external requests with configurable TTL (default 7 days). Cache hit rate logged.

**Technical Notes:** Implement `APIClient` base class. Credentials: `*_API_KEY`, `*_TOKEN` patterns. Cache location: `data/api_cache/{service_name}/`. Cache key: hash of URL + params.

**Definition of Done:** APIClient with auth | Rate limiting with throttling | Response caching | Cache hit logging | Unit tests

**Implementation Status:** ✅ COMPLETE (2025-12-04) | **Tests:** Infrastructure for 72 tests

**Implementation Notes:**
- APIClient base class with auth, rate limiting, caching
- Cache keys: SHA256(URL + sorted params)
- Proactive throttling at 80% limit threshold
- Graceful errors: returns None, never raises
- Enables rapid API client authoring (E2.S2, S5, S6)

---

## Epic 2 Completion Summary

**Status:** COMPLETE (7/7 stories) | **Completed:** 2025-12-05
**Total Tests:** 182+ | **Extractors:** 5 implemented

### Test Coverage

| Story | Tests | Focus |
|-------|-------|-------|
| E2.S1 | 37 | CLI flags, CSV validation |
| E2.S2 | 25 | Live County API integration |
| E2.S3 | 18 | Stealth browser, fallbacks |
| E2.S4 | 25 | Content-addressed storage |
| E2.S5-S7 | 72 | API track (shared) |

### Major Spec Changes

1. **E2.S4 Storage**: Content-addressed (`{hash[:8]}/{hash}.png`) vs address-based folders
2. **E2.S4 Lineage**: Added property_hash, created_by_run_id, content_hash
3. **E2.S3 UA Pool**: 24 signatures (not "20+")
4. **E2.S6 API**: SchoolDigger selected over GreatSchools direct

### Active Blockers

| ID | Issue | Impact | Remediation |
|----|-------|--------|-------------|
| BLOCK-001 | Zillow CAPTCHA | 67% extraction failure | zpid URLs, residential proxies |
| BLOCK-002 | Redfin 404 | Session-bound URLs | Single-session extract+download |

### Next Steps
- Run Epic 2 retrospective
- Remediate BLOCK-001/002
- Begin Epic 3: Kill-Switch Filtering
