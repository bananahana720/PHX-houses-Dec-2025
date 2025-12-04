# Source Code Documentation

### Core Library (`src/phx_home_analysis/`)

**Package README:** `src/phx_home_analysis/CLAUDE.md`

**Module Structure:**
```
src/phx_home_analysis/
├── __init__.py (package exports)
├── config/ (scoring weights, constants, settings)
├── domain/ (entities, value objects, enums)
├── repositories/ (CSV, JSON data access)
├── services/ (22 service modules)
│   ├── kill_switch/ (filtering logic)
│   ├── scoring/ (18 scoring strategies)
│   ├── cost_estimation/ (monthly cost projection)
│   ├── image_extraction/ (stealth automation)
│   ├── data_integration/ (multi-source merging)
│   ├── quality/ (data quality metrics)
│   └── [16 other services]
├── validation/ (Pydantic schemas, validators)
├── pipeline/ (main orchestrator)
├── reporters/ (output formatters)
└── visualizations/ (chart generation)
```

**Key Files:**
- `config/constants.py` (601 lines) - All magic numbers and thresholds
- `config/scoring_weights.py` (380 lines) - 600-point scoring system definition
- `config/settings.py` (417 lines) - Application configuration
- `domain/entities.py` - Property entity (complete property data)
- `services/kill_switch/constants.py` (89 lines) - Kill-switch configuration
- `pipeline/orchestrator.py` - Main analysis pipeline

---

### Scripts (`scripts/`)

**Scripts README:** `scripts/CLAUDE.md`

**Key Scripts:**
- `phx_home_analyzer.py` - Main scoring pipeline
- `extract_county_data.py` - Phase 0: County Assessor API
- `extract_images.py` - Phase 1: Image extraction
- `validate_phase_prerequisites.py` - Pre-spawn validation
- `deal_sheets/` - Report generation module (Python package)
- `generate_all_visualizations.py` - Chart generation
- `data_quality_report.py` - Data quality assessment
- `integration_verification.py` - Integration testing

---

### Tests (`tests/`)

**Tests README:** `tests/CLAUDE.md`

**Test Structure:**
```
tests/
├── unit/ (fast, no I/O)
│   ├── test_domain.py (entities, value objects)
│   ├── test_scorer.py (scoring strategies)
│   ├── test_kill_switch.py (kill-switch logic)
│   └── [15+ other unit tests]
├── integration/ (slower, with I/O)
│   ├── test_pipeline.py (complete workflow)
│   ├── test_deal_sheets_simple.py
│   └── [4 other integration tests]
├── benchmarks/ (performance)
│   └── test_lsh_performance.py
├── fixtures/ (test data)
└── conftest.py (pytest configuration)
```

**Test Coverage:** ~75% (estimated)

---
