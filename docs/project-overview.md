# PHX Houses Analysis Pipeline - Project Overview

## Executive Summary

The PHX Houses Analysis Pipeline is a comprehensive, multi-phase data analysis system designed for first-time home buyers evaluating residential properties in the Phoenix metropolitan area. The system implements sophisticated kill-switch filtering, 600-point weighted scoring, and multi-agent AI orchestration to identify properties that match strict buyer criteria.

**Project Type:** Data Analysis Pipeline / Backend System
**Primary Language:** Python 3.11+
**Architecture:** Domain-Driven Design with Multi-Agent Orchestration
**Lines of Code:** ~15,000+ LOC (source), ~5,000+ LOC (tests)
**Development Status:** Production (v1.0.0)

## What This System Does

### Core Functionality

1. **Multi-Source Data Integration**
   - Imports listing data from CSV (Zillow/Redfin exports)
   - Enriches with Maricopa County Assessor API data
   - Extracts images from listing sites using stealth automation
   - Integrates geographic data (schools, crime, flood zones, walkability)
   - Performs visual analysis of property images for interior quality assessment

2. **Kill-Switch Filtering** (Pass/Fail/Warning)
   - **Hard Criteria (Instant Fail):**
     - HOA fee > $0
     - Bedrooms < 4
     - Bathrooms < 2
   - **Soft Criteria (Severity Accumulation, threshold ≥3.0 fails):**
     - Septic system (not city sewer): +2.5 severity
     - Year built ≥2024: +2.0 severity
     - Garage < 2 spaces: +1.5 severity
     - Lot size outside 7k-15k sqft: +1.0 severity

3. **600-Point Weighted Scoring**
   - **Section A: Location & Environment (250 pts)**
     - School district (42pts), Quietness (30pts), Crime index (47pts)
     - Supermarket proximity (23pts), Parks/walkability (23pts)
     - Sun orientation (25pts), Flood risk (23pts), Walk/transit (22pts), Air quality (15pts)
   - **Section B: Lot & Systems (170 pts)**
     - Roof condition (45pts), Backyard utility (35pts)
     - Plumbing/electrical (35pts), Pool condition (20pts), Cost efficiency (35pts)
   - **Section C: Interior & Features (180 pts)**
     - Kitchen layout (40pts), Master suite (35pts), Natural light (30pts)
     - High ceilings (25pts), Fireplace (20pts), Laundry (20pts), Aesthetics (10pts)

4. **Tier Classification**
   - **Unicorn:** >480 points (80%+) - Exceptional properties
   - **Contender:** 360-480 points (60-80%) - Strong candidates
   - **Pass:** <360 points (<60%) - Meets minimums only

5. **Multi-Agent AI Pipeline**
   - Phase 0: County Assessor API data extraction
   - Phase 1: listing-browser (Haiku) + map-analyzer (Haiku) run in parallel
   - Phase 2: image-assessor (Sonnet) for visual scoring (requires Phase 1 complete)
   - Phase 3: Synthesis - scoring, tier assignment, kill-switch verdict
   - Phase 4: Report generation - deal sheets, visualizations, rankings

## Project Structure

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

## Key Technologies

### Core Stack
- **Python 3.11+** - Primary language
- **Pydantic 2.x** - Data validation and schemas
- **Pandas** - Data manipulation
- **Jinja2** - HTML templating for reports
- **Plotly & Folium** - Interactive visualizations

### Stealth Automation (Anti-Detection)
- **nodriver 0.48+** - Stealth Chrome automation (PerimeterX bypass)
- **curl-cffi** - HTTP client with browser TLS fingerprinting
- **Playwright** - Fallback browser automation (MCP integration)

### AI/LLM Integration
- **Claude Code** - Multi-agent orchestration framework
- **Claude Haiku** - Fast agents (listing-browser, map-analyzer)
- **Claude Sonnet 4.5** - Visual analysis (image-assessor)

### Development Tools
- **pytest** - Testing framework
- **ruff** - Linting and formatting
- **mypy** - Static type checking
- **pre-commit** - Git hooks for code quality

