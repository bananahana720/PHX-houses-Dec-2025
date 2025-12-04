---
last_updated: 2025-12-04
updated_by: Claude (Agent)
staleness_hours: 24
flags: []
---
# tests/unit/errors

## Purpose

Unit tests for error handling module covering error classification, retry decorator, and pipeline integration. Validates transient error detection, exponential backoff calculation, retry context state management, and work_items.json integration.

## Contents

| Test File | Purpose | Test Count |
|-----------|---------|-----------|
| `test_classification.py` | Error classification: HTTP codes, exception types, error messages | ~40 tests |
| `test_retry.py` | Retry decorator, backoff calculation, retry context state | ~30 tests |
| `__init__.py` | Module initialization |  |

## Test Organization

**Classification Tests (test_classification.py):**
- `TestIsTransientError` - HTTP 429, 503, 504, 502, 500, ConnectionError, TimeoutError
- `TestGetErrorCategory` - ErrorCategory.TRANSIENT, PERMANENT assignment
- `TestFormatErrorMessage` - Actionable suggestions for common HTTP codes

**Retry Tests (test_retry.py):**
- `TestCalculateBackoffDelay` - Exponential formula (1s, 2s, 4s, 8s, 16s), jitter, max_delay cap
- `TestRetryWithBackoff` - Async decorator, transient retries, permanent errors, exhausted retries
- `TestRetryContext` - State management, should_retry(), handle_error(), get_delay()

## Key Test Coverage

**Transient Classification:**
- HTTP codes: 429 (rate limit), 503 (unavailable), 504 (timeout), 502 (bad gateway), 500 (error)
- Exception types: ConnectionError, TimeoutError
- Error attributes: status_code, response.status_code

**Permanent Errors:**
- HTTP codes: 400, 401 (unauthorized), 403 (forbidden), 404 (not found)
- Other: ValueError, RuntimeError (non-transient)

**Backoff Sequence (max_retries=5, min_delay=1.0, jitter=0.5):**
- Attempt 1: 1.0s + jitter
- Attempt 2: 2.0s + jitter
- Attempt 3: 4.0s + jitter
- Attempt 4: 8.0s + jitter
- Attempt 5: 16.0s + jitter (capped at max_delay=60.0s)

## Tasks

- [x] Document error classification test scenarios
- [x] Map backoff calculation test cases (exponential, jitter, caps)
- [x] Document async retry decorator test patterns
- [x] Extract test counts per file (70 total error tests)
- [ ] Add integration with work_items.json state tracking P:M
- [ ] Add performance benchmarks for concurrent retry storms P:L

## Learnings

- **Conservative default:** Unknown errors default to non-transient to prevent infinite retry loops
- **Jitter critical:** Random jitter prevents "thundering herd" after service recovery
- **Async-only:** Decorator is async-only; use RetryContext for sync retry patterns
- **Retry state explicit:** RetryContext provides imperative control when decorator is insufficient

## Refs

- Classification: `test_classification.py:1-50` (HTTP codes, exception types)
- Backoff math: `test_retry.py:50-100` (exponential formula, caps)
- Decorator tests: `test_retry.py:100-200` (async retry patterns)
- Backoff sequence: `calculate_backoff_delay()` (1, 2, 4, 8, 16s)

## Deps

← Imports from:
  - `src/phx_home_analysis/errors/__init__.py` - Classification functions
  - `src/phx_home_analysis/errors/retry.py` - Retry decorator, context
  - pytest, unittest.mock (AsyncMock, patch)

→ Imported by:
  - CI/CD pipeline (must pass before merge)
  - Integration tests validate end-to-end retry + work_items tracking
