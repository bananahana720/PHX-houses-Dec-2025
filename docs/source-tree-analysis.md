# PHX Houses - Source Tree Analysis

**Generated:** 2025-12-05
**Scan Level:** exhaustive

---

## Repository Root Structure

```
PHX-houses-Dec-2025/
├── .bmad/                      # BMAD workflow methodology
│   ├── bmb/                    # Builder module
│   ├── bmm/                    # Main methodology module
│   └── core/                   # Core tasks and agents
│
├── .claude/                    # Claude Code configuration
│   ├── agents/                 # Subagent definitions
│   ├── commands/               # Custom slash commands
│   ├── hooks/                  # Pre/post tool hooks
│   └── skills/                 # Domain expertise modules
│
├── data/                       # Data files (git-tracked selectively)
│   ├── phx_homes.csv           # Property listings (address, price, beds)
│   ├── enrichment_data.json    # Enriched property data (JSON)
│   ├── work_items.json         # Pipeline state tracking
│   └── property_images/        # Downloaded property images
│       ├── processed/          # Content-addressed storage
│       └── metadata/           # Manifests and run history
│
├── docs/                       # Technical documentation
│   ├── architecture/           # System design docs
│   ├── artifacts/              # Generated reports
│   ├── sprint-artifacts/       # Sprint tracking (BMAD)
│   └── templates/              # Jinja2 HTML templates
│
├── reports/                    # Generated output
│   ├── html/                   # Interactive dashboards
│   ├── csv/                    # Tabular exports
│   └── images/                 # Static visualizations
│
├── scripts/                    # CLI tools (42 scripts)
│   ├── analyze.py              # Main analysis entry point
│   ├── extract_*.py            # Data extraction scripts
│   ├── generate_*.py           # Report generation
│   └── pipeline_cli.py         # Typer CLI orchestrator
│
├── src/                        # Source code
│   └── phx_home_analysis/      # Main package
│
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   ├── integration/            # Integration tests
│   └── live/                   # Live API tests (skipped by default)
│
├── pyproject.toml              # Project configuration
├── CLAUDE.md                   # Project documentation
└── README.md                   # Quick start guide
```

---

## Source Package Structure (`src/phx_home_analysis/`)

```
phx_home_analysis/
│
├── __init__.py                 # Package exports (185 lines)
├── logging_config.py           # Logging setup
├── CLAUDE.md                   # Module documentation
│
├── config/                     # Configuration management
│   ├── __init__.py
│   ├── loader.py               # Config loading with env overrides
│   ├── schemas.py              # Pydantic config schemas
│   └── scoring_weights.py      # 605-point system definition
│
├── domain/                     # Domain entities (DDD)
│   ├── __init__.py             # 45 exports
│   ├── entities.py             # Property (156+ fields)
│   ├── entities_provenance.py  # Field lineage tracking
│   ├── enums.py                # Tier, Orientation, SolarStatus...
│   └── value_objects.py        # Address, Score, ScoreBreakdown
│
├── errors/                     # Error handling
│   ├── __init__.py             # Error classification
│   ├── classification.py       # Transient vs permanent errors
│   └── retry.py                # Exponential backoff decorator
│
├── pipeline/                   # Orchestration
│   ├── __init__.py
│   ├── orchestrator.py         # AnalysisPipeline (legacy)
│   ├── phase_coordinator.py    # Phase sequencing (930 lines)
│   ├── progress.py             # Rich progress bars
│   └── resume.py               # Crash recovery
│
├── reporters/                  # Output generation
│   ├── __init__.py
│   ├── base.py                 # Reporter interface
│   ├── csv_reporter.py         # CSV output
│   └── html_reporter.py        # Jinja2 HTML reports
│
├── repositories/               # Data persistence
│   ├── __init__.py
│   ├── base.py                 # Repository interface
│   ├── csv_repository.py       # CSV file handling
│   ├── json_repository.py      # JSON enrichment data
│   ├── cached_manager.py       # Caching layer
│   └── work_items.py           # Pipeline state
│
├── services/                   # Business logic
│   ├── ai_enrichment/          # AI-powered data inference
│   ├── air_quality/            # Air quality API client
│   ├── analysis/               # Property analysis
│   ├── census_data/            # Census API client
│   ├── classification/         # Tier classification
│   ├── cost_estimation/        # Monthly cost calculator
│   ├── county_data/            # County assessor models
│   ├── crime_data/             # Crime statistics
│   ├── data_integration/       # Data merge strategies
│   ├── enrichment/             # Enrichment merging
│   ├── flood_data/             # FEMA flood zone client
│   ├── image_extraction/       # Image downloading (9 files)
│   │   ├── orchestrator.py     # Extraction coordination
│   │   ├── extractors/         # Zillow, Redfin, Assessor
│   │   ├── file_lock.py        # Concurrent write safety
│   │   ├── validators.py       # Manifest integrity
│   │   └── reconciliation.py   # Sync checks
│   ├── infrastructure/         # Cross-cutting concerns
│   │   ├── browser_pool.py     # Playwright pool
│   │   ├── proxy_manager.py    # Residential proxy rotation
│   │   └── stealth_http_client.py
│   ├── kill_switch/            # Kill-switch filtering
│   │   ├── base.py             # Criterion interface
│   │   ├── criteria.py         # 8 HARD criteria
│   │   ├── filter.py           # KillSwitchFilter
│   │   └── explanation.py      # Human-readable output
│   ├── lifecycle/              # Data lifecycle
│   ├── location_data/          # Location services
│   ├── noise_data/             # Noise level extraction
│   ├── permits/                # Building permits client
│   ├── quality/                # Data quality metrics
│   ├── schema/                 # Schema versioning
│   ├── schools/                # GreatSchools client
│   ├── scoring/                # 605-point scoring
│   │   ├── base.py             # Strategy interface
│   │   ├── scorer.py           # PropertyScorer
│   │   └── strategies/         # 18 scoring strategies
│   └── walkscore/              # WalkScore client
│
├── utils/                      # Shared utilities
│   ├── file_ops.py             # Atomic JSON save
│   └── address_utils.py        # Address normalization
│
└── validation/                 # Data validation
    ├── schemas.py              # Pydantic schemas
    ├── validators.py           # Custom validators
    ├── normalizer.py           # Data normalization
    └── deduplication.py        # Duplicate detection
```

