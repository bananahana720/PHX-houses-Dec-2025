# 7. Impact Analysis

### Severity by Field Category

| Category | Impact | Risk | Effort |
|----------|--------|------|--------|
| Synonym Fields (7) | Low | Low | Low (1 day) |
| Computed Fields (6) | Medium | Medium | Medium (2-3 days) |
| Orphaned Metadata (12+) | Low-Medium | Low | Medium (1-2 days) |

### Dependencies to Verify

1. **Scoring Configuration** (`src/phx_home_analysis/config/`)
   - Which field names are referenced in weights?
   - Will `high_ceilings_score` vs `ceiling_height_score` cause mismatches?

2. **Deal Sheet Templates** (`scripts/deal_sheets/templates.py`)
   - Which fields are rendered?
   - Will consolidation break rendering?

3. **Console Reporter** (`src/phx_home_analysis/reporters/`)
   - What's displayed?
   - Any formatting assumptions?

4. **LineageTracker** (`src/phx_home_analysis/services/quality/lineage.py`)
   - Does it actually use `*_source` fields from enrichment_data.json?
   - Or does it maintain separate `field_lineage.json`?

### Fields Used by LineageTracker

**Finding:** LineageTracker uses dedicated `data/field_lineage.json` file, NOT the enrichment_data.json source fields.

- `record_field(property_hash, field_name, source, confidence)` writes to `field_lineage.json`
- `get_field_lineage()` reads from `field_lineage.json`
- `*_source` and `*_confidence` in enrichment_data.json are DUPLICATES of LineageTracker's tracking

**Implication:** `*_source` and `*_confidence` fields in enrichment_data.json can be removed without impact - they're redundant with LineageTracker.

---
