---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
flags: []
---

# repositories

## Purpose
Data persistence layer providing abstract repository patterns (PropertyRepository, EnrichmentRepository) for CSV listings and JSON enrichment data. Implements atomic writes, backups, and address normalization for crash-safe access.

## Contents
| Path | Purpose |
|------|---------|
| `base.py` | Abstract PropertyRepository, EnrichmentRepository interfaces; DataLoadError, DataSaveError exceptions |
| `csv_repository.py` | CsvPropertyRepository - reads/writes phx_homes.csv; 50-field Property↔CSV conversion; caching |
| `json_repository.py` | JsonEnrichmentRepository - reads/writes enrichment_data.json; atomic saves, backups, address matching |
| `work_items_repository.py` | WorkItemsRepository - pipeline state & job queue; extraction progress, retry counts, phase status (NEW) |
| `__init__.py` | Module exports (PropertyRepository, EnrichmentRepository, exceptions) |

## Key Classes

**PropertyRepository (base.py):** Abstract for property data access
- `load_all() → list[Property]` - Load all properties
- `load_by_address(full_address) → Property | None` - Single property lookup
- `save_all(properties) → None` - Persist all properties

**CsvPropertyRepository (csv_repository.py):** CSV implementation
- Parses phx_homes.csv (50 fields: address, listing, county, enrichment, scores, analysis)
- Type coercion helpers (_parse_int, _parse_float, _parse_bool, _parse_enum, _parse_list)
- Graceful null handling ("None" strings, empty values)

**JsonEnrichmentRepository (json_repository.py):** JSON implementation
- Atomic writes: temp file + atomic rename (crash-safe)
- Auto-creates timestamped backups before write
- Optional Pydantic validation on load/save
- Normalized address lookup (case-insensitive, punctuation-removed)
- Dict/list JSON format flexibility

## Design Patterns
- **Dual-repo architecture:** PropertyRepository (CSV base) + EnrichmentRepository (JSON overlay)
- **Immutable entities:** Property/EnrichmentData are frozen dataclasses
- **In-memory caching:** load_by_address() triggers populate-on-demand cache population
- **Lazy validation:** JsonEnrichmentRepository accepts validate=False for crash recovery

## Commands
```bash
# Repos are used by pipeline, not directly
from phx_home_analysis.repositories import PropertyRepository, EnrichmentRepository
```

## Learnings
- Atomic writes prevent data corruption via temp file + rename pattern
- Address normalization (case/punctuation-insensitive) enables robust matching
- Timestamped backup naming allows recovery without overwrites
- Enum conversion requires explicit str→enum mapping in _parse_enum()
- Empty JSON should create template to guide users

## Refs
- Base classes: `base.py:8-190`
- CSV parsing: `csv_repository.py:117-392`
- JSON atomic save: `json_repository.py:146-201`
- Module exports: `__init__.py:1-22`

## Deps
**← Imports:** domain.entities, domain.enums, validation.validators, utils.address_utils, utils.file_ops, pathlib, csv, json, abc, typing
**→ Imported by:** pipeline.orchestrator, scripts/phx_home_analyzer.py, tests/unit/test_repositories.py
