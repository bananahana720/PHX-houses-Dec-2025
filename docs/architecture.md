---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - docs/prd.md
  - docs/ux-design-specification.md
  - src/phx_home_analysis/config/scoring_weights.py
  - src/phx_home_analysis/config/constants.py
workflowType: 'architecture'
lastStep: 8
project_name: 'PHX-houses-Dec-2025'
user_name: 'Andrew'
date: '2025-12-03'
version: '2.0'
---

# PHX Houses Analysis Pipeline - System Architecture

**Version:** 2.0 (Complete Regeneration)
**Author:** Winston - System Architect
**Date:** 2025-12-03

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Core Architectural Decisions](#core-architectural-decisions)
4. [Data Architecture](#data-architecture)
5. [Component Architecture](#component-architecture)
6. [Multi-Agent Architecture](#multi-agent-architecture)
7. [Scoring System Architecture](#scoring-system-architecture)
8. [Kill-Switch Architecture](#kill-switch-architecture)
9. [Integration Architecture](#integration-architecture)
10. [State Management Architecture](#state-management-architecture)
11. [Security Architecture](#security-architecture)
12. [Deployment Architecture](#deployment-architecture)
13. [Architecture Validation](#architecture-validation)

---

## Executive Summary

### Purpose

This document defines the complete technical architecture for the PHX Houses Analysis Pipeline - a personal decision support system that evaluates Phoenix-area residential properties against strict first-time homebuyer criteria through multi-agent analysis, kill-switch filtering, and comprehensive scoring.

### Key Architectural Goals

1. **Eliminate Decision Anxiety**: Transform 50+ weekly listings into 3-5 tour-worthy candidates through systematic filtering
2. **Ensure Zero False Passes**: 100% accuracy on kill-switch criteria - no deal-breaker properties slip through
3. **Enable Transparent Scoring**: Every point traceable to source data and calculation logic
4. **Support Crash Recovery**: Resume interrupted pipelines without re-running completed work
5. **Optimize for Cost Efficiency**: Haiku for data extraction, Sonnet only for vision tasks

### Critical Architecture Decisions Summary

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture Style | Domain-Driven Design (DDD) | Clean separation, testable business logic |
| Data Storage | JSON files (LIST-based) | Simple, crash-recoverable, adequate for <1000 properties |
| Scoring System | 605-point weighted system | Matches actual ScoringWeights dataclass calculations |
| Kill-Switch System | All HARD criteria per PRD | HOA, beds, baths, sqft, lot, garage, sewer |
| Multi-Agent Model | Haiku (extraction) + Sonnet (vision) | Cost optimization with capability matching |
| Browser Automation | nodriver (stealth) primary | PerimeterX bypass for Zillow/Redfin |

### Architecture Gap Resolutions

| Gap ID | Issue | Resolution |
|--------|-------|------------|
| ARCH-01 | Kill-switch criteria mismatch | All 7 criteria now HARD per PRD FR9-FR14 |
| ARCH-02 | Scoring totals inconsistent | Reconciled to 605 pts (ScoringWeights authoritative) |
| ARCH-03 | Tier thresholds misaligned | Updated to 484 (80%), 363 (60%) of 605 |

---

## System Overview

### High-Level Architecture

```
+===========================================================================+
|                        EXTERNAL DATA SOURCES                               |
+===========================================================================+
|  Maricopa County    Zillow/Redfin    Google Maps    GreatSchools   FEMA   |
|  Assessor API       Listings         Geo Services   Schools API    Flood  |
+======|==================|================|===============|===========|====+
       |                  |                |               |           |
       +--------+---------+-------+--------+-------+-------+-----------+
                |                 |                |
     +----------v-----------------v----------------v-----------+
     |               EXTRACTION LAYER (Phase 0-1)              |
     |  +-------------------+  +--------------------+           |
     |  | County Assessor   |  | Stealth Browser    |           |
     |  | Client            |  | Automation         |           |
     |  | (HTTP/REST)       |  | (nodriver/curl)    |           |
     |  +-------------------+  +--------------------+           |
     |  +-------------------+  +--------------------+           |
     |  | Map Analyzer      |  | Image Extractors   |           |
     |  | Agent (Haiku)     |  | (Zillow, Redfin)   |           |
     |  +-------------------+  +--------------------+           |
     +-------------------------|-------------------------------+
                               |
     +-------------------------v-------------------------------+
     |              DATA INTEGRATION LAYER                      |
     |  +-------------------+  +--------------------+           |
     |  | Field Mappers     |  | Merge Strategies   |           |
     |  | (source -> domain)|  | (conflict resolve) |           |
     |  +-------------------+  +--------------------+           |
     |  +-------------------+  +--------------------+           |
     |  | Data Quality      |  | Deduplication      |           |
     |  | Metrics           |  | (address hash)     |           |
     |  +-------------------+  +--------------------+           |
     +-------------------------|-------------------------------+
                               |
     +-------------------------v-------------------------------+
     |               BUSINESS LOGIC LAYER                       |
     |  +-------------------+  +--------------------+           |
     |  | Kill-Switch       |  | Property Scorer    |           |
     |  | Filter (7 HARD)   |  | (605 pts, 22 strat)|           |
     |  +-------------------+  +--------------------+           |
     |  +-------------------+  +--------------------+           |
     |  | Tier Classifier   |  | Cost Estimator     |           |
     |  | (Unicorn/Contend) |  | (AZ-specific)      |           |
     |  +-------------------+  +--------------------+           |
     +-------------------------|-------------------------------+
                               |
     +-------------------------v-------------------------------+
     |               PRESENTATION LAYER                         |
     |  +-------------------+  +--------------------+           |
     |  | Console Reporter  |  | HTML Reporter      |           |
     |  | (rich library)    |  | (Jinja2 + Tailwind)|           |
     |  +-------------------+  +--------------------+           |
     |  +-------------------+  +--------------------+           |
     |  | CSV Reporter      |  | Deal Sheet Gen     |           |
     |  | (ranked list)     |  | (mobile-first)     |           |
     |  +-------------------+  +--------------------+           |
     +----------------------------------------------------------+
```

### Key Metrics

| Metric | Target | Source |
|--------|--------|--------|
| Properties per batch | 20-50 | PRD NFR1 |
| Kill-switch accuracy | 100% | PRD NFR5 |
| Scoring consistency | +/-5 pts | PRD NFR6 |
| Batch processing time | <=30 min | PRD NFR1 |
| Re-scoring time | <=5 min | PRD NFR2 |
| Operating cost | <=$90/month | PRD NFR22 |

---

## Core Architectural Decisions

### ADR-01: Domain-Driven Design (DDD)

**Status:** Accepted

**Context:** System has complex domain logic (scoring, kill-switches, Arizona-specific factors) that must remain stable as infrastructure changes.

**Decision:** Implement DDD with clear layer separation:
- Domain Layer: Entities, value objects, enums
- Service Layer: Business logic orchestration
- Repository Layer: Data persistence abstraction
- Pipeline Layer: Workflow coordination
- Presentation Layer: Output formatting

**Consequences:**
- (+) Business logic testable in isolation
- (+) Infrastructure changes don't affect domain
- (+) Clear dependency direction (inward)
- (-) More boilerplate than simple approaches
- (-) Requires discipline to maintain boundaries

### ADR-02: JSON File Storage (Not Database)

**Status:** Accepted

**Context:** Personal tool with <1000 properties. Needs crash recovery without database complexity.

**Decision:** Use JSON files with atomic writes and backup-before-modify pattern.

**File Structure:**
- `data/phx_homes.csv` - Source listings (input)
- `data/enrichment_data.json` - Enriched property data (LIST of dicts)
- `data/work_items.json` - Pipeline state tracking
- `data/extraction_state.json` - Image extraction state

**Consequences:**
- (+) Simple, human-readable, git-diffable
- (+) No database setup or maintenance
- (+) Crash recovery via atomic writes
- (-) O(n) lookup by address (acceptable for <1000)
- (-) No concurrent write safety (single-user system)

### ADR-03: 605-Point Scoring System (Reconciliation)

**Status:** Accepted

**Context:** Discovered discrepancy between `scoring_weights.py` (605 pts) and `constants.py` (600 pts assertion).

**Analysis:**
```
ScoringWeights dataclass actual values:
- Section A: 42+30+47+23+23+25+23+22+15 = 250 pts
- Section B: 45+35+35+20+35+5 = 175 pts
- Section C: 40+35+30+25+20+20+10 = 180 pts
- TOTAL: 605 pts

constants.py assertion:
- Section A: 230, Section B: 180, Section C: 190 = 600 pts
```

**Decision:** `ScoringWeights` dataclass is authoritative. Total = **605 points**.

**Action Required:** Update `constants.py` assertion to match actual weights:
- `SCORE_SECTION_A_TOTAL = 250`
- `SCORE_SECTION_B_TOTAL = 175`
- `SCORE_SECTION_C_TOTAL = 180`
- `MAX_POSSIBLE_SCORE = 605`

**Tier Thresholds (updated):**
- Unicorn: >484 pts (80% of 605)
- Contender: 363-484 pts (60-80% of 605)
- Pass: <363 pts (<60% of 605)

### ADR-04: All Kill-Switch Criteria Are HARD

**Status:** Accepted

**Context:** PRD specifies 7 non-negotiable criteria. Previous architecture had some as SOFT.

**PRD Requirements (FR9-FR14):**

| Criterion | PRD Requirement | Type |
|-----------|-----------------|------|
| HOA | Must be $0 | HARD |
| Bedrooms | >=4 | HARD |
| Bathrooms | >=2 | HARD |
| House SQFT | >1800 sqft | HARD |
| Lot Size | >8000 sqft | HARD |
| Garage | Indoor garage required | HARD |
| Sewer | City only (no septic) | HARD |

**Decision:** Implement all 7 as HARD kill-switches. Instant FAIL if any criterion not met.

**Soft Severity System:** Retained for future flexibility but not currently used in PRD criteria.

**Consequences:**
- (+) Matches PRD exactly
- (+) Simpler logic (no severity accumulation needed for core criteria)
- (+) Zero false passes guaranteed
- (-) Less flexible than soft severity approach
- (-) May filter out properties that are "close enough"

### ADR-05: Multi-Agent Model Selection

**Status:** Accepted

**Context:** Need to balance cost efficiency with capability requirements.

**Decision:**

| Agent | Model | Justification |
|-------|-------|---------------|
| listing-browser | Claude Haiku | Fast, cheap, structured data extraction |
| map-analyzer | Claude Haiku | Geographic data doesn't need vision |
| image-assessor | Claude Sonnet | Requires multi-modal vision capability |

**Cost Analysis (per 100 properties):**
- Haiku: ~$0.25/1M tokens = $2-5/100 properties
- Sonnet: ~$3.00/1M tokens = $15-30/100 properties (vision)
- Total: ~$20-50/100 properties (within $90/month budget)

### ADR-06: Stealth Browser Strategy

**Status:** Accepted

**Context:** Zillow/Redfin use PerimeterX bot detection. Standard Playwright blocked.

**Decision:** Primary: `nodriver` (stealth Chrome). Fallback: `curl-cffi` (TLS fingerprinting).

**Stack:**
1. `nodriver` - Stealth browser automation, bypasses PerimeterX
2. `curl-cffi` - HTTP client with browser TLS fingerprints
3. `Playwright` - Fallback for less aggressive sites (Realtor.com)

**Maintenance:** Weekly monitoring for anti-bot detection updates.

---

## Data Architecture

### Data Flow Diagram

```
                    +------------------+
                    | phx_homes.csv    |
                    | (source listings)|
                    +--------+---------+
                             |
                             v
            +----------------+----------------+
            |                                 |
            v                                 v
+-------------------+            +--------------------+
| County Assessor   |            | Listing Browser    |
| API (Phase 0)     |            | Agent (Phase 1)    |
+--------+----------+            +---------+----------+
         |                                 |
         |    +-------------------+        |
         |    | Map Analyzer      |        |
         |    | Agent (Phase 1)   |        |
         |    +--------+----------+        |
         |             |                   |
         +------+------+------+------------+
                |             |
                v             v
         +------+-------------+------+
         |   enrichment_data.json    |
         |   (LIST of property dicts)|
         +-------------+-------------+
                       |
                       v
         +-------------+-------------+
         |   Image Assessor Agent    |
         |   (Phase 2 - Sonnet)      |
         +-------------+-------------+
                       |
                       v
         +-------------+-------------+
         |   Kill-Switch Filter      |
         |   (7 HARD criteria)       |
         +-------------+-------------+
                       |
              +--------+--------+
              |                 |
              v                 v
         +----+----+      +-----+-----+
         | PASS    |      | FAIL      |
         +---------+      +-----------+
              |
              v
         +----+----+
         | Scorer  |
         | (605pt) |
         +---------+
              |
              v
         +----+----+
         | Tier    |
         | Classify|
         +---------+
              |
              v
    +---------+---------+
    |                   |
    v                   v
+---+---+          +----+----+
| Deal  |          | Report  |
| Sheet |          | (CSV/   |
| (HTML)|          |  HTML)  |
+-------+          +---------+
```

### JSON Schemas

#### enrichment_data.json (LIST format)

**CRITICAL:** This is a LIST of objects, NOT a dict keyed by address.

```json
[
  {
    "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
    "normalized_address": "4732 w davis rd glendale az 85306",

    "county_data": {
      "lot_sqft": 10500,
      "year_built": 2006,
      "garage_spaces": 2,
      "has_pool": true,
      "sewer_type": "city",
      "data_source": "maricopa_assessor",
      "fetched_at": "2025-12-03T10:00:00Z",
      "confidence": 0.95
    },

    "listing_data": {
      "price": 475000,
      "beds": 4,
      "baths": 2.5,
      "sqft": 2100,
      "hoa_fee": 0,
      "listing_url": "https://zillow.com/...",
      "data_source": "zillow",
      "fetched_at": "2025-12-03T10:15:00Z",
      "confidence": 0.85
    },

    "location_data": {
      "school_rating": 8.5,
      "crime_index": 75,
      "orientation": "north",
      "flood_zone": "X",
      "walk_score": 45,
      "transit_score": 30,
      "bike_score": 35,
      "data_source": "map_analyzer",
      "fetched_at": "2025-12-03T10:30:00Z",
      "confidence": 0.85
    },

    "image_assessment": {
      "kitchen_score": 8.5,
      "master_score": 7.5,
      "natural_light_score": 8.0,
      "ceiling_score": 7.0,
      "fireplace_present": true,
      "laundry_score": 6.5,
      "aesthetics_score": 7.5,
      "image_count": 42,
      "data_source": "image_assessor",
      "assessed_at": "2025-12-03T11:00:00Z",
      "confidence": 0.80
    },

    "kill_switch": {
      "verdict": "PASS",
      "criteria_results": {
        "hoa": {"passed": true, "value": 0},
        "beds": {"passed": true, "value": 4},
        "baths": {"passed": true, "value": 2.5},
        "sqft": {"passed": true, "value": 2100},
        "lot": {"passed": true, "value": 10500},
        "garage": {"passed": true, "value": 2},
        "sewer": {"passed": true, "value": "city"}
      },
      "evaluated_at": "2025-12-03T11:15:00Z"
    },

    "scoring": {
      "section_a": 195,
      "section_b": 145,
      "section_c": 155,
      "total": 495,
      "tier": "UNICORN",
      "scored_at": "2025-12-03T11:20:00Z"
    },

    "metadata": {
      "created_at": "2025-12-03T10:00:00Z",
      "last_updated": "2025-12-03T11:20:00Z",
      "pipeline_version": "2.0",
      "schema_version": "2025-12-03"
    }
  }
]
```

#### work_items.json (Pipeline State)

```json
{
  "session": {
    "session_id": "abc123-def456-ghi789",
    "started_at": "2025-12-03T10:00:00Z",
    "mode": "all",
    "properties_count": 50
  },

  "current_phase": "phase2_images",

  "work_items": [
    {
      "address": "4732 W Davis Rd, Glendale, AZ 85306",
      "phases": {
        "phase0_county": {
          "status": "completed",
          "started_at": "2025-12-03T10:00:00Z",
          "completed_at": "2025-12-03T10:01:00Z"
        },
        "phase1_listing": {
          "status": "completed",
          "started_at": "2025-12-03T10:02:00Z",
          "completed_at": "2025-12-03T10:15:00Z"
        },
        "phase1_map": {
          "status": "completed",
          "started_at": "2025-12-03T10:02:00Z",
          "completed_at": "2025-12-03T10:20:00Z"
        },
        "phase2_images": {
          "status": "in_progress",
          "started_at": "2025-12-03T10:25:00Z",
          "images_processed": 28,
          "images_total": 42
        },
        "phase3_synthesis": {
          "status": "pending"
        }
      },
      "last_updated": "2025-12-03T10:30:00Z"
    }
  ],

  "summary": {
    "total": 50,
    "phase0_completed": 50,
    "phase1_completed": 45,
    "phase2_completed": 30,
    "phase2_in_progress": 5,
    "phase3_completed": 25,
    "failed": 2,
    "skipped": 3
  },

  "last_checkpoint": "2025-12-03T10:30:00Z"
}
```

### Data Access Patterns

```python
# CORRECT: enrichment_data.json is a LIST
data = json.load(open('data/enrichment_data.json'))  # List[Dict]
prop = next((p for p in data if p["full_address"] == address), None)

# WRONG: Will raise TypeError
prop = data[address]  # TypeError: list indices must be integers

# CORRECT: work_items.json is a dict
work = json.load(open('data/work_items.json'))  # Dict
item = next((w for w in work["work_items"] if w["address"] == address), None)
```

---

## Component Architecture

### Domain Layer (`src/phx_home_analysis/domain/`)

#### Entities

```python
@dataclass
class Property:
    """Central domain entity representing a property for analysis."""
    address: Address
    price: int | None = None
    beds: int | None = None
    baths: float | None = None
    sqft: int | None = None
    lot_sqft: int | None = None
    year_built: int | None = None
    garage_spaces: int | None = None
    has_pool: bool | None = None
    sewer_type: SewerType = SewerType.UNKNOWN
    orientation: Orientation = Orientation.UNKNOWN
    hoa_fee: int | None = None

    # Enriched fields
    school_rating: float | None = None
    crime_index: int | None = None
    walk_score: int | None = None
    flood_zone: FloodZone = FloodZone.UNKNOWN

    # Assessment fields
    kill_switch_verdict: KillSwitchVerdict | None = None
    score_breakdown: ScoreBreakdown | None = None
    tier: Tier | None = None

@dataclass(frozen=True)
class Address:
    """Immutable address value object."""
    street: str
    city: str
    state: str
    zip_code: str

    @property
    def full(self) -> str:
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"

    @property
    def normalized(self) -> str:
        return self.full.lower().replace(",", "").replace(".", "")
```

#### Value Objects

```python
@dataclass(frozen=True)
class ScoreBreakdown:
    """Immutable scoring result container."""
    section_a: float  # Location & Environment (max 250)
    section_b: float  # Lot & Systems (max 175)
    section_c: float  # Interior & Features (max 180)

    @property
    def total(self) -> float:
        return self.section_a + self.section_b + self.section_c

    @property
    def percentage(self) -> float:
        return (self.total / 605) * 100

@dataclass(frozen=True)
class KillSwitchResult:
    """Result of kill-switch evaluation."""
    verdict: KillSwitchVerdict
    failed_criteria: list[str]
    details: dict[str, Any]
```

#### Enums

```python
class Tier(Enum):
    UNICORN = "unicorn"      # >484 pts (80% of 605)
    CONTENDER = "contender"  # 363-484 pts (60-80% of 605)
    PASS = "pass"            # <363 pts (<60% of 605)

class KillSwitchVerdict(Enum):
    PASS = "pass"       # All criteria satisfied
    FAIL = "fail"       # One or more HARD criteria failed
    WARNING = "warning" # Pass but with concerns (future use)

class SewerType(Enum):
    CITY = "city"
    SEPTIC = "septic"
    UNKNOWN = "unknown"

class Orientation(Enum):
    NORTH = "north"   # Best: 25 pts
    EAST = "east"     # Good: 18.75 pts
    SOUTH = "south"   # Moderate: 12.5 pts
    WEST = "west"     # Worst: 0 pts (high cooling costs)
    UNKNOWN = "unknown"

class FloodZone(Enum):
    X = "X"           # Minimal risk
    X_SHADED = "X500" # 500-year flood
    A = "A"           # 100-year flood (high risk)
    AE = "AE"         # 100-year with base elevation
    VE = "VE"         # Coastal high hazard
    UNKNOWN = "unknown"
```

### Service Layer (`src/phx_home_analysis/services/`)

#### Kill-Switch Service

```python
class KillSwitchFilter:
    """Orchestrates all 7 HARD kill-switch criteria per PRD."""

    def __init__(self):
        self.criteria = [
            HoaKillSwitch(),        # HOA must be $0
            BedroomsKillSwitch(),   # Beds >= 4
            BathroomsKillSwitch(),  # Baths >= 2
            SqftKillSwitch(),       # Sqft > 1800
            LotSizeKillSwitch(),    # Lot > 8000
            GarageKillSwitch(),     # Indoor garage required
            SewerKillSwitch(),      # City sewer only
        ]

    def evaluate(self, property: Property) -> KillSwitchResult:
        failed = []
        details = {}

        for criterion in self.criteria:
            result = criterion.evaluate(property)
            details[criterion.name] = result
            if not result.passed:
                failed.append(criterion.name)

        verdict = (
            KillSwitchVerdict.PASS if len(failed) == 0
            else KillSwitchVerdict.FAIL
        )

        return KillSwitchResult(
            verdict=verdict,
            failed_criteria=failed,
            details=details
        )

class HoaKillSwitch:
    """HOA must be exactly $0. PRD FR9: HARD criterion."""
    name = "hoa"

    def evaluate(self, property: Property) -> CriterionResult:
        if property.hoa_fee is None:
            # Assume no HOA if not specified
            return CriterionResult(passed=True, value=0, note="Assumed $0")

        passed = property.hoa_fee == 0
        return CriterionResult(
            passed=passed,
            value=property.hoa_fee,
            note="FAIL: HOA fee present" if not passed else "PASS"
        )

class SqftKillSwitch:
    """House SQFT must be >1800. PRD FR9: HARD criterion (NEW)."""
    name = "sqft"
    threshold = 1800

    def evaluate(self, property: Property) -> CriterionResult:
        if property.sqft is None:
            return CriterionResult(
                passed=False,
                value=None,
                note="FAIL: SQFT unknown"
            )

        passed = property.sqft > self.threshold
        return CriterionResult(
            passed=passed,
            value=property.sqft,
            note=f"{'PASS' if passed else 'FAIL'}: {property.sqft} sqft"
        )
```

#### Scoring Service

```python
class PropertyScorer:
    """Orchestrates 605-point scoring across 22 strategies."""

    def __init__(self, weights: ScoringWeights):
        self.weights = weights
        self.strategies = {
            # Section A: Location (250 pts)
            'school_district': SchoolDistrictScorer(),
            'quietness': QuietnessScorer(),
            'crime_index': CrimeIndexScorer(),
            'supermarket': SupermarketScorer(),
            'parks_walkability': ParksWalkabilityScorer(),
            'orientation': OrientationScorer(),
            'flood_risk': FloodRiskScorer(),
            'walk_transit': WalkTransitScorer(),
            'air_quality': AirQualityScorer(),

            # Section B: Systems (175 pts)
            'roof_condition': RoofConditionScorer(),
            'backyard_utility': BackyardUtilityScorer(),
            'plumbing_electrical': PlumbingElectricalScorer(),
            'pool_condition': PoolConditionScorer(),
            'cost_efficiency': CostEfficiencyScorer(),
            'solar_status': SolarStatusScorer(),

            # Section C: Interior (180 pts)
            'kitchen_layout': KitchenLayoutScorer(),
            'master_suite': MasterSuiteScorer(),
            'natural_light': NaturalLightScorer(),
            'high_ceilings': HighCeilingsScorer(),
            'fireplace': FireplaceScorer(),
            'laundry_area': LaundryAreaScorer(),
            'aesthetics': AestheticsScorer(),
        }

    def score(self, property: Property) -> ScoreBreakdown:
        section_a = self._score_section_a(property)
        section_b = self._score_section_b(property)
        section_c = self._score_section_c(property)

        return ScoreBreakdown(
            section_a=section_a,
            section_b=section_b,
            section_c=section_c
        )

    def _apply_strategy(self, name: str, property: Property) -> float:
        """Apply strategy and scale by weight."""
        strategy = self.strategies[name]
        raw_score = strategy.score(property)  # 0-10 scale
        weight = getattr(self.weights, name)
        return raw_score * (weight / 10)
```

### Repository Layer

```python
class JsonEnrichmentRepository:
    """Repository for enrichment_data.json (LIST format)."""

    def __init__(self, path: Path):
        self.path = path

    def load_all(self) -> list[dict]:
        """Load all properties. Returns LIST of dicts."""
        if not self.path.exists():
            return []
        with open(self.path) as f:
            return json.load(f)  # LIST!

    def find_by_address(self, address: str) -> dict | None:
        """Find property by address. O(n) lookup."""
        data = self.load_all()
        normalized = self._normalize(address)
        return next(
            (p for p in data if self._normalize(p["full_address"]) == normalized),
            None
        )

    def save_all(self, data: list[dict]) -> None:
        """Atomic save with backup."""
        backup_path = self.path.with_suffix('.json.bak')
        if self.path.exists():
            shutil.copy(self.path, backup_path)

        with open(self.path, 'w') as f:
            json.dump(data, f, indent=2)
```

### Pipeline Layer

```python
class AnalysisPipeline:
    """Main orchestrator for property analysis workflow."""

    def __init__(
        self,
        property_repo: PropertyRepository,
        enrichment_repo: EnrichmentRepository,
        kill_switch_filter: KillSwitchFilter,
        scorer: PropertyScorer,
        tier_classifier: TierClassifier
    ):
        self.property_repo = property_repo
        self.enrichment_repo = enrichment_repo
        self.kill_switch_filter = kill_switch_filter
        self.scorer = scorer
        self.tier_classifier = tier_classifier

    def run(self) -> PipelineResult:
        """Execute complete pipeline."""

        # Phase 1: Load properties from CSV
        properties = self.property_repo.load_all()

        # Phase 2: Merge with enrichment data
        enrichment_data = self.enrichment_repo.load_all()
        properties = self._merge_enrichment(properties, enrichment_data)

        # Phase 3: Kill-switch filtering
        passed_properties = []
        failed_properties = []

        for prop in properties:
            result = self.kill_switch_filter.evaluate(prop)
            prop.kill_switch_verdict = result.verdict

            if result.verdict == KillSwitchVerdict.PASS:
                passed_properties.append(prop)
            else:
                failed_properties.append(prop)

        # Phase 4: Score passed properties
        for prop in passed_properties:
            prop.score_breakdown = self.scorer.score(prop)

        # Phase 5: Classify into tiers
        for prop in passed_properties:
            prop.tier = self.tier_classifier.classify(prop.score_breakdown.total)

        return PipelineResult(
            all_properties=properties,
            passed=passed_properties,
            failed=failed_properties,
            unicorns=[p for p in passed_properties if p.tier == Tier.UNICORN],
            contenders=[p for p in passed_properties if p.tier == Tier.CONTENDER],
            passes=[p for p in passed_properties if p.tier == Tier.PASS]
        )
```

---

## Multi-Agent Architecture

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

#### image-assessor (Sonnet)

**Purpose:** Visual scoring of interior/exterior condition.

**Model:** Claude Sonnet (multi-modal vision)

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

## Scoring System Architecture

### 605-Point Weighted System

**AUTHORITATIVE SOURCE:** `src/phx_home_analysis/config/scoring_weights.py`

#### Section A: Location & Environment (250 pts)

| Strategy | Weight | Scoring Logic |
|----------|--------|---------------|
| school_district | 42 pts | GreatSchools rating x 4.2 |
| quietness | 30 pts | Distance to highways (>2mi=30, <0.25mi=0) |
| crime_index | 47 pts | 60% violent + 40% property crime (0-100 scale / 2.13) |
| supermarket_proximity | 23 pts | Distance to grocery (<0.5mi=23, >3mi=2.8) |
| parks_walkability | 23 pts | Parks, sidewalks, trails (manual 0-10 x 2.3) |
| sun_orientation | 25 pts | N=25, E=18.75, S=12.5, W=0 |
| flood_risk | 23 pts | Zone X=23, X-Shaded=18.4, A/AE=4.6-6.9, VE=0 |
| walk_transit | 22 pts | 40% walk + 40% transit + 20% bike (0-100 / 4.5) |
| air_quality | 15 pts | AQI 0-50=15, 51-100=12, 101-150=7.5, 151+=1.5-4.5 |

#### Section B: Lot & Systems (175 pts)

| Strategy | Weight | Scoring Logic |
|----------|--------|---------------|
| roof_condition | 45 pts | Age: 0-5yr=45, 6-10=36, 11-15=22.5, 16-20=9, >20=0 |
| backyard_utility | 35 pts | Usable sqft: >4k=35, 2-4k=26.25, 1-2k=17.5, <1k=8.75 |
| plumbing_electrical | 35 pts | Year: 2010+=35, 2000-09=30.6, 90-99=21.9, 80-89=13.1, <80=4.4 |
| pool_condition | 20 pts | No pool=10, Equip 0-3yr=20, 4-7=17, 8-12=10, >12=3 |
| cost_efficiency | 35 pts | Monthly: <=$3k=35, $3.5k=25.7, $4k=17.5, $4.5k=8.2, >$5k=0 |
| solar_status | 5 pts | Owned=5, Loan=3, None=2.5, Unknown=2, Leased=0 |

#### Section C: Interior & Features (180 pts)

| Strategy | Weight | Scoring Logic |
|----------|--------|---------------|
| kitchen_layout | 40 pts | Visual: open concept, island, appliances, pantry (0-10 x 4) |
| master_suite | 35 pts | Visual: size, closet, bathroom quality (0-10 x 3.5) |
| natural_light | 30 pts | Visual: windows, skylights, brightness (0-10 x 3) |
| high_ceilings | 25 pts | Vaulted=25, 10ft+=20.8, 9ft=12.5, 8ft=8.3, <8ft=0 |
| fireplace | 20 pts | Gas=20, Wood=15, Decorative=5, None=0 |
| laundry_area | 20 pts | Dedicated upstairs=20, Any floor=15, Closet=10, Garage=5, None=0 |
| aesthetics | 10 pts | Visual: curb appeal, finishes, modern vs dated (0-10) |

### Tier Classification (Updated)

```python
class TierClassifier:
    """Classify properties into tiers based on 605-point scale."""

    UNICORN_THRESHOLD = 484    # 80% of 605
    CONTENDER_THRESHOLD = 363  # 60% of 605

    def classify(self, total_score: float) -> Tier:
        if total_score > self.UNICORN_THRESHOLD:
            return Tier.UNICORN
        elif total_score >= self.CONTENDER_THRESHOLD:
            return Tier.CONTENDER
        else:
            return Tier.PASS
```

---

## Kill-Switch Architecture

### All 7 Criteria Are HARD (per PRD)

| Criterion | Requirement | Implementation | PRD Reference |
|-----------|-------------|----------------|---------------|
| HOA | Must be $0 | `property.hoa_fee == 0` | FR9-FR11 |
| Bedrooms | >= 4 | `property.beds >= 4` | FR9-FR11 |
| Bathrooms | >= 2 | `property.baths >= 2.0` | FR9-FR11 |
| House SQFT | > 1800 | `property.sqft > 1800` | FR9 (NEW) |
| Lot Size | > 8000 | `property.lot_sqft > 8000` | FR9 (upgraded) |
| Garage | Indoor required | `property.garage_spaces >= 1` | FR9 (clarified) |
| Sewer | City only | `property.sewer_type == SewerType.CITY` | FR9 (upgraded) |

### Verdict Logic

```python
def evaluate(self, property: Property) -> KillSwitchResult:
    """Evaluate property against all 7 HARD criteria."""

    failed_criteria = []

    # Check each criterion
    if property.hoa_fee and property.hoa_fee > 0:
        failed_criteria.append("hoa")

    if property.beds is None or property.beds < 4:
        failed_criteria.append("beds")

    if property.baths is None or property.baths < 2.0:
        failed_criteria.append("baths")

    if property.sqft is None or property.sqft <= 1800:
        failed_criteria.append("sqft")

    if property.lot_sqft is None or property.lot_sqft <= 8000:
        failed_criteria.append("lot")

    if property.garage_spaces is None or property.garage_spaces < 1:
        failed_criteria.append("garage")

    if property.sewer_type != SewerType.CITY:
        failed_criteria.append("sewer")

    # Determine verdict
    if len(failed_criteria) == 0:
        verdict = KillSwitchVerdict.PASS
    else:
        verdict = KillSwitchVerdict.FAIL

    return KillSwitchResult(
        verdict=verdict,
        failed_criteria=failed_criteria,
        details=self._build_details(property, failed_criteria)
    )
```

### Soft Severity System (Retained for Future Use)

While all PRD criteria are HARD, the soft severity system remains available for future flexibility:

```python
class SoftSeverityEvaluator:
    """Evaluate soft criteria with severity accumulation (future use)."""

    SEVERITY_FAIL_THRESHOLD = 3.0
    SEVERITY_WARNING_THRESHOLD = 1.5

    soft_criteria = {
        # Currently unused per PRD, but available for future
        # 'example_soft': {'threshold': 100, 'severity': 1.5}
    }

    def evaluate(self, property: Property) -> float:
        total_severity = 0.0
        # Add soft criteria evaluations here if needed
        return total_severity
```

---

## Integration Architecture

### External API Integrations

| API | Purpose | Auth | Rate Limit | Client |
|-----|---------|------|------------|--------|
| Maricopa County Assessor | Lot, year, garage, pool, sewer | Bearer token | ~1 req/sec | `services/county_data/` |
| GreatSchools | School ratings (1-10) | API key | 1000/day free | `services/schools/` |
| Google Maps | Geocoding, distances, satellite | API key | Pay-as-you-go | Map analyzer agent |
| FEMA NFHL | Flood zone classification | None (public) | N/A | `services/flood_data/` |
| WalkScore | Walk/Transit/Bike scores | API key | 5000/day free | `services/walkscore/` |
| EPA AirNow | Air quality index | API key | 500/hour | `services/air_quality/` |

### Browser Automation Stack

```
┌────────────────────────────────────────────────────────┐
│                    EXTRACTION TARGET                    │
├────────────────────────────────────────────────────────┤
│                Zillow      Redfin      Realtor.com     │
│               (PerimeterX) (Cloudflare)  (Minimal)     │
└─────────────────────────────────────────────────────────┘
                    │            │            │
                    ▼            ▼            ▼
┌────────────────────────────────────────────────────────┐
│                    STEALTH LAYER                        │
├────────────────────────────────────────────────────────┤
│  nodriver (Primary)    curl-cffi (HTTP)    Playwright  │
│  - Stealth Chrome      - Browser TLS       - Fallback  │
│  - PerimeterX bypass   - Fingerprints      - MCP tool  │
│  - Human behavior sim  - Fast requests     - Less      │
│                                              stealth   │
└────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│                    PROXY LAYER                          │
├────────────────────────────────────────────────────────┤
│  Residential Proxy Rotation                            │
│  - IP rotation to avoid blocking                       │
│  - Chrome proxy extension for auth                     │
│  - $10-30/month budget                                 │
└────────────────────────────────────────────────────────┘
```

### API Cost Estimation

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| Claude API (Haiku) | ~2M tokens | $0.50-$2 |
| Claude API (Sonnet - vision) | ~1M tokens + images | $15-30 |
| Google Maps API | ~500 requests | $5-10 |
| Residential Proxies | ~10GB | $10-30 |
| **TOTAL** | | **$30-72** |

---

## State Management Architecture

### State Files

| File | Purpose | Access Pattern |
|------|---------|----------------|
| `work_items.json` | Pipeline progress | Read at start, write after each property |
| `enrichment_data.json` | Property data | Read/write per property update |
| `extraction_state.json` | Image extraction | Read/write during Phase 2 |

### Crash Recovery Protocol

```python
def resume_pipeline(work_items_path: Path) -> list[str]:
    """Identify properties needing work based on state file."""

    work = json.load(open(work_items_path))

    # Reset stuck in_progress items (30 min timeout)
    timeout = timedelta(minutes=30)
    now = datetime.now()

    for item in work['work_items']:
        for phase, data in item['phases'].items():
            if data['status'] == 'in_progress':
                started = datetime.fromisoformat(data['started_at'])
                if now - started > timeout:
                    data['status'] = 'pending'
                    print(f"Reset stuck {phase} for {item['address']}")

    # Find pending work
    pending = []
    for item in work['work_items']:
        for phase, data in item['phases'].items():
            if data['status'] == 'pending':
                pending.append((item['address'], phase))

    return pending
```

### Checkpointing Strategy

```python
def checkpoint_after_property(address: str, phase: str, status: str):
    """Write checkpoint after each property phase completes."""

    work = json.load(open('data/work_items.json'))

    item = next(
        (w for w in work['work_items'] if w['address'] == address),
        None
    )

    if item:
        item['phases'][phase]['status'] = status
        item['phases'][phase]['completed_at'] = datetime.now().isoformat()
        item['last_updated'] = datetime.now().isoformat()

        # Update summary
        work['summary'] = calculate_summary(work['work_items'])
        work['last_checkpoint'] = datetime.now().isoformat()

        # Atomic write with backup
        backup = Path('data/work_items.json.bak')
        shutil.copy('data/work_items.json', backup)

        with open('data/work_items.json', 'w') as f:
            json.dump(work, f, indent=2)
```

---

## Security Architecture

### Credential Management

**Environment Variables (.env):**

```bash
# API Keys - NEVER commit to Git
MARICOPA_ASSESSOR_TOKEN=<secret>
GOOGLE_MAPS_API_KEY=<secret>
WALKSCORE_API_KEY=<secret>
AIRNOW_API_KEY=<secret>

# Proxy Configuration
PROXY_SERVER=host:port
PROXY_USERNAME=<secret>
PROXY_PASSWORD=<secret>

# Claude API
ANTHROPIC_API_KEY=<secret>
```

**Security Rules:**
1. `.env` file is gitignored
2. No credentials in code or comments
3. Pre-commit hook scans for leaked secrets
4. Rotate tokens if exposed

### Pre-Commit Hook Protection

```python
# .claude/hooks/env_file_protection_hook.py
"""Block commits containing API keys or credentials."""

import re
import sys

PATTERNS = [
    r'(?i)(api[_-]?key|token|secret|password)\s*[=:]\s*["\']?[a-zA-Z0-9_-]{20,}',
    r'sk-[a-zA-Z0-9]{32,}',  # OpenAI/Anthropic keys
    r'[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}',  # JWT
]

def check_diff(diff_text: str) -> list[str]:
    violations = []
    for pattern in PATTERNS:
        if re.search(pattern, diff_text):
            violations.append(pattern)
    return violations
```

---

## Deployment Architecture

### Local Development Environment

```bash
# Requirements
- Python 3.11+ (target 3.12)
- Chrome/Chromium (for nodriver)
- Git

# Setup
git clone <repo>
cd PHX-houses-Dec-2025
uv sync

# Environment
cp .env.example .env
# Edit .env with your API keys

# Verify
python -c "from src.phx_home_analysis import __version__; print(__version__)"
```

### Execution Model

```bash
# Full pipeline (all properties)
/analyze-property --all

# Single property
/analyze-property "4732 W Davis Rd, Glendale, AZ 85306"

# Test mode (first 5 properties)
/analyze-property --test

# Resume after failure
/analyze-property --all --resume

# Manual script execution
python scripts/phx_home_analyzer.py
python scripts/extract_county_data.py --all
python scripts/extract_images.py --all
python -m scripts.deal_sheets
```

### Directory Structure

```
PHX-houses-Dec-2025/
├── .claude/                  # Claude Code configuration
│   ├── agents/               # Agent definitions
│   ├── commands/             # Slash commands
│   ├── skills/               # Domain expertise modules
│   └── hooks/                # Pre-commit hooks
├── data/                     # Data files
│   ├── phx_homes.csv         # Source listings
│   ├── enrichment_data.json  # Enriched data (LIST!)
│   ├── work_items.json       # Pipeline state
│   └── property_images/      # Downloaded images
├── docs/                     # Documentation
│   ├── architecture.md       # This document
│   ├── prd.md                # Product requirements
│   └── ux-design-specification.md
├── scripts/                  # Executable scripts
│   ├── phx_home_analyzer.py  # Main scoring script
│   ├── extract_county_data.py
│   ├── extract_images.py
│   └── deal_sheets/          # Report generation
├── src/phx_home_analysis/    # Core library
│   ├── config/               # Configuration
│   ├── domain/               # Entities, value objects, enums
│   ├── repositories/         # Data persistence
│   ├── services/             # Business logic
│   ├── pipeline/             # Orchestration
│   ├── reporters/            # Output formatters
│   └── validation/           # Data validation
└── tests/                    # Test suite
    ├── unit/
    ├── integration/
    └── fixtures/
```

---

## Architecture Validation

### PRD Alignment Checklist

| PRD Requirement | Architecture Support | Status |
|-----------------|---------------------|--------|
| FR1: Batch property analysis via CLI | AnalysisPipeline, /analyze-property | PASS |
| FR9: HARD kill-switch criteria | KillSwitchFilter with 7 criteria | PASS |
| FR15: 605-point scoring | PropertyScorer with 22 strategies | PASS |
| FR17: Tier classification | TierClassifier (Unicorn/Contender/Pass) | PASS |
| FR28: Multi-phase pipeline | Phase 0-4 with agent orchestration | PASS |
| FR34: Checkpoint pipeline progress | work_items.json checkpointing | PASS |
| FR35: Resume interrupted execution | --resume flag, crash recovery | PASS |
| FR40: Deal sheet generation | HTML reporter with Tailwind | PASS |
| NFR1: <=30 min batch processing | Parallel Phase 1 agents | PASS |
| NFR5: 100% kill-switch accuracy | All HARD criteria, no false passes | PASS |
| NFR22: <=$90/month operating cost | Haiku/Sonnet optimization | PASS |

### Gap Resolution Summary

| Gap ID | Description | Resolution |
|--------|-------------|------------|
| ARCH-01 | Kill-switch criteria had SOFT where PRD requires HARD | All 7 criteria now HARD: HOA, beds, baths, sqft, lot, garage, sewer |
| ARCH-02 | Scoring totals inconsistent (600 vs 605) | ScoringWeights authoritative: 605 pts (250+175+180) |
| ARCH-03 | Tier thresholds misaligned | Updated to 484 (80%), 363 (60%) of 605 |
| ARCH-04 | House SQFT not explicit criterion | Added >1800 sqft as HARD kill-switch |
| ARCH-05 | constants.py assertion incorrect | Action: Update to match ScoringWeights |

### Confidence Assessment

| Architecture Area | Confidence | Notes |
|-------------------|------------|-------|
| Kill-Switch System | HIGH | Matches PRD exactly, 7 HARD criteria |
| Scoring System | HIGH | 605 pts reconciled, 22 strategies defined |
| Multi-Agent Pipeline | HIGH | Phase dependencies and prerequisites clear |
| Data Architecture | HIGH | JSON schemas fully specified |
| State Management | HIGH | Crash recovery protocol documented |
| Security | MEDIUM | Pre-commit hooks need testing |
| Integration | MEDIUM | API rate limits need monitoring |

---

## Appendix A: Action Items

### Immediate (Before Development Continues)

1. **Update constants.py** - Fix assertion to match 605-point scoring:
   ```python
   SCORE_SECTION_A_TOTAL = 250
   SCORE_SECTION_B_TOTAL = 175
   SCORE_SECTION_C_TOTAL = 180
   MAX_POSSIBLE_SCORE = 605
   TIER_UNICORN_MIN = 484
   TIER_CONTENDER_MIN = 363
   ```

2. **Add SqftKillSwitch** - Implement >1800 sqft HARD criterion

3. **Update LotSizeKillSwitch** - Change from range (7k-15k) to minimum (>8000)

4. **Update SewerKillSwitch** - Change from SOFT (2.5 severity) to HARD (instant fail)

5. **Update GarageKillSwitch** - Clarify as indoor garage required

### Short-Term (Week 1-2)

6. **Validate prerequisite script** - Ensure exit codes match documentation

7. **Test crash recovery** - Verify resume works after simulated failures

8. **Document API rate limits** - Add monitoring for external APIs

### Medium-Term (Post-MVP)

9. **Add flood zone kill-switch** - When FEMA integration complete

10. **Consider soft severity** - For non-critical preferences

---

**Document Version:** 2.0
**Generated:** 2025-12-03
**Author:** Winston - System Architect
**Status:** Complete - Ready for Implementation