## Arizona-Specific Domain Knowledge

The system incorporates deep Arizona real estate expertise:

### HVAC Lifespan (10-15 years, not 20+)
Arizona's extreme heat significantly reduces HVAC lifespan compared to national averages. Replacement cost: ~$8,000.

### Pool Economics ($250-400/month)
- Service: $125/month
- Energy (pump, heater): $75/month
- Equipment replacement: ~$5,500 every 8 years
- Scoring: No pool = 10pts neutral (no burden), not 0pts penalty

### Solar Lease Liability
Solar leases are liabilities, not assets:
- Monthly cost: $100-200
- Transfer complications on sale
- Buyer assumption required
- Impact: Captured in cost_efficiency scoring (35pts)

### Sun Orientation Critical
- **North-facing:** 25pts (best) - Minimal sun exposure, lowest cooling costs
- **East-facing:** 18.75pts - Morning sun only
- **South-facing:** 12.5pts - Moderate sun exposure
- **West-facing:** 0pts (worst) - Afternoon sun, highest AC costs

## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       DATA FLOW PIPELINE                        │
└─────────────────────────────────────────────────────────────────┘

Phase 0: County Data (Optional, runs independently)
┌────────────────────────┐
│ Maricopa Assessor API  │ ─→ lot_sqft, year_built, garage, pool
└────────────────────────┘
         ↓
   enrichment_data.json

Phase 1: Listing + Map (Parallel execution)
┌────────────────────────┐   ┌────────────────────────┐
│ listing-browser (Haiku)│   │ map-analyzer (Haiku)   │
│  - Zillow/Redfin       │   │  - Google Maps         │
│  - stealth automation  │   │  - GreatSchools        │
│  - images, price, HOA  │   │  - crime, walkability  │
└────────────────────────┘   └────────────────────────┘
         ↓                              ↓
   property_images/            enrichment_data.json
         │                              │
         └──────────┬───────────────────┘
                    ↓
              [Prerequisites Met]

Phase 2: Image Assessment (REQUIRES Phase 1 complete)
┌────────────────────────┐
│ image-assessor (Sonnet)│ ─→ kitchen, master, light, ceilings,
│  - Visual analysis     │    fireplace, laundry, aesthetics scores
│  - Claude Vision       │
│  - Era calibration     │
└────────────────────────┘
         ↓
   enrichment_data.json (Section C scores)

Phase 3: Synthesis
┌────────────────────────┐
│ PropertyScorer         │
│ KillSwitchFilter       │ ─→ total_score, tier, verdict
│ TierClassifier         │
└────────────────────────┘
         ↓
   enrichment_data.json (complete analysis)

Phase 4: Report Generation
┌────────────────────────┐
│ Deal Sheets            │
│ Visualizations         │ ─→ HTML reports, CSV rankings,
│ Rankings               │    radar charts, maps
└────────────────────────┘
         ↓
   reports/ directory
```

## Data Structures (CRITICAL)

### enrichment_data.json - LIST, not dict!
```python
# CORRECT - It's a list of property dicts
data = json.load(open('data/enrichment_data.json'))  # List[Dict]
prop = next((p for p in data if p["full_address"] == address), None)

# WRONG - Common mistake
prop = data[address]  # TypeError: list indices must be integers
prop = data.get(address)  # AttributeError: 'list' object has no attribute 'get'
```

### work_items.json - Dict with metadata + work_items list
```python
data = json.load(open('data/work_items.json'))
session = data["session"]  # Session metadata
items = data["work_items"]  # List of work item dicts
prop = next((w for w in items if w["address"] == address), None)
```

### address_folder_lookup.json - Dict with "mappings" key
```python
lookup = json.load(open('data/property_images/metadata/address_folder_lookup.json'))
mapping = lookup.get("mappings", {}).get(address)
if mapping:
    folder = mapping["folder"]  # e.g., "686067a4"
    path = mapping["path"]
    image_count = mapping["image_count"]
