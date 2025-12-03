# PHX Houses Analysis Pipeline - Documentation Index

**Project:** PHX Houses Dec 2025
**Version:** 1.0.0
**Generated:** 2025-12-03
**Documentation Generator:** Claude Code (Sonnet 4.5) - Exhaustive Scan Level 3

---

## Quick Navigation

| For... | Start Here |
|--------|------------|
| **New Developers** | [Project Overview](#project-overview) → [Development Guide](#development-guide) |
| **System Understanding** | [Architecture](#architecture) → [Data Models](#data-models) |
| **API Integration** | [API Contracts](#api-contracts) → [Integration Points](#integration-points) |
| **Adding Features** | [Development Guide](#development-guide) → [Component Inventory](#component-inventory) |
| **Troubleshooting** | [Development Guide](#development-guide) → [Known Issues](#known-issues) |

---

## Core Documentation

### Project Overview
**File:** `docs/project-overview.md`
**Purpose:** Executive summary, what the system does, key technologies, data flow
**Audience:** Everyone
**Key Sections:**
- Executive Summary
- Core Functionality (Kill-Switch, Scoring, Multi-Agent)
- Project Structure
- Arizona-Specific Domain Knowledge
- Data Flow Architecture
- Integration Pain Points
- Success Metrics

[Read Project Overview →](./project-overview.md)

---

### Architecture
**File:** `docs/architecture.md`
**Purpose:** System design, architectural patterns, layer breakdown
**Audience:** Developers, Architects
**Key Sections:**
- System Overview
- Architectural Style (DDD)
- Layer Architecture (Domain, Service, Repository, Pipeline)
- Multi-Agent Orchestration
- Data Architecture
- Scoring System Architecture
- Kill-Switch Architecture
- Image Extraction Architecture
- State Management
- Integration Points
- Security Architecture

[Read Architecture →](./architecture.md)

---

### Development Guide
**File:** `docs/development-guide.md`
**Purpose:** How to develop, test, and extend the system
**Audience:** Developers
**Key Sections:**
- Quick Start (installation, running)
- Development Workflow
- Adding Features (scoring criteria, data sources)
- Testing Strategy
- Code Style Guidelines
- Git Workflow
- Multi-Agent Development
- Common Tasks
- Performance Optimization
- Troubleshooting

[Read Development Guide →](./development-guide.md)

---

## Supplementary Documentation

### Data Models
**File:** `docs/data-models.md` (to be generated)
**Purpose:** Detailed documentation of all data structures
**Key Topics:**
- Property entity schema
- EnrichmentData structure
- Value objects (Address, Score, etc.)
- Enums (Tier, Orientation, etc.)
- JSON file formats (enrichment_data.json, work_items.json)
- CSV formats (phx_homes.csv)

**Current Status:** See inline documentation in:
- `src/phx_home_analysis/domain/entities.py`
- `src/phx_home_analysis/domain/value_objects.py`
- `src/phx_home_analysis/domain/enums.py`
- `.claude/AGENT_BRIEFING.md` (data structure reference)

---

### API Contracts
**File:** `docs/api-contracts.md` (to be generated)
**Purpose:** External API integration specifications
**Key Topics:**
- Maricopa County Assessor API
- GreatSchools API
- Google Maps API
- FEMA Flood API
- WalkScore API
- Zillow/Redfin web scraping

**Current Status:** See inline documentation in:
- `src/phx_home_analysis/services/county_data/`
- `src/phx_home_analysis/services/schools/`
- `src/phx_home_analysis/services/image_extraction/extractors/`

---

### Component Inventory
**File:** `docs/component-inventory.md` (to be generated)
**Purpose:** Complete catalog of all modules, classes, functions
**Key Topics:**
- Service modules (kill_switch, scoring, cost_estimation, etc.)
- Scoring strategies (18 strategies documented)
- Extractors (Zillow, Redfin, MLS, Assessor)
- Reporters (Console, CSV, HTML, Deal Sheets)
- Utilities and helpers

**Current Status:** See:
- `src/phx_home_analysis/__init__.py` (package exports)
- `src/phx_home_analysis/CLAUDE.md` (module overview)

---

## Existing Project Documentation

### Root Level
- `CLAUDE.md` - **PRIMARY REFERENCE** - Tool usage rules, principles, quick commands
- `README.md` - Quick start guide
- `.claude/AGENT_BRIEFING.md` - Agent orientation, data structures, error recovery
- `.claude/protocols.md` - Operational protocols (TIER 0-3)

### Architecture Subdirectory
- `docs/architecture/phase-orchestration.md` - Multi-phase pipeline flow
- `docs/architecture/state-management.md` - State file management patterns

### Specifications
- `docs/AI_TECHNICAL_SPEC.md` - Original technical specification
- `docs/MC-Assessor-API-Documentation.md` - County Assessor API docs
- `docs/RENOVATION_GAP_README.md` - Renovation analysis documentation

### Implementation Artifacts
- `docs/artifacts/` - 100+ implementation summaries, deliverables, test reports
- `docs/artifacts/zillow-bug-fix/` - Zillow extraction bug fix documentation
- `docs/artifacts/deal_sheets/` - Deal sheet generation examples

### Security & Audits
- `docs/SECURITY.md` - Security guidelines
- `docs/SECURITY_AUDIT_REPORT_NEW.md` - Latest security audit
- `docs/DATA_ENGINEERING_AUDIT.md` - Data engineering audit

### Testing
- `docs/RECOMMENDED_TESTS.md` - Test coverage recommendations
- `docs/TEST_COVERAGE_ANALYSIS.md` - Current test coverage analysis
- `docs/artifacts/TESTING_SUMMARY.md` - Testing deliverables index

### Configuration & Standards
- `docs/CONFIG_EXTERNALIZATION_INDEX.md` - Configuration management
- `docs/CONSTANTS_MIGRATION.md` - Constants consolidation
- `docs/DEPRECATION_GUIDE.md` - Deprecated code inventory
- `docs/CODE_REFERENCE.md` - Code organization reference

### Visualizations & Reports
- `docs/VISUALIZATIONS_GUIDE.md` - Chart and map generation guide

---

## Knowledge Graphs (Claude Code)

### Toolkit Knowledge Graph
**File:** `.claude/knowledge/toolkit.json`
**Purpose:** Machine-readable tool schemas, relationships, phase dependencies
**Key Sections:**
- `tool_tiers` - Tool priority hierarchy (native > scripts > agents > MCP)
- `native_tools` - Claude native tools (Read, Write, Edit, Grep, Glob, Bash, etc.)
- `project_scripts` - Analysis scripts (phx_home_analyzer.py, extract_*.py, etc.)
- `agents` - Agent definitions (listing-browser, map-analyzer, image-assessor)
- `skills` - Skill modules (property-data, scoring, kill-switch, etc.)
- `slash_commands` - Custom commands (/analyze-property, /commit)
- `mcp_tools` - MCP tool integrations (Playwright, fetch)
- `relationships` - Tool relationships (replaces, spawns, loads, etc.)
- `phase_dependencies` - Pipeline phase flow and spawn order
- `common_mistakes` - Frequent errors and fixes

[View Toolkit →](../.claude/knowledge/toolkit.json)

### Context Management Knowledge Graph
**File:** `.claude/knowledge/context-management.json`
**Purpose:** State management, staleness, handoff protocols
**Key Sections:**
- `discovery_protocol` - Auto-discover CLAUDE.md files in directories
- `staleness_protocol` - Check file freshness before use
- `update_triggers` - When to update context files
- `state_files` - Critical state files (work_items.json, enrichment_data.json)
- `agent_handoff` - Agent spawn and completion protocols
- `spawn_validation_protocol` - Pre-spawn validation (MANDATORY for Phase 2)
- `failure_response_protocols` - Structured error handling
- `directory_contexts` - Context for each major directory

[View Context Management →](../.claude/knowledge/context-management.json)

---

## Claude Code Multi-Agent System

### Agent Definitions
**Location:** `.claude/agents/`

1. **listing-browser.md** (Claude Haiku)
   - Extracts listing data from Zillow/Redfin
   - Uses stealth browsers (nodriver)
   - Outputs: price, beds, baths, HOA, images
   - Duration: ~30-60s per property

2. **map-analyzer.md** (Claude Haiku)
   - Geographic analysis (schools, crime, orientation)
   - Uses Google Maps, GreatSchools, crime APIs
   - Outputs: school_rating, safety_score, orientation, distances
   - Duration: ~45-90s per property

3. **image-assessor.md** (Claude Sonnet 4.5)
   - Visual scoring of interior quality (Section C: 190 pts)
   - Uses Claude Vision for image analysis
   - Outputs: kitchen, master, light, ceilings, fireplace, laundry, aesthetics scores
   - Duration: ~2-5 min per property
   - Prerequisites: Phase 1 complete, images downloaded

### Skill Modules
**Location:** `.claude/skills/`

- `property-data/` - Load, query, update property data
- `state-management/` - Checkpointing & crash recovery
- `kill-switch/` - Buyer criteria validation
- `scoring/` - 600-point scoring system
- `county-assessor/` - Maricopa County API
- `arizona-context/` - AZ-specific factors
- `arizona-context-lite/` - Lightweight AZ context for image assessment
- `listing-extraction/` - Browser automation
- `map-analysis/` - Schools, safety, distances
- `image-assessment/` - Visual scoring rubrics
- `exterior-assessment/` - Exterior visual scoring
- `deal-sheets/` - Report generation
- `visualizations/` - Charts & plots
- `quality-metrics/` - Data quality tracking
- `file-organization/` - File placement standards

### Slash Commands
**Location:** `.claude/commands/`

- `/analyze-property` - Multi-agent orchestrated analysis
- `/commit` - Git commit helper

---

## Source Code Documentation

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

## Configuration Files

### Project Configuration
- `pyproject.toml` - Python project metadata, dependencies, tool configs
- `uv.lock` - Dependency lock file (uv package manager)
- `.python-version` - Python version pinning (3.11+)

### Environment Variables
- `.env` - API keys, proxy settings (gitignored)
- `.env.example` - Template for environment variables

### Git Configuration
- `.gitignore` - Ignored files and directories
- `.pre-commit-config.yaml` - Pre-commit hook configuration

### Tool Configuration (in pyproject.toml)
- `[tool.pytest.ini_options]` - Pytest settings
- `[tool.ruff]` - Ruff linter/formatter settings
- `[tool.mypy]` - Mypy type checker settings

---

## Data Files

### Primary Data Files
- `data/phx_homes.csv` - Source listing data
- `data/enrichment_data.json` - **LIST** of property dicts (not dict!)
- `data/work_items.json` - Pipeline state tracking
- `data/field_lineage.json` - Data provenance

### Image Data
- `data/property_images/processed/` - Resized, deduplicated images
- `data/property_images/metadata/extraction_state.json` - Extraction state
- `data/property_images/metadata/image_manifest.json` - Image inventory
- `data/property_images/metadata/address_folder_lookup.json` - Address → folder mapping
- `data/property_images/metadata/hash_index.json` - Perceptual hash index

---

## Generated Outputs

### Reports
- `reports/html/dashboard.html` - Main HTML report
- `reports/csv/phx_homes_ranked.csv` - Ranked property list
- `reports/deal_sheets/` - Per-property summary sheets

### Visualizations
- `reports/html/golden_zone_map.html` - Interactive property map
- `reports/html/radar_comparison.html` - Property comparison charts
- `reports/html/value_spotter.html` - Value analysis visualization

---

## Integration Points

### External APIs
| API | Purpose | Authentication | Rate Limit |
|-----|---------|----------------|------------|
| Maricopa County Assessor | Lot size, year built, garage, pool | Bearer token | ~1 req/sec |
| GreatSchools | School ratings (1-10) | API key | 1000 req/day |
| Google Maps | Geocoding, distances, orientation | API key | Pay-as-you-go |
| FEMA Flood | Flood zone classification | None (public) | Unknown |
| WalkScore | Walk/Transit/Bike Scores | API key | 5000 req/day |

### Web Scraping
| Site | Method | Detection | Data |
|------|--------|-----------|------|
| Zillow | nodriver (stealth) | PerimeterX | Images, price, details |
| Redfin | nodriver (stealth) | Cloudflare | Images, listing data |
| Realtor.com | Playwright | Minimal | Listing details |

---

## Known Issues & Limitations

### Data Structure Confusion
**Issue:** `enrichment_data.json` is a LIST, but commonly treated as dict.
**Impact:** `TypeError`, `AttributeError`.
**Solution:** Always iterate to find properties by address.

[See Troubleshooting in Development Guide →](./development-guide.md#troubleshooting)

### Browser Detection
**Issue:** PerimeterX detects Playwright on Zillow/Redfin.
**Impact:** 403 Forbidden, CAPTCHA challenges.
**Solution:** Use nodriver (stealth) instead of Playwright.

### Phase Dependency Validation
**Issue:** Phase 2 requires Phase 1 complete, but no automatic validation.
**Impact:** Agent failures, wasted API calls.
**Solution:** MANDATORY pre-spawn validation via `validate_phase_prerequisites.py`.

### Single-Threaded Scoring
**Issue:** Scoring is single-threaded.
**Impact:** Slow for large datasets (100+ properties).
**Solution:** Consider parallelizing scoring strategies.

### Arizona-Specific
**Issue:** System is tailored to Phoenix metro.
**Impact:** Not portable to other markets without recalibration.
**Solution:** Extract constants, create regional profiles.

---

## Future Enhancements

### Near-Term
- [ ] Add caching layer for property lookups
- [ ] Implement file locking for concurrent writes
- [ ] Add comprehensive integration tests
- [ ] Create performance benchmarks
- [ ] Add retry logic with exponential backoff

### Mid-Term
- [ ] Migrate to PostgreSQL
- [ ] Add REST API (FastAPI)
- [ ] Implement real-time listing monitoring
- [ ] Add email/SMS alerts
- [ ] Create web UI

### Long-Term
- [ ] Expand to other markets
- [ ] Add ML for value prediction
- [ ] Implement automated offer generation
- [ ] Add mortgage pre-qualification integration
- [ ] Create mobile app

---

## Document Generation History

### Initial Documentation Scan
**Date:** 2025-12-03
**Scan Level:** Exhaustive (Level 3)
**Generator:** Claude Code (Sonnet 4.5)
**Files Analyzed:** ~100+ Python files, ~40+ documentation files
**Total LOC Analyzed:** ~20,000+ (source + tests)

**Generated Documents:**
1. `project-overview.md` - Executive summary and system overview
2. `architecture.md` - System architecture and design patterns
3. `development-guide.md` - Developer onboarding and workflows
4. `index.md` (this file) - Master documentation index

**Remaining Work:**
- `data-models.md` - Detailed data structure documentation
- `api-contracts.md` - External API specifications
- `component-inventory.md` - Complete module/class catalog

---

## Contributing

### Documentation Updates

When adding features or making changes:

1. **Update inline documentation** (docstrings in source code)
2. **Update relevant CLAUDE.md files** (directory-level context)
3. **Update generated docs if major changes** (architecture.md, etc.)
4. **Update knowledge graphs if tool/agent changes** (toolkit.json, context-management.json)

### Documentation Standards

- **Format:** Markdown
- **Style:** Technical but accessible
- **Structure:** Progressive complexity (overview → details)
- **Code Examples:** Actual working code, not pseudocode
- **References:** Link to source files with line numbers

---

## Quick Reference

### Key Commands
```bash
# Run main analysis
python scripts/phx_home_analyzer.py

# Extract county data
python scripts/extract_county_data.py --all

# Extract images
python scripts/extract_images.py --all

# Validate prerequisites
python scripts/validate_phase_prerequisites.py --address "..." --phase phase2_images --json

# Generate deal sheets
python -m scripts.deal_sheets

# Multi-agent analysis
/analyze-property --all
```

### Key Files
```
CLAUDE.md                          # Primary reference
.claude/AGENT_BRIEFING.md          # Agent orientation
.claude/protocols.md               # Operational protocols
src/phx_home_analysis/config/constants.py  # All magic numbers
data/enrichment_data.json          # Property data (LIST!)
data/work_items.json               # Pipeline state
```

### Key Concepts
- **Kill-Switch:** Hard criteria (instant fail) + Soft criteria (severity accumulation)
- **Scoring:** 600 points across Location (250), Systems (170), Interior (180)
- **Tiers:** Unicorn (>480), Contender (360-480), Pass (<360)
- **Multi-Agent:** listing-browser + map-analyzer (parallel) → image-assessor (sequential)
- **Data Structure:** enrichment_data.json is a LIST, not dict!

---

## Contact & Support

**Project Owner:** Andrew
**Project Type:** Personal (First-time home buying)
**Claude Code Version:** Latest (December 2025)
**Python Version:** 3.11+

---

**Document Version:** 1.0
**Generated:** 2025-12-03
**Last Updated:** 2025-12-03
**Maintainer:** Andrew + Claude Code
