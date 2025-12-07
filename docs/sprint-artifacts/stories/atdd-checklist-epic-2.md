# ATDD Checklist - Epic 2: Data Acquisition Testing

**Date:** 2025-12-04
**Author:** Murat (Master Test Architect - TEA Agent)
**Primary Test Level:** Live API Integration
**Status:** RED Phase Complete ✅

---

## Story Summary

**As a** property analysis pipeline operator
**I want** live API integration tests for data acquisition sources
**So that** I can detect bot detection blocks, API schema drift, rate limit issues, and data quality degradation before they impact production

---

## Acceptance Criteria

From test-design-epic-2-7.md:

1. ✅ County Assessor API expanded from 10 → 25 tests
2. ✅ Zillow/Redfin extraction with 15 new tests
3. ✅ Bot detection bypass validation (PerimeterX)
4. ✅ Rate limiting behavior tests
5. ✅ Schema drift detection tests
6. ✅ Fallback chain validation (nodriver → curl_cffi → playwright)

---

## Failing Tests Created (RED Phase)

### County Assessor Tests (25 tests)

**File:** `tests/live/test_county_assessor_live.py` (654 lines)

#### Existing Tests (10)

| Test | Class | Status |
|------|-------|--------|
| test_client_initializes_with_valid_token | TestCountyAssessorAuthentication | EXISTING |
| test_api_accepts_authentication | TestCountyAssessorAuthentication | EXISTING |
| test_response_returns_parcel_data_type | TestCountyAssessorSchemaValidation | EXISTING |
| test_parcel_data_has_required_fields | TestCountyAssessorSchemaValidation | EXISTING |
| test_field_types_are_correct | TestCountyAssessorSchemaValidation | EXISTING |
| test_multiple_requests_no_rate_limit_error | TestCountyAssessorRateLimiting | EXISTING |
| test_known_address_data_within_constraints[x2] | TestCountyAssessorDataAccuracy | EXISTING |
| test_invalid_address_handles_gracefully | TestCountyAssessorErrorHandling | EXISTING |
| test_empty_address_handles_gracefully | TestCountyAssessorErrorHandling | EXISTING |

#### NEW Tests (15)

| Test ID | Test Name | Class | Verifies |
|---------|-----------|-------|----------|
| LIVE_COUNTY_016 | test_token_refresh_near_expiration | TestCountyAssessorTokenRefresh | Token refresh before expiry |
| LIVE_COUNTY_017 | test_token_refresh_during_batch_operation | TestCountyAssessorTokenRefresh | Mid-batch auth stability |
| LIVE_COUNTY_018 | test_response_schema_drift_new_field | TestCountyAssessorSchemaDrift | Forward compatibility |
| LIVE_COUNTY_019 | test_response_schema_drift_field_rename | TestCountyAssessorSchemaDrift | Breaking change detection |
| LIVE_COUNTY_020 | test_partial_data_missing_garage_spaces | TestCountyAssessorPartialData | Null garage handling |
| LIVE_COUNTY_021 | test_partial_data_missing_pool_indicator | TestCountyAssessorPartialData | Null pool handling |
| LIVE_COUNTY_012 | test_edge_case_new_subdivision_no_data | TestCountyAssessorEdgeCases | New construction handling |
| LIVE_COUNTY_013 | test_edge_case_po_box_address_rejection | TestCountyAssessorEdgeCases | PO Box rejection |
| LIVE_COUNTY_014 | test_edge_case_commercial_property_rejection | TestCountyAssessorEdgeCases | Commercial property handling |
| LIVE_COUNTY_015 | test_edge_case_condo_unit_number_handling | TestCountyAssessorEdgeCases | Unit number parsing |
| LIVE_COUNTY_023 | test_geographic_boundary_scottsdale_adjacent | TestCountyAssessorEdgeCases | Boundary classification |
| LIVE_COUNTY_022 | test_data_freshness_recent_sale_updated_year | TestCountyAssessorAdvanced | Data freshness validation |
| LIVE_COUNTY_024 | test_concurrent_requests_race_condition | TestCountyAssessorAdvanced | Concurrency safety |
| LIVE_COUNTY_025 | test_ssl_certificate_validation | TestCountyAssessorAdvanced | SSL security |
| LIVE_COUNTY_011 | test_batch_extraction_50_properties_performance | TestCountyAssessorAdvanced | Batch SLA compliance |