```

## Integration Pain Points (User Reported)

The user has mentioned "integration issues" - the system has several known integration challenges:

### 1. Data Structure Confusion
**Problem:** `enrichment_data.json` is a LIST, but developers often treat it as a dict keyed by address.
**Impact:** `TypeError` and `AttributeError` when trying dict operations.
**Solution:** Always iterate to find properties by address.

### 2. Phase Dependency Validation
**Problem:** Phase 2 (image-assessor) requires Phase 1 complete, but no automatic validation.
**Impact:** Spawning agents prematurely causes failures.
**Solution:** MANDATORY pre-spawn validation via `validate_phase_prerequisites.py`.

### 3. State File Staleness
**Problem:** Multiple agents writing to shared state files can cause race conditions.
**Impact:** Lost updates, stale in_progress status.
**Solution:** Read-modify-write with atomic operations, staleness checks.

### 4. Browser Detection
**Problem:** PerimeterX detects Playwright on Zillow/Redfin.
**Impact:** 403 Forbidden, CAPTCHA challenges.
**Solution:** Use stealth browsers (nodriver + curl_cffi) instead of Playwright.

### 5. Missing Prerequisites Errors
**Problem:** Phase 2 agents fail if images not downloaded.
**Impact:** Agent failures, wasted Claude API calls.
**Solution:** Check image manifest before spawning agents.

## Configuration Management

### Centralized Constants
All magic numbers live in `src/phx_home_analysis/config/constants.py`:
- Scoring thresholds and tier boundaries
- Kill-switch severity weights
- Confidence/quality thresholds
- Cost estimation rates (Arizona-specific)
- Arizona constants (HVAC lifespan, pool costs, etc.)
- Image processing settings
- Stealth extraction parameters

### Environment Variables
```bash
# Required for Phase 0
MARICOPA_ASSESSOR_TOKEN=<token>

# Optional for proxy support
PROXY_SERVER=host:port
PROXY_USERNAME=username
PROXY_PASSWORD=password

# Browser automation
BROWSER_HEADLESS=true  # or false
BROWSER_ISOLATION=virtual_display  # or secondary_display, off_screen, minimize, none
```

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Domain entities and value objects
- Scoring strategies (each strategy tested independently)
- Kill-switch criteria (hard and soft)
- Data repositories (with mock data)
- Validators and normalizers

### Integration Tests (`tests/integration/`)
- Complete pipeline workflow
- Multi-source data merging
- Kill-switch chain evaluation
- Deal sheet generation
- Proxy extension builder

### Benchmarks (`tests/benchmarks/`)
- LSH performance for deduplication
- Image hash performance
- Cache performance

### Test Coverage
- Target: 80%+ coverage
- Current: ~75% (estimated)
- Gaps: External API integrations (mocked), browser automation

## Key Design Patterns

### 1. Repository Pattern
Abstracts data access from business logic:
```python
PropertyRepository (abstract)
├── CsvPropertyRepository (CSV)
└── [Future: DatabaseRepository]

EnrichmentRepository (abstract)
├── JsonEnrichmentRepository (JSON)
└── [Future: DatabaseRepository]
```

### 2. Strategy Pattern
Each scoring component is an independent strategy:
```python
ScoringStrategy (base class)
├── SchoolDistrictScorer (42pts)
├── QuietnessScorer (30pts)
├── CrimeIndexScorer (47pts)
└── [18 other strategies]
```

### 3. Domain-Driven Design
Clean separation of concerns:
```
Domain Layer (entities, value objects, enums)
    ↓
Service Layer (kill-switch, scoring, enrichment)
    ↓
Pipeline Layer (orchestration)
    ↓
