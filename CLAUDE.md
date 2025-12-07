---
last_updated: 2025-12-05T12:00:00Z
updated_by: agent
staleness_hours: 72
line_target: 80
---


# PHX Houses Analysis Pipeline

## Purpose
Evaluates Phoenix properties against 8 HARD kill-switches and scores (605 pts max) into Unicorn/Contender/Pass tiers.

## Critical Rules
| Category | Items |
|----------|-------|
| Stop-the-line | Data corruption, kill-switch changes w/o recalc, Phase 2 w/o Phase 1 |
| Ask before | Kill-switch thresholds, scoring weights, `enrichment_data.json` schema |
| Never | Placeholders/TODOs, bypass checks, destructive `data/*.json` ops |

## Stack
| Component | Version/Tool |
|-----------|--------------|
| Python | 3.10+ (3.13 dev) |
| Testing | pytest 9.0.1, respx 0.22.0 |
| Data | Pydantic 2.12.5, pandas 2.3.3 |
| Browser | nodriver 0.48.1 (stealth), playwright 1.56 (fallback) |
| Linting | ruff 0.14.7, mypy 1.19.0 |
| Package | uv (preferred), hatchling build |

## Tool Usage (MANDATORY)
| NEVER | ALWAYS Instead |
|-------|----------------|
| `bash cat/head/tail` | `Read` tool |
| `bash grep/rg` | `Grep` tool |
| `bash find/ls` | `Glob` tool |
| Playwright for Zillow | `scripts/extract_images.py` |

## Kill-Switches (8 HARD - instant fail)
`HOA=$0` | `beds>=4` | `baths>=2` | `sqft>1800` | `lot>8k` | `garage>=1` | `sewer=city` | `year<=2024`

## Scoring (605 pts max)
- **Location** (250): schools, safety, orientation, proximity
- **Systems** (175): HVAC, roof, pool, solar
- **Interior** (180): kitchen, master, layout, finishes
- **Tiers**: Unicorn >480, Contender 360-480, Pass <360

## Pipeline Phases
| Phase | Action | Output |
|-------|--------|--------|
| 0 | County API | lot, year, garage |
| 1 | listing-browser + map-analyzer | images, hoa, schools, orientation |
| 2 | image-assessor (Opus 4.5) | interior/exterior scores |
| 3 | Synthesis | total score, tier |
| 4 | Reports | deal sheets |

## Key Locations
| Purpose | Path |
|---------|------|
| Property data | `data/enrichment_data.json` |
| Pipeline state | `data/work_items.json` |
| Kill-switch | `src/phx_home_analysis/services/kill_switch/` |
| Scoring | `src/phx_home_analysis/services/scoring/` |
| Image extraction | `src/phx_home_analysis/services/image_extraction/` |
| Scripts | `scripts/*.py` |

## Quick Commands
```bash
/analyze-property --all           # All properties
/analyze-property "123 Main"      # Single property
pytest tests/unit/ -v             # Run tests
ruff check --fix && ruff format   # Lint/format
```

## Arizona Specifics
| Factor | Value |
|--------|-------|
| Orientation | North=30pts (best), West=0pts (worst) |
| HVAC lifespan | 10-15yr (not 20+) |
| Pool cost | $250-400/mo |
| Solar leases | Liability, not asset |

## CI/CD Checks
`ruff check` | `mypy src/` | `pytest` | `pip-audit --strict`

## Dependencies Policy
- **Blocked**: selenium, requests (use nodriver, httpx)
- **Secrets**: `.env` file (`MARICOPA_ASSESSOR_TOKEN`, proxy creds)
- **Licenses**: MIT/Apache/BSD allowed, GPL blocked
