---
last_updated: 2025-12-05T23:30:00Z
updated_by: agent
staleness_hours: 24
line_target: 60
---

# scripts/

CLI interfaces and orchestration scripts for the PHX home analysis pipeline. Handles data extraction, validation, scoring, visualization, and reporting workflows.

## Contents

| File | Purpose |
|------|---------|
| `pipeline_cli.py` | Unified Typer CLI for complete end-to-end execution (Phase 0-4) |
| `phx_home_analyzer.py` | Kill-switch filtering + 605-point scoring |
| `extract_county_data.py` | Maricopa Assessor API extraction (lot, year, garage, sewer, pool) |
| `extract_images.py` | Multi-source image extraction (PhoenixMLS, Zillow, Redfin) with stealth browsers |
| `validate_phase_prerequisites.py` | Pre-spawn validation + data reconciliation |
| `generate_all_visualizations.py` | Master runner: golden_zone_map, value_spotter, radar_charts, etc. |
| `generate_single_deal_sheet.py` | HTML deal sheet generation (single property) |
| `data_quality_report.py` | Completeness analysis + gap detection |

## Key Patterns

- **CLI pattern**: All scripts support `--all`, `--address "..."`, `--dry-run`, `--verbose`, `--resume` / `--fresh`
- **State tracking**: Pipeline persists progress in `data/work_items.json` for crash recovery
- **Browser stealth**: `extract_images.py` uses nodriver + curl_cffi to bypass anti-bot (NOT Playwright)
- **Source priority**: PhoenixMLS Search → Zillow → Redfin (fallback chain)

## Tasks

- [ ] Consolidate legacy `deal_sheets.py` with `deal_sheets/` package `P:M`
- [ ] Remove `lib/kill_switch.py` compat shim after migration `P:M`
- [ ] Add retry logic to `extract_images.py` for failed extractions `P:L`
- [ ] Implement parallel scoring for large batches `P:L`

## Learnings

- **Browser automation**: Zillow/Redfin block standard Playwright; nodriver + curl_cffi required for stealth
- **County API**: Official token-gated API provides complete data (sewer, pool age); public ArcGIS fallback missing critical fields
- **Validation critical**: Always run `validate_phase_prerequisites.py` with `--repair` before spawning Phase 2 agents; exit code 1 = blocked

## Refs

- Scoring logic: `phx_home_analyzer.py:1-200`
- County client: `src/phx_home_analysis/services/county_data.py:1-300`
- Kill-switch service: `src/phx_home_analysis/services/kill_switch/evaluator.py:1-150`
- Validation: `validate_phase_prerequisites.py:1-400`

## Deps

← imports: `src/phx_home_analysis/`, `dotenv`, `httpx`, `Pydantic`, `nodriver`, `curl_cffi`
→ imported by: `.claude/commands/analyze-property.md`, agents
