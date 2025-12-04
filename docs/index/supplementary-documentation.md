# Supplementary Documentation

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
