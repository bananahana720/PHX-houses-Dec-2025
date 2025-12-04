# Project Structure

```
PHX-houses-Dec-2025/
├── src/phx_home_analysis/         # Core analysis library (Python package)
│   ├── config/                    # Scoring weights, constants, settings
│   ├── domain/                    # Entities, value objects, enums
│   ├── repositories/              # Data persistence (CSV, JSON)
│   ├── services/                  # Business logic services
│   │   ├── kill_switch/           # Filtering logic
│   │   ├── scoring/               # Scoring strategies
│   │   ├── cost_estimation/       # Monthly cost projection
│   │   ├── image_extraction/      # Stealth browser automation
│   │   ├── data_integration/      # Multi-source merging
│   │   ├── quality/               # Data quality metrics
│   │   └── [17 other services]/   # Enrichment, analysis, lifecycle, etc.
│   ├── validation/                # Pydantic schemas, validators
│   ├── pipeline/                  # Main orchestrator
│   └── reporters/                 # Output formatters
│
├── scripts/                       # Executable analysis scripts
│   ├── phx_home_analyzer.py       # Main scoring pipeline
│   ├── extract_county_data.py     # Phase 0: County API
│   ├── extract_images.py          # Phase 1: Image extraction
│   ├── validate_phase_prerequisites.py  # Pre-spawn validation
│   ├── deal_sheets/               # Report generation module
│   └── [40+ other scripts]        # Utilities, visualizations, QA
│
├── .claude/                       # Claude Code multi-agent system
│   ├── agents/                    # Subagent definitions (3 agents)
│   │   ├── listing-browser.md     # Zillow/Redfin extraction (Haiku)
│   │   ├── map-analyzer.md        # Geographic analysis (Haiku)
│   │   └── image-assessor.md      # Visual scoring (Sonnet)
│   ├── skills/                    # Domain expertise modules (15 skills)
│   ├── commands/                  # Slash commands (/analyze-property)
│   ├── knowledge/                 # Tool schemas, relationships (JSON)
│   └── protocols.md               # Operational protocols (TIER 0-3)
│
├── data/                          # Data files and state
│   ├── phx_homes.csv              # Source listing data
│   ├── enrichment_data.json       # Enriched property data (LIST of dicts!)
│   ├── work_items.json            # Pipeline state tracking
│   ├── property_images/           # Downloaded property images
│   │   ├── processed/             # Resized, deduplicated images
│   │   └── metadata/              # Extraction state, manifests
│   └── field_lineage.json         # Data provenance tracking
│
├── tests/                         # Test suite (pytest)
│   ├── unit/                      # Unit tests for core logic
│   ├── integration/               # Integration tests
│   ├── benchmarks/                # Performance tests
│   └── fixtures/                  # Test data fixtures
│
├── docs/                          # Technical documentation
│   ├── architecture/              # Architecture decision records
│   ├── artifacts/                 # Implementation summaries
│   └── [40+ documentation files]  # Specs, guides, audits
│
├── reports/                       # Generated outputs
│   ├── html/                      # Interactive HTML reports
│   ├── csv/                       # Ranked property lists
│   └── deal_sheets/               # Per-property summaries
│
├── pyproject.toml                 # Python project configuration
├── uv.lock                        # Dependency lock file (uv package manager)
├── CLAUDE.md                      # Project documentation (priority rules)
└── README.md                      # Quick start guide
```
