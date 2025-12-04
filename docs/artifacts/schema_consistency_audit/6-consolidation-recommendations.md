# 6. CONSOLIDATION RECOMMENDATIONS

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
