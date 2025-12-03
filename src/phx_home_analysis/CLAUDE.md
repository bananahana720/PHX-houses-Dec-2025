# src/phx_home_analysis/CLAUDE.md

---
last_updated: 2025-12-02
updated_by: Claude (Assistant)
staleness_hours: 72
---

## Purpose

Core analysis library for Phoenix home evaluation. Provides domain models, scoring logic, kill-switch filtering, data persistence, and orchestration for the PHX Houses pipeline.

This is the main Python package (`phx_home_analysis`) that implements the complete analysis workflow from data loading through scoring and reporting.

## Subdirectories

| Directory | Purpose |
|-----------|---------|
| `config/` | Application configuration, scoring weights (600pt system), tier thresholds, buyer profile, Arizona context |
| `domain/` | Domain entities (Property, EnrichmentData), value objects (Address, Score), enums (Tier, Orientation, SewerType) |
| `repositories/` | Data persistence layer - CSV (listings), JSON (enrichment), abstract base classes |
| `services/` | Business logic services (kill-switch, scoring, enrichment, data integration, quality, lifecycle) |
| `validation/` | Pydantic schemas, validators, normalizers, deduplication |
| `pipeline/` | Main orchestrator coordinating load → enrich → filter → score → report workflow |
| `reporters/` | Output formatters - console, CSV, HTML report generation |
| `visualizations/` | Chart generation - radar charts, scatter plots, comparison visualizations |
| `utils/` | Shared utilities - file operations, helpers |

## Services Breakdown

| Service | Purpose |
|---------|---------|
| `kill_switch/` | Buyer criteria filtering with hard (HOA, beds, baths) and soft (sewer, garage, lot, year) severity accumulation |
| `scoring/` | 600-point weighted scoring across Location (230pts), Systems (180pts), Interior (190pts) sections |
| `classification/` | Tier assignment (Unicorn >480, Contender 360-480, Pass <360) |
| `enrichment/` | Data merging, field mapping, protocols for combining CSV listings with JSON enrichment |
| `cost_estimation/` | Monthly cost projection (mortgage, taxes, insurance, HOA, pool, solar lease) |
| `quality/` | Data quality metrics, lineage tracking, completeness scoring |
| `lifecycle/` | Data staleness detection, archival, state management |
| `ai_enrichment/` | Field inference, confidence scoring for AI-generated data |
| `data_integration/` | Merge strategies, field mapping, multi-source data reconciliation |
| `image_extraction/` | Extractors for Zillow, Redfin, Realtor.com, Maricopa Assessor (stealth browsers) |
| `analysis/` | Property analyzer orchestration |
| `location_data/` | State management and orchestration for geographic data extraction |
| `schools/` | GreatSchools API integration (school_rating, 45pts max) |
| `crime_data/` | Crime index extraction (safety_score, 50pts max) |
| `walkscore/` | Walk Score, Transit Score, Bike Score (25pts max) |
| `flood_data/` | FEMA flood zone classification (25pts max) |
| `census_data/` | US Census geocoding and demographic data |
| `noise_data/` | Noise pollution assessment |
| `county_data/` | Maricopa County Assessor API models |
| `infrastructure/` | Proxy management for web scraping |
| `schema/` | Schema versioning for data evolution |
| `renovation/` | Renovation cost estimation |
| `risk_assessment/` | Property risk evaluation |

## Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `__init__.py` | Package exports - config, domain, repositories, services, pipeline | 172 |
| `config/scoring_weights.py` | 600-point scoring system definition with detailed docstrings | 366 |
| `config/__init__.py` | Config module exports (AppConfig, BuyerProfile, ScoringWeights, etc.) | 23 |
| `domain/entities.py` | Property and EnrichmentData domain entities | - |
| `domain/value_objects.py` | Address, Score, ScoreBreakdown, RiskAssessment, RenovationEstimate | - |
| `domain/enums.py` | Tier, Orientation, SewerType, SolarStatus, RiskLevel enums | - |
| `repositories/base.py` | Abstract PropertyRepository and EnrichmentRepository interfaces | - |
| `repositories/csv_repository.py` | CsvPropertyRepository for phx_homes.csv | - |
| `repositories/json_repository.py` | JsonEnrichmentRepository for enrichment_data.json | - |
| `services/kill_switch/constants.py` | Kill-switch severity thresholds and weights (HARD/SOFT criteria) | 89 |
| `services/kill_switch/filter.py` | KillSwitchFilter orchestration | - |
| `services/kill_switch/criteria.py` | Individual kill-switch criterion implementations | - |
| `services/scoring/scorer.py` | PropertyScorer orchestrating all scoring strategies | - |
| `services/scoring/base.py` | ScoringStrategy base class | - |
| `services/scoring/strategies/` | Individual scoring strategies (SchoolDistrictScorer, OrientationScorer, etc.) | - |
| `pipeline/orchestrator.py` | AnalysisPipeline and PipelineResult - main workflow coordinator | - |
| `validation/schemas.py` | Pydantic schemas for property and enrichment data validation | - |
| `validation/validators.py` | Validation logic and ValidationResult container | - |
| `validation/normalizer.py` | Address normalization, type inference | - |
| `validation/deduplication.py` | Hash-based duplicate detection | - |
| `reporters/console_reporter.py` | Console output formatting | - |
| `reporters/csv_reporter.py` | CSV export | - |
| `reporters/html_reporter.py` | HTML report generation | - |
| `logging_config.py` | Centralized logging configuration | 6989 bytes |
| `visualizations/` | Visualization generation modules | - |

## Key Design Patterns

### Repository Pattern
- `PropertyRepository` (CSV) and `EnrichmentRepository` (JSON) abstract data access
- Decouples data storage from business logic
- Enables testing with mock repositories

### Strategy Pattern
- Scoring strategies implement `ScoringStrategy` base class
- Each strategy is independent and composable
- Location (7 strategies), Systems (4 strategies), Interior (7 strategies)

### Domain-Driven Design
- Clean separation: Domain → Services → Pipeline → Reporters
- Domain entities are immutable dataclasses
- Value objects encapsulate domain concepts (Address, Score, etc.)

### Orchestration
- `AnalysisPipeline` coordinates entire workflow
- Services are composable and dependency-injected
- `PipelineResult` provides unified result container

## Scoring System Architecture

**600-Point Weighted System** (defined in `config/scoring_weights.py`):

```
Section A: Location & Environment (230 pts)
├── school_district (45 pts) - GreatSchools rating × 4.5
├── quietness (30 pts) - Distance to highways
├── crime_index (50 pts) - 60% violent + 40% property crime
├── supermarket_proximity (25 pts) - Distance to grocery
├── parks_walkability (25 pts) - Parks, sidewalks, trails
├── sun_orientation (25 pts) - N=25, E=18.75, S=12.5, W=0
├── flood_risk (25 pts) - FEMA flood zones
└── walk_transit (25 pts) - Walk/Transit/Bike Score composite

Section B: Lot & Systems (180 pts)
├── roof_condition (45 pts) - Age/condition based on year_built
├── backyard_utility (35 pts) - Usable backyard space
├── plumbing_electrical (35 pts) - Age-based infrastructure score
├── pool_condition (20 pts) - Pool equipment age (if present)
└── cost_efficiency (35 pts) - Monthly cost vs $3k-$5k+ target

Section C: Interior & Features (190 pts)
├── kitchen_layout (40 pts) - Visual inspection from photos
├── master_suite (35 pts) - Bedroom, closet, bathroom quality
├── natural_light (30 pts) - Windows, skylights, brightness
├── high_ceilings (25 pts) - Vaulted/10ft/9ft/8ft
├── fireplace (20 pts) - Gas/wood/decorative/none
├── laundry_area (20 pts) - Dedicated room vs closet vs garage
└── aesthetics (10 pts) - Overall visual appeal
```

**Tier Classification** (defined in `config/scoring_weights.py`):
- **Unicorn**: >480 pts (80%+) - Exceptional, immediate action
- **Contender**: 360-480 pts (60-80%) - Strong, serious consideration
- **Pass**: <360 pts (<60%) - Meets minimums but unremarkable

## Kill-Switch Architecture

**Hard Criteria (Instant Fail)** - defined in `services/kill_switch/constants.py`:
- HOA fee > $0
- Bedrooms < 4
- Bathrooms < 2

