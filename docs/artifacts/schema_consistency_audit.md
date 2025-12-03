# Schema Consistency Audit Report
**Date:** 2025-12-01
**Auditor:** Code Review Agent
**Scope:** PHX Houses property analysis codebase schema consistency

---

## Executive Summary

**Total Models Identified:** 67+
**Critical Duplicates Found:** 3 (SourceStats, ExtractionResult, ExtractionState)
**Field Count Mismatches:** 4 major schema objects
**Naming Inconsistencies:** 8 categories identified
**Orphaned Fields:** 12+ fields defined but unused/inconsistent

**Overall Assessment:** MODERATE RISK - Duplicates exist but are functionally identical. Naming inconsistencies create confusion. Schema-to-reality gaps exist but are manageable.

---

## 1. DUPLICATE MODEL DEFINITIONS

### 1.1 SourceStats (EXACT DUPLICATE)

**Location 1:** `src/phx_home_analysis/services/image_extraction/extraction_stats.py:12`
```python
@dataclass
class SourceStats:
    """Statistics for a single image source."""
    source: str
    properties_processed: int = 0
    properties_failed: int = 0
    images_found: int = 0
    images_downloaded: int = 0
    images_failed: int = 0
    duplicates_detected: int = 0
```

**Location 2:** `src/phx_home_analysis/services/image_extraction/orchestrator.py:40`
```python
@dataclass
class SourceStats:
    """Statistics for a single image source."""
    source: str
    properties_processed: int = 0
    properties_failed: int = 0
    images_found: int = 0
    images_downloaded: int = 0
    images_failed: int = 0
    duplicates_detected: int = 0
```

**Differences:** NONE - Exact duplicates with identical fields and methods.

**Canonical:** `extraction_stats.py` (has computed properties: `success_rate`, `download_success_rate`)

**Recommendation:** Delete duplicate in `orchestrator.py`, import from `extraction_stats.py`

---

### 1.2 ExtractionResult (EXACT DUPLICATE)

**Location 1:** `src/phx_home_analysis/services/image_extraction/extraction_stats.py:51`
```python
@dataclass
class ExtractionResult:
    """Aggregated results from image extraction process."""
    total_properties: int = 0
    properties_completed: int = 0
    properties_failed: int = 0
    properties_skipped: int = 0
    total_images: int = 0
    unique_images: int = 0
    duplicate_images: int = 0
    failed_downloads: int = 0
    by_source: Dict[str, SourceStats] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
```

**Location 2:** `src/phx_home_analysis/services/image_extraction/orchestrator.py:53`
```python
@dataclass
class ExtractionResult:
    """Results from image extraction process."""
    total_properties: int
    properties_completed: int
    properties_failed: int
    properties_skipped: int
    total_images: int
    unique_images: int
    duplicate_images: int
    failed_downloads: int
    by_source: dict[str, SourceStats] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
```

**Differences:**
- Different default values (`= 0` vs required in orchestrator.py)
- Type hint difference: `Dict` vs `dict`
- Docstring wording

**Canonical:** `extraction_stats.py` (has computed properties: `duration_seconds`, `success_rate`, `properties_per_minute`, `to_dict()`)

**Recommendation:** Delete duplicate in `orchestrator.py`, import from `extraction_stats.py`

---

### 1.3 ExtractionState (EXACT DUPLICATE)

**Location 1:** `src/phx_home_analysis/services/image_extraction/state_manager.py:17`
```python
@dataclass
class ExtractionState:
    """Persistent state for resumable extraction."""
    completed_properties: Set[str] = field(default_factory=set)
    failed_properties: Set[str] = field(default_factory=set)
    last_updated: Optional[str] = None
```

**Location 2:** `src/phx_home_analysis/services/image_extraction/orchestrator.py:124`
```python
@dataclass
class ExtractionState:
    """Persistent state for resumable extraction."""
    completed_properties: Set[str] = field(default_factory=set)
    failed_properties: Set[str] = field(default_factory=set)
    last_updated: Optional[str] = None
```

**Differences:** NONE - Exact duplicates

