# 5. Migration Strategy (Future)

### Phase 1: Audit (Week 1)
- [ ] Search codebase for references to all `*_source` fields
- [ ] Search for references to all `*_confidence` fields
- [ ] Verify which confidence fields are used by LineageTracker
- [ ] Document findings in `INVESTIGATION.md`

### Phase 2: Consolidation (Week 2)
- [ ] Consolidate synonym fields (ceiling, kitchen, master, laundry)
- [ ] Remove `list_price` and `sqft` from enrichment layer
- [ ] Consolidate confidence fields into single system
- [ ] Update config/templates to use canonical field names

### Phase 3: Removal (Week 3)
- [ ] Remove computed fields (`cost_breakdown`, `monthly_cost`, `kill_switch_*`, section scores)
- [ ] Remove orphaned `*_source` fields not used by LineageTracker
- [ ] Update all references in code to compute/fetch from proper sources
- [ ] Add validation to prevent re-addition of computed fields

### Phase 4: Validation (Week 4)
- [ ] Run full pipeline with cleaned schema
- [ ] Verify deal sheets generate correctly
- [ ] Verify scoring is unaffected
- [ ] Update tests to match new schema

---
