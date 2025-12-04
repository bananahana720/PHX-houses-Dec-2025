# Sprint 2: Data Acquisition

> **Epic**: E2
> **Objective**: Gather complete, authoritative property data from all sources
> **Stories**: 7
> **PRD Coverage**: FR1-6, FR58-62

### Stories

#### E2.S1 - Batch Analysis CLI Entry Point

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S1, E1.S4 |
| **FRs** | FR1 |

**Acceptance Criteria**:
- [ ] `python scripts/phx_home_analyzer.py --all` processes all CSV properties
- [ ] `--test` flag limits to first 5 properties
- [ ] `--dry-run` validates without API calls
- [ ] Progress display with ETA using rich library

**Definition of Done**:
- [ ] argparse CLI with all flags: --all, --test, --resume, --strict, --dry-run, --json
- [ ] CSV validation with row-specific error messages
- [ ] ETA calculation: rolling average of last 5 properties

---

#### E2.S2 - Maricopa County Assessor API Integration

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S3, E1.S6, E2.S7 |
| **FRs** | FR2 |

**Acceptance Criteria**:
- [ ] Retrieve: lot_sqft, year_built, garage_spaces, has_pool, sewer_type
- [ ] Data stored in county_data section with provenance (confidence=0.95)
- [ ] Missing properties flagged with 'county_data_missing' warning
- [ ] Rate limit handling (~1 req/sec)

**Definition of Done**:
- [ ] CountyAssessorClient in `src/phx_home_analysis/services/county_data/`
- [ ] Bearer token auth from MARICOPA_ASSESSOR_TOKEN env var
- [ ] Integration test with mocked API

---

#### E2.S3 - Zillow/Redfin Listing Extraction

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E2.S1, E2.S7 |
| **FRs** | FR3, FR61, FR62 |

**Acceptance Criteria**:
- [ ] **Primary**: nodriver (stealth Chrome) for PerimeterX bypass
- [ ] **Fallback 1**: curl-cffi with browser TLS fingerprints
- [ ] **Fallback 2**: Playwright MCP via browser_navigate
- [ ] Extract: price, beds, baths, sqft, hoa_fee, listing_url, images[]
- [ ] User-Agent rotation from pool of 20+ signatures

**Definition of Done**:
- [ ] Implementation in `scripts/extract_images.py`
- [ ] User-Agent pool in `config/user_agents.txt`
- [ ] Randomized delays (2-5 seconds between requests)
- [ ] Integration test with mock server

---

#### E2.S4 - Property Image Download and Caching

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E2.S3 |
| **FRs** | FR4 |

**Acceptance Criteria**:
- [ ] Images saved to `data/property_images/{normalized_address}/`
- [ ] Filenames: img_001.jpg, img_002.jpg, etc.
- [ ] Manifest: `images_manifest.json` with URL -> filename mapping
- [ ] Cache hit detection (skip existing images)
- [ ] `--clean-images` removes images older than 14 days

**Definition of Done**:
- [ ] Async downloads with httpx
- [ ] Semaphore (max 5 concurrent downloads)
- [ ] Image format normalization to jpg
- [ ] Unit tests for download and caching

---

#### E2.S5 - Google Maps API Geographic Data

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E2.S7 |
| **FRs** | FR5 |

**Acceptance Criteria**:
- [ ] Geocoding API: latitude, longitude, formatted address
- [ ] Distance Matrix: work location, supermarket, park distances
- [ ] Satellite imagery for orientation determination
- [ ] Cache with 7-day TTL in `data/api_cache/google_maps/`

**Definition of Done**:
- [ ] Orientation scoring: N=25pts, E=18.75pts, S=12.5pts, W=0pts
- [ ] API key from GOOGLE_MAPS_API_KEY env var
- [ ] Cost tracking (~$0.05-0.10 per property)

---

#### E2.S6 - GreatSchools API School Ratings

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E2.S5, E2.S7 |
| **FRs** | FR6 |

**Acceptance Criteria**:
- [ ] Elementary, middle, high school ratings (1-10 scale)
- [ ] Assigned schools identified (not just nearby)
- [ ] Cache with 30-day TTL
- [ ] Fallback to Google Places if API unavailable (confidence=0.5)

**Definition of Done**:
- [ ] GreatSchools API client
- [ ] Composite formula: (elementary*0.3) + (middle*0.3) + (high*0.4)
- [ ] Cache in `data/api_cache/greatschools/`

---

#### E2.S7 - API Integration Infrastructure [CRITICAL PATH]

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S6 |
| **FRs** | FR58, FR59, FR60 |

**Acceptance Criteria**:
- [ ] APIClient base class with authentication, retry, caching
- [ ] Credentials from environment (*_API_KEY, *_TOKEN patterns)
- [ ] Rate limiting with proactive throttling
- [ ] Cache hit rate logging for cost optimization

**Definition of Done**:
- [ ] Base APIClient class implemented
- [ ] Cache location: `data/api_cache/{service_name}/`
- [ ] Cache key: hash of request URL + params
- [ ] Rate limit tracking per service

---
