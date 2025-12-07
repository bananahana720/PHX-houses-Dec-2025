# Session Compact: Pipeline Alignment Review (2025-12-06)

## Goal
Align PHX Houses image extraction pipeline with data pipeline best practices while fixing PhoenixMLS Search navigation blocker.

## Key Decisions Made
1. **Scope**: Align existing code with pipeline principles (not just PhoenixMLS fix)
2. **Priority**: Error handling + schema versioning (AP-2/AP-6, AP-3)
3. **Breaking Changes**: Soft migration (add new fields, ignore missing)
4. **Tests**: Maintain current coverage (119 tests)

## Critical Files
| File | Lines | Purpose |
|------|-------|---------|
| `orchestrator.py` | 1672 | Main coordinator (god object) |
| `state_manager.py` | 376 | Atomic writes, crash recovery |
| `state_tracker.py` | 474 | Unified state facade |
| `concurrency_manager.py` | 397 | Circuit breaker, semaphores |
| `image_processor.py` | 361 | Deduplication, content-addressed storage |
| `validators.py` | 390 | Pre/during/post validation |
| `phoenix_mls_search.py` | 687 | PhoenixMLS Search extractor (0 images issue) |

## Anti-Patterns to Address
| ID | Issue | Priority | Fix |
|----|-------|----------|-----|
| AP-2/AP-6 | Silent failures, missing retries | HIGH | Add retry decorator, error classification |
| AP-3 | No schema versioning | MEDIUM | Add version field to state files |
| AP-1 | Scattered transformation logic | MEDIUM | Complete ImageProcessor refactor |
| AP-4 | Dual write without transactions | LOW | Add WAL pattern |

## PhoenixMLS Navigation Blocker
- **Symptom**: Autocomplete click succeeds, but page doesn't navigate to listing
- **Evidence**: `Phoenix MLS Search extracted 0 image URLs`
- **Hypothesis**: Autocomplete click submits search form instead of navigating
- **Debug Status**: Live testing agent launched

## Architecture Strategy
- **Pattern**: ETL with staged validation
- **Ingestion**: Multi-source extractors (Zillow, Redfin, PhoenixMLS, Assessor)
- **Transform**: ImageProcessor (dedup + standardize + content-address)
- **Load**: Atomic JSON writes with checkpointing
- **Quality**: Pre/during/post validation with reconciliation

## Existing Strengths (Keep)
- Atomic file writes (temp + os.replace)
- Circuit breaker (3 failures = 5min timeout)
- Content-addressed storage (MD5-based)
- Perceptual hash dedup with LSH
- URL-level incremental tracking
- Comprehensive validation (6 error types)

## Next Steps
1. Wait for live test results (PhoenixMLS debug)
2. Implement error handling improvements (AP-2/AP-6)
3. Add schema versioning (AP-3)
4. Complete ImageProcessor integration (AP-1)
5. Run full test suite validation

## Constraints
- Python 3.10+ (3.13 dev)
- nodriver 0.48.1 for stealth browser
- pytest 9.0.1 for testing
- Atomic writes required for all state files
- No Playwright for Zillow (use scripts/extract_images.py)