**Soft Criteria (Severity Accumulation)** - weights in `services/kill_switch/constants.py`:
- City sewer (not septic): severity 2.5
- Year built < 2024: severity 2.0
- Garage spaces >= 2: severity 1.5
- Lot size 7k-15k sqft: severity 1.0

**Verdict Logic**:
- Any HARD fail → FAIL (instant)
- Total severity >= 3.0 → FAIL (threshold exceeded)
- Total severity 1.5-3.0 → WARNING
- Total severity < 1.5 → PASS

## Data Flow

```
1. Load: CSV listings (phx_homes.csv) → Property entities
2. Enrich: Merge with JSON enrichment (enrichment_data.json) → EnrichmentData
3. Filter: Kill-switch evaluation → PASS/WARNING/FAIL verdict
4. Score: PropertyScorer applies all strategies → Score (0-600)
5. Classify: TierThresholds → Unicorn/Contender/Pass
6. Report: Reporters generate console/CSV/HTML outputs
```

## Integration Points

### Used By
- `scripts/phx_home_analyzer.py` - Main scoring script
- `scripts/extract_county_data.py` - County API extraction
- `scripts/extract_images.py` - Image extraction orchestration
- `scripts/deal_sheets/` - Report generation
- `.claude/agents/` - Multi-agent analysis pipeline

### Uses
- `data/phx_homes.csv` - Source listings (CsvPropertyRepository)
- `data/enrichment_data.json` - Enrichment data (JsonEnrichmentRepository)
- `data/work_items.json` - Pipeline state (via scripts)

## Key Learnings

### Scoring System
- **Total: 600 points** not 500 - Section A is 230pts (not 150) per actual weights
- Tier thresholds calibrated to 600pt scale: Unicorn >480, Contender 360-480, Pass <360
- Cost efficiency (35pts) captures total monthly ownership cost including pool, solar lease, HOA
- Pool condition scoring: No pool = 10pts neutral (no burden), not 0pts penalty

### Kill-Switch System
- **Severity accumulation** - SOFT criteria add up; threshold >= 3.0 fails
- Sewer (2.5) + year (2.0) = 4.5 severity → FAIL
- Garage (1.5) + lot (1.0) = 2.5 severity → WARNING
- HARD criteria (HOA, beds, baths) cause instant failure, severity N/A

### Arizona-Specific Factors
- **HVAC lifespan**: 10-15 years in AZ heat (not 20+ like elsewhere)
- **Pool costs**: $250-400/month total ownership (maintenance, chemicals, equipment, insurance)
- **Solar leases**: Liability not asset - $100-200/mo + transfer issues on sale
- **Orientation critical**: West-facing = 0pts (highest cooling), North = 25pts (best)

### Data Quality
- `enrichment_data.json` is source of truth for enriched fields
- CSV provides base listings; JSON overlay adds Phase 0/1/2 data
- Validation uses Pydantic schemas with strict type checking
- Deduplication via address hashing (normalized addresses)

### Testing
- Repository pattern enables mock data for unit tests
- Strategy pattern allows isolated testing of each scorer
- Domain entities are immutable for predictable testing

## Pending Tasks

- [ ] Add integration tests for complete pipeline workflow
- [ ] Document scoring strategy extension pattern for new criteria
- [ ] Add examples for custom reporter implementations
- [ ] Implement caching layer for repeated property lookups
- [ ] Add benchmark tests for scoring performance on large datasets

## Dependencies

### Internal
- Python 3.11+ (dataclasses, typing)
- Pydantic for validation schemas
- Standard library: json, csv, pathlib, logging

### External (via requirements.txt)
- No direct external dependencies in this package
- Services use external APIs (GreatSchools, WalkScore, FEMA, Census) but calls are in scripts

### Downstream
- `scripts/` - Analysis scripts that import this package
- `.claude/skills/` - Skills that reference config and domain models
- `tests/` - Test suite

## References

- Main config: `config/scoring_weights.py:1-366`
- Kill-switch constants: `services/kill_switch/constants.py:1-89`
- Domain models: `domain/entities.py`, `domain/value_objects.py`, `domain/enums.py`
- Package exports: `__init__.py:1-172`
- Pipeline orchestrator: `pipeline/orchestrator.py`
- Validation schemas: `validation/schemas.py`

---
**Package Version**: 1.0.0
**Python Version**: 3.11+
**Lines**: ~186 (target: <200)
