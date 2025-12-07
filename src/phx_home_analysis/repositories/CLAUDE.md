---
last_updated: 2025-12-07
updated_by: agent
staleness_hours: 24
flags: []
---

# repositories

## Purpose
Data persistence layer providing abstract repository patterns (PropertyRepository, EnrichmentRepository) for CSV listings and JSON enrichment data. Implements atomic writes, backups, and full E2-R3 field serialization.

## Contents
| Path | Purpose |
|------|---------|
| `base.py` | Abstract PropertyRepository, EnrichmentRepository interfaces |
| `csv_repository.py` | CsvPropertyRepository - reads/writes phx_homes.csv (50 fields) |
| `json_repository.py` | JsonEnrichmentRepository - atomic saves, 120+ field serialization (E2-R3) |
| `work_items_repository.py` | WorkItemsRepository - pipeline state, job queue, retry counts |
| `cached_manager.py` | CachedDataManager - in-memory cache layer for repositories |
| `__init__.py` | Module exports |

## Key Changes (E2-R3)
- `json_repository.py:540-728` - Added 42 E2-R3 fields to `_enrichment_to_dict()`
- `json_repository.py:485-673` - Added 42 E2-R3 fields to `_dict_to_enrichment()`
- **Total serialized fields**: 120+ (core + E2-R2 + E2-R3)

## Key Classes

| Class | File | Purpose |
|-------|------|---------|
| `PropertyRepository` | `base.py` | Abstract base for property data access |
| `EnrichmentRepository` | `base.py` | Abstract base for enrichment data |
| `CsvPropertyRepository` | `csv_repository.py` | CSV implementation with 50-field parsing |
| `JsonEnrichmentRepository` | `json_repository.py` | JSON with atomic writes, 120+ fields |
| `WorkItemsRepository` | `work_items_repository.py` | Pipeline state and job queue |
| `CachedDataManager` | `cached_manager.py` | In-memory caching layer |

## Serialization Coverage (json_repository.py)

| Category | Fields | Lines |
|----------|--------|-------|
| Core fields | 20 | 540-560 |
| E2-R2 MLS fields | 33 | 561-600 |
| E2-R3 Extended fields | 42 | 601-680 |
| Assessment fields | 25 | 681-728 |

## Tasks
- [x] Add E2-R3 field serialization (42 fields)
- [x] Add E2-R3 field deserialization (42 fields)
- [ ] Consider dynamic serialization from dataclass fields `P:M`

## Learnings
- Atomic writes prevent data corruption via temp file + rename pattern
- E2-R3 exposed hardcoded serialization gap - fields need explicit dict mapping
- Address normalization (case/punctuation-insensitive) enables robust matching

## Refs
- Base classes: `base.py:8-190`
- CSV parsing: `csv_repository.py:117-392`
- JSON E2-R3 serialization: `json_repository.py:540-728`
- JSON E2-R3 deserialization: `json_repository.py:485-673`

## Deps
- **← Imports:** domain.entities, domain.enums, validation.validators
- **→ Imported by:** pipeline.orchestrator, MetadataPersister, scripts/