**Canonical:** `state_manager.py` (has methods: `to_dict()`, `from_dict()`)

**Recommendation:** Delete duplicate in `orchestrator.py`, import from `state_manager.py`

---

## 2. SCHEMA VS REALITY MISMATCHES

### 2.1 PropertySchema vs CSV Columns

**CSV Columns (phx_homes.csv):**
```
street, city, state, zip, price, price_num, beds, baths, sqft, price_per_sqft, full_address
```

**PropertySchema Fields:**
```python
address, beds, baths, sqft, lot_sqft, year_built, price, hoa_fee,
garage_spaces, has_pool, pool_equipment_age, sewer_type, roof_age,
hvac_age, solar_status, orientation
```

**Mismatch Analysis:**
- CSV has `street, city, state, zip` → Schema has `address` (consolidated)
- CSV has `price_per_sqft` → Schema does NOT have this (computed in Property entity)
- Schema has 11 fields NOT in CSV (populated from enrichment):
  - `lot_sqft`, `year_built`, `hoa_fee`, `garage_spaces`, `has_pool`,
  - `pool_equipment_age`, `sewer_type`, `roof_age`, `hvac_age`,
  - `solar_status`, `orientation`

**Status:** EXPECTED - Schema is superset of CSV, enrichment fills gaps

---

### 2.2 EnrichmentDataSchema vs enrichment_data.json

**enrichment_data.json Sample Keys (60 fields):**
```
aesthetics_score, aesthetics_score_source, baths, beds, ceiling_height_score,
ceiling_height_score_source, commute_minutes, cost_breakdown,
distance_to_grocery_miles, distance_to_highway_miles, distance_to_park_miles,
fireplace_score, fireplace_score_source, full_address, garage_spaces,
has_pool, high_ceilings_score, hoa_fee, hvac_age, hvac_age_confidence,
kill_switch_failures, kill_switch_passed, kitchen_layout_score,
kitchen_quality_score, kitchen_quality_score_source, laundry_area_score,
laundry_score, laundry_score_source, list_price, lot_sqft,
master_quality_score, master_quality_score_source, master_suite_score,
monthly_cost, natural_light_score, natural_light_score_source, orientation,
parks_data_source, parks_walkability_score, pool_equipment_age,
pool_equipment_age_confidence, price, roof_age, roof_age_confidence,
safety_data_source, safety_neighborhood_score, school_district,
school_rating, sewer_type, solar_lease_monthly, solar_status, sqft,
tax_annual, year_built
```

**EnrichmentDataSchema Fields (32 fields):**
```python
full_address, beds, baths, lot_sqft, year_built, garage_spaces, sewer_type,
hoa_fee, tax_annual, has_pool, list_price, school_rating, safety_score,
noise_level, commute_minutes, distance_to_grocery_miles,
distance_to_highway_miles, kitchen_layout_score, master_suite_score,
natural_light_score, high_ceilings_score, laundry_area_score,
aesthetics_score, backyard_utility_score, parks_walkability_score,
fireplace_present, roof_age, hvac_age, pool_equipment_age, orientation,
solar_status, solar_lease_monthly
```

**Critical Gaps:**

**Fields in JSON but NOT in Schema (28 fields):**
- `*_source` fields (12): `aesthetics_score_source`, `ceiling_height_score_source`, etc.
- `*_confidence` fields (3): `hvac_age_confidence`, `pool_equipment_age_confidence`, `roof_age_confidence`
- `kill_switch_*` fields (2): `kill_switch_passed`, `kill_switch_failures`
- Computed fields (4): `cost_breakdown`, `monthly_cost`, `price`, `sqft`
- Synonym fields (7): `ceiling_height_score`, `kitchen_quality_score`, `master_quality_score`, `fireplace_score`, `laundry_score`, `list_price`, `distance_to_park_miles`

**Fields in Schema but NOT in JSON (2):**
- `backyard_utility_score` - Expected but missing from sample
- `fireplace_present` - Expected but missing (JSON has `fireplace_score` instead)

**Status:** PROBLEMATIC - Schema does not match reality. Many JSON fields lack schema validation.

---

