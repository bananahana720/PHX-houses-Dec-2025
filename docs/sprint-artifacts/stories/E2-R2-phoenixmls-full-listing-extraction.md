---
story_id: E2-R2
epic: epic-2-property-data-acquisition
title: PhoenixMLS Full Listing Attribute Extraction
status: backlog
priority: P1
points: 8
created: 2025-12-07
---

# E2-R2: PhoenixMLS Full Listing Attribute Extraction

## Summary
Expand PhoenixMLS extractor from 10 kill-switch fields to 47+ comprehensive listing attributes to support full 605-point scoring system and deal analysis.

## Background
Gap analysis identified that while kill-switch fields (8/8) are complete, scoring and deal analysis fields are missing:

| Priority | Fields | Status | Impact |
|----------|--------|--------|--------|
| 🔴 CRITICAL | 8 kill-switch | ✅ Complete | Filtering |
| 🟡 HIGH | 22 scoring | ❌ Missing | 605-point system |
| 🟢 MEDIUM | 25 deal analysis | ❌ Missing | Property profiles |

## Acceptance Criteria

### Phase 1: HIGH Priority Scoring Fields (22 fields)
- [ ] **Location (Section A - 250 pts)**:
  - [ ] Extract `geo_lat`, `geo_lon` for map analysis
  - [ ] Extract `elementary_school`, `jr_high_school`, `high_school`
  - [ ] Extract orientation from `property_description` (N/S/E/W exposure)

- [ ] **Systems (Section B - 175 pts)**:
  - [ ] Extract `roofing` (roof material/condition)
  - [ ] Extract `private_pool_yn`, `pool_partial_full`, `pool_features`, `spa`
  - [ ] Extract `cooling`, `heating` (HVAC types)
  - [ ] Extract `price_per_sqft` for cost efficiency

- [ ] **Interior (Section C - 180 pts)**:
  - [ ] Extract `kitchen_features` (appliances, counters, layout)
  - [ ] Extract `master_bathroom`, `master_bedroom` features
  - [ ] Extract `fireplace_yn`, `fireplaces_total`
  - [ ] Extract `interior_features` (ceiling height, flooring)
  - [ ] Extract `laundry` location and features
  - [ ] Extract `flooring` types

### Phase 2: MEDIUM Priority Deal Analysis Fields (25 fields)
- [ ] **Pricing & Status**:
  - [ ] Extract `list_price`, `current_price`, `status`, `list_date`

- [ ] **Property Structure**:
  - [ ] Extract `dwelling_type`, `exterior_stories`, `total_bathrooms`

- [ ] **Lot & Community**:
  - [ ] Extract `lot_acres`, `subdivision`, `community_features`

- [ ] **Exterior & Utilities**:
  - [ ] Extract `construction`, `exterior_features`, `water_source`, `utilities`, `fencing`, `landscaping`

- [ ] **Parking & Rooms**:
  - [ ] Extract `carport_spaces`, `total_covered_spaces`, `other_rooms`

- [ ] **Assessor**:
  - [ ] Extract `assessor_number`, `tax_year`

### Technical Requirements
- [ ] Refactor `_extract_kill_switch_fields()` → `_extract_listing_metadata()`
- [ ] Add 22 HIGH-priority regex patterns
- [ ] Add 25 MEDIUM-priority regex patterns
- [ ] Add corresponding fields to EnrichmentData schema
- [ ] Update MetadataPersister field mapping
- [ ] Add unit tests for new extraction patterns
- [ ] Verify with 5+ diverse test properties

## Dependencies
- E2-R1: PhoenixMLS Pivot + Multi-Wave Remediation ✅ (complete)
- MetadataPersister service ✅ (implemented in 02041da)
- EnrichmentData schema ✅ (beds/baths/sqft added in 02041da)

## Estimated Effort
- Phase 1 (HIGH): 2-3 hours
- Phase 2 (MEDIUM): 3-4 hours
- Testing: 1-2 hours
- **Total**: 6-9 hours (8 story points)

## Notes
- Replaces original E2.R2 "Redfin Session-Bound Download" (Redfin coverage now sufficient via PhoenixMLS + Zillow)
- BLOCK-002 mitigated - Redfin no longer blocking
