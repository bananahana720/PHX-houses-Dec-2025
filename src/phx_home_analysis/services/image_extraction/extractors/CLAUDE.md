---
last_updated: 2025-12-06T21:30:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# extractors

## Purpose
Source-specific property image extraction drivers with anti-bot bypass. Supports Zillow, Redfin, Maricopa Assessor, and Phoenix MLS using nodriver (stealth) or Playwright (fallback).

## Contents
| File | Purpose |
|------|---------|
| `base.py` | `ImageExtractor` ABC, exception classes (`ExtractionError`, `SourceUnavailableError`) |
| `stealth_base.py` | `StealthBrowserExtractor` - nodriver + curl_cffi anti-bot base class |
| `zillow.py` | `ZillowExtractor` (nodriver) - ZPID extraction, gallery navigation |
| `redfin.py` | `RedfinExtractor` (nodriver) - CDN image extraction |
| `phoenix_mls_search.py` | `PhoenixMLSSearchExtractor` - autocomplete + direct URL navigation |
| `maricopa_assessor.py` | `MaricopaAssessorExtractor` - County API integration |
| `__init__.py` | Conditional imports based on `USE_PLAYWRIGHT_EXTRACTORS` env var |

## Key Patterns
- **Stealth-first**: nodriver + curl_cffi bypasses PerimeterX (Zillow/Redfin)
- **Fallback chain**: nodriver -> Playwright via `USE_PLAYWRIGHT_EXTRACTORS=1`
- **Retry decorator**: `@retry_with_backoff` on `download_image` for transient errors
- **CAPTCHA solving**: 2-layer press-and-hold with CDP shadow DOM traversal

## Tasks
- [ ] Add performance benchmarks for concurrent extraction `P:M`

## Learnings
- Zillow/Redfin block standard Playwright - must use nodriver stealth
- PhoenixMLS uses ARIA tree pattern (`[role='treeitem']`) for autocomplete
- Direct URL construction from MLS# more reliable than autocomplete click
- PerimeterX detects Bezier curve patterns - need random control points

## Refs
- Stealth base: `stealth_base.py:42-170` (class definition + download_image)
- CAPTCHA solver: `stealth_base.py:733-920` (_attempt_captcha_solve)
- PhoenixMLS autocomplete: `phoenix_mls_search.py:200-350`

## Deps
- nodriver 0.48, playwright 1.56, httpx, PIL/Pillow
- imported by: `orchestrator.py`, `/analyze-property` command
