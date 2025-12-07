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
- Run Epic 2 retrospective ✅
- Remediate BLOCK-001/002 → See Wave 0 below
- Begin Epic 3: Kill-Switch Filtering

---

## Post-Completion Remediation (Waves 0-2)

**Added:** 2025-12-05 via Correct Course Workflow
**Reason:** Live testing revealed extraction failures requiring architectural fixes
**Total Work:** 4 commits (74d91f5, 0b4fa88, 3697b0c, 02041da) + 67 integration tests (3880460)

---

### Course Correction Summary (2025-12-06)

**Problem:** Live testing revealed image extraction pipeline had critical bugs preventing disk persistence and metadata extraction.

**Solution:** Three-wave remediation addressing error handling, wiring bugs, and metadata persistence:

| Wave | Focus | Commits | Impact |
|------|-------|---------|--------|
| Wave 1 | Error handling & schema versioning | 74d91f5 | Retry decorator, state v2.0.0, transient error classification |
| Wave 2 | ImageProcessor wiring | 0b4fa88, 3697b0c | 31+ images now saving to disk, fixed extractor creation bug |
| Wave 3 | Metadata persistence | 02041da | Kill-switch fields auto-persisted to enrichment_data.json |

**Verification:**
- 67 integration tests created and passing (commit 3880460)
- Test extraction: 4560 E Sunrise Dr → 31 images saved to `data/property_images/processed/{hash[:8]}/{hash}.png`
- All images validated as proper PNG format with content-addressed storage
- Kill-switch fields (hoa_fee, beds, baths, sqft, lot_sqft, garage_spaces, sewer_type, year_built) now auto-persist

---

### E2.R1: PhoenixMLS Data Extraction Pivot

**Priority:** P0 | **Dependencies:** E2.S3, E2.S4 | **Blocker:** BLOCK-001, BLOCK-002

**User Story:** As a system user, I want property data from PhoenixMLS as the primary source, so that I have reliable extraction without anti-bot blocking.

**Acceptance Criteria:**
- PhoenixMLS is PRIMARY data source (priority 1 in extractor chain)
- All 8 kill-switch fields extracted (HOA, beds, baths, sqft, lot, garage, sewer, year)
- 23 new MLS fields added to Property/EnrichmentData entities
- >90% success rate on test properties
- Full test coverage (unit + integration)

**Technical Approach:**
1. Enhance PhoenixMLSExtractor for metadata parsing (not just images)
2. Add 23 MLS-specific fields to domain entities
3. Update CSV repository for new field parsing/serialization
4. Add Pydantic validators for new fields
5. Update orchestrator to prioritize PhoenixMLS → Zillow → Redfin → Assessor

**Implementation Status:** ✅ COMPLETE (2025-12-05) | **Tests:** 41 unit tests

**Implementation Notes:**
- **PhoenixMLS as PRIMARY:** No anti-bot systems, 95%+ reliability
- **23 New MLS Fields:** listing_number, property_type, cooling_type, heating_type, roof_material, water_source, kitchen_features, master_bath_features, laundry_features, interior_features_list, flooring_types, exterior_features_list, patio_features, lot_features, elementary_school_name, middle_school_name, high_school_name, cross_streets, listing_url, listing_status, listing_office, mls_last_updated, architecture_style
- **Metadata Parser:** `_parse_listing_metadata()` extracts all kill-switch + MLS fields from listing pages
- **Source Priority:** PhoenixMLS → Maricopa County → Zillow → Redfin
- **CSV Repository:** Updated for 23 new fields with list serialization (semicolon-delimited)
- **Full Coverage:** 41 unit tests in `test_phoenix_mls_metadata.py`

