# Multi-Agent Architecture

### Agent Definitions

#### listing-browser (Haiku)

**Purpose:** Extract listing data from Zillow and Redfin using stealth browsers.

**Model:** Claude Haiku (fast, cost-effective)

**Skills:** listing-extraction, property-data, state-management, kill-switch

**Tools:**
- nodriver (stealth Chrome automation)
- curl-cffi (HTTP with browser TLS fingerprints)
- MCP Playwright (fallback)

**Outputs:**
- Price, beds, baths, sqft
- HOA fee (critical for kill-switch)
- Listing images
- Property description

**Duration:** 30-60 seconds per property

#### map-analyzer (Haiku)

**Purpose:** Geographic analysis using APIs and satellite imagery.

**Model:** Claude Haiku

**Skills:** map-analysis, property-data, state-management, arizona-context, scoring

**Tools:**
- Google Maps API (geocoding, distances, satellite)
- GreatSchools API (school ratings)
- Crime data APIs

**Outputs:**
- School ratings (elementary, middle, high)
- Crime index
- Sun orientation (from satellite imagery)
- Distances to amenities
- Flood zone classification

**Duration:** 45-90 seconds per property

#### image-assessor (Opus 4.5)

**Purpose:** Visual scoring of interior/exterior condition.

**Model:** Claude Opus 4.5 (multi-modal vision, extended thinking)

**Skills:** image-assessment, property-data, state-management, arizona-context-lite, scoring

**Prerequisites:** Phase 1 complete, images downloaded

**Outputs:**
- Section C scores (kitchen, master, light, ceilings, fireplace, laundry, aesthetics)
- Exterior condition notes
- Pool equipment age estimation
- Roof condition assessment

**Duration:** 2-5 minutes per property

### Phase Dependencies

```
Phase 0: County Assessor API
    |
    | (lot_sqft, year_built, garage, pool, sewer)
    |
    v
Phase 1a: listing-browser ----+
    |                         |
    | (price, beds, baths,    | (parallel)
    |  sqft, hoa, images)     |
    |                         |
Phase 1b: map-analyzer -------+
    |
    | (schools, crime, orientation, flood)
    |
    v
[PREREQUISITE VALIDATION]
    |
    | scripts/validate_phase_prerequisites.py
    | Exit 0 = proceed, Exit 1 = BLOCK
    |
    v
Phase 2: image-assessor
    |
    | (Section C scores)
    |
    v
Phase 3: Synthesis
    |
    | Kill-switch + Scoring + Tier
    |
    v
Phase 4: Reports
    |
    | Deal sheets + CSV + Visualizations
    v
```

### Prerequisite Validation (MANDATORY)

```bash
# ALWAYS run before spawning Phase 2
python scripts/validate_phase_prerequisites.py \
    --address "ADDRESS" \
    --phase phase2_images \
    --json

# Output:
# {"can_spawn": true, "missing_data": [], "reasons": []}
# Exit code 0 = proceed
#
# {"can_spawn": false, "missing_data": ["images"], "reasons": ["No images downloaded"]}
# Exit code 1 = BLOCK - do NOT spawn agent
```

---
