---
last_updated: 2025-12-04T10:30:00Z
updated_by: agent
staleness_hours: 72
line_target: 80
flags: []
---
# PHX Houses Analysis Pipeline

## Purpose
Evaluates Phoenix residential properties against buyer kill-switches (8 HARD criteria) and scores them (605 pts max) to identify Unicorn/Contender/Pass tiers.

## Critical Rules
- Inherits `~/.claude/CLAUDE.md` rules; project rules add but cannot relax
- **Stop-the-line**: data corruption, kill-switch changes without recalc, Phase 2 spawn without Phase 1 validation
- **Ask before**: modifying kill-switch thresholds, scoring dimensions, `enrichment_data.json` schema
- **Never**: placeholders/TODOs, bypass failing checks, destructive `data/*.json` ops without backup

## Tool Usage (MANDATORY)
| NEVER | ALWAYS Instead |
|-------|----------------|
| `bash cat/head/tail` | `Read` tool |
| `bash grep/rg` | `Grep` tool |
| `bash find/ls` | `Glob` tool |
| Playwright for Zillow | `scripts/extract_images.py` |

## Stack
- **Python**: 3.12, pandas 2.3, Pydantic 2.12, httpx 0.28
- **Browser**: nodriver 0.48 (stealth), playwright 1.56 (fallback)
- **Tools**: ruff 0.14.7, mypy 1.19, pytest 9.0.1, uv

## Kill-Switches (8 HARD - instant fail)
HOA=$0 | beds≥4 | baths≥2 | sqft>1800 | lot>8k | garage≥1 | sewer=city | year≤2024

## Scoring (605 pts max)
- **Location** (250): schools, safety, orientation, proximity
- **Systems** (175): HVAC, roof, pool, solar
- **Interior** (180): kitchen, master, layout, finishes
- **Tiers**: Unicorn >480, Contender 360-480, Pass <360

## Pipeline Phases
```
Phase 0: County API → lot, year, garage
Phase 1: listing-browser + map-analyzer (Haiku) → images, hoa, schools, orientation
Phase 2: image-assessor (Sonnet) → interior/exterior scores
Phase 3: Synthesis → total score, tier, verdict
Phase 4: Reports → deal sheets
```

## Key Locations
| Purpose | Path |
|---------|------|
| Property data | `data/enrichment_data.json` |
| Pipeline state | `data/work_items.json` |
| Scoring config | `src/phx_home_analysis/config/` |
| Scripts | `scripts/phx_home_analyzer.py`, `scripts/extract_*.py` |
| Agents | `.claude/agents/*.md` |

## Quick Commands
```bash
/analyze-property --all        # All properties
/analyze-property "123 Main"   # Single property
python scripts/phx_home_analyzer.py  # Manual scoring
```

## Arizona Specifics
- **Orientation**: North=30pts (best), West=0pts (worst)
- **HVAC**: 10-15yr lifespan (not 20+)
- **Pool**: $250-400/mo ownership
- **Solar leases**: Liability, not asset

## Refs
| Resource | Path |
|----------|------|
| Kill-switch | `src/phx_home_analysis/config/constants.py:1-50` |
| Scoring | `src/phx_home_analysis/config/scoring_weights.py` |
| Protocols | `.claude/protocols.md` |