---

## Scripts Directory (`scripts/`)

| Script | Purpose |
|--------|---------|
| `analyze.py` | Main analysis entry point |
| `extract_images.py` | Image extraction from listings |
| `extract_county_data.py` | County Assessor API extraction |
| `pipeline_cli.py` | Typer CLI for pipeline orchestration |
| `generate_all_reports.py` | Generate all HTML/CSV reports |
| `generate_single_deal_sheet.py` | Single property deal sheet |
| `golden_zone_map.py` | Interactive Folium map |
| `radar_charts.py` | Property comparison charts |
| `value_spotter.py` | Value opportunity analysis |
| `quality_check.py` | Data quality validation |
| `smoke_test.py` | Quick validation tests |
| `serve_reports.py` | Local report server |

---

## Test Directory (`tests/`)

```
tests/
├── conftest.py                 # Pytest fixtures
├── __init__.py
│
├── unit/                       # Unit tests (~80 files)
│   ├── test_*.py               # Direct module tests
│   ├── domain/                 # Domain entity tests
│   ├── errors/                 # Error handling tests
│   ├── pipeline/               # Pipeline tests
│   ├── repositories/           # Repository tests
│   └── services/               # Service tests
│       ├── api_client/         # HTTP client tests
│       ├── image_extraction/   # Image extraction tests
│       ├── kill_switch/        # Kill-switch tests
│       ├── maps/               # Google Maps tests
│       ├── quality/            # Quality metrics tests
│       ├── schools/            # School ratings tests
│       └── scoring/            # Scoring tests
│
├── integration/                # Integration tests
│   ├── test_pipeline.py        # Full pipeline test
│   ├── test_kill_switch_chain.py
│   └── test_checkpoint_workflow.py
│
└── live/                       # Live API tests (requires network)
    ├── test_zillow_redfin_live.py
    └── test_county_assessor_live.py
```

---

## Data Directory (`data/`)

```
data/
├── phx_homes.csv               # Source listings
├── enrichment_data.json        # Enriched property data
├── work_items.json             # Pipeline state
├── geocoded_homes.json         # Lat/long coordinates
│
└── property_images/
    ├── processed/              # Content-addressed storage
    │   └── {hash[:8]}/{hash}.png
    └── metadata/
        ├── extraction_state.json
        ├── image_manifest.json
        ├── url_tracker.json
        └── run_history/
```

---

## Critical Entry Points

| Entry Point | File | Purpose |
|-------------|------|---------|
| Main Package | `src/phx_home_analysis/__init__.py` | Package exports |
| CLI | `scripts/pipeline_cli.py` | Typer CLI |
| Pipeline | `src/phx_home_analysis/pipeline/orchestrator.py` | Analysis pipeline |
| Config | `src/phx_home_analysis/config/loader.py` | Configuration |
| Kill-Switch | `src/phx_home_analysis/services/kill_switch/filter.py` | Filtering |
| Scoring | `src/phx_home_analysis/services/scoring/scorer.py` | Scoring |
