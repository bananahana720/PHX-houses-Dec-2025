---
last_updated: 2025-12-05T15:10:00Z
updated_by: agent
staleness_hours: 24
line_target: 80
flags: []
---
# tests/unit/services/image_extraction

## Purpose
Unit tests for image extraction service layer covering file locking, data integrity validation, and reconciliation logic for concurrent safety and deterministic storage.

## Contents
| File | Purpose |
|------|---------|
| `test_file_lock.py` | FileLock, PropertyLock, ManifestLock: acquire/release, context managers, stale detection (5 classes) |
| `test_validators.py` | Pre/during-extraction validators: address hashing, batch validation, integrity assertions (6 classes) |
| `test_reconciliation.py` | Manifest reconciliation: ghost entries, orphans, hash mismatches, quality scoring |

## Key Patterns
- **File-based locking**: PID:timestamp format enables stale lock detection (dead processes, timeouts)
- **Address normalization**: Case-insensitive, whitespace-trimmed → deterministic property_hash for dedup
- **Assertion validators**: Pre-extraction (batch dups), during-extraction (address/hash/file safety)

## Tasks
- [x] Test FileLock acquire/release and stale detection `P:H`
- [x] Test PropertyLock and ManifestLock wrappers `P:H`
- [x] Test pre-extraction batch validation and during-extraction assertions `P:H`
- [ ] Add reconciliation tests for manifest integrity gaps `P:M`
- [ ] Add concurrent extraction safety scenarios `P:M`

## Learnings
- **Lock format design**: PID+timestamp allows stale detection without OS-specific code
- **Address hashing**: Normalized address → 8-char hash enables consistent folder lookup
- **Batch validation**: Detects duplicate addresses in same batch; warns about overwrites
- **Assertion timing**: Pre-extraction (fast), during-extraction (comprehensive), post-extraction (reconciliation)

## Refs
- FileLock: `src/phx_home_analysis/services/image_extraction/file_lock.py:23-120`
- Validators: `src/phx_home_analysis/services/image_extraction/validators.py:1-300`
- Reconciliation: `src/phx_home_analysis/services/image_extraction/reconciliation.py:1-150`

## Deps
← imports: pytest, pathlib, FileLock, PropertyLock, ManifestLock, PreExtractionValidator, DuringExtractionAssertions
→ used by: Image extraction orchestrator, Phase 1 orchestration
