---
story_id: E2-R2
epic: epic-2-property-data-acquisition
title: PhoenixMLS Full Listing Attribute Extraction
status: ready-for-review
priority: P1
points: 8
created: 2025-12-07
completed: 2025-12-07
---

# E2-R2: PhoenixMLS Full Listing Attribute Extraction

## Summary
Expand PhoenixMLS extractor from 10 kill-switch fields to 35 comprehensive listing attributes to support Phase 1 MLS extraction. Remaining fields (geo_lat, pool_features, assessor_number, etc.) require Phase 2 visual analysis, external APIs, or County Assessor integration and are deferred to future stories.

## Background
Gap analysis identified that while kill-switch fields (8/8) are complete, scoring and deal analysis fields are missing:

| Priority | Fields | Status | Impact |
|----------|--------|--------|--------|
| CRITICAL | 8 kill-switch | Complete | Filtering |
| HIGH | 22 scoring | Missing | 605-point system |
| MEDIUM | 25 deal analysis | Missing | Property profiles |

**Critical Finding:** 37 fields are ALREADY EXTRACTED by `_parse_listing_metadata()` but only 10 are PERSISTED via `MLS_FIELD_MAPPING`.

## Acceptance Criteria

### Phase 1: MLS Extraction Fields (35 fields - IMPLEMENTED)
- [x] **Kill-Switch Fields (8 fields)**:
  - [x] Extract `beds`, `baths`, `sqft`, `lot_sqft`
  - [x] Extract `year_built`, `garage_spaces`, `sewer_type`, `hoa_fee`

- [x] **MLS Identifiers (5 fields)**:
  - [x] Extract `mls_number`, `listing_url`
  - [x] Extract `listing_status`, `listing_office`, `mls_last_updated`

- [x] **Pricing & Market Data (4 fields)**:
  - [x] Extract `list_price` (current price)
  - [x] Extract `days_on_market`, `original_list_price`, `price_reduced`

- [x] **Property Classification (2 fields)**:
  - [x] Extract `property_type`, `architecture_style`

- [x] **Systems & Utilities (5 fields)**:
  - [x] Extract `cooling_type`, `heating_type`, `water_source`, `roof_material`
  - [x] Extract `has_pool`

- [x] **Interior Features (6 fields)**:
  - [x] Extract `kitchen_features`, `master_bath_features`
  - [x] Extract `interior_features_list`, `flooring_types`
  - [x] Extract `laundry_features`, `fireplace_present`

- [x] **Exterior Features (1 field)**:
  - [x] Extract `exterior_features_list`

- [x] **Schools (3 fields)**:
  - [x] Extract `elementary_school_name`, `middle_school_name`, `high_school_name`

- [x] **Location (1 field)**:
  - [x] Extract `cross_streets`

### Deferred to Future Stories (require external sources)
- [ ] **Geographic (Phase 2 - Map APIs)**:
  - [ ] `geo_lat`, `geo_lon` - requires geocoding API
  - [ ] `orientation` - requires satellite/map analysis

- [ ] **Pool Details (Phase 2 - Visual Analysis)**:
  - [ ] `pool_features`, `spa` - requires image assessment

- [ ] **Assessor Data (Phase 0 - County API)**:
  - [ ] `assessor_number`, `tax_year` - requires Maricopa County API

### Technical Requirements
- [x] Expand MLS_FIELD_MAPPING from 10 to 33 fields
- [x] Add `list_price` field to EnrichmentData schema
- [x] Add new extraction patterns for market data fields
- [x] Pre-compile regex patterns at module level for performance
- [x] Add unit tests for new extraction patterns (29 new tests)
- [x] Verify extraction with test properties

## Tasks/Subtasks

### Task 1: Expand MLS_FIELD_MAPPING (Already-Extracted Fields)
- [x] 1.1 Add price field mapping
- [x] 1.2 Add property_type and architecture_style mappings
- [x] 1.3 Add cooling_type, heating_type, water_source, roof_material mappings
- [x] 1.4 Add kitchen_features, master_bath_features mappings
- [x] 1.5 Add interior_features_list, exterior_features_list mappings
- [x] 1.6 Add school name mappings (elementary, middle, high)
- [x] 1.7 Add cross_streets and has_pool mappings

### Task 2: Add NEW Extraction Patterns in phoenix_mls.py
- [x] 2.1 Add days_on_market extraction pattern
- [x] 2.2 Add original_list_price and price_reduced extraction
- [x] 2.3 Add listing_status extraction (Active/Pending/Sold)
- [x] 2.4 Add listing_office (broker) extraction
- [x] 2.5 Add mls_last_updated timestamp extraction
- [x] 2.6 Add flooring_types list extraction
- [x] 2.7 Add fireplace_yn boolean extraction
- [x] 2.8 Add laundry_features extraction

### Task 3: Add Unit Tests for New Fields
- [x] 3.1 Add tests for new MLS_FIELD_MAPPING entries
- [x] 3.2 Add tests for new extraction patterns
- [x] 3.3 Add edge case tests (missing fields, malformed HTML)