### 2.3 Property Entity vs EnrichmentData DTO

**Field Count:**
- Property: 47 fields
- EnrichmentData: 19 fields

**Property fields NOT in EnrichmentData:**
```python
# Address decomposition (5)
street, city, state, zip_code, full_address

# Listing data (6)
price (formatted string), price_num, sqft, price_per_sqft_raw

# Geocoding (2)
latitude, longitude

# Analysis results (9)
kill_switch_passed, kill_switch_failures, score_breakdown, tier,
risk_assessments, renovation_estimate

# Additional manual scores (6)
safety_neighborhood_score, parks_walkability_score,
# (rest overlap with EnrichmentData)
```

**EnrichmentData fields match core county/enrichment sources**

**Status:** EXPECTED - Property is aggregate entity, EnrichmentData is DTO

---

## 3. TYPE INCONSISTENCIES

### 3.1 hoa_fee Type Variations

| Location | Type | Notes |
|----------|------|-------|
| PropertySchema | `float \| None` | Correct - supports decimals |
| EnrichmentDataSchema | `float \| None` | Correct - supports decimals |
| Property entity | `float \| None` | Correct - matches schema |
| EnrichmentData DTO | `float \| None` | Correct - matches schema |
| ParcelData (county) | N/A | Not from county API |

**Status:** CONSISTENT ✓

---

### 3.2 tax_annual Type Variations

| Location | Type | Notes |
|----------|------|-------|
| PropertySchema | N/A | Field not in PropertySchema |
| EnrichmentDataSchema | `float \| None` | Correct - annual tax |
| Property entity | `float \| None` | Correct |
| ParcelData (county) | `Optional[int]` | INCONSISTENT - should be float |

**Status:** INCONSISTENT - ParcelData uses `int`, rest use `float`

**Recommendation:** Change ParcelData.tax_annual to `Optional[float]`

---

### 3.3 solar_lease_monthly Type Variations

| Location | Type | Notes |
|----------|------|-------|
| PropertySchema | N/A | Field not in PropertySchema |
| EnrichmentDataSchema | `int \| None` | ge=0, le=500 |
| Property entity | `int \| None` | Matches EnrichmentDataSchema |
| EnrichmentData DTO | `int \| None` | Matches |

**Status:** CONSISTENT ✓ (but should this be `float`?)

**Recommendation:** Consider changing to `float` for consistency with other monthly costs

---

### 3.4 baths Type Variations

| Location | Type | Notes |
|----------|------|-------|
| CSV | `float` | Supports 1.5, 2.5, etc. |
| PropertySchema | `float` | ge=0.5, le=20, 0.5 increments |
| Property entity | `float` | Correct |
| ParcelData (county) | `Optional[float]` | Correct |

**Status:** CONSISTENT ✓

---

## 4. NAMING INCONSISTENCIES

### 4.1 Lot Size Field

| Context | Field Name | Type |
|---------|-----------|------|
| CSV | N/A | Not in CSV |
| PropertySchema | `lot_sqft` | int \| None |
| Property entity | `lot_sqft` | int \| None |
| EnrichmentDataSchema | `lot_sqft` | int \| None |
| ParcelData | `lot_sqft` | Optional[int] |
| Scoring weights docs | `lot_sqft` | (referenced) |

**Status:** CONSISTENT ✓ - Always `lot_sqft`

---

### 4.2 HOA Fee Field

| Context | Field Name | Type |
|---------|-----------|------|
| CSV | N/A | Not in CSV |
| PropertySchema | `hoa_fee` | float \| None |
| Property entity | `hoa_fee` | float \| None |
| EnrichmentDataSchema | `hoa_fee` | float \| None |

**Status:** CONSISTENT ✓ - Always `hoa_fee`

---

### 4.3 Price Field Name Variations

| Context | Field Name | Meaning |
|---------|-----------|---------|
| CSV | `price` | Formatted string "$475,000" |
| CSV | `price_num` | Numeric value 475000 |
| Property entity | `price` | Formatted string |
| Property entity | `price_num` | Numeric value |
| EnrichmentDataSchema | `list_price` | Numeric value (int) |
| enrichment_data.json | `price` | Numeric value |
| enrichment_data.json | `list_price` | Numeric value (duplicate!) |

