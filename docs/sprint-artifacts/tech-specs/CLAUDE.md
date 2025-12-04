---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
---

# tech-specs

## Purpose
Technical specifications for sprint implementation. Each spec provides detailed architecture, API contracts, data models, and implementation guidance for complex user stories. Specs bridge the gap between story requirements and actual code implementation.

## Contents
| Path | Purpose |
|------|---------|
| `tech-spec-live-testing-infrastructure.md` | Live testing infrastructure spec (AC1-AC7): test suite, smoke script, recording fixtures |

## Tasks
- [x] Create tech spec for live testing infrastructure `P:H`
- [ ] Add tech spec template for future stories `P:M`
- [ ] Cross-reference specs with implementation PRs `P:L`

## Learnings
- Tech specs should include actual code signatures with type hints (not pseudocode)
- Reference existing file:line for patterns to follow ensures consistency
- Implementation order with dependency graph prevents blocking
- API contracts and data models enable parallel development

## Refs
- Story source: `../stories/story-live-testing-infrastructure.md`
- Test patterns: `tests/conftest.py:1-638`
- CLI patterns: `scripts/extract_county_data.py:164-489`
- Rate limiter: `src/phx_home_analysis/services/api_client/rate_limiter.py:62-257`

## Deps
<- `../stories/` (story requirements)
<- `tests/` (existing test patterns)
<- `src/phx_home_analysis/services/` (API clients)
-> Implementation PRs (consume specs)
-> Story completion (spec guides implementation)
