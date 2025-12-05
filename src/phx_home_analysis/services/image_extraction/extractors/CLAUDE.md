---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
flags: []
---

# extractors

## Purpose
Source-specific property image extraction drivers supporting Zillow, Redfin, Maricopa Assessor, and Phoenix MLS. Stealth-based async extractors with anti-bot resilience, screenshot capture, and content-addressed storage integration.

## Contents
| Path | Purpose |
|------|---------|
| `base.py` | ImageExtractor abstract base class; interface for all extractors |
| `stealth_base.py` | StealthExtractor base: nodriver-based anti-bot, browser management, screenshot ops |
| `zillow.py` | ZillowExtractor (nodriver) - Zillow listing navigation, image extraction, error recovery |
| `zillow_playwright.py` | ZillowExtractor (Playwright) - Fallback implementation for Zillow |
| `redfin.py` | RedfdinExtractor (nodriver) - Redfin listing data and image extraction |
| `redfin_playwright.py` | RedffinExtractor (Playwright) - Fallback for Redfin |
| `maricopa_assessor.py` | MaricopaAssessorExtractor - County API integration for property records |
| `phoenix_mls.py` | PhoenixMlsExtractor - MLS data and images via stealth browser |
| `__init__.py` | Package exports (ImageExtractor, StealthExtractor, all concrete implementations) |

## Design Patterns
- **Async-first architecture:** All extractors async for concurrent multi-property processing
- **Stealth-based extraction:** nodriver (preferred) + Playwright fallback for anti-bot resilience
- **Screenshot-to-storage:** Screenshots → content-addressed file path (hash-based) → manifest tracking
- **Error recovery:** Retry logic, fallback selectors, graceful degradation on missing data
- **Circuit breaker:** Extractors track failures; disabled temporarily on repeated failures

## Tasks
- [x] Implement base ImageExtractor interface `P:H`
- [x] Implement StealthExtractor for anti-bot resilience `P:H`
- [x] Implement Zillow, Redfin, Assessor, MLS extractors `P:H`
- [x] Add fallback Playwright implementations `P:H`
- [ ] Add performance benchmarks for concurrent extraction `P:M`

## Learnings
- **Stealth extraction critical:** Standard browser automation blocked by PerimeterX; nodriver + anti-detection required
- **Fallback required:** Zillow/Redfin extractors need Playwright fallback for robustness
- **Screenshot reliability:** Image quality varies by source; Assessor API most reliable
- **Concurrent safety:** Multiple extractors can run in parallel; file locking prevents overwrites

## Refs
- ImageExtractor interface: `base.py:1-80`
- StealthExtractor base: `stealth_base.py:1-200`
- Zillow (nodriver): `zillow.py:1-400`
- Redfin (nodriver): `redfin.py:1-350`
- Maricopa Assessor: `maricopa_assessor.py:1-250`

## Deps
← Imports from:
  - `nodriver 0.48` (stealth browser automation)
  - `playwright 1.56` (fallback browser automation)
  - `PIL/Pillow` (image processing)
  - `httpx` (HTTP requests)

→ Imported by:
  - `orchestrator.py` (SourceCircuitBreaker, extraction coordination)
  - `image_extraction/__init__.py` (package exports)
  - `/analyze-property` command (Phase 1)