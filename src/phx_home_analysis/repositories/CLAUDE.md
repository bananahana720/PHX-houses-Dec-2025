---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---

# repositories

## Purpose

Data persistence layer providing abstract repository patterns for property and enrichment data. Decouples data access from business logic via PropertyRepository (CSV listings) and EnrichmentRepository (JSON enrichment). Implements atomic writes, backups, and address normalization for crash-safe data persistence.

## Contents

| Path | Purpose |
|------|---------|
| `__init__.py` | Module exports - PropertyRepository, EnrichmentRepository, exceptions, concrete implementations |
| `base.py` | Abstract PropertyRepository and EnrichmentRepository interfaces; DataLoadError, DataSaveError exceptions |
| `csv_repository.py` | CsvPropertyRepository - reads/writes phx_homes.csv listings; Property↔CSV row conversion; caching |
| `json_repository.py` | JsonEnrichmentRepository - reads/writes enrichment_data.json; atomic saves, backup/restore, address matching |

## Key Classes & Methods

### PropertyRepository (base.py:18-114)
Abstract base class defining property data access contract.

**Methods:**
- `load_all() → list[Property]` - Load all properties from source
- `load_by_address(full_address) → Property | None` - Load single property
- `save_all(properties) → None` - Persist all properties
- `save_one(property) → None` - Persist single property (optional)

**Exceptions:**
- `DataLoadError` - Raised on read failures
- `DataSaveError` - Raised on write failures

### CsvPropertyRepository (csv_repository.py)
Reads and writes phx_homes.csv property listings.

**Constructor:** `__init__(csv_file_path, ranked_csv_path=None)`

**Methods:**
- `load_all() → list[Property]` - Parse CSV, convert rows to Property entities, cache results
- `load_by_address(full_address) → Property | None` - Lookup from cache (populates if needed)
- `save_all(properties) → None` - Rank by score and write to ranked_csv_path
- `save_one(property) → None` - Raises NotImplementedError

**CSV Columns:** ~50 fields including address, listing data (beds/baths/sqft/price), county assessor data (lot_sqft, year_built, garage), enrichment data, scores, and analysis results

**Parsing Features:**
- Type coercion helpers: _parse_int, _parse_float, _parse_bool, _parse_enum, _parse_list
- Graceful null handling (empty string, "None" string)
- Enum conversion for sewer_type, orientation, solar_status, tier

### EnrichmentRepository (base.py:130-190)
Abstract base class for enrichment data persistence.

**Methods:**
- `load_all(validate=True) → dict[str, EnrichmentData]` - Load enrichment, returns dict keyed by address
- `load_for_property(property) → EnrichmentData | None` - Load enrichment for single property
- `save_all(data) → None` - Persist enrichment data
- `apply_enrichment_to_property(property, enrichment) → Property` - Merge enrichment into property

### JsonEnrichmentRepository (json_repository.py)
Reads and writes enrichment_data.json with advanced features.

**Constructor:** `__init__(json_file_path)`

**Core Methods:**
- `load_all(validate=True)` - Load JSON (list or dict format), optional validation, returns dict by address
- `load_for_property(property)` - Lookup enrichment by normalized address (case-insensitive, punctuation-removed)
- `save_all(enrichment_list)` - Atomic save with automatic backup creation
- `apply_enrichment_to_property(property, enrichment)` - Merge EnrichmentData fields into Property

**Advanced Features:**
- **Atomic writes**: Write-to-temp (`.json.tmp`) + atomic rename prevents corruption on crash
- **Automatic backups**: Creates timestamped backup (e.g., `enrichment.20251203_143000.bak.json`) before write
- **Validation**: Optional Pydantic schema validation on load/save; can load unvalidated for recovery
- **Format flexibility**: Accepts both list and dict JSON formats; converts dict to list internally
- **Address matching**: Normalized address lookup (case-insensitive, punctuation-removed) via normalize_address utility
- **Backup/Restore**: `restore_from_backup()` finds most recent backup or specified file
- **Template creation**: Auto-creates template JSON with example structure if file missing
- **Normalized address recomputation**: If normalized_address missing, computes and reapplies during load

