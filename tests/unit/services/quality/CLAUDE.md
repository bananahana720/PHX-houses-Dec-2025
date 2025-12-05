---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
flags: []
---
# tests/unit/services/quality

## Purpose
Unit tests for data quality and provenance tracking services. Tests data source confidence levels, field-level provenance recording (single/batch/derived), and confidence display formatting for deal sheets and reports.

## Contents
| Path | Purpose |
|------|---------|
| `test_provenance.py` | Provenance tracking, data source confidence, field lineage (3 test classes, 24+ tests) |

## Test Classes (3)

### TestDataSource (8 tests)
Tests confidence mappings for each DataSource enum value:
- ASSESSOR_API: 0.95 (highest authority)
- ZILLOW: 0.85, REDFIN: 0.85
- GOOGLE_MAPS: 0.90, GREATSCHOOLS: 0.90
- IMAGE_ASSESSMENT: 0.80
- CSV: 0.90
- AI_INFERENCE: 0.70 (lowest)
- MANUAL: 0.85
- Validates all sources have confidence in 0.0-1.0 range

### TestProvenanceService (6 tests)
Tests provenance recording and field lineage:
- `record_field()` - Single field with source + optional confidence override
- `record_batch()` - Multiple fields from same source with consistent confidence
- `record_derived()` - Computed fields with minimum confidence from source fields
- Custom confidence overrides source defaults
- Agent ID and phase tracking for audit trails
- Field provenance attached to EnrichmentData entities

### TestConfidenceDisplay (10 tests)
Tests confidence formatting and HTML badge generation:
- **ConfidenceLevel.from_score()**: HIGH (≥0.90), MEDIUM (0.70-0.89), LOW (<0.70)
- **format_confidence()**: Text format with optional [Verify]/[Unverified] badges
- **get_confidence_html()**: HTML badges with CSS classes (confidence-green/yellow/red)
- Badges: "" (HIGH), "Verify" (MEDIUM), "Unverified" (LOW)
- Colors: green → HIGH, yellow → MEDIUM, red → LOW

## Tasks
- [x] Map provenance service test coverage `P:H`
- [x] Document data source confidence tiers `P:H`
- [ ] Add integration tests for confidence rollup across deal sheets `P:M`
- [ ] Add visualization tests for confidence indicators `P:L`

## Learnings
- **Confidence hierarchy**: County API (0.95) > Maps/Schools (0.90) > CSV (0.90) > Web (0.85) > Image (0.80) > AI (0.70)
- **Derived fields use minimum**: Confidence floor when combining sources prevents false confidence inflation
- **Custom overrides**: Manual validation can boost confidence (e.g., 0.99 for verified data)
- **Three-tier display system**: HIGH (verified), MEDIUM (verify), LOW (unverified) guides buyer attention
- **Phase/agent tracking**: Enables audit trail for data transformations across pipeline phases

## Refs
- Data sources: `src/phx_home_analysis/services/quality/models.py:DataSource`
- Provenance service: `src/phx_home_analysis/services/quality/provenance_service.py`
- Confidence display: `src/phx_home_analysis/services/quality/confidence_display.py`
- Enrichment entity: `src/phx_home_analysis/domain/entities.py:EnrichmentData`

## Deps
← Imports from:
  - `phx_home_analysis.services.quality.models` (DataSource)
  - `phx_home_analysis.services.quality.provenance_service` (ProvenanceService)
  - `phx_home_analysis.services.quality.confidence_display` (ConfidenceLevel, format_confidence, get_confidence_html)
  - `phx_home_analysis.domain.entities` (EnrichmentData)

→ Imported by:
  - Deal sheet generator (confidence badges)
  - Data quality reports
  - CI/CD pipeline
  - Future integration tests for multi-source merge
