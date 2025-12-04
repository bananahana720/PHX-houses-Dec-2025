# 4. NAMING INCONSISTENCIES

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