**Data Flow:**
1. JSON load → Validate schema → Convert to EnrichmentData objects → Cache by address
2. Lookup by address (exact or normalized)
3. Merge enrichment into Property entity via apply_enrichment_to_property()
4. On save: Create backup → Write to temp → Atomic rename → Log completion

## Repository Pattern Benefits

### Abstraction
- Concrete implementations (CSV, JSON) hidden behind abstract interfaces
- Easy to add new sources (database, API) without changing services
- Services depend on abstractions, not concrete implementations

### Testing
- Mock repositories for unit tests (no I/O, deterministic)
- Fixture-based test data in conftest.py
- No external dependencies during test execution

### Single Responsibility
- Repositories handle data persistence only
- Services handle business logic (kill-switch, scoring, enrichment merge)
- Validation layer handles schema enforcement

## Design Decisions

### Dual-Repository Architecture
- **PropertyRepository** (CSV) provides base listings with all known fields
- **EnrichmentRepository** (JSON) provides enrichment overlay with Phase 0/1/2 data
- **Merge strategy**: JSON enrichment overlays/fills missing CSV fields; original CSV preserved

### Immutable Entity Design
- Property and EnrichmentData are frozen dataclasses
- Repositories return new instances on load
- Prevents unintended mutations during processing

### Caching Strategy
- Both repos cache loaded data in memory (_properties_cache, _enrichment_cache)
- load_by_address() calls load_all() if cache is None (populate-on-demand)
- Cache invalidation handled at service layer (fresh pipeline run = new repository instance)

### Lazy Validation
- JsonEnrichmentRepository can load unvalidated data (validate=False) for crash recovery
- Validation enforced before save (validate=True by default)
- Enables resilience when data corrupted mid-pipeline

### Backward Compatibility
- JSON repository handles both list and dict formats (accepts dict, converts internally)
- Optional normalized_address field (defaults to None, computed if missing)
- Type coercion in CSV handles "None" string and empty values gracefully

## Learnings

- **CSV output ordering critical**: ranked_csv_path exports ordered columns (address → listing → county → location → features → assessment → analysis → geocoding) enabling human review
- **Atomic writes prevent data corruption**: write-to-temp + atomic rename ensures either old or new file intact (never partial) on crash
- **Address normalization enables robust matching**: Case-insensitive, punctuation-removed lookup handles formatting variations across sources
- **Backup naming with timestamps**: Multiple versions per file enable recovery without overwriting
- **Enum conversion requires explicit mapping**: SewerType.CITY vs "city" string needs explicit str→enum conversion in _parse_enum()
- **Empty JSON file should create template**: Guides users on expected structure; prevents "unsupported format" errors
- **Dict-to-list JSON conversion**: Flexible format acceptance enables manual JSON editing while maintaining uniform internal representation

## Refs

- Abstract base classes: `base.py:8-190`
- DataLoadError/DataSaveError exceptions: `base.py:8-15`
- CSV property conversion: `csv_repository.py:117-270`
- CSV output fieldnames: `csv_repository.py:272-301`
- CSV parsing helpers: `csv_repository.py:303-392`
- JSON validation on load: `json_repository.py:25-106`
- JSON atomic save: `json_repository.py:146-201`
- JSON backup/restore: `json_repository.py:203-278`
- JSON enrichment application: `json_repository.py:280-334`
- JSON dict conversions: `json_repository.py:336-413`
- Module exports: `__init__.py:1-22`

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
- Tests: `tests/unit/test_repositories.py`, `tests/integration/test_pipeline.py`

## Tasks

- [x] Assess repository patterns and CRUD operations `P:H`
- [x] Document data sources (CSV, JSON) and access patterns `P:H`
- [x] Identify key dependencies and downstream consumers `P:H`
- [ ] Add benchmarks for lookup performance on large datasets `P:M`
- [ ] Implement generic query interface (filter_by, sort_by) `P:L`
- [ ] Add database repository implementation for production deployment `P:L`

---

**Pattern Focus**: Repository pattern abstracts data persistence, enabling easy testing with mocks and future addition of new sources (database, API) without changing services.

**Package Version**: 1.0.0
**Lines**: 450+ total (base + csv_repository + json_repository)
