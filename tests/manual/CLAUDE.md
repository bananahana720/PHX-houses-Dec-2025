---
last_updated: 2025-12-05T15:10:00Z
updated_by: agent
staleness_hours: 24
line_target: 80
flags: []
---
# tests/manual

## Purpose
Manual integration tests for image extraction pipeline validating content-addressed storage, determinism, and run metadata propagation without mocking external services.

## Contents
| File | Purpose |
|------|---------|
| `test_content_addressed_storage.py` | Verify content-hash determinism, file paths, run_id propagation for deduplication |

## Key Patterns
- **Content-addressed storage**: MD5 hash of image bytes → file path (deterministic, collision-free)
- **Run ID tracking**: 8-character run_id embedded in path for audit/recovery
- **Deterministic structure**: Same image content always → same file path across runs

## Tasks
- [ ] Add concurrent write safety tests `P:M`
- [ ] Add hash collision detection tests `P:L`
- [ ] Document manual test execution steps `P:M`

## Learnings
- **Content hash as image_id**: MD5 hash of bytes enables deduplication across multiple download sources
- **Directory sharding**: `processed/{hash_prefix_8}/{full_hash}.png` structure avoids I/O hotspots
- **Run tracking**: 8-char run_id provides crash recovery and audit trail

## Refs
- Orchestrator: `src/phx_home_analysis/services/image_extraction/orchestrator.py:56-120`
- Content hashing: `test_content_addressed_storage.py:36-45` (MD5 computation)
- Storage path: `test_content_addressed_storage.py:42-50` (path validation)

## Deps
← imports: asyncio, hashlib, tempfile, pathlib, ImageExtractionOrchestrator
→ used by: Manual verification, integration validation