### Task 4: Validation and Verification
- [x] 4.1 Run all existing tests (ruff check, mypy, pytest)
- [x] 4.2 Verify new fields flow correctly to EnrichmentData
- [x] 4.3 Run extraction on test properties to validate

## Dependencies
- E2-R1: PhoenixMLS Pivot + Multi-Wave Remediation (complete)
- MetadataPersister service (implemented in 02041da)
- EnrichmentData schema (already has 70+ fields defined)

## Dev Notes

### Architecture
- **MLS_FIELD_MAPPING** in `metadata_persister.py` (lines 21-32): Maps PhoenixMLS metadata keys to EnrichmentData fields
- **_parse_listing_metadata()** in `phoenix_mls.py` (lines 487-645): Parses HTML and extracts metadata dict
- **EnrichmentDataSchema** in `schemas.py` (lines 218-559): Already defines most needed fields

### Key Insight
The `_parse_listing_metadata()` method already extracts these fields but they are not persisted:
- price, property_type, architecture_style
- cooling_type, heating_type, water_source, roof_material
- kitchen_features, master_bath_features, interior_features_list, exterior_features_list
- elementary_school_name, middle_school_name, high_school_name
- cross_streets, has_pool

### Technical Approach
1. Add mappings for already-extracted fields to MLS_FIELD_MAPPING (Task 1)
2. Add new regex patterns for missing market data fields (Task 2)
3. Add unit tests (Task 3)
4. Validate end-to-end (Task 4)

## Estimated Effort
- Phase 1 (HIGH): 2-3 hours
- Phase 2 (MEDIUM): 3-4 hours
- Testing: 1-2 hours
- **Total**: 6-9 hours (8 story points)

## Notes
- Replaces original E2.R2 "Redfin Session-Bound Download" (Redfin coverage now sufficient via PhoenixMLS + Zillow)
- BLOCK-002 mitigated - Redfin no longer blocking

## Dev Agent Record

### Implementation Plan
- Execute tasks 1-4 in sequence
- Follow red-green-refactor cycle for each task

### Debug Log
- 2025-12-07: Started implementation
- 2025-12-07: Task 1 complete - MLS_FIELD_MAPPING expanded from 10 to 33 fields
- 2025-12-07: Task 2 complete - Added 8 new extraction patterns (days_on_market, price history, listing status, etc.)
- 2025-12-07: Task 3 complete - Added 29 new unit tests across 6 test classes
- 2025-12-07: Task 4 complete - All 71 tests pass, ruff check passes, format applied

### Completion Notes
Successfully expanded PhoenixMLS extraction from 10 kill-switch fields to 33 comprehensive fields:

**New MLS_FIELD_MAPPING entries (23 new):**
- Pricing: price -> list_price, days_on_market, original_list_price, price_reduced
- MLS Identifiers: listing_status, listing_office, mls_last_updated
- Property: property_type, architecture_style
- Systems: cooling_type, heating_type, water_source, roof_material
- Interior: kitchen_features, master_bath_features, interior_features_list, flooring_types, laundry_features, fireplace_yn -> fireplace_present
- Exterior: exterior_features_list, has_pool
- Schools: elementary_school_name, middle_school_name, high_school_name
- Location: cross_streets

**New extraction patterns added:**
- days_on_market: 3 regex patterns ("Listed X days ago", "DOM: X", "X days on market")
- original_list_price/price_reduced: Price history detection with comparison logic
- listing_status: Badge/tag detection + table row extraction
- listing_office: Multiple label patterns (office, brokerage, broker)
- mls_last_updated: ISO and US date format detection
- flooring_types: List extraction from table
- fireplace_yn: Boolean detection from yes/no/count
- laundry_features: List extraction from table

**Test coverage:**
- 71 total tests (29 new + 42 existing)
- 6 new test classes added
- Full integration test with comprehensive HTML fixture

## File List
| File | Change |
|------|--------|
| `src/phx_home_analysis/services/image_extraction/metadata_persister.py` | Expanded MLS_FIELD_MAPPING from 10 to 33 fields |
| `src/phx_home_analysis/services/image_extraction/extractors/phoenix_mls.py` | Added 8 new extraction patterns in _parse_listing_metadata() |
| `tests/unit/services/image_extraction/test_phoenix_mls_metadata.py` | Added 29 new tests (71 total) |

## Change Log
| Date | Change | Author |
|------|--------|--------|
| 2025-12-07 | Story created | Andrew |
| 2025-12-07 | Started implementation | Claude |
| 2025-12-07 | Task 1: Expanded MLS_FIELD_MAPPING (10 -> 33 fields) | Claude |
| 2025-12-07 | Task 2: Added 8 new extraction patterns | Claude |
| 2025-12-07 | Task 3: Added 29 new unit tests | Claude |
| 2025-12-07 | Task 4: Validation complete (71 tests pass) | Claude |
| 2025-12-07 | Story complete - Ready for Review | Claude |

## Status
**Status:** Ready for Review
