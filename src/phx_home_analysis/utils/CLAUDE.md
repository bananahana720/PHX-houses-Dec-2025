---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---

# utils

## Purpose

Provides shared utility functions for address normalization, file operations, and data handling. Ensures consistent address matching across the pipeline and provides atomic, crash-safe JSON persistence with backup support for critical data files.

## Contents

| Path | Purpose |
|------|---------|
| `__init__.py` | Package exports - atomic_json_save, normalize_address, addresses_match |
| `address_utils.py` | Address normalization and matching for consistent property lookups (65 lines) |
| `file_ops.py` | Atomic JSON save with backup, cleanup utilities (131 lines) |

## Key Functions

### address_utils.py
- **normalize_address(address: str) -> str**: Converts address to lowercase, removes punctuation/commas/periods, collapses spaces for consistent lookups
  - Example: "123 Main St., Phoenix, AZ 85001" → "123 main st phoenix az 85001"
  - Used by repositories, deduplication, enrichment merge logic

- **addresses_match(address1: str, address2: str) -> bool**: Compares two addresses after normalization
  - Used to detect duplicate records across CSV listings and JSON enrichment

### file_ops.py
- **atomic_json_save(path, data, create_backup, backup_dir, indent) -> Path | None**: Writes JSON atomically with write-to-temp + atomic-rename pattern
  - Prevents data corruption on crash/power loss mid-write
  - Creates backup with timestamp before writing (if create_backup=True)
  - Returns backup path or None
  - Used by JsonEnrichmentRepository to persist enrichment_data.json safely

- **cleanup_old_backups(directory, pattern, keep_count) -> list[Path]**: Removes old backup files, keeping N most recent
  - Prevents backup directory bloat
  - Pattern example: "enrichment_data.*.bak.json"
  - Returns list of deleted paths

## Design Patterns

### Address Normalization
- Canonical form: lowercase, no punctuation, single spaces
- Used for deduplication and multi-source data merging
- Epic spec compliance per `e1-s2-property-data-storage-layer.md`

### Atomic File Operations
- Write-to-temp (`.json.tmp`) + atomic rename (`Path.replace()`)
- On POSIX: atomic at OS level | On Windows: `Path.replace()` is atomic
- Backup naming: `{stem}.{YYYYMMDD_HHMMSS}.bak{suffix}`
- Error cleanup: temp file removed on exception

## Learnings

- Address normalization is case-insensitive and punctuation-agnostic for robust matching
- Atomic save pattern is critical for `enrichment_data.json` to prevent data loss during updates
- Backup versioning uses timestamps to support multiple versions per file
- Both functions imported at package level (`__init__.py`) for easy access throughout the package

## Refs

- Address normalization spec: `src/phx_home_analysis/domain/entities.py` (Address value object)
- Repository usage: `src/phx_home_analysis/repositories/json_repository.py:161,194`
- Deduplication usage: `src/phx_home_analysis/validation/deduplication.py:31`
- Epic story: `docs/stories/e1-s2-property-data-storage-layer.md`

## Deps

← Imports from:
- Standard library: `json`, `logging`, `shutil`, `datetime`, `pathlib`, `re`
- No external dependencies

→ Imported by:
- `src/phx_home_analysis/__init__.py` (package exports)
- `src/phx_home_analysis/repositories/json_repository.py` (atomic save for enrichment data)
- `src/phx_home_analysis/validation/deduplication.py` (address normalization for duplicate detection)
- `src/phx_home_analysis/validation/normalizer.py` (address normalization)
- `src/phx_home_analysis/services/quality/lineage.py` (address normalization)
- `src/phx_home_analysis/services/lifecycle/archiver.py` (atomic save for backups)
- `tests/unit/utils/test_address_utils.py` (unit tests)
- Scripts: `scripts/extract_county_data.py`, `scripts/deal_sheets/renderer.py`

## Tasks

- [x] Address normalization (done - handles lowercase, punctuation removal, whitespace collapse)
- [x] Atomic JSON save (done - temp write + rename pattern with backup)
- [x] Backup cleanup (done - keeps N most recent backups)
- [ ] Add address validation (postal code, street name validation) `P:L`
- [ ] Add file checksum verification for backup integrity `P:M`

---

**Package Version**: 1.0.0
**Python Version**: 3.10+
**Lines**: 230 total (~65 address_utils + ~131 file_ops + ~4 __init__)
