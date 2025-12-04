# scripts/CLAUDE.md

---
last_updated: 2025-12-02
updated_by: Claude Code
staleness_hours: 48
---

## Purpose

Main analysis scripts and utilities for the PHX Home Analysis pipeline. Orchestrates data extraction, scoring, filtering, visualization, and reporting workflows. Scripts here provide CLI interfaces to the core library (`src/phx_home_analysis/`) and handle end-to-end pipeline operations.

## Core Pipeline Scripts

| Script | Purpose | Usage | Phase |
|--------|---------|-------|-------|
| `pipeline_cli.py` | Modern unified CLI for complete pipeline execution with progress reporting and phase coordination (NEW - E5.S1) | `python scripts/pipeline_cli.py --all` | All (0-4) |
| `phx_home_analyzer.py` | Main scoring pipeline - applies kill-switch filters and weighted scoring | `python scripts/phx_home_analyzer.py` | Phase 3 |
| `extract_county_data.py` | Extract official county data from Maricopa Assessor API (lot size, year built, garage, sewer, pool) | `python scripts/extract_county_data.py --all [--update-only]` | Phase 0 |
| `extract_images.py` | Multi-source image extraction with stealth browsers (Zillow, Redfin) using nodriver + curl_cffi | `python scripts/extract_images.py --all [--sources zillow,redfin]` | Phase 1 |
| `validate_phase_prerequisites.py` | Pre-spawn validation and data quality reconciliation - ensures dependencies met before agent dispatch | `python scripts/validate_phase_prerequisites.py --address "ADDR" --phase phase2_images --json` | Pre-Phase 2 |
| `analyze.py` | CLI entry point for complete analysis pipeline - loads CSV/JSON, filters, scores, ranks properties | `python scripts/analyze.py [--input CSV] [--enrichment JSON]` | Phase 3 |

### Extract County Data Details
- **API Modes**: Official API (requires `MARICOPA_ASSESSOR_TOKEN`) or ArcGIS Public API (no auth, basic data)
- **Outputs**: `lot_sqft`, `year_built`, `garage_spaces`, `sewer_type`, `pool`, `tax_annual`
- **Options**: `--all`, `--address "ADDR"`, `--dry-run`, `--update-only`, `-v`

### Extract Images Details
- **Sources**: Zillow, Redfin, Phoenix MLS, Maricopa County Assessor
- **Features**: Perceptual hash deduplication, state persistence, resumable operations
- **Options**: `--all`, `--address "ADDR"`, `--sources LIST`, `--dry-run`, `--resume`, `--fresh`, `-v`
- **Security**: Uses stealth browsers (nodriver) to bypass anti-bot protections
- **Output**: `data/property_images/processed/{folder}/` with metadata in `extraction_state.json`

### Validate Prerequisites Details
- **Validation**: Checks Phase 1 listing completion, image folder exists, required fields present
- **Reconciliation**: `--reconcile` flag repairs data inconsistencies between work_items.json, enrichment_data.json, CSV
- **Returns**: JSON with `can_spawn`, `reason`, `context` (image_folder, image_count, property_data)
- **Exit Codes**: 0 = success/can_spawn, 1 = blocked/errors_found

### Pipeline CLI Details (NEW - E5.S1)
- **Framework**: Typer CLI framework with async/await support
- **Progress**: Rich library progress bar with percentage, ETA, status table
- **Commands**: `--all` (all properties), `--test` (first 5), `<address>` (single), `--status` (current state)
- **Options**: `--resume` (default), `--fresh` (clear state), `--strict` (fail fast), `--skip-phase N`
- **Output**: Real-time progress, phase transitions, final tier breakdown, deal sheet generation
- **State**: Tracks in work_items.json for crash recovery and resumption

## Visualization Scripts

| Script | Output | Description |
|--------|--------|-------------|
| `generate_all_visualizations.py` | All visualizations in parallel | Master runner for all viz scripts |
| `golden_zone_map.py` | `reports/html/golden_zone_map.html` | Interactive Folium map with kill-switch status, score-based marker size |
| `generate_map.py` | `reports/html/golden_zone_map.html` | Interactive property map (alternative implementation) |
| `generate_flood_map.py` | `reports/html/flood_zone_map.html` | Flood zone overlay map |
| `generate_crime_heatmap.py` | `reports/html/crime_heatmap.html` | Crime data heatmap visualization |
| `value_spotter.py` | `reports/html/value_spotter.html` | Scatter plot: score vs price (identifies underpriced gems in "Value Zone") |
| `radar_charts.py` | `reports/html/radar_comparison.html` | Comparative radar chart for top 3 properties (5 dimensions: price, location, systems, interior, schools) |
| `sun_orientation_analysis.py` | Orientation analysis visualization | Analyzes sun exposure impacts on cooling costs |

