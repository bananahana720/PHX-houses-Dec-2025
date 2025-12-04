---
last_updated: 2025-12-04T17:33:00Z
updated_by: agent
staleness_hours: 24
flags: []
---

# errors

## Purpose
Transient error recovery & classification module. Provides error categorization (transient/permanent), retry logic with exponential backoff, and pipeline integration for tracking per-item failures in work_items.json.

## Contents
| Path | Purpose |
|------|---------|
| `__init__.py` | Error classification: `ErrorCategory` enum, `is_transient_error()`, `format_error_message()`, exception classes (`TransientError`, `PermanentError`) |
| `retry.py` | `@retry_with_backoff` decorator, `calculate_backoff_delay()`, `RetryContext` class for async retry logic |
| `pipeline.py` | `mark_item_failed()`, `get_failure_summary()`, `clear_failure_status()` for work_items.json integration |

## Tasks
- [x] Implement error classification (transient/permanent HTTP codes)
- [x] Implement exponential backoff decorator for async functions
- [x] Implement pipeline error tracking (per-address/phase failures)
- [ ] Add integration tests for transient error recovery (PR pending)

## Learnings
- HTTP status codes: 5xx + 429 = transient (retry); 4xx = permanent (fail)
- Exponential backoff prevents thundering herd; jitter required for concurrent retries
- Conservative default: unknown errors treated as non-transient (safe)
- Pipeline integration uses atomic temp-file writes for work_items.json safety

## Refs
- Status codes: `__init__.py:32-54`
- Retry decorator: `retry.py:33-124`
- Backoff calculation: `retry.py:127-164`
- Pipeline integration: `pipeline.py:26-105`

## Deps
← `src/phx_home_analysis/__init__.py`
← (imported by future agents: listing-browser, map-analyzer, image-assessor)