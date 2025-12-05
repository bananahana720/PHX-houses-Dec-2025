---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
flags: []
---

# errors

## Purpose
Transient error recovery & classification module. Provides error categorization (transient/permanent), retry logic with exponential backoff (async & sync), and pipeline integration for tracking per-item failures in work_items.json.

## Contents
| Path | Purpose |
|------|---------|
| `__init__.py` | Error classification: `ErrorCategory` enum, `is_transient_error()`, `format_error_message()`, exception classes (`TransientError`, `PermanentError`) |
| `retry.py` | `@retry_with_backoff` (async) & `retry_with_backoff_sync()` (sync), `calculate_backoff_delay()`, `RetryContext` class for retry logic |
| `pipeline.py` | `mark_item_failed()`, `get_failure_summary()`, `clear_failure_status()` for work_items.json integration |

## Tasks
- [x] Implement error classification (transient/permanent HTTP codes) `P:H`
- [x] Implement exponential backoff decorator for async functions `P:H`
- [x] Implement sync retry function `retry_with_backoff_sync()` `P:H`
- [x] Implement pipeline error tracking (per-address/phase failures) `P:H`
- [ ] Add integration tests for transient error recovery `P:M`

## Learnings
- HTTP status codes: 5xx + 429 = transient (retry); 4xx = permanent (fail)
- Exponential backoff prevents thundering herd; jitter required for concurrent retries
- Conservative default: unknown errors treated as non-transient (safe)
- Pipeline integration uses atomic temp-file writes for work_items.json safety
- Sync retry available via `retry_with_backoff_sync()` wrapper function

## Refs
- Status codes: `__init__.py:32-54`
- Async retry decorator: `retry.py:33-200`
- Sync retry function: `retry.py:202-250`
- Backoff calculation: `retry.py:251-300`
- Pipeline integration: `pipeline.py:26-105`

## Deps
← `src/phx_home_analysis/__init__.py`
→ imported by: agents (listing-browser, map-analyzer, image-assessor), image extraction services, data enrichment pipelines