## Quality & Utility Scripts

| Script | Purpose |
|--------|---------|
| `data_quality_report.py` | Analyzes field completeness, identifies gaps, flags data quality issues |
| `integration_verification.py` | Comprehensive integration checks - imports, circular dependencies, regressions |
| `quality_check.py` | Quick quality validation checks |
| `quality_baseline.py` | Establishes quality baseline metrics |
| `check_data_freshness.py` | Checks staleness of state files and enrichment data |
| `backfill_lineage.py` | Adds data lineage tracking to existing records |
| `security_check.py` | Validates security configuration for image extraction |
| `verify_security_setup.py` | Verifies security sandboxing for browser automation |
| `test_kill_switch_config.py` | Tests kill-switch criteria configuration |
| `test_external_apis.py` | Tests connectivity to external APIs (County Assessor, etc.) |

## Reporting Scripts

| Script | Output | Description |
|--------|--------|-------------|
| `deal_sheets.py` | `reports/deal_sheets/*.html` | Legacy deal sheet generator |
| `generate_single_deal_sheet.py` | Single property deal sheet | Generate deal sheet for one property |
| `generate_all_reports.py` | All reports in parallel | Master runner for all report types |
| `demo_reporters.py` | Demo reporter outputs | Demonstration of various reporter formats |
| `serve_reports.py` | HTTP server on :8000 | Local server for viewing HTML reports |

### Deal Sheets Package (`deal_sheets/`)
- **Module**: `python -m scripts.deal_sheets`
- **Components**:
  - `templates.py`: HTML/CSS Jinja2 templates
  - `data_loader.py`: CSV/JSON loading utilities
  - `renderer.py`: HTML generation functions
  - `utils.py`: Helper functions (slugify, feature extraction)
  - `generator.py`: Main orchestration logic
- **Outputs**: One-page HTML reports with kill-switch indicators, score breakdowns, metrics, master index

## Data Management Scripts

| Script | Purpose |
|--------|---------|
| `build_folder_lookup.py` | Builds `address_folder_lookup.json` mapping addresses to image folders |
| `consolidate_geodata.py` | Consolidates geographic data from multiple sources |
| `geocode_homes.py` | Geocodes property addresses to lat/lon coordinates |
| `extract_location_data.py` | Extracts location-related data (distances, orientation) |
| `migrate_schema.py` | Schema migration for data structure changes |
| `migrate_to_work_items.py` | Migrates legacy state files to `work_items.json` format |
| `archive_properties.py` | Archives old or inactive property records |
| `clear_corrupted_properties.py` | Removes corrupted property data from enrichment files |

## Analysis Scripts

| Script | Purpose |
|--------|---------|
| `show_best_values.py` | Identifies and displays best value properties (high score, low price) |
| `cost_breakdown_analysis.py` | Detailed monthly cost breakdown by component (mortgage, tax, insurance, utilities, pool) |
| `renovation_gap.py` | Analyzes renovation potential and value gaps |
| `risk_report.py` | Generates risk assessment report for properties |
| `estimate_ages.py` | Estimates equipment ages (HVAC, roof, pool) from property data |
| `benchmark_cache.py` | Benchmarks caching performance for data operations |

## Extraction/Batch Scripts

| Script | Purpose |
|--------|---------|
| `extract_county_batch.py` | Batch extraction from County Assessor (wrapper for extract_county_data.py) |
| `generate_extraction_report.py` | Generates summary report of extraction operations |

## Subdirectories

### `lib/`
Library code for scripts (shared utilities, compatibility layers).

**Contents**:
- `kill_switch.py`: Compatibility shim for kill-switch logic (delegates to `src/phx_home_analysis/services/kill_switch/`)
  - **DEPRECATED**: New code should import directly from service layer
  - Used by: `phx_home_analyzer.py`, `deal_sheets.py`, other analysis scripts
  - Provides: `apply_kill_switch()`, `evaluate_kill_switches()` wrapper functions

### `deal_sheets/`
Package for generating property deal sheet reports (see Reporting Scripts section above).

## Environment Variables

- `MARICOPA_ASSESSOR_TOKEN` - Required for official County Assessor API (extract_county_data.py)
- Environment loaded via `python-dotenv` from `.env` file in project root