---

### Zillow/Redfin Tests (15 tests)

**File:** `tests/live/test_zillow_redfin_live.py` (813 lines)

| Test ID | Test Name | Class | Verifies |
|---------|-----------|-------|----------|
| LIVE_SCRAPE_001 | test_nodriver_perimeter_x_bypass_success | TestZillowPerimeterXBypass | Bot detection evasion |
| LIVE_SCRAPE_002 | test_nodriver_blocked_fallback_to_curl_cffi | TestZillowPerimeterXBypass | Fallback chain tier 1 |
| LIVE_SCRAPE_003 | test_curl_cffi_blocked_fallback_to_playwright | TestZillowPerimeterXBypass | Fallback chain tier 2 |
| LIVE_SCRAPE_004 | test_user_agent_rotation_20_signatures | TestZillowStealthTechniques | UA diversity validation |
| LIVE_SCRAPE_010 | test_captcha_detection_and_retry | TestZillowStealthTechniques | CAPTCHA handling |
| LIVE_SCRAPE_011 | test_rate_limiting_zillow_5_requests_per_minute | TestZillowStealthTechniques | Rate limit compliance |
| LIVE_SCRAPE_005 | test_image_url_extraction_accuracy | TestZillowExtraction | Image URL extraction |
| LIVE_SCRAPE_006 | test_image_download_bulk_25_photos | TestZillowExtraction | Bulk download SLA |
| LIVE_SCRAPE_007 | test_field_extraction_price_beds_baths_hoa | TestZillowExtraction | Metadata extraction |
| LIVE_SCRAPE_008 | test_listing_status_active_pending_sold | TestZillowExtraction | Status detection |
| LIVE_SCRAPE_009 | test_selector_drift_detection_price_field | TestZillowReliability | Selector drift detection |
| LIVE_SCRAPE_014 | test_javascript_rendered_content_extraction | TestZillowReliability | JS content capture |
| LIVE_SCRAPE_015 | test_proxy_rotation_to_avoid_ip_ban | TestZillowReliability | Proxy rotation |
| LIVE_SCRAPE_012 | test_redfin_vs_zillow_data_consistency | TestRedfinCrossValidation | Cross-source validation |
| LIVE_SCRAPE_013 | test_mobile_viewport_scraping | TestRedfinCrossValidation | Mobile layout handling |

---

## Data Factories Created

### Existing Fixtures (from conftest.py)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `assessor_token` | module | Load MARICOPA_ASSESSOR_TOKEN from env |
| `assessor_client` | module | Real MaricopaAssessorClient factory |
| `shared_rate_limiter` | module | 60 req/min with proactive throttling |
| `record_response` | function | API response recording for drift detection |
| `live_rate_limit` | module | CLI-configurable rate limit |

### NEW Fixtures (from conftest.py lines 195-389)

| Fixture | Scope | Purpose |
|---------|-------|---------|
| `stealth_extraction_config` | module | StealthExtractionConfig with test timeouts |
| `browser_pool` | module | nodriver browser pool management |
| `zillow_extractor` | function | ZillowExtractor instance |
| `redfin_extractor` | function | RedfinExtractor instance |
| `extraction_rate_limiter` | module | 5 req/min for Zillow/Redfin |
| `known_zillow_urls` | session | Regression test URLs |

---

## Mock Requirements

### External Services Requiring Real API Calls

| Service | Endpoint | Test Type |
|---------|----------|-----------|
| Maricopa County Assessor | mcassessor.maricopa.gov | Live API |
| Zillow | www.zillow.com | Stealth Browser |
| Redfin | www.redfin.com | Stealth Browser |

**Note:** These are LIVE tests - no mocking required. Tests validate real API behavior.

---

## Implementation Checklist

### Phase 1: Core Telemetry (DEV Team)

- [ ] Implement token refresh logic in MaricopaAssessorClient
- [ ] Add token expiration tracking
- [ ] Implement proactive refresh before expiry

### Phase 2: Schema Drift Detection

