# 10. MIGRATION PATH

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