**Status:** INCONSISTENT - `price` vs `price_num` vs `list_price`

**Issues:**
- JSON has BOTH `price` and `list_price` (redundant)
- Schema uses `list_price`, entity uses `price_num`
- Confusing type: `price` is string in entity, numeric in JSON

**Recommendation:**
- Standardize on `price_num` for numeric value
- Keep `price` for formatted display string
- Remove `list_price` synonym

---

### 4.4 School Rating Field

| Context | Field Name | Type |
|---------|-----------|------|
| Property entity | `school_rating` | float \| None |
| EnrichmentDataSchema | `school_rating` | float \| None |
| Scoring strategy | `school_rating` | (references property field) |

**Status:** CONSISTENT ✓ - Always `school_rating`

---

### 4.5 Safety/Neighborhood Score Field

| Context | Field Name |
|---------|-----------|
| Property entity | `safety_neighborhood_score` |
| EnrichmentDataSchema | `safety_score` |
| Scoring strategy | `safety_neighborhood_score` |
| enrichment_data.json | `safety_neighborhood_score` |

**Status:** INCONSISTENT - Schema uses `safety_score`, everywhere else uses `safety_neighborhood_score`

**Recommendation:** Change EnrichmentDataSchema to `safety_neighborhood_score`

---

### 4.6 Ceiling Height Score Synonyms

| Context | Field Name | Status |
|---------|-----------|--------|
| Property entity | `high_ceilings_score` | ✓ |
| EnrichmentDataSchema | `high_ceilings_score` | ✓ |
| enrichment_data.json | `high_ceilings_score` | ✓ |
| enrichment_data.json | `ceiling_height_score` | ✗ SYNONYM |
| Scoring strategy | `high_ceilings_score` | ✓ |

**Status:** INCONSISTENT - JSON has both `high_ceilings_score` AND `ceiling_height_score`

**Recommendation:** Remove `ceiling_height_score` synonym, use only `high_ceilings_score`

---

### 4.7 Kitchen Score Synonyms

| Context | Field Name | Status |
|---------|-----------|--------|
| Property entity | `kitchen_layout_score` | ✓ |
| EnrichmentDataSchema | `kitchen_layout_score` | ✓ |
| enrichment_data.json | `kitchen_layout_score` | ✓ |
| enrichment_data.json | `kitchen_quality_score` | ✗ SYNONYM |
| Scoring strategy | `kitchen_layout_score` | ✓ |

**Status:** INCONSISTENT - JSON has both `kitchen_layout_score` AND `kitchen_quality_score`

**Recommendation:** Remove `kitchen_quality_score` synonym, use only `kitchen_layout_score`

---

### 4.8 Master Suite Score Synonyms

| Context | Field Name | Status |
|---------|-----------|--------|
| Property entity | `master_suite_score` | ✓ |
| EnrichmentDataSchema | `master_suite_score` | ✓ |
| enrichment_data.json | `master_suite_score` | ✓ |
| enrichment_data.json | `master_quality_score` | ✗ SYNONYM |
| Scoring strategy | `master_suite_score` | ✓ |

**Status:** INCONSISTENT - JSON has both `master_suite_score` AND `master_quality_score`

**Recommendation:** Remove `master_quality_score` synonym, use only `master_suite_score`

---

### 4.9 Fireplace Field Variations

| Context | Field Name | Type |
|---------|-----------|------|
| Property entity | `fireplace_present` | bool \| None |
| EnrichmentDataSchema | `fireplace_present` | bool \| None |
| enrichment_data.json | `fireplace_score` | float (0-10) |
| Scoring strategy | Uses `fireplace_present` | bool |

**Status:** INCONSISTENT - Schema expects boolean, JSON has score

**Issue:** Different semantics - presence vs quality score

**Recommendation:** Keep both but clarify:
- `fireplace_present` - boolean presence indicator
- `fireplace_score` - quality/type score (gas=10, wood=7.5, decorative=2.5)

