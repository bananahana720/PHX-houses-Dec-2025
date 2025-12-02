# PHX Houses Dec 2025

First-time home buyer analysis for Phoenix metropolitan area with kill-switch filtering and weighted scoring.

## Project Overview

Data pipeline analyzing Phoenix listings against strict buyer criteria: hard kill-switches (pass/fail) + weighted scoring (600 pts max).

**Target Buyer:** Max $4k/month payment, 4+ bed, 2+ bath, 2-car garage, 7k-15k sqft lot, NO HOA, city sewer, pre-2024 builds only.

## Kill Switches (Weighted Threshold System)

### HARD Criteria (Instant Fail)
- NO HOA (hoa_fee = 0 or None)
- Min 4 beds
- Min 2 baths

### SOFT Criteria (Contribute to Severity Score)
| Criterion | Requirement | Severity |
|-----------|-------------|----------|
| City sewer | No septic | 2.5 |
| No new builds | year_built < 2024 | 2.0 |
| Min 2-car garage | garage_spaces >= 2 | 1.5 |
| Lot size | 7,000-15,000 sqft | 1.0 |

**Verdict**: FAIL if any HARD fails OR severity >= 3.0 | WARNING if 1.5-3.0 | PASS if < 1.5

## Scoring System (600 pts max)

**Section A: Location (230 pts)** - School (50), Quietness (40), Safety (50), Supermarket (30), Parks (30), Sun (30)
**Section B: Lot/Systems (180 pts)** - Roof (50), Backyard (40), Plumbing (40), Pool (20), Cost Efficiency (30)
**Section C: Interior (190 pts)** - Kitchen (40), Master (40), Light (30), Ceilings (30), Fireplace (20), Laundry (20), Aesthetics (10)

**Tiers:** Unicorn (>480), Contender (360-480), Pass (<360)

## Key Commands

```bash
# Analysis pipeline
python scripts/phx_home_analyzer.py

# Deal sheets (multiple entry points)
python -m scripts.deal_sheets
python scripts/deal_sheets/generator.py

# Image extraction (stealth browsers: nodriver + curl_cffi)
python scripts/extract_images.py --all                    # All properties
python scripts/extract_images.py --address "123 Main St"  # Single property
python scripts/extract_images.py --sources zillow,redfin  # Filter sources
python scripts/extract_images.py --dry-run                # Discover only
python scripts/extract_images.py --fresh                  # Clear state
python scripts/extract_images.py --resume                 # Resume (default)

# County data extraction
python scripts/extract_county_data.py --all --update-only

# Multi-agent analysis
/analyze-property --test          # First 5 properties
/analyze-property --all           # Full batch
/analyze-property "123 Main St"   # Single property
```

## Project Structure

```
src/phx_home_analysis/
├── services/
│   ├── cost_estimation/      # Monthly cost estimator
│   ├── ai_enrichment/        # Field inference & triage
│   ├── quality/              # Quality metrics & lineage
│   ├── scoring/              # Property scoring
│   └── kill_switch/          # Kill-switch filtering
├── validation/               # Pydantic validation layer
├── config/                   # Scoring weights config
└── domain/                   # Entities & value objects

scripts/
├── phx_home_analyzer.py      # Main pipeline (uses PropertyScorer)
├── deal_sheets/              # Package (was single file)
│   ├── generator.py          # Main entry
│   ├── data_loader.py
│   ├── templates.py
│   └── renderer.py
├── lib/
│   └── kill_switch.py        # Canonical kill-switch logic

data/
├── phx_homes.csv             # Listing data
├── enrichment_data.json      # Research data
└── phx_homes_ranked.csv      # Output with scores
```

## Data Sources

| Source | Data | Access |
|--------|------|--------|
| Maricopa County Assessor | Lot size, year built, garage, sewer | API (token required) |
| GreatSchools | School ratings | Manual/scraping |
| Google Maps | Commute, distances | Manual/API |
| Zillow/Redfin | Price, beds, baths, photos | Stealth browsers (nodriver, curl_cffi) |

**Architecture:** Async concurrent processing, perceptual hash deduplication, PerimeterX bypass

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/phx_home_analyzer.py` | Main analysis pipeline |
| `scripts/deal_sheets/generator.py` | Deal summary sheets |
| `scripts/extract_images.py` | Image extraction orchestrator |
| `scripts/extract_county_data.py` | Maricopa County API |
| `scripts/estimate_ages.py` | Estimate roof/HVAC/pool ages |
| `scripts/geocode_homes.py` | Geocode addresses |
| `scripts/value_spotter.py` | Identify value opportunities |
| `scripts/radar_charts.py` | Generate radar visuals |
| `scripts/quality_baseline.py` | Measure quality before changes |
| `scripts/quality_check.py` | CI/CD quality gate (95% threshold) |

## Arizona-Specific Considerations

**Solar:** Owned = value-add, Leased = $100-200/mo burden + transfer issues
**Pool:** $100-150/mo service, $3k-8k equipment, $50-100/mo energy
**Sun:** West-facing = high cooling costs, North-facing = best for AZ
**HVAC:** 10-15yr lifespan (vs 20+ elsewhere), dual-zone preferred for 2-story

## Maricopa County Assessor API

**Requires:** `MARICOPA_ASSESSOR_TOKEN` env var

```bash
# Extract all properties
python scripts/extract_county_data.py --all --update-only
```

**Fields Available:** lot_sqft, year_built, garage_spaces, has_pool, livable_sqft, baths (estimated), full_cash_value, roof_type
**NOT Available:** sewer_type (manual), beds (listings), hoa_fee (listings), tax_annual (Treasurer API)

## Property Hash

```python
import hashlib
hashlib.md5(address.lower().encode()).hexdigest()[:8]
# Example: "4732 W Davis Rd, Glendale, AZ 85306" -> "ef7cd95f"
```

## Development Guidelines

- Use `uv` instead of `pip`
- Follow existing code patterns
- Document all data sources in enrichment_data.json
- Manual assessment fields default to 5.0 until inspected
- Keep analysis reproducible

## Environment Variables

- `MARICOPA_ASSESSOR_TOKEN` - County Assessor API

## File Organization

**Root Directory Policy:** Keep root CLEAN - only standard config files allowed.

| File Type | Destination | Example |
|-----------|-------------|---------|
| Python scripts | `scripts/` | `extract_*.py`, `*_analyzer.py` |
| Test files | `tests/` | `test_*.py` |
| Benchmarks | `tests/benchmarks/` | `test_*_performance.py` |
| Implementation notes | `docs/artifacts/implementation-notes/` | `*_SUMMARY.md` |
| Reference docs | `docs/` | `*_REFERENCE.md`, `CHANGELOG` |
| Data files | `data/` | `*.csv`, `*.json` |
| Temp/log files | Delete or `TRASH/` | `*.log`, `tmp_*` |

**Never in root:** `*.py`, `*_SUMMARY.md`, `*.log`, `tmp_*`, data files

**See:** `.claude/skills/file-organization/SKILL.md` for full rules

---

## Protocols and Multi-Agent Analysis

**Full protocols:** See `.claude/protocols.md` (TIER 0-3, all operational standards)

**Multi-agent orchestration:** See `.claude/commands/analyze-property.md`
- 3 agents: listing-browser (Haiku), map-analyzer (Haiku), image-assessor (Sonnet)
- Pipeline: Phase 0 (County) → Phase 1 (Listing + Map) → Phase 2 (Images) → Phase 3 (Synthesis)
- State: `data/property_images/metadata/{extraction_state,image_manifest,hash_index}.json`

---

*Lines: ~150 (target: <200)*
