# 8. RISK ASSESSMENT

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