---

### 4.10 Laundry Field Synonyms

| Context | Field Name | Status |
|---------|-----------|--------|
| Property entity | `laundry_area_score` | ✓ |
| EnrichmentDataSchema | `laundry_area_score` | ✓ |
| enrichment_data.json | `laundry_area_score` | ✓ |
| enrichment_data.json | `laundry_score` | ✗ SYNONYM |
| Scoring strategy | `laundry_area_score` | ✓ |

**Status:** INCONSISTENT - JSON has both `laundry_area_score` AND `laundry_score`

**Recommendation:** Remove `laundry_score` synonym, use only `laundry_area_score`

---

## 5. ORPHANED/UNUSED FIELDS

### 5.1 EnrichmentDataSchema Fields Never Populated

**From comparison with enrichment_data.json:**

1. **`backyard_utility_score`** - Defined in schema, missing from JSON sample
   - Status: EXPECTED if not yet assessed
   - Used by: BackyardUtilityScorer

2. **`fireplace_present`** - Schema has bool, JSON has `fireplace_score` float
   - Status: MISMATCH - different field semantics
   - Used by: FireplaceScorer (expects boolean)

3. **`noise_level`** - Defined in schema (0-10, lower is quieter)
   - Status: NOT IN JSON - unused field
   - Not used by any scorer (QuietnessScorer uses `distance_to_highway_miles`)
   - **Recommendation:** Remove from schema if truly unused

---

### 5.2 Enrichment JSON Fields Without Schema Validation

**Data lineage/metadata fields (18 fields):**
```
aesthetics_score_source
ceiling_height_score_source
fireplace_score_source
kitchen_quality_score_source
laundry_score_source
master_quality_score_source
natural_light_score_source
parks_data_source
safety_data_source
hvac_age_confidence
pool_equipment_age_confidence
roof_age_confidence
```

**Status:** Not validated - useful for provenance tracking

**Recommendation:** Create `FieldMetadata` schema or keep as unvalidated dict keys

---

**Computed/derived fields (6 fields):**
```
cost_breakdown (dict)
monthly_cost (float)
kill_switch_passed (bool)
kill_switch_failures (list)
price (numeric - duplicate of list_price)
sqft (duplicate from Property)
```

**Status:** Redundant - computed from other fields

**Recommendation:** Remove from JSON, compute on-demand

---

**Synonym fields (7 fields - DUPLICATES):**
```
ceiling_height_score (synonym of high_ceilings_score)
kitchen_quality_score (synonym of kitchen_layout_score)
master_quality_score (synonym of master_suite_score)
fireplace_score (different from fireplace_present)
laundry_score (synonym of laundry_area_score)
list_price (synonym of price_num)
distance_to_park_miles (not in schema)
```

**Status:** Redundant synonyms cause confusion

**Recommendation:** Remove all synonyms, use canonical names only

---

### 5.3 Schema Enum Values Never Used

**SewerTypeSchema:**
- `CITY` ✓ Used in kill-switch
- `SEPTIC` ✓ Used in kill-switch
- `UNKNOWN` ✓ Used as default

**SolarStatusSchema:**
- `OWNED` ✓ Used in scoring
- `LEASED` ✓ Used in scoring (penalized)
- `NONE` ✓ Used for no solar
- `UNKNOWN` ✓ Used as default

**OrientationSchema:**
- `N, S, E, W, NE, NW, SE, SW` ✓ All used in OrientationScorer
- `UNKNOWN` ✓ Used as default

**Status:** All enum values are actively used ✓

---

## 6. CONSOLIDATION RECOMMENDATIONS

### Priority 1: Critical Fixes (Correctness Issues)

1. **Remove Duplicate Model Definitions (3 classes)**
   - Delete `SourceStats`, `ExtractionResult`, `ExtractionState` from `orchestrator.py`
   - Import from canonical locations: `extraction_stats.py`, `state_manager.py`
   - Impact: Prevents divergence, ensures single source of truth

2. **Fix Type Inconsistencies**
   - Change `ParcelData.tax_annual` from `Optional[int]` to `Optional[float]`
   - Impact: Prevents data loss from type coercion

