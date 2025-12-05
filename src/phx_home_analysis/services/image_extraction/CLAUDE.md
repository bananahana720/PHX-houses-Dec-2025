---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
flags: []
---
# src/phx_home_analysis/services/image_extraction

## Purpose
Image extraction service orchestrating multi-source downloads with deterministic content-addressed storage, deduplication, validation, and crash recovery. Supports Zillow, Redfin, Maricopa Assessor, and Phoenix MLS sources.

## Contents
| File | Purpose |
|------|---------|
| `orchestrator.py` | Main orchestrator: source coordination, run_id, --force flag, content-addressed storage |
| `extractors/` | Source-specific extractors: zillow, redfin, maricopa_assessor, phoenix_mls (stealth-based) |
| `file_lock.py` | Cross-process locking: FileLock, PropertyLock, ManifestLock with stale detection |
| `validators.py` | Pre/during-extraction validators: address hashing, batch validation, integrity assertions |
| `reconciliation.py` | Post-extraction reconciliation: manifest integrity, quality scoring, orphan detection |
| `state_manager.py` | Checkpoint/recovery state management (extraction_state.json) |
| `deduplicator.py` | Image content deduplication via MD5 hashing |
| `standardizer.py` | Image normalization and format standardization |
| `url_tracker.py` | URL-level tracking for incremental extraction |
| `metrics.py` | Extraction performance metrics and CAPTCHA tracking |
| `run_logger.py` | Run history and property change logging |

## Key Patterns
- **Content-addressed storage**: File path from MD5(content), not URL → deterministic dedup
- **Run ID tracking**: 8-char run_id embedded for audit trail and crash recovery
- **Cross-process locks**: File-based locking with stale detection (PID:timestamp format)
- **Validator stack**: Pre-extraction (batch dups) → during-extraction (address/hash/file) → post-extraction (reconciliation)
- **Circuit breaker**: Temporarily disable failing sources to prevent cascade failures

## Tasks
- [x] Implement content-addressed storage (E2.S4) `P:H`
- [x] Add pre/during-extraction validators `P:H`
- [x] Implement reconciliation service `P:H`
- [ ] Add concurrent extraction safety tests `P:M`
- [ ] Implement storage quota and cleanup policy `P:M`

## Learnings
- **Address normalization critical**: Case-insensitive, whitespace-trimmed → 8-char property_hash for consistent lookup
- **Lock staleness detection**: Format PID:timestamp enables cleanup without OS dependencies
- **Manifest reconciliation**: Ghost entries (manifest w/o file) vs orphans (file w/o manifest) require separate handling
- **Batch validation**: Detect duplicate addresses in single batch before extraction to avoid overwrites
- **Circuit breaker pattern**: Prevents cascade failures when sources experience rate limits or outages

## Refs
- Orchestrator: `orchestrator.py:56-350` (SourceCircuitBreaker, ImageExtractionOrchestrator)
- FileLock: `file_lock.py:23-150` (FileLock, PropertyLock, ManifestLock)
- Validators: `validators.py:40-300` (PreExtractionValidator, DuringExtractionAssertions)
- Reconciliation: `reconciliation.py:16-200` (ReconciliationReport, reconcile_manifest)
- Extractors: `extractors/base.py:1-100` (ImageExtractor base class)

## Deps
← imports: httpx (downloads), asyncio (concurrency), pathlib (file ops), Image (PIL)
→ used by: /analyze-property command, Phase 1 listing-browser agent, image-assessor agent (Phase 2)
