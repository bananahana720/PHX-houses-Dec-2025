---
last_updated: 2025-12-05T15:10:00Z
updated_by: agent
staleness_hours: 24
line_target: 80
flags: []
---
# data/property_images/processed

## Purpose
Content-addressed image storage using MD5 hashes of file content for deterministic deduplication and efficient lookup. No source code; managed exclusively by ImageExtractionOrchestrator.

## Contents
| Directory | Purpose |
|-----------|---------|
| `{hash_prefix_8}/` | Subdirectories using first 8 chars of MD5 hash for I/O sharding |
| `{hash_prefix_8}/{full_hash}.png` | Image files named by full MD5 content hash |

## Key Patterns
- **Content-addressed layout**: File path derived from file content (MD5), not source URL
- **Hash-based deduplication**: Byte-for-byte identical images stored once regardless of source count
- **Deterministic structure**: Same image always written to same path across all runs

## Tasks
- [ ] Monitor directory size and implement orphan cleanup `P:M`
- [ ] Add periodic integrity verification (hash vs path) `P:M`
- [ ] Document storage quota and retention policy `P:L`

## Learnings
- **I/O efficiency**: Prefix sharding (8-char) distributes files across many directories, avoiding hotspots
- **No stale images**: Content-addressed storage only retains images actively referenced in manifest
- **Atomic safety**: Images written to temp file first, then moved to final path; cleanup on crash

## Refs
- Orchestrator storage: `src/phx_home_analysis/services/image_extraction/orchestrator.py:200-350`
- Manual test: `tests/manual/test_content_addressed_storage.py:37-50`
- Manifest structure: `data/property_images/metadata/image_manifest.json`

## Deps
← imports: ImageExtractionOrchestrator (writes), HTTP client (downloads)
→ used by: Image assessment service (Phase 2), deal sheet generation, visualization pipeline