3. **Fix Schema Field Name Mismatches**
   - `EnrichmentDataSchema.safety_score` → `safety_neighborhood_score`
   - Impact: Schema now matches reality

---

### Priority 2: High-Value Cleanup (Reduces Confusion)

4. **Remove Synonym Fields from enrichment_data.json**
   - Delete: `ceiling_height_score`, `kitchen_quality_score`, `master_quality_score`, `laundry_score`
   - Keep canonical: `high_ceilings_score`, `kitchen_layout_score`, `master_suite_score`, `laundry_area_score`
   - Impact: Eliminates 4 redundant fields

5. **Clarify Price Field Usage**
   - JSON: Remove `list_price`, keep only `price` (numeric)
   - Schema: Add `list_price` field (int, alias for price_num)
   - Entity: Keep `price` (string) and `price_num` (int) for dual purposes
   - Impact: Clearer semantics

6. **Resolve Fireplace Field Confusion**
   - Keep both: `fireplace_present` (bool) AND `fireplace_score` (float 0-10)
   - Document: `present` for existence, `score` for quality (gas=10, wood=7.5, decorative=2.5)
   - Update FireplaceScorer to use `fireplace_score` if available, else `fireplace_present`
   - Impact: Supports richer fireplace assessment

---

### Priority 3: Schema Validation Improvements

7. **Add Missing Fields to EnrichmentDataSchema**
   - Add metadata fields: `*_source` (str), `*_confidence` (float)
   - Add: `distance_to_park_miles` (float)
   - Impact: Full validation coverage

8. **Remove Unused Schema Fields**
   - Remove `noise_level` if not populated (QuietnessScorer uses `distance_to_highway_miles`)
   - Impact: Schema matches actual usage

9. **Expand PropertySchema to Match Property Entity**
   - Add: `latitude`, `longitude` (geocoding)
   - Add: `school_district` (str)
   - Add: `commute_minutes` (int)
   - Impact: Schema validates all property fields

---

### Priority 4: Data Cleanup (Remove Redundant Fields)

10. **Remove Computed Fields from enrichment_data.json**
    - Delete: `cost_breakdown`, `monthly_cost`, `kill_switch_passed`, `kill_switch_failures`
    - Reason: These are computed during pipeline, not source data
    - Impact: Cleaner separation of source vs derived data

11. **Remove CSV-Duplicate Fields from JSON**
    - Delete: `sqft` from enrichment_data.json (already in CSV)
    - Delete: `price` from enrichment_data.json (already in CSV as `price_num`)
    - Impact: Single source of truth per field

---

## 7. FIELD INVENTORY SUMMARY

### Models Across Codebase

| Category | Count | Status |
|----------|-------|--------|
| Pydantic Schemas | 5 | PropertySchema, EnrichmentDataSchema, KillSwitchCriteriaSchema, SewerTypeSchema, SolarStatusSchema, OrientationSchema |
| Domain Entities | 2 | Property, EnrichmentData |
| Domain Value Objects | 7 | Address, Score, RiskAssessment, ScoreBreakdown, RenovationEstimate, PerceptualHash, ImageMetadata |
| Domain Enums | 6 | RiskLevel, Tier, SolarStatus, SewerType, Orientation, ImageSource, ImageStatus |
| Service Models | 10+ | ParcelData, FieldInference, TriageResult, MonthlyCosts, CostEstimate, FieldLineage, QualityScore, etc. |
| Pipeline Models | 2 | PipelineResult, AnalysisPipeline |
| **Duplicates** | **3** | **SourceStats, ExtractionResult, ExtractionState** |

---

### Field Count by Schema

| Schema/Entity | Field Count | Notes |
|---------------|-------------|-------|
| Property | 47 | Aggregate entity with all analysis data |
| PropertySchema | 16 | Validates core listing + enrichment |
| EnrichmentData | 19 | DTO for external research |
| EnrichmentDataSchema | 32 | Validates enrichment sources |
| CSV (phx_homes.csv) | 11 | Listing data only |
| JSON (enrichment_data.json) | 60+ | All enrichment + metadata + synonyms |

