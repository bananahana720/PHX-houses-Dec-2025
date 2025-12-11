---
last_updated: 2025-12-10
updated_by: agent
---
# scripts

## Purpose
Orchestration and CLI scripts for the end-to-end PHX home analysis pipeline (Phase 0-4): data extraction, validation, kill-switch filtering, scoring, visualization, and reporting.

## Contents
| Script | Purpose |
|--------|---------|
| `pipeline_cli.py` | Unified Typer CLI entry point for complete workflow execution |
| `phx_home_analyzer.py` | Kill-switch filtering + 605-point scoring orchestration |
| `extract_county_data.py` | Maricopa Assessor API extraction (lot, year, garage, sewer) |
| `extract_images.py` | Multi-source image extraction with nodriver stealth browser |
| `validate_phase_prerequisites.py` | Pre-phase validation + data reconciliation |
| `generate_all_visualizations.py` | Golden zone map, value spotter, radar charts |
| `generate_single_deal_sheet.py` | HTML deal sheet generation |
| `data_quality_report.py` | Completeness + gap detection analysis |
| `quality_check.py` | Linting + dependency audit |
| `smoke_test.py` | Integration sanity checks |

## CLI Patterns
- **Modes**: `--all`, `--test`, `--address "..."`, `--status`, `--dry-run`
- **Recovery**: `--resume` (default, checkpoint-based), `--fresh` (clear state)
- **State**: Persisted in `data/work_items.json`, `data/enrichment_data.json`
- **Browser**: nodriver + curl_cffi for Zillow/Redfin (stealth required)

## Key Files
- `lib/kill_switch.py` - Kill-switch evaluator compat shim
- `lib/` - Shared utilities (country data, schema, models)