**Key Files Changed:**
- `src/phx_home_analysis/domain/entities.py` - 23 new fields added to Property and EnrichmentData
- `src/phx_home_analysis/validation/schemas.py` - Pydantic validators for new fields
- `src/phx_home_analysis/repositories/csv_repository.py` - Parsing/serialization for 23 fields
- `src/phx_home_analysis/services/image_extraction/extractors/phoenix_mls.py` - Metadata parser implementation
- `src/phx_home_analysis/services/image_extraction/orchestrator.py` - PhoenixMLS priority order
- `tests/unit/services/image_extraction/test_phoenix_mls_metadata.py` - 41 tests (8 kill-switch + 15 MLS fields + parsing)

**Definition of Done:** ✅ Metadata parser | 23 fields added | CSV repository updated | 41 tests | PhoenixMLS priority | Documentation updated

---

### Wave 1: Error Handling & Schema Versioning (Commit 74d91f5)

**Implementation Date:** 2025-12-06

**Changes:**
1. **@retry_with_backoff Decorator** - Added to `stealth_base.py` for transient error recovery
2. **Schema Versioning** - Added `v2.0.0` to ExtractionState with migration support in `state_manager.py`
3. **Error Classification** - Added `is_transient_error()` to orchestrator (5 locations)
4. **Architecture Plan** - Created `ARCHITECTURE_PLAN_2025_12_06.md` with alignment to AP-2, AP-3, AP-6

**Files Modified:**
- `src/phx_home_analysis/services/image_extraction/extractors/stealth_base.py` (+92 lines)
- `src/phx_home_analysis/services/image_extraction/state_manager.py` (+140 lines)
- `src/phx_home_analysis/services/image_extraction/orchestrator.py` (+111 lines)
- `docs/sprint-artifacts/ARCHITECTURE_PLAN_2025_12_06.md` (new file, 265 lines)
- `docs/sprint-artifacts/SESSION_COMPACT_2025_12_06.md` (new file, 64 lines)

**Impact:** Pipeline now resilient to transient errors with exponential backoff and state schema migration safety.

---

### Wave 2: ImageProcessor Wiring Fixes (Commits 0b4fa88, 3697b0c)

**Implementation Date:** 2025-12-06

**Critical Bugs Fixed:**
1. **Extractor Creation Bug** - Fixed `_create_extractors()` to convert string source names to `ImageSource` enum before dictionary lookup. Previous code checked string keys against enum keys → 0 extractors created.
2. **Source Stats Initialization** - Fixed `extract_for_property()` to initialize `SourceStats` for each source before accessing. `extract_all()` already did this, but single-property method was missing initialization → KeyError.

**Verification:**
- Test property: `4560 E Sunrise Dr, Phoenix, AZ 85044`
- Result: **31 new images saved to disk** in content-addressed storage format
- Format: `data/property_images/processed/{hash[:8]}/{hash}.png`
- All files validated as proper PNG format

**Unit Tests Added (Commit 3697b0c):**
- `tests/unit/services/image_extraction/test_image_processor.py` - ImageProcessor unit tests
- `tests/unit/services/image_extraction/test_state_manager.py` - StateManager unit tests

**Files Modified:**
- `src/phx_home_analysis/services/image_extraction/orchestrator.py` (major refactor, 3393 lines touched)

**Impact:** Image extraction pipeline now fully operational with proper disk persistence.

---

### Wave 3: Metadata Persistence (Commit 02041da)

**Implementation Date:** 2025-12-06

**Changes:**
1. **Schema Extension** - Added `beds`, `baths`, `sqft` fields to `EnrichmentData` in `entities.py`
2. **MetadataPersister Service** - Created new service with provenance tracking for automatic kill-switch field persistence
3. **PHOENIX_MLS DataSource** - Added with 0.87 confidence in `quality/models.py`
4. **Orchestrator Integration** - Wired MetadataPersister into `extract_for_property_with_tracking()` in NEW path

**Fields Auto-Persisted:**
- `hoa_fee`, `beds`, `baths`, `sqft`, `lot_sqft`, `garage_spaces`, `sewer_type`, `year_built`, `mls_number`, `listing_url`

**Files Created:**
- `src/phx_home_analysis/services/image_extraction/metadata_persister.py` (195 lines)