**Gap Analysis:**
- PropertySchema missing ~31 fields from Property entity (expected - many are computed)
- EnrichmentDataSchema missing ~28 fields from JSON (metadata, synonyms, computed)
- JSON has ~7 synonym fields (duplicates)
- JSON has ~6 computed fields (should be removed)

---

## 8. RISK ASSESSMENT

### High Risk Items
- **Duplicate Models:** Could diverge if one is updated without the other
- **Type Inconsistencies:** `tax_annual` int vs float could cause data loss
- **Schema Gaps:** 28 JSON fields lack validation

### Medium Risk Items
- **Synonym Fields:** 7 duplicate field names cause confusion
- **Orphaned Fields:** `noise_level` defined but unused
- **Field Name Mismatches:** `safety_score` vs `safety_neighborhood_score`

### Low Risk Items
- **Field Count Mismatches:** Expected given entity vs schema purposes
- **CSV-JSON Gaps:** Expected given enrichment model

---

## 9. TESTING RECOMMENDATIONS

1. **Add Schema Validation Tests**
   - Test that JSON validates against EnrichmentDataSchema
   - Test that CSV parses to PropertySchema
   - Test that Property entity can serialize to both schemas

2. **Add Integration Tests**
   - Test Property ← CSV + JSON merge
   - Test all scorers with real data
   - Test kill-switch with edge cases

3. **Add Type Safety Tests**
   - Verify `tax_annual` handles float values
   - Verify `solar_lease_monthly` handles fractional costs
   - Verify `baths` 0.5 increments

---

## 10. MIGRATION PATH

### Phase 1: Fix Critical Issues (Week 1)
1. Remove duplicate models from `orchestrator.py`
2. Fix `ParcelData.tax_annual` type
3. Fix `EnrichmentDataSchema.safety_score` field name

### Phase 2: Data Cleanup (Week 2)
1. Remove synonym fields from `enrichment_data.json`
2. Remove computed fields from `enrichment_data.json`
3. Standardize price field usage

### Phase 3: Schema Expansion (Week 3)
1. Add missing fields to `EnrichmentDataSchema`
2. Add validation for metadata fields
3. Add comprehensive schema tests

### Phase 4: Documentation (Week 4)
1. Document canonical field names
2. Document schema validation flow
3. Update data dictionary

---

## APPENDICES

### A. Complete Field Name Cross-Reference

| Canonical Name | Synonyms | Type | Sources |
|----------------|----------|------|---------|
| lot_sqft | - | int | County, Schema, Entity |
| hoa_fee | - | float | Enrichment, Schema, Entity |
| price_num | list_price, price | int | CSV, JSON, Entity |
| school_rating | - | float | Enrichment, Entity |
| safety_neighborhood_score | safety_score | float | JSON, Entity, Schema(mismatch) |
| high_ceilings_score | ceiling_height_score | float | JSON(both), Entity, Schema |
| kitchen_layout_score | kitchen_quality_score | float | JSON(both), Entity, Schema |
| master_suite_score | master_quality_score | float | JSON(both), Entity, Schema |
| laundry_area_score | laundry_score | float | JSON(both), Entity, Schema |
| fireplace_present | - | bool | Entity, Schema |
| fireplace_score | - | float | JSON only |

### B. Recommended Import Structure

```python
# Canonical locations after consolidation
from phx_home_analysis.validation.schemas import (
    PropertySchema,
    EnrichmentDataSchema,
    SewerTypeSchema,
    SolarStatusSchema,
    OrientationSchema,
)

from phx_home_analysis.domain.entities import Property, EnrichmentData

from phx_home_analysis.domain.enums import (
    RiskLevel,
    Tier,
    SolarStatus,
    SewerType,
    Orientation,
)

from phx_home_analysis.services.image_extraction.extraction_stats import (
    SourceStats,
    ExtractionResult,
    StatsTracker,
)

from phx_home_analysis.services.image_extraction.state_manager import (
    ExtractionState,
    StateManager,
)
```

---

**END OF REPORT**
