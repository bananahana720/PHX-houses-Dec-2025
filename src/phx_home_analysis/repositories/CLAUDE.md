---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# repositories

## Purpose
Data persistence layer providing abstract repository patterns for property and enrichment data. Decouples data access from business logic via PropertyRepository (CSV listings) and EnrichmentRepository (JSON enrichment).

## Contents
| Path | Purpose |
|------|---------|
| `__init__.py` | Module exports (abstract bases, exceptions, concrete implementations) |
| `base.py` | Abstract PropertyRepository and EnrichmentRepository interfaces; DataLoadError, DataSaveError exceptions |
| `csv_repository.py` | CsvPropertyRepository - reads/writes phx_homes.csv listings; implements Property ↔ CSV row conversion; supports caching |
| `json_repository.py` | JsonEnrichmentRepository - reads/writes enrichment_data.json; atomic saves, backup/restore, normalized address matching |

## Tasks
- [x] Assess repository patterns and CRUD operations `P:H`
- [x] Document data sources (CSV, JSON) and access patterns `P:H`
- [x] Identify key dependencies and downstream consumers `P:H`
- [ ] Add benchmarks for lookup performance on large datasets `P:M`
- [ ] Implement generic query interface (filter_by, sort_by) `P:L`

## Learnings

### Repository Pattern
- **Two-repository design**: PropertyRepository (CSV) for listings, EnrichmentRepository (JSON) for enrichment overlay
- **Abstract bases** define contracts; concrete impls are decoupled from business logic
- **Caching**: Both repos cache loaded data in memory (_properties_cache, _enrichment_cache) for fast lookups on repeated calls
- **Load-once semantics**: load_by_address() calls load_all() if cache is None, ensuring single load per session

### CSV Repository (CsvPropertyRepository)
- **Data source**: phx_homes.csv (from Zillow/Redfin scraping pipeline)
- **CRUD operations**: load_all(), load_by_address(), save_all() (bulk only), save_one() raises NotImplementedError
- **Type conversion**: Extensive parsing helpers (_parse_int, _parse_float, _parse_bool, _parse_enum, _parse_list) handle CSV nulls/empty strings gracefully
- **Field mapping**: ~45 fields including address, listing basics (beds, baths, sqft, price), county data (lot_sqft, year_built, garage), Arizona-specific (solar_status, has_pool, hvac_age), scoring results (total_score, tier, kill_switch_passed)
- **Output format**: save_all() writes ranked CSV with ordered columns (address → listing → county → location → features → assessment scores → analysis results → geocoding)

### JSON Repository (JsonEnrichmentRepository)
- **Data source**: enrichment_data.json (Phase 0/1/2 data from county API, listing extraction, image analysis)
- **CRUD operations**: load_all(), load_for_property(), save_all() (no save_one)
- **Format flexibility**: Accepts both list and dict JSON formats; dict format converted to list internally for uniform handling
- **Validation**: Pydantic schema validation on load/save (validate parameter = True by default); supports backward compatibility (validate = False)
- **Atomic writes**: Uses atomic_json_save (write-to-temp + rename) to prevent corruption on crash; creates backups automatically
- **Address matching**: Supports exact lookup (fast) and normalized lookup (case-insensitive, punctuation-removed) via normalize_address utility
- **Backup/restore**: restore_from_backup() finds most recent backup or specified file; validates structure before restore; preserves corrupted file for diagnosis
- **Data application**: apply_enrichment_to_property() merges EnrichmentData fields into Property entity; handles enum conversions for sewer_type, orientation, solar_status
- **Template creation**: Auto-creates template JSON with example structure if file missing, guiding manual data entry

### Data Flow & Integration
- **Load path**: CsvPropertyRepository.load_all() → Property entities → JsonEnrichmentRepository.apply_enrichment_to_property() → enriched Property
- **Save path**: Property entities (scored, kill-switched) → CsvPropertyRepository.save_all() → ranked CSV; JsonEnrichmentRepository.save_all() → enrichment JSON
- **Error handling**: Custom exceptions (DataLoadError on read failures, DataSaveError on write failures) propagate to calling services

### Design Decisions
- **Repository pattern**: Enables mock repositories for testing; easy to add new sources (API, database) without changing services
- **Immutable entity design**: Property and EnrichmentData are frozen dataclasses; repositories return new instances on load, preventing unintended mutations
- **Lazy validation**: JsonEnrichmentRepository can load unvalidated data (for crash recovery) or validate on read; validation happens before save always
- **Backward compatibility**: JSON repository handles both list/dict formats; computed normalized_address if missing; optional validation flag

## Refs
- Abstract base classes: `base.py:18-114`
- DataLoadError/DataSaveError exceptions: `base.py:8-15`
- CSV property conversion: `csv_repository.py:117-186` (row→Property), `csv_repository.py:188-270` (Property→row), `csv_repository.py:303-392` (parsing helpers)
- CSV output fieldnames: `csv_repository.py:272-301`
- JSON validation on load: `json_repository.py:25-106`
- JSON atomic save: `json_repository.py:146-201`
- JSON backup/restore: `json_repository.py:203-278`
- JSON enrichment application: `json_repository.py:280-334`
- JSON dict conversions: `json_repository.py:336-413`
- Module exports: `__init__.py:12-22`

## Deps
← Imports from:
  - `domain.entities` (Property, EnrichmentData)
  - `domain.enums` (Orientation, SewerType, SolarStatus, Tier)
  - `validation.validators` (validate_enrichment_entry)
  - `utils.address_utils` (normalize_address)
  - `utils.file_ops` (atomic_json_save)
  - Standard library: json, csv, logging, pathlib, abc, typing

→ Imported by:
  - `pipeline.orchestrator` (main workflow coordinator)
  - `__init__.py` (package-level exports)
  - Scripts: `scripts/phx_home_analyzer.py`, `scripts/extract_county_data.py`
