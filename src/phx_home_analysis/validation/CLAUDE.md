---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
flags: []
---
# validation

## Purpose
Pydantic schemas (V1 & V2) for property and image data validation with field constraints, cross-field rules, normalization, and deduplication.

## Contents
| Path | Purpose |
|------|---------|
| `schemas.py` | PropertySchema, SewerTypeSchema, SolarStatusSchema (V1: 436 lines) |
| `image_schemas.py` | ImageEntryV2, URLEntryV2, ManifestV2 (V2: 153 lines, hash validation) |
| `normalizer.py` | normalize_address, infer_type, clean_numeric (331 lines) |
| `deduplication.py` | DeduplicationRule, find_duplicates, compute_phash (120 lines) |
| `validators.py` | Custom validators: is_valid_price, is_valid_year, validate_kill_switch (370 lines) |
| `config_schemas.py` | AppConfig, PipelineConfig validation (616 lines) |

## Key Patterns
- **V1 → V2**: image_schemas.py (new E2.S4) adds lineage: property_hash (8-char), created_by_run_id, content_hash (MD5)
- **Immutable models**: BaseModel config with validate_assignment=True; @field_validator for constraints
- **Cross-field rules**: @model_validator for dependent validations (e.g., hash vs address consistency)

## Tasks
- [x] Implement ImageEntryV2, URLEntryV2, ManifestV2 with hash validation `P:H`
- [ ] Add type coercion tests for normalizer.infer_type `P:M`
- [ ] Document deduplication algorithm for image dedup `P:L`

## Learnings
- **V2 schemas (E2.S4)**: Separate image_schemas.py from generic schemas; enables schema versioning
- **Hash consistency**: property_hash must match sha256(normalize(address))[:8]; validated on entry
- **Lineage tracking**: created_by_run_id and content_hash enable crash recovery & dedup

## Refs
- ImageEntryV2: `image_schemas.py:28-68` (lineage fields)
- PropertySchema: `schemas.py:43-100` (V1 validation)
- Normalizer: `normalizer.py:11-50` (address standardization)
- Deduplication: `deduplication.py:1-50` (phash/dhash)

## Deps
← imports: Standard lib, pydantic 2.12, Pillow (image hash)
→ used by: Repositories, Pipeline, Data integration services