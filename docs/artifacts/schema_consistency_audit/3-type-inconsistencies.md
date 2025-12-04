# 3. TYPE INCONSISTENCIES

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
