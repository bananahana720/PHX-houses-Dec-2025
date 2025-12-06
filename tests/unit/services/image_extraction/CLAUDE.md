---
last_updated: 2025-12-05T22:15:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# tests/unit/services/image_extraction

## Purpose
Unit tests for image extraction service layer covering file locking, data integrity validation, reconciliation logic, and category indexing for concurrent safety and deterministic storage.

## Contents
| File | Purpose |
|------|---------|
| `test_file_lock.py` | FileLock, PropertyLock, ManifestLock: acquire/release, context managers, stale detection (5 classes) |
| `test_validators.py` | Pre/during-extraction validators: address hashing, batch validation, integrity assertions (6 classes) |
| `test_reconciliation.py` | Manifest reconciliation: ghost entries, orphans, hash mismatches, quality scoring |
| `test_category_index.py` | CategoryIndex O(1) reverse lookup: add/remove, persistence, multi-category images (7 classes, 30+ tests) |

## Key Patterns
- **File-based locking**: PID:timestamp format enables stale lock detection (dead processes, timeouts)
- **Address normalization**: Case-insensitive, whitespace-trimmed -> deterministic property_hash for dedup
- **Reverse index testing**: Verify O(1) has_image(), get_image_categories(), and remove() operations

## Tasks
- [x] Test FileLock acquire/release and stale detection `P:H`
- [x] Test CategoryIndex reverse mapping operations `P:H`
- [ ] Add concurrent extraction safety scenarios `P:M`
- [ ] Add reconciliation tests for manifest integrity gaps `P:M`

## Learnings
- **Lock format design**: PID+timestamp allows stale detection without OS-specific code
- **Reverse index persistence**: Rebuilt on load from forward index - not serialized separately
- **Category tuples**: (location, subject, property_hash) uniquely identify image placement

## Refs
- FileLock: `src/phx_home_analysis/services/image_extraction/file_lock.py:23-120`
- CategoryIndex: `src/phx_home_analysis/services/image_extraction/category_index.py`
- Validators: `src/phx_home_analysis/services/image_extraction/validators.py:1-300`

## Deps
<- imports: pytest, pathlib, FileLock, PropertyLock, ManifestLock, CategoryIndex
-> used by: CI/CD pipeline, pre-commit hooks