Presentation Layer (reporters)
```

### 4. Multi-Agent Orchestration
Claude Code agents for parallel data extraction:
- **listing-browser (Haiku):** Fast, cost-effective for scraping
- **map-analyzer (Haiku):** Parallel with listing-browser
- **image-assessor (Sonnet):** Visual analysis requires stronger model

## Known Limitations

### 1. Single-Threaded Scoring
Scoring is currently single-threaded. For large datasets (100+ properties), consider parallelizing.

### 2. No Database
All data stored in JSON/CSV files. For production scale, migrate to PostgreSQL or similar.

### 3. Manual Interior Scoring
Section C (Interior) scores require manual photo review or Sonnet vision analysis. Not fully automated.

### 4. Arizona-Specific
Scoring weights, cost estimates, and domain knowledge are tailored to Phoenix metro. Not portable to other markets without recalibration.

### 5. Image Extraction Fragility
Stealth automation is fragile - site structure changes break extractors. Requires maintenance.

### 6. No Real-Time Updates
Data is static snapshots. No real-time listing updates or price change alerts.

## Future Enhancements

### Near-Term
- [ ] Add caching layer for repeated property lookups
- [ ] Implement file locking for concurrent state writes
- [ ] Add more comprehensive integration tests
- [ ] Create performance benchmarks for scoring at scale
- [ ] Add retry logic with exponential backoff for API calls

### Mid-Term
- [ ] Migrate to PostgreSQL for data persistence
- [ ] Add REST API for remote access
- [ ] Implement real-time listing monitoring
- [ ] Add email/SMS alerts for new properties matching criteria
- [ ] Create web UI for property browsing

### Long-Term
- [ ] Expand to other markets (adapt scoring for different climates/regions)
- [ ] Add ML models for property value prediction
- [ ] Implement automated offer generation
- [ ] Add mortgage pre-qualification integration
- [ ] Create mobile app

## Success Metrics

### System Performance
- **Scoring throughput:** ~10-15 properties/minute (single-threaded)
- **Kill-switch accuracy:** 100% (deterministic rules)
- **Image extraction success rate:** ~85% (depends on site availability)
- **Data quality score:** 95%+ (per quality gates)

### Business Impact
- **Time savings:** ~2 hours → 15 minutes per property evaluation
- **Objectivity:** Eliminates emotional decision-making with quantified scores
- **Coverage:** Evaluates 100+ properties vs 5-10 manual reviews
- **Consistency:** Standardized scoring across all properties

## Getting Started

### Installation
```bash
# Clone repository
cd PHX-houses-Dec-2025

# Install dependencies (using uv)
uv sync

# Set environment variables
export MARICOPA_ASSESSOR_TOKEN=<token>
```

### Basic Usage
```bash
# Run main analysis pipeline
python scripts/phx_home_analyzer.py

# Extract county data for all properties
python scripts/extract_county_data.py --all

# Extract images from listing sites
python scripts/extract_images.py --all

# Generate deal sheets
python -m scripts.deal_sheets

# Multi-agent analysis (orchestrated)
/analyze-property --all
```

### Adding New Properties
1. Add listing to `data/phx_homes.csv`
2. Run county data extraction: `python scripts/extract_county_data.py --address "123 Main St"`
3. Run image extraction: `python scripts/extract_images.py --address "123 Main St"`
4. Run multi-agent analysis: `/analyze-property "123 Main St"`

## Documentation Index

- **CLAUDE.md** - Project instructions, tool usage rules, priority hierarchy
- **.claude/AGENT_BRIEFING.md** - Agent orientation, data structures, error recovery
- **.claude/protocols.md** - Operational protocols (TIER 0-3), verification checklists
- **.claude/knowledge/toolkit.json** - Tool schemas, relationships, phase dependencies
- **.claude/knowledge/context-management.json** - State tracking, staleness, handoff protocols
- **docs/AI_TECHNICAL_SPEC.md** - Original technical specification
- **docs/architecture/** - Architecture decision records
- **src/phx_home_analysis/CLAUDE.md** - Core library documentation

## Contact & Contribution

This is a personal project for first-time home buying in Phoenix metro.

**User:** Andrew
**Project Maintainer:** Andrew
**Claude Code Version:** Latest (December 2025)
**Python Version:** 3.11+

---

**Document Version:** 1.0
**Generated:** 2025-12-03
**Generator:** Claude Code (Sonnet 4.5) - Exhaustive Scan Level 3
**Total LOC Analyzed:** ~20,000+ (source + tests)
