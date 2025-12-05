# PHX Houses Analysis Pipeline - Project Overview

**Generated:** 2025-12-05
**Workflow:** document-project v1.2.0
**Scan Level:** exhaustive

---

## Executive Summary

PHX Houses Analysis Pipeline is a Python data pipeline that evaluates Phoenix metropolitan real estate properties for first-time home buyers. It implements a sophisticated 605-point scoring system with 8 HARD kill-switch criteria to filter unsuitable properties before detailed analysis.

The system integrates multiple data sources (County Assessor API, Zillow, Redfin, GreatSchools, Google Maps) to provide comprehensive property evaluation with automated deal sheet generation.

---

## Project Identity

| Attribute | Value |
|-----------|-------|
| **Name** | phx-home-analysis |
| **Version** | 1.0.0 |
| **License** | MIT |
| **Python** | >=3.10 (dev: 3.13) |
| **Type** | Data Pipeline / Backend |
| **Architecture** | Domain-Driven Design |

---

## Technology Stack Summary

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| **Language** | Python | 3.10+ | Core runtime |
| **Data Validation** | Pydantic | 2.12.5 | Schema validation |
| **Data Processing** | pandas | 2.3.3 | CSV/DataFrame ops |
| **HTTP Client** | httpx | 0.28.1 | Async HTTP requests |
| **Browser Automation** | nodriver | 0.48.1 | Stealth scraping (Zillow) |
| **Browser Fallback** | Playwright | 1.56.0 | Browser fallback |
| **Templating** | Jinja2 | 3.1.6 | HTML report generation |
| **Visualization** | Plotly/Folium | 6.5.0/0.20.0 | Charts and maps |
| **Testing** | pytest | 9.0.1 | Test framework |
| **Linting** | ruff | 0.14.7 | Fast Python linter |
| **Type Checking** | mypy | 1.19.0 | Static type analysis |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHX Houses Pipeline                          │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 0: County Data    │  PHASE 1: Listing + Maps             │
│  ├─ Assessor API         │  ├─ Zillow/Redfin Extraction         │
│  └─ Lot, Year, Garage    │  ├─ GreatSchools Ratings             │
│                          │  └─ Google Maps Distance             │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 2: Image Analysis │  PHASE 3: Synthesis                  │
│  ├─ Exterior Assessment  │  ├─ Score Calculation (605 pts)      │
│  └─ Interior Scoring     │  └─ Tier Classification              │
├─────────────────────────────────────────────────────────────────┤
│  PHASE 4: Report Generation                                      │
│  ├─ Deal Sheets (per property)                                   │
│  ├─ Radar Charts (comparison)                                    │
│  └─ Interactive Maps (golden zone)                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Kill-Switch System (8 HARD Criteria)

All criteria are **instant fail** - any violation disqualifies the property:

| Criterion | Requirement | Rationale |
|-----------|-------------|-----------|
| HOA | = $0 | No HOA properties only |
| Beds | >= 4 | Family size requirement |
| Baths | >= 2 | Minimum comfort |
| SqFt | > 1800 | Space requirement |
| Lot | > 8,000 sqft | Yard size |
| Garage | >= 1 space | Arizona essential |
| Sewer | City | No septic systems |
| Year | <= 2024 | Existing construction |

---

## Scoring System (605 Points)

| Section | Points | Weight | Components |
|---------|--------|--------|------------|
| **A: Location** | 250 | 41% | Schools, safety, orientation, proximity |
| **B: Systems** | 175 | 29% | HVAC, roof, pool, cost efficiency |
| **C: Interior** | 180 | 30% | Kitchen, master, layout, finishes |
| **Total** | **605** | 100% | |

### Tier Classification

| Tier | Score Range | Percentage |
|------|-------------|------------|
| UNICORN | >480 | 80%+ |
| CONTENDER | 360-480 | 60-80% |
| PASS | <360 | <60% |

---

## Key Directories

| Directory | Purpose |
|-----------|---------|
| `src/phx_home_analysis/` | Core analysis library |
| `scripts/` | CLI tools (42 scripts) |
| `tests/` | Unit, integration, live tests |
| `data/` | Property data, images, enrichment |
| `docs/` | Technical documentation |
| `reports/` | Generated HTML/CSV reports |

---

## Quick Commands

```bash
# Run full analysis pipeline
python scripts/phx_home_analyzer.py

# Extract images from listings
python scripts/extract_images.py --all

# Generate deal sheets
python -m scripts.deal_sheets

# Run tests
pytest tests/unit/ -v

# Lint and format
ruff check --fix && ruff format
```

---

## Links to Detailed Documentation

- [Architecture](./architecture.md) - System architecture and patterns
- [Source Tree Analysis](./source-tree-analysis.md) - Directory structure
- [Development Guide](./development-guide.md) - Setup and contribution
- [Data Models](./data-models.md) - Domain entities and schemas
- [API Contracts](./api-contracts.md) - Service interfaces

---

## Project Status

| Metric | Value |
|--------|-------|
| Epics Complete | 2/7 |
| Stories Done | 19/42 (45%) |
| Test Coverage | ~90% |
| Last Updated | 2025-12-05 |
