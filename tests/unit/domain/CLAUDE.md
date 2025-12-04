---
last_updated: 2025-12-04T13:45:00
updated_by: agent
staleness_hours: 24
flags: []
---
# tests/unit/domain

## Purpose
Unit tests for domain entity provenance tracking, including FieldProvenance dataclass validation and EnrichmentData provenance methods. Tests confidence scoring, field source attribution, and data quality tracking for the property analysis pipeline.

## Contents
| Path | Purpose |
|------|---------|
| `test_field_provenance.py` | FieldProvenance validation (confidence, sources, timestamps) and EnrichmentData provenance methods |

## Test Classes (191 lines, 11 tests)

### TestFieldProvenance (5 tests)
- `test_field_provenance_valid` - Basic object creation with all fields
- `test_field_provenance_confidence_range_valid` - Boundary values (0.0, 1.0)
- `test_field_provenance_confidence_range_invalid_high` - Rejects >1.0
- `test_field_provenance_confidence_range_invalid_low` - Rejects <0.0
- `test_field_provenance_derived_from` - Tracking derived field lineage

### TestEnrichmentDataProvenance (6 tests)
- `test_enrichment_set_provenance` - Setting provenance on fields
- `test_enrichment_get_provenance_nonexistent` - Returns None for untracked fields
- `test_enrichment_low_confidence_fields` - Identifying fields below threshold (default 0.80)
- `test_enrichment_low_confidence_fields_custom_threshold` - Custom confidence threshold (0.95)
- `test_enrichment_set_provenance_default_timestamp` - Auto-generates ISO timestamp when not provided
- (Implicit): Assertion of ISO timestamp validity via `datetime.fromisoformat()`

## Key Patterns

**Confidence Validation:**
- Strict bounds checking (0.0-1.0 inclusive)
- ValueError on violation with clear message
- Boundary values tested (0.0, 1.0 explicitly)

**Provenance Tracking:**
- Per-field source attribution (assessor_api, zillow, google_maps, greatschools, manual, ai_inference)
- Phase tracking (phase0, phase1, phase2, etc.)
- Agent tracking (county-api-agent, listing-browser, image-assessor)

**Threshold Pattern:**
- Default threshold 0.80 (matches quality-metrics 80% gate)
- Custom thresholds supported for strict evaluation
- Returns list of field names below threshold

**Timestamp Handling:**
- ISO 8601 format (`2025-12-04T10:30:00`)
- Auto-generation when not provided (production safety)
- Validation via `datetime.fromisoformat()`

## Tasks
- [x] Map test file structure and count `P:H`
- [x] Document test classes and methods `P:H`
- [ ] Add derived field chain validation tests `P:M`
- [ ] Test multi-source provenance merging `P:M`

## Learnings
- Confidence threshold (0.80) aligns with quality-metrics 80% minimum gate
- FieldProvenance immutable; derived_from tracks computation lineage
- ISO timestamp auto-generation prevents missing audit trails in production
- EnrichmentData methods gracefully handle unmapped fields (return None)

## Refs
- FieldProvenance entity: `src/phx_home_analysis/domain/entities.py:FieldProvenance`
- EnrichmentData entity: `src/phx_home_analysis/domain/entities.py:EnrichmentData`
- Quality metrics: `src/phx_home_analysis/services/quality/metrics.py` (0.80 threshold)
- Confidence scoring: Quality metrics module (60% completeness + 40% confidence)

## Deps
← Imports from:
- pytest 9.0.1+
- src.phx_home_analysis.domain.entities (FieldProvenance, EnrichmentData)
- datetime (ISO timestamp validation)

→ Imported by:
- CI/CD pipeline (pytest tests/unit/domain/)
- Quality assurance checks (data provenance validation)
- Data enrichment audit trails
