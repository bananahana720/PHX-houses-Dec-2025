---
last_updated: 2025-12-04
updated_by: main
staleness_hours: 24
flags: []
---
# data_integration

## Purpose

Provides data source integration and canonical field mapping between county API, listing platforms (Zillow/Redfin), enrichment JSON, and CSV sources. Ensures consistent field names and data normalization across the pipeline.

## Contents

| Path | Purpose |
|------|---------|
| `field_mapper.py` | Canonical field definitions and source-to-canonical mappings |
| `merge_strategy.py` | Data merging and prioritization strategies across sources |
| `__init__.py` | Module exports and public API |

## Tasks

- [x] Correct field mapper scoring point comments to match actual system
- [ ] Add source confidence weighting per merge-strategy P:M
- [ ] Create integration test suite for field mappings P:M

## Learnings

- **Scoring sections corrected:** Location Section A = 250pts, Interior Section C = 180pts, Systems Section B = 175pts (total 605pts mapped across scoring)
- **Field grouping strategy:** CANONICAL_FIELDS organized by category (identifiers, features, scores, metadata) for maintainability
- **Source priority:** County API → Listing → Enrichment → CSV for field value resolution

## Refs

- Canonical fields definition: `field_mapper.py:19-90`
- Section A scoring: `field_mapper.py:47` (250 pts)
- Section C scoring: `field_mapper.py:57` (180 pts)
- Section B scoring: `field_mapper.py:69` (175 pts)
- Merge strategies: `merge_strategy.py:1-50`

## Deps

← Imports from:
  - `typing` (standard library)
  - Parent: `services/` module

→ Imported by:
  - `validation/` schemas
  - `repositories/` data access layer
  - Pipeline orchestration