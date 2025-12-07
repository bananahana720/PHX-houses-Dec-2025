---
story_id: E2-R3
epic: epic-2-property-data-acquisition
title: PhoenixMLS Extended Field Extraction
status: done
priority: P1
points: 13
created: 2025-12-07
completed: 2025-12-07
depends_on: E2-R2
---

# E2-R3: PhoenixMLS Extended Field Extraction

## Summary
Expand PhoenixMLS extraction from 33 fields (E2-R2) to 70+ comprehensive fields, capturing all available MLS data including geo coordinates, legal/parcel data, feature lists, school districts, and contract information.

## Background
E2-R2 implemented 33 fields focused on kill-switch and scoring requirements. Gap analysis of actual PhoenixMLS listings revealed 40+ additional fields available for extraction that provide valuable property intelligence.

**Current State (E2-R2):** 33 fields extracted and persisted
**Target State (E2-R3):** 70+ fields with full MLS coverage

## Acceptance Criteria

### Phase 1: Immediate Wins (Schema Exists)
- [x] **Geo Coordinates (2 fields)**:
  - [ ] Extract `Geo Lat` → `latitude`
  - [ ] Extract `Geo Lon` → `longitude`

- [ ] **Lot/Exterior Features (2 fields)**:
  - [ ] Extract `Fencing` → `lot_features` (list)
  - [ ] Extract `Landscaping` → `lot_features` (append)
  - [ ] Extract `Patio and Porch Features` → `patio_features` (list)

### Phase 2: Legal/Parcel Data (6 new schema fields)
- [ ] **Legal Description**:
  - [ ] Add `township: str | None` to EnrichmentData
  - [ ] Add `range_section: str | None` to EnrichmentData
  - [ ] Add `section: str | None` to EnrichmentData
  - [ ] Add `lot_number: str | None` to EnrichmentData
  - [ ] Add `subdivision: str | None` to EnrichmentData
  - [ ] Add `apn: str | None` to EnrichmentData (Assessor Parcel Number)
  - [ ] Extract all 6 fields from MLS table rows

### Phase 3: Property Structure (4 new schema fields)
- [ ] **Building Details**:
  - [ ] Add `exterior_stories: int | None` to EnrichmentData
  - [ ] Add `interior_levels: str | None` to EnrichmentData
  - [ ] Add `builder_name: str | None` to EnrichmentData
  - [ ] Add `dwelling_styles: str | None` to EnrichmentData (Detached, Attached, etc.)
  - [ ] Extract all 4 fields from MLS

### Phase 4: Feature Lists (10+ new schema fields)
- [ ] **View & Environment**:
  - [ ] Add `view_features: list[str] | None` to EnrichmentData
  - [ ] Add `community_features: list[str] | None` to EnrichmentData
  - [ ] Add `property_description: list[str] | None` to EnrichmentData (N/S Exposure, etc.)

- [ ] **Interior Categories**:
  - [ ] Add `dining_area_features: list[str] | None` to EnrichmentData
  - [ ] Add `technology_features: list[str] | None` to EnrichmentData
  - [ ] Add `window_features: list[str] | None` to EnrichmentData
  - [ ] Add `other_rooms: list[str] | None` to EnrichmentData

- [ ] **Exterior Categories**:
  - [ ] Add `construction_materials: list[str] | None` to EnrichmentData
  - [ ] Add `construction_finish: list[str] | None` to EnrichmentData
  - [ ] Add `parking_features: list[str] | None` to EnrichmentData
  - [ ] Add `fencing_types: list[str] | None` to EnrichmentData

### Phase 5: School Districts (3 new schema fields)
- [ ] **District Names (separate from school names)**:
  - [ ] Add `elementary_district: str | None` to EnrichmentData
  - [ ] Add `middle_district: str | None` to EnrichmentData
  - [ ] Add `high_district: str | None` to EnrichmentData
  - [ ] Extract from "Elementary School District", "Jr. High School District", "High School District"

### Phase 6: Contract/Listing Info (4 new schema fields)
- [ ] **Contract Details**:
  - [ ] Add `list_date: str | None` to EnrichmentData (ISO format)
  - [ ] Add `ownership_type: str | None` to EnrichmentData (Fee Simple, Leasehold)
  - [ ] Add `possession_terms: str | None` to EnrichmentData
  - [ ] Add `new_financing: list[str] | None` to EnrichmentData (Cash, VA, FHA, Conv)

### Phase 7: Additional Fields
- [ ] **Pool Details**:
  - [ ] Add `private_pool_features: list[str] | None` to EnrichmentData
  - [ ] Add `spa_features: str | None` to EnrichmentData
  - [ ] Add `community_pool: bool | None` to EnrichmentData

- [ ] **Updates/Renovations**:
  - [ ] Add `kitchen_year_updated: int | None` to EnrichmentData
  - [ ] Add `kitchen_update_scope: str | None` to EnrichmentData (Partial/Full)

- [ ] **Basement**:
  - [ ] Add `has_basement: bool | None` to EnrichmentData

- [ ] **Additional Details**:
  - [ ] Add `fireplaces_total: int | None` to EnrichmentData
  - [ ] Add `total_covered_spaces: int | None` to EnrichmentData
  - [ ] Add `utilities_provider: list[str] | None` to EnrichmentData (APS, SW Gas)
  - [ ] Add `services_available: list[str] | None` to EnrichmentData

