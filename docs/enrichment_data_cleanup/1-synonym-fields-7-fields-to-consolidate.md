# 1. Synonym Fields (7 fields to consolidate)

These fields have canonical equivalents and should eventually use only one name:

### 1.1 Ceiling Height vs High Ceilings
- **Current:** `ceiling_height_score`, `high_ceilings_score`
- **Canonical:** `high_ceilings_score`
- **Rationale:** Section C scoring system uses `high_ceilings_score`. `ceiling_height_score` is legacy naming.
- **Dependencies:** None
- **Migration Script:** Keep `high_ceilings_score`, remove `ceiling_height_score` and `ceiling_height_score_source`
- **Data Sample:** Both exist in all/most properties with potentially different values

### 1.2 Kitchen Quality vs Kitchen Layout
- **Current:** `kitchen_quality_score`, `kitchen_layout_score`
- **Canonical:** `kitchen_layout_score`
- **Rationale:** Scoring system uses `kitchen_layout_score`. `kitchen_quality_score` is older variant.
- **Dependencies:** Scoring configuration and templates may reference both
- **Migration Script:** Keep `kitchen_layout_score`, remove `kitchen_quality_score` and `kitchen_quality_score_source`
- **Data Sample:** `kitchen_layout_score` is 9.0, `kitchen_quality_score` is 5.0 in example - different sources/assessment times

### 1.3 Master Quality vs Master Suite
- **Current:** `master_quality_score`, `master_suite_score`
- **Canonical:** `master_suite_score`
- **Rationale:** Section C scoring and templates use `master_suite_score`. `master_quality_score` is legacy.
- **Dependencies:** Deal sheet templates and scoring configuration
- **Migration Script:** Keep `master_suite_score`, remove `master_quality_score` and `master_quality_score_source`
- **Data Sample:** Example has `master_suite_score=6.0`, `master_quality_score=5.0`

### 1.4 Laundry Area vs Laundry
- **Current:** `laundry_score`, `laundry_area_score`
- **Canonical:** `laundry_area_score`
- **Rationale:** Config uses `laundry_area_score`. `laundry_score` is shorter, legacy name.
- **Dependencies:** Scoring weights configuration
- **Migration Script:** Keep `laundry_area_score`, remove `laundry_score` and `laundry_score_source`
- **Data Sample:** Both exist with identical values (5.0)

### 1.5 List Price vs Price
- **Current:** `list_price`, `price`
- **Canonical:** `price`
- **Rationale:** CSV header uses `price`. `list_price` is redundant property-level storage.
- **Dependencies:** Cost estimation queries `price` (not `list_price`)
- **Migration Script:** Remove `list_price` - reference CSV's `price` column directly
- **Data Sample:** Example has both = 475000

### 1.6 Fireplace Score Clarification
- **Current:** `fireplace_score`, potentially `fireplace_present`, `interior_fireplace_score`
- **Issue:** Unclear if `fireplace_score` represents presence (binary) or quality (0-10)
- **Recommendation:**
  - Decide on single field: either `fireplace_present` (bool) or `fireplace_score` (0-10 quality)
  - Document the schema in `DESIGN.md`
- **Data Sample:** `fireplace_score=6.0` suggests quality score, not boolean

---