## Script Conventions

### Common CLI Patterns
```bash
# Process all properties
--all

# Single property
--address "123 Main St, Phoenix, AZ 85001"

# Dry run (preview without changes)
--dry-run

# Update only missing fields
--update-only

# Verbose output
-v / --verbose

# Resume interrupted operation
--resume

# Fresh start (ignore state)
--fresh
```

### Exit Codes
- `0` - Success
- `1` - General error
- `2` - File not found error
- `3` - Data loading error

## Common Operations

### Full Pipeline Execution
```bash
# NEW (E5.S1): Single unified command for complete pipeline
python scripts/pipeline_cli.py --all

# OR manual phase-by-phase execution:
# Phase 0: County data
python scripts/extract_county_data.py --all --update-only

# Phase 1: Images (requires stealth browsers)
python scripts/extract_images.py --all --sources zillow,redfin

# Phase 2: Image assessment (via agent)
/analyze-property --all

# Phase 3: Scoring
python scripts/phx_home_analyzer.py

# Phase 4: Reports
python -m scripts.deal_sheets
python scripts/generate_all_visualizations.py
```

### Data Quality Workflow
```bash
# Check data quality
python scripts/data_quality_report.py

# Check data freshness
python scripts/check_data_freshness.py

# Reconcile inconsistencies
python scripts/validate_phase_prerequisites.py --reconcile --all

# Auto-repair issues
python scripts/validate_phase_prerequisites.py --reconcile --all --repair
```

### Single Property Analysis
```bash
# Validate prerequisites
python scripts/validate_phase_prerequisites.py \
  --address "123 Main St" --phase phase2_images --json

# Extract county data
python scripts/extract_county_data.py --address "123 Main St"

# Extract images
python scripts/extract_images.py --address "123 Main St"

# Analyze (via agent)
/analyze-property "123 Main St"

# Generate deal sheet
python scripts/generate_single_deal_sheet.py --address "123 Main St"
```

## Dependencies

- **Core Library**: `src/phx_home_analysis/` - Domain entities, services, repositories
- **Data Files**:
  - `data/phx_homes.csv` - Property listings
  - `data/enrichment_data.json` - Enriched property data
  - `data/work_items.json` - Pipeline state tracking
  - `data/property_images/metadata/extraction_state.json` - Image extraction state
  - `data/property_images/metadata/address_folder_lookup.json` - Address-to-folder mapping
- **Configuration**:
  - `config/scoring_weights.yaml` - Scoring configuration
  - `.env` - Environment variables (API tokens)

## Pending Tasks

- [ ] Consolidate legacy `deal_sheets.py` with `deal_sheets/` package
- [ ] Remove `lib/kill_switch.py` compatibility shim after migration complete
- [ ] Add retry logic to `extract_images.py` for failed extractions
- [ ] Implement parallel processing for `phx_home_analyzer.py` (large batches)

## Key Learnings

### Image Extraction
- Zillow/Redfin require stealth browsers (nodriver + curl_cffi) to bypass anti-bot protections
- Playwright MCP works for Realtor.com but NOT for Zillow/Redfin (gets blocked)
- Perceptual hashing prevents duplicate images across sources
- State persistence critical for resuming long extraction runs

### County API
- Official API requires token but provides complete data (sewer, pool equipment age)
- Public ArcGIS API is fallback but missing critical fields
- Rate limiting: 1 request/second recommended

### Validation
- Always run `validate_phase_prerequisites.py` before spawning Phase 2 image-assessor agents
- Reconciliation with `--repair` flag can fix most data inconsistencies automatically
- Exit code 1 means blocked - DO NOT spawn agent

### Data Quality
- `work_items.json` is source of truth for pipeline progress
- `enrichment_data.json` may be stale - check timestamps before use
- CSV and JSON can drift - reconciliation script repairs mismatches

## References

- Main scoring pipeline: `phx_home_analyzer.py:1-200`
- County API client: `src/phx_home_analysis/services/county_data.py:1-300`
- Image extraction orchestrator: `src/phx_home_analysis/services/image_extraction.py:1-500`
- Kill-switch service: `src/phx_home_analysis/services/kill_switch/evaluator.py:1-150`
- Validation script: `validate_phase_prerequisites.py:1-400`
- Deal sheets package: `deal_sheets/__init__.py:1-30`

---

**Note**: This directory contains CLI interfaces to core library functionality. For service-layer logic, see `src/phx_home_analysis/`. For agent definitions, see `.claude/agents/`. For skills, see `.claude/skills/`.
