# PHX Houses Analysis Pipeline - Documentation Index

**Generated:** 2025-12-05
**Workflow:** document-project v1.2.0
**Scan Level:** exhaustive

---

## Project Overview

| Property | Value |
|----------|-------|
| **Type** | Backend Data Pipeline (Monolith) |
| **Language** | Python 3.10+ |
| **Architecture** | Domain-Driven Design |
| **Primary Framework** | Custom Pipeline + Pydantic |
| **Repository** | Single cohesive codebase |

---

## Quick Reference

### Tech Stack

| Category | Technology | Version |
|----------|------------|---------|
| Runtime | Python | 3.10+ |
| Validation | Pydantic | 2.12.5 |
| Data | pandas | 2.3.3 |
| HTTP | httpx | 0.28.1 |
| Browser | nodriver | 0.48.1 |
| Testing | pytest | 9.0.1 |
| Linting | ruff | 0.14.7 |

### Entry Points

| Script | Purpose |
|--------|---------|
| `scripts/phx_home_analyzer.py` | Main analysis pipeline |
| `scripts/pipeline_cli.py` | Typer CLI orchestrator |
| `scripts/extract_images.py` | Image extraction |
| `scripts/analyze.py` | Scoring analysis |

### Architecture Pattern

**Domain-Driven Design** with:
- Domain Layer (entities, value objects, enums)
- Service Layer (kill-switch, scoring, classification)
- Repository Layer (CSV, JSON persistence)
- Pipeline Layer (orchestration, checkpointing)

---

## Generated Documentation

### Core Documents

| Document | Description |
|----------|-------------|
| [Project Overview](./project-overview.md) | Executive summary, tech stack, quick start |
| [Architecture](./architecture.md) | System design, DDD patterns, diagrams |
| [Source Tree Analysis](./source-tree-analysis.md) | Complete directory structure |
| [Development Guide](./development-guide.md) | Setup, testing, contribution guide |

### Technical References

| Document | Description |
|----------|-------------|
| [Data Models](./data-models.md) | Domain entities, value objects, schemas |
| [API Contracts](./api-contracts.md) | Service interfaces, client contracts |

### Existing Documentation

| Document | Description |
|----------|-------------|
| [CLAUDE.md](../CLAUDE.md) | Root project documentation |
| [README.md](../README.md) | Quick start guide |
| [Config Guide](./CONFIG_IMPLEMENTATION_GUIDE.md) | Configuration system reference |
| [Security](./SECURITY.md) | Security best practices |
| [Visualizations Guide](./VISUALIZATIONS_GUIDE.md) | Chart and map generation |
| [MC Assessor API](./MC-Assessor-API-Documentation.md) | County API reference |

### Sprint Artifacts

| Document | Description |
|----------|-------------|
| [Sprint Status](./sprint-artifacts/sprint-status.yaml) | Current sprint progress |
| [Workflow Status](./sprint-artifacts/workflow-status.yaml) | BMAD workflow tracking |
| [Stories](./sprint-artifacts/stories/) | User story definitions |

---

## Kill-Switch System

All 8 criteria are **HARD** (instant fail):

| # | Criterion | Requirement |
|---|-----------|-------------|
| 1 | HOA | = $0 (no HOA) |
| 2 | Beds | >= 4 |
| 3 | Baths | >= 2 |
| 4 | SqFt | > 1,800 |
| 5 | Lot | > 8,000 sqft |
| 6 | Garage | >= 1 space |
| 7 | Sewer | City (no septic) |
| 8 | Year | <= 2024 |

---

## Scoring System (605 Points)

| Section | Points | Components |
|---------|--------|------------|
| **A: Location** | 250 | Schools, safety, orientation, proximity |
| **B: Systems** | 175 | HVAC, roof, pool, cost efficiency |
| **C: Interior** | 180 | Kitchen, master, layout, finishes |
| **Total** | **605** | |

### Tier Classification

| Tier | Score | Percentage |
|------|-------|------------|
| UNICORN | >480 | 80%+ |
| CONTENDER | 360-480 | 60-80% |
| PASS | <360 | <60% |

---

## Pipeline Phases

```
Phase 0: County Data      → Assessor API (lot, year, garage)
    ↓
Phase 1: Listing + Maps   → Zillow, GreatSchools, Google Maps
    ↓
Phase 2: Image Analysis   → Exterior/Interior scoring
    ↓
Phase 3: Synthesis        → Kill-switch + Scoring
    ↓
Phase 4: Reports          → Deal sheets, dashboards, maps
```

---

## Getting Started

### Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/example/phx-houses-dec-2025.git
cd phx-houses-dec-2025
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Run analysis
python scripts/phx_home_analyzer.py

# 4. View results
open reports/html/dashboard.html
```

### Development

```bash
# Run tests
pytest tests/unit/ -v

# Lint and format
ruff check --fix && ruff format

# Type check
mypy src/
```

---

## Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project configuration |
| `data/phx_homes.csv` | Property listings |
| `data/enrichment_data.json` | Enriched property data |
| `data/work_items.json` | Pipeline state |

---

## AI-Assisted Development

When using AI assistants for this project:

1. **Start here** - This index provides project context
2. **Architecture** - See [architecture.md](./architecture.md) for patterns
3. **Domain** - See [data-models.md](./data-models.md) for entities
4. **APIs** - See [api-contracts.md](./api-contracts.md) for interfaces

### Multi-Agent Commands

```bash
# Full property analysis
/analyze-property --all

# Single property
/analyze-property "123 Main St, Phoenix, AZ"

# Test mode (first 5 properties)
/analyze-property --test
```

---

## Project Status

| Metric | Value |
|--------|-------|
| Epics Complete | 2/7 |
| Stories Done | 19/42 (45%) |
| Test Count | ~200 tests |
| Last Updated | 2025-12-05 |

---

## Links

- [Project Root](../)
- [Scripts](../scripts/)
- [Source Code](../src/phx_home_analysis/)
- [Tests](../tests/)
