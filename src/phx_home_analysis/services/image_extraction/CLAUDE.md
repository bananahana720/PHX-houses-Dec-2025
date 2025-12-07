---
last_updated: 2025-12-06T19:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# image_extraction

## Purpose
Multi-source image extraction with deduplication, state persistence, and crash recovery. Supports Zillow, Redfin, Maricopa Assessor, and PhoenixMLS sources.

## Contents
| File | Purpose |
|------|---------|
| `orchestrator.py` | Main coordinator (~1618 lines, being refactored) |
| `concurrency_manager.py` | Circuit breaker + error aggregation + semaphore |
| `image_processor.py` | Dedup + standardize + content-addressed storage |
| `state_tracker.py` | Consolidated state + URL tracking + manifest |
| `state_manager.py` | ExtractionState persistence (extraction_state.json) |
| `url_tracker.py` | URL lifecycle tracking (url_tracker.json) |
| `deduplicator.py` | Perceptual hash (pHash/dHash) with LSH |
| `validators.py` | Pre/during/post extraction validation |
| `extractors/` | Source-specific extractors (stealth browser-based) |

## Key Patterns
- **Content-addressed storage**: MD5(content) → file path `{hash[:8]}/{hash}.png`
- **Atomic writes**: temp file + os.replace() for crash safety
- **Circuit breaker**: 3 failures → 5min timeout per source
- **Async checkpoints**: run_in_executor for non-blocking I/O

## Tasks
- [ ] Complete orchestrator refactor to use new services `P:H`
- [ ] Wire ConcurrencyManager, ImageProcessor, StateTracker `P:H`

## Learnings
- Decomposed from 1618-line god object into 3 services
- StateTracker consolidates 4 services into single facade
- 93 new unit tests added for decomposed services

## Refs
- ConcurrencyManager: `concurrency_manager.py:1-350`
- ImageProcessor: `image_processor.py:1-300`
- StateTracker: `state_tracker.py:1-473`
- Extractors: `extractors/base.py`, `extractors/stealth_base.py`

## Deps
← domain/entities.py, domain/enums.py
→ /analyze-property command, scripts/extract_images.py