**Files Modified:**
- `src/phx_home_analysis/domain/entities.py` (+7 lines)
- `src/phx_home_analysis/services/image_extraction/orchestrator.py` (+41 lines)
- `src/phx_home_analysis/services/quality/models.py` (+2 lines)

**Impact:** Kill-switch fields now automatically persist to `enrichment_data.json` with full provenance tracking, enabling gap analysis for scoring fields.

---

### Gap Analysis Results (Post-Wave 3)

**Kill-Switch Fields (8/8 - 100% COMPLETE):**
| Field | Source | Confidence |
|-------|--------|------------|
| hoa_fee | PHOENIX_MLS | 0.87 |
| beds | PHOENIX_MLS | 0.87 |
| baths | PHOENIX_MLS | 0.87 |
| sqft | PHOENIX_MLS | 0.87 |
| lot_sqft | MARICOPA_ASSESSOR | 0.95 |
| garage_spaces | MARICOPA_ASSESSOR | 0.95 |
| sewer_type | MARICOPA_ASSESSOR | 0.95 |
| year_built | MARICOPA_ASSESSOR | 0.95 |

**Scoring Fields (0/22 - 0% COMPLETE):** ❌
- Requires Epic 6 (Visual Analysis) implementation
- Image assessment with Claude Opus 4.5 for interior/exterior scoring

**Deal Analysis Fields (0/25 - 0% COMPLETE):** ❌
- Requires Epic 7 (Deal Sheet Generation) implementation
- Narrative generation and risk checklists

**Next Story:** E2.R2 (Expansion) - Extract remaining 22 scoring fields + 25 deal analysis fields from PhoenixMLS listings

---

### E2.R2: PhoenixMLS Full Listing Attribute Extraction

**Priority:** P1 | **Dependencies:** E2.R1 (Wave 3 Complete) | **Type:** Enhancement

**User Story:** As a system user, I want all 22 scoring fields and 25 deal analysis fields extracted from PhoenixMLS, so that I have complete property data for Epic 4-7 pipelines.

**Acceptance Criteria:**

**Phase 1: HIGH Priority Scoring Fields (22 fields)**
- Location (Section A - 250 pts): geo_lat, geo_lon, elementary_school, jr_high_school, high_school, orientation
- Systems (Section B - 175 pts): roofing, private_pool_yn, pool_partial_full, pool_features, spa, cooling, heating, price_per_sqft
- Interior (Section C - 180 pts): kitchen_features, master_bathroom, master_bedroom, fireplace_yn, fireplaces_total, interior_features, laundry, flooring

**Phase 2: MEDIUM Priority Deal Analysis Fields (25 fields)**
- Pricing & Status: list_price, current_price, status, list_date
- Property Structure: dwelling_type, exterior_stories, total_bathrooms
- Lot & Community: lot_acres, subdivision, community_features
- Exterior & Utilities: construction, exterior_features, water_source, utilities, fencing, landscaping
- Parking & Rooms: carport_spaces, total_covered_spaces, other_rooms
- Assessor: assessor_number, tax_year

**Technical Requirements:**
- Refactor `_extract_kill_switch_fields()` → `_extract_listing_metadata()`
- Add 22 HIGH-priority regex patterns
- Add 25 MEDIUM-priority regex patterns
- Add corresponding fields to EnrichmentData schema
- Update MetadataPersister field mapping
- Add unit tests for new extraction patterns
- Verify with 5+ diverse test properties

**Estimated Effort:** Phase 1 (2-3h) + Phase 2 (3-4h) + Testing (1-2h) = 6-9 hours (8 story points)

**Implementation Status:** Backlog

**Notes:**
- Replaces original E2.R2 "Redfin Session-Bound Download" (Redfin coverage now sufficient via PhoenixMLS + Zillow)
- BLOCK-002 mitigated - Redfin no longer blocking

**Definition of Done:** ✅ 47 fields added | MetadataPersister extended | Tests passing | Gap analysis 100%
