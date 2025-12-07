---
last_updated: 2025-12-07T22:37:45Z
updated_by: agent
staleness_hours: 24
flags: []
---
# tech-specs

## Purpose
Technical specifications bridging user story requirements to implementation with detailed architecture, API contracts, data models, and implementation guidance.

## Contents
| Path | Purpose |
|------|---------|
| `tech-spec-live-testing-infrastructure.md` | Live testing infra (AC1-AC7): test suite, smoke script, recording fixtures |
| `tech-spec-phoenixmls-search-nodriver.md` | PhoenixMLS Search extractor spec (COMPLETED WITH LIMITATIONS) |
| `tech-spec-phoenixmls-pivot.md` | PhoenixMLS pivot strategy (fallback to Zillow ZPID + Redfin) |
| `e2e-validation-phoenixmls-2025-12-05.md` | End-to-end validation report |
| `debug-notes-phoenixmls-search-2025-12-06.md` | Debug session 2 notes (autocomplete fixes) |

## Key Patterns
- **Actual code signatures**: Use real type hints, not pseudocode
- **Reference existing patterns**: Link to file:line for consistency (e.g., `tests/conftest.py:1-638`)
- **Implementation order with deps**: Dependency graph prevents blocking
- **API contracts enable parallel dev**: Define contracts first
- **Debug notes separate**: Move lengthy debug sessions to separate files for spec readability

## Tasks
- [ ] Create tech spec template for future stories `P:M`
- [ ] Cross-reference specs with implementation PRs `P:L`
- [ ] Archive completed specs to separate directory `P:L`

## Learnings
- **Tech specs save implementation time**: Convert story AC to concrete architecture upfront
- **PhoenixMLS Search blocker**: Navigation autocomplete breaks nodriver; Zillow ZPID + Redfin fallback achieves 100% image coverage
- **Multi-source resilience validated**: 3-tier strategy (PhoenixMLS → Zillow ZPID → Redfin) handles individual source failures
- **Documentation cleanup valuable**: 159-line debug session moved to separate file improves readability

## Refs
- Story source: `../stories/`
- Test patterns: `../../../tests/conftest.py:1-638`
- CLI patterns: `../../../scripts/extract_county_data.py:164-489`
- Rate limiter: `../../../src/phx_home_analysis/services/api_client/rate_limiter.py:62-257`

## Deps
← imports: `../stories/` (requirements), existing test/API patterns
→ used by: implementation PRs, Epic completion validation