- [ ] **Listing Remarks**:
  - [ ] Add `public_remarks: str | None` to EnrichmentData (Supplements/Description)
  - [ ] Add `directions: str | None` to EnrichmentData

## Technical Requirements

### Schema Changes (entities.py)
- Add ~35 new fields to EnrichmentData class
- Use appropriate types: str | None, int | None, bool | None, list[str] | None
- Group by category with section comments

### Extraction Patterns (phoenix_mls.py)
- Add regex patterns for new field labels
- Handle comma-separated values → list conversion
- Parse boolean values (Yes/No/Y/N)
- Handle numeric extraction (year, counts)

### Field Mapping (metadata_persister.py)
- Expand MLS_FIELD_MAPPING from 33 to ~68 entries
- Maintain category organization

### Unit Tests
- Test each new extraction pattern
- Test edge cases (missing fields, malformed HTML)
- Integration test with comprehensive HTML fixture

## Tasks/Subtasks

### Task 1: Schema Updates (entities.py)
- [ ] 1.1 Add Legal/Parcel fields (6 fields)
- [ ] 1.2 Add Property Structure fields (4 fields)
- [ ] 1.3 Add Feature List fields (11 fields)
- [ ] 1.4 Add School District fields (3 fields)
- [ ] 1.5 Add Contract/Listing fields (4 fields)
- [ ] 1.6 Add Pool/Updates/Misc fields (10 fields)

### Task 2: Extraction Patterns (phoenix_mls.py)
- [ ] 2.1 Add geo coordinate extraction (lat/lon)
- [ ] 2.2 Add legal/parcel extraction patterns
- [ ] 2.3 Add property structure extraction patterns
- [ ] 2.4 Add feature list extraction patterns (comma → list)
- [ ] 2.5 Add school district extraction patterns
- [ ] 2.6 Add contract/listing extraction patterns
- [ ] 2.7 Add pool/updates/misc extraction patterns

### Task 3: Field Mapping (metadata_persister.py)
- [ ] 3.1 Add mappings for all new extracted fields
- [ ] 3.2 Maintain category organization in MLS_FIELD_MAPPING

### Task 4: Unit Tests
- [ ] 4.1 Create comprehensive HTML fixture with all fields
- [ ] 4.2 Add tests for each new extraction category
- [ ] 4.3 Add edge case tests

### Task 5: Validation
- [ ] 5.1 Run ruff check --fix && ruff format
- [ ] 5.2 Run mypy src/
- [ ] 5.3 Run pytest tests/unit/services/image_extraction/test_phoenix_mls_metadata.py -v
- [ ] 5.4 Run full test suite

## Dependencies
- E2-R2: PhoenixMLS Full Listing Attribute Extraction (complete)
- EnrichmentData schema (entities.py)
- PhoenixMLS extractor (phoenix_mls.py)

## Dev Notes

### Field Categories Reference (from actual MLS listing)

**Contract Information:**
- List Price, Status, Current Price, List Date, Type, Ownership, Co-Ownership Agreement YN

**Location Tax Legal:**
- House Number, Compass, Street Name, St Suffix, City/Town Code, State/Province
- Zip Code, Zip4, County Code, Assessor Number, Subdivision, Tax Year

**Legal Info:**
- Township, Range, Section, Lot Number

**General Property Description:**
- Dwelling Type, Dwelling Styles, Exterior Stories, Interior Levels
- Bedrooms, Full Bathrooms, Total Bathrooms, Approx SQFT, Price/SqFt
- Horses, Builder Name, Year Built, Approx Lot SqFt, Approx Lot Acres
- Community Pool Y/N, Private Pool Y/N, Fireplace YN, Fireplaces Total

**Schools:**
- Elementary School District, High School District
- Elementary School, Jr. High School, High School

**Geo:**
- Geo Lat, Geo Lon

**Items Updated:**
- Kitchen Yr Updated, Kitchen Partial/Full

**Parking:**
- Garage Spaces, Total Covered Spaces

**Property Features (comma-separated lists):**
- View, Master Bathroom, Master Bedroom, Additional Bedroom
- Fireplace Features, Flooring, Window Features
- Private Pool Features, Spa, Community Features
- Dining Area, Kitchen Features, Laundry, Other Rooms
- Interior Features, Technology, Exterior Features
- Parking Features, Construction, Const - Finish, Roofing
- Cooling, Heating, Utilities, Water Source, Sewer
- Services, Fencing, Property Description, Landscaping
- Possession, Unit Style, Association Fee Incl
- New Financing, Disclosures

**Supplements:**
- Public Remarks (description paragraph)

## Estimated Effort
- Schema changes: 2 hours
- Extraction patterns: 4 hours
- Field mapping: 1 hour
- Unit tests: 3 hours
- Validation: 1 hour
- **Total**: 11 hours (13 story points)

## File List
| File | Change |
|------|--------|
| `src/phx_home_analysis/domain/entities.py` | Add ~35 new EnrichmentData fields |
| `src/phx_home_analysis/services/image_extraction/extractors/phoenix_mls.py` | Add extraction patterns |
| `src/phx_home_analysis/services/image_extraction/metadata_persister.py` | Expand MLS_FIELD_MAPPING |
| `tests/unit/services/image_extraction/test_phoenix_mls_metadata.py` | Add comprehensive tests |

## Change Log
| Date | Change | Author |
|------|--------|--------|
| 2025-12-07 | Story created from gap analysis | Claude |