- [ ] Add Pydantic `extra='ignore'` for forward compatibility
- [ ] Add schema version tracking
- [ ] Create drift alerting mechanism

### Phase 3: Fallback Cascade

- [ ] Implement curl_cffi fallback in extraction
- [ ] Implement Playwright fallback tier
- [ ] Add cascade telemetry

### Phase 4: Proxy Rotation

- [ ] Implement proxy pool configuration
- [ ] Add exit IP tracking
- [ ] Implement rotation strategy

---

## Running Tests

```bash
# Collect all tests (verify 40)
pytest tests/live/ -m live --collect-only -q

# Run all live tests (requires API keys and browser)
pytest tests/live/ -m live -v

# Run County Assessor tests only
pytest tests/live/test_county_assessor_live.py -m live -v

# Run Zillow/Redfin tests only
pytest tests/live/test_zillow_redfin_live.py -m live -v

# Run with response recording
pytest tests/live/ -m live -v --record-responses

# Run specific test class
pytest tests/live/test_county_assessor_live.py::TestCountyAssessorAdvanced -m live -v

# Debug specific test
pytest tests/live/test_zillow_redfin_live.py::TestZillowPerimeterXBypass::test_nodriver_perimeter_x_bypass_success -m live -v -s
```

---

## Red-Green-Refactor Workflow

### RED Phase (Complete) ✅

**TEA Agent Responsibilities:**

- ✅ 40 tests written (25 County + 15 Zillow/Redfin)
- ✅ Fixtures created with auto-cleanup
- ✅ Test IDs mapped to test-design-epic-2-7.md
- ✅ Given-When-Then comments in all tests
- ✅ xfail markers for unimplemented features

**Verification:**

```bash
$ pytest tests/live/ -m live --collect-only -q
collected 40 items
```

---

### GREEN Phase (DEV Team - Next Steps)

**Priority Order:**

1. **Token Refresh** - Implement LIVE_COUNTY_016, LIVE_COUNTY_017
2. **Schema Drift** - Implement LIVE_COUNTY_018, LIVE_COUNTY_019
3. **Fallback Cascade** - Implement LIVE_SCRAPE_002, LIVE_SCRAPE_003
4. **Proxy Rotation** - Implement LIVE_SCRAPE_015

**Key Principles:**

- One test at a time (don't try to fix all at once)
- Minimal implementation (don't over-engineer)
- Run tests frequently (immediate feedback)

---

### REFACTOR Phase (After All Tests Pass)

1. Extract common patterns into utilities
2. Optimize rate limiting strategies
3. Add comprehensive logging
4. Document API contract versions

---

## Test Execution Evidence

### Initial Test Collection (RED Phase)

**Command:** `pytest tests/live/ -m live --collect-only -q`

**Results:**

```
collected 40 items

tests/live/test_county_assessor_live.py: 25 tests
tests/live/test_zillow_redfin_live.py: 15 tests

========================= 40 tests collected =========================
```

**Summary:**

- Total tests: 40
- Status: ✅ RED phase verified (tests collected, implementation pending)

---

## Knowledge Base References Applied

This ATDD workflow consulted:

- **fixture-architecture.md** - Playwright-style fixture patterns
- **network-first.md** - Rate limiting and network stability
- **data-factories.md** - Test data generation patterns
- **test-quality.md** - Given-When-Then structure
- **test-levels-framework.md** - Live vs Mock test selection

See `tea-index.csv` for complete knowledge fragment mapping.

---

## Notes

- **Token Required**: MARICOPA_ASSESSOR_TOKEN environment variable required for County tests
- **Browser Required**: nodriver/Chrome required for Zillow/Redfin tests
- **Rate Limits**: Conservative 5 req/min for extraction, 60 req/min for County API
- **xfail Tests**: Tests marked xfail are expected to fail until implementation complete
- **Response Recording**: Use `--record-responses` flag to capture API baselines

---

## Contact

**Questions or Issues?**

- Consult test-design-epic-2-7.md for detailed test specifications
- Refer to `.bmad/bmm/testarch/knowledge/` for testing best practices
- Check `tests/live/README.md` for execution troubleshooting

---

**Generated by BMad TEA Agent** - 2025-12-04
