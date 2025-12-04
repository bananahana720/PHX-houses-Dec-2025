---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# tests/live

## Purpose
Live API tests for external service validation. Makes real HTTP calls to Maricopa County Assessor API to validate authentication, schema compliance, rate limiting, data accuracy, and error handling. Excluded from default pytest runs (use `-m live` flag).

## Contents
| Path | Purpose |
|------|---------|
| `__init__.py` | Module docstring + setup instructions (11 lines) |
| `conftest.py` | Live test fixtures: token loading, API client factory, rate limiter, response recording (185 lines) |
| `test_county_assessor_live.py` | 10 parameterized live tests across 5 categories: authentication (2), schema validation (3), rate limiting (1), data accuracy (2), error handling (2) (259 lines) |
| `README.md` | Comprehensive documentation: prerequisites, running tests, test categories, troubleshooting, CI/CD integration (660 lines) |

## Tasks
- [x] Implementation complete (all 10 tests passing)
- [x] Response recording for drift detection (--record-responses flag)
- [x] Rate limiting configured (0.5s default, configurable via CLI)
- [x] Documentation complete (README + inline docstrings)

## Learnings
- Live tests catch mock drift between recorded responses and real API behavior—essential for integration validation before releases
- Rate limiter at 60 requests/min prevents 429 errors; proactive throttling at 70% prevents threshold violations
- Recording format (tests/fixtures/recorded/) with schema_version enables version-aware drift detection workflows
- Tests skip gracefully when MARICOPA_ASSESSOR_TOKEN missing (pytest auto-skip in fixture)
- Parametrized tests with known addresses + constraint ranges allow range-based validation (catch major changes, tolerate minor updates)

## Refs
- Fixture definitions: `conftest.py:33-185` (pytest hooks, token/client/rate-limiter/recording)
- Test categories: `test_county_assessor_live.py:57-277` (5 test classes, 10 tests total)
- Known test addresses: `test_county_assessor_live.py:37-54` (2 parametrized addresses with constraints)
- Rate limit config: `conftest.py:119-125` (60/min, 0.7 throttle threshold, 0.5s min_delay)
- Response recording: `conftest.py:129-185` (recording fixture with JSON output to tests/fixtures/recorded/)
- Module docstring: `__init__.py:1-10` (quick reference)

## Deps
← Imports from:
- `phx_home_analysis.services.county_data.MaricopaAssessorClient` (real API client)
- `phx_home_analysis.services.api_client.rate_limiter.RateLimit, RateLimiter` (rate limiting)
- `pytest` (framework, markers, fixtures)
- `os, json, datetime, pathlib` (stdlib)

→ Imported by:
- CI/CD nightly jobs (pytest tests/live/ -m live)
- Manual integration validation before releases
- Response baseline recording for drift detection workflows