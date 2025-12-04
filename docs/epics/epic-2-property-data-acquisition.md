# Epic 2: Property Data Acquisition

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

---

### E2.S2: Maricopa County Assessor API Integration

**Priority:** P0 | **Dependencies:** E1.S3, E1.S6, E2.S7 | **FRs:** FR2

**User Story:** As a system user, I want to fetch authoritative property data from Maricopa County Assessor, so that I have reliable lot size, year built, and system information.

**Acceptance Criteria:** Retrieves lot_sqft, year_built, garage_spaces, has_pool, sewer_type. Data stored in `county_data` section with 0.95 confidence. Missing properties flagged with "county_data_missing" warning and 0.0 confidence. Rate limit (429) triggers exponential backoff per E1.S6.

**Technical Notes:** API requires Bearer token from `MARICOPA_ASSESSOR_TOKEN`. Rate limit ~1 req/sec. Implement `CountyAssessorClient` in `src/phx_home_analysis/services/county_data/`.

**Definition of Done:** CountyAssessorClient | Field mapping | Provenance metadata | Missing property handling | Mocked integration test

---

### E2.S3: Zillow/Redfin Listing Extraction

**Priority:** P0 | **Dependencies:** E2.S1, E2.S7 | **FRs:** FR3, FR61, FR62

**User Story:** As a system user, I want to extract listing data from Zillow and Redfin using stealth browsers, so that I have current price, HOA, and property details.

**Acceptance Criteria:** Retrieves price, beds, baths, sqft, hoa_fee, listing_url, images[] stored in `listing_data`. Primary: nodriver (stealth Chrome). Fallback 1: curl-cffi. Fallback 2: Playwright MCP. User-Agent rotated from 20+ signatures with residential proxy and 2-5s random delays. Not found properties flagged with 0.0 confidence.

**Technical Notes:** Primary nodriver for PerimeterX bypass. User-Agent pool in `config/user_agents.txt`. Implement in `scripts/extract_images.py` and `src/phx_home_analysis/services/listing_extraction/`.

**Definition of Done:** nodriver extraction | curl-cffi fallback | Playwright fallback | UA/proxy rotation | Image URL extraction | Mock server integration test

---

### E2.S4: Property Image Download and Caching

**Priority:** P0 | **Dependencies:** E2.S3 | **FRs:** FR4

**User Story:** As a system user, I want property images downloaded and cached locally, so that visual assessment can be performed offline.

**Acceptance Criteria:** Images saved to `data/property_images/{normalized_address}/` as `img_001.jpg`, etc. with manifest in `images_manifest.json`. Failed downloads logged, continue with remaining. Existing images preserved (not re-downloaded). `--clean-images` removes images older than 14 days.

**Technical Notes:** Use httpx for async downloads with semaphore (max 5 concurrent). Convert webp/png to jpg for consistency.

**Definition of Done:** Image download with manifest | Cache hit detection | Parallel downloads with rate limiting | Cache cleanup | Unit tests

---

### E2.S5: Google Maps API Geographic Data

**Priority:** P0 | **Dependencies:** E2.S7 | **FRs:** FR5

**User Story:** As a system user, I want geographic data from Google Maps API, so that I have accurate geocoding, distances, and orientation.

**Acceptance Criteria:** Geocoding returns lat/lng and formatted address, cached to minimize API costs. Distances computed to work location, supermarket, and park. Sun orientation inferred from satellite imagery with scoring: N=25pts, E=18.75pts, S=12.5pts, W=0pts.

**Technical Notes:** APIs: Geocoding, Distance Matrix, Places (nearby search). Key from `GOOGLE_MAPS_API_KEY`. Cache in `data/api_cache/google_maps/` with 7-day TTL. Cost ~$0.05-0.10 per property.

**Definition of Done:** Geocoding with caching | Distance calculations | Orientation determination | API cost tracking | Mocked integration test

---

### E2.S6: GreatSchools API School Ratings

**Priority:** P0 | **Dependencies:** E2.S5, E2.S7 | **FRs:** FR6

**User Story:** As a system user, I want school ratings from GreatSchools API, so that I can assess neighborhood education quality.

**Acceptance Criteria:** Elementary, middle, and high school ratings (1-10) with names and distances, cached 30 days. Identifies assigned schools (not just nearby). Fallback to Google Places with 0.5 confidence if unavailable.

**Technical Notes:** Free tier 1000 requests/day. Key from `GREATSCHOOLS_API_KEY`. Composite: (elem*0.3) + (mid*0.3) + (high*0.4). Cache in `data/api_cache/greatschools/`.

**Definition of Done:** GreatSchools client | Assigned school determination | Composite rating | Caching with TTL | Google Places fallback

---

### E2.S7: API Integration Infrastructure

**Priority:** P0 | **Dependencies:** E1.S6 | **FRs:** FR58, FR59, FR60

**User Story:** As a system user, I want robust API integration with authentication, rate limiting, and caching, so that external data sources are accessed reliably and cost-efficiently.

**Acceptance Criteria:** Credentials from environment variables, never logged. Approaching limits triggers proactive throttling, 429 responses use exponential backoff. Cache checked before external requests with configurable TTL (default 7 days). Cache hit rate logged.

**Technical Notes:** Implement `APIClient` base class. Credentials: `*_API_KEY`, `*_TOKEN` patterns. Cache location: `data/api_cache/{service_name}/`. Cache key: hash of URL + params.

**Definition of Done:** APIClient with auth | Rate limiting with throttling | Response caching | Cache hit logging | Unit tests

---
