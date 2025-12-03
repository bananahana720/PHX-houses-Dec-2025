# PHX Houses Analysis Pipeline - System Architecture

## Table of Contents

1. [System Overview](#system-overview)
2. [Architectural Style](#architectural-style)
3. [Layer Architecture](#layer-architecture)
4. [Multi-Agent Orchestration](#multi-agent-orchestration)
5. [Data Architecture](#data-architecture)
6. [Scoring System Architecture](#scoring-system-architecture)
7. [Kill-Switch Architecture](#kill-switch-architecture)
8. [Image Extraction Architecture](#image-extraction-architecture)
9. [State Management](#state-management)
10. [Integration Points](#integration-points)
11. [Security Architecture](#security-architecture)
12. [Deployment Architecture](#deployment-architecture)

---

## System Overview

The PHX Houses Analysis Pipeline is a sophisticated data analysis system that evaluates Phoenix-area residential properties through a multi-phase pipeline combining automated data extraction, AI-powered visual analysis, and quantitative scoring.

###

 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES                        │
├─────────────────────────────────────────────────────────────────┤
│  Maricopa County    Zillow/Redfin    Google Maps    APIs        │
│  Assessor API       Listings         Geo Services   (External)  │
└──────┬──────────────────┬────────────────┬──────────────────┬───┘
       │                  │                │                  │
       └──────────┬───────┴────────┬───────┴──────────────────┘
                  │                │
        ┌─────────▼────────────────▼─────────┐
        │   EXTRACTION LAYER                 │
        │  - County Assessor Client          │
        │  - Stealth Browser Automation      │
        │  - Image Extractors (Zillow, etc.) │
        │  - Map Analysis Agents             │
        └──────────┬─────────────────────────┘
                   │
        ┌──────────▼─────────────────────────┐
        │   DATA INTEGRATION LAYER           │
        │  - Field Mappers                   │
        │  - Merge Strategies                │
        │  - Data Quality Metrics            │
        │  - Deduplication                   │
        └──────────┬─────────────────────────┘
                   │
        ┌──────────▼─────────────────────────┐
        │   BUSINESS LOGIC LAYER             │
        │  - Kill-Switch Filter              │
        │  - Property Scorer                 │
        │  - Tier Classifier                 │
        │  - Cost Estimator                  │
        └──────────┬─────────────────────────┘
                   │
        ┌──────────▼─────────────────────────┐
        │   PRESENTATION LAYER               │
        │  - Console Reporter                │
        │  - CSV Reporter                    │
        │  - HTML Reporter                   │
        │  - Deal Sheet Generator            │
        └────────────────────────────────────┘
```

---

## Architectural Style

### Primary Style: Domain-Driven Design (DDD)

The system follows DDD principles with clear separation between:

1. **Domain Layer** - Core business entities and logic
2. **Application Layer** - Use cases and orchestration
3. **Infrastructure Layer** - External service integration
4. **Presentation Layer** - Output formatting and reports

### Secondary Patterns

1. **Repository Pattern** - Abstract data access
2. **Strategy Pattern** - Composable scoring strategies
3. **Pipeline Pattern** - Sequential data transformation
4. **Multi-Agent Pattern** - Parallel AI task execution

---

## Layer Architecture

### 1. Domain Layer (`src/phx_home_analysis/domain/`)

**Purpose:** Define core business concepts independent of infrastructure.

**Components:**

#### Entities
- `Property` - Central domain entity with all property data
- `EnrichmentData` - Structured enrichment information container

#### Value Objects
- `Address` - Immutable address representation
- `Score` - Scoring results (raw score + tier)
- `ScoreBreakdown` - Detailed section scores
- `RiskAssessment` - Property risk evaluation
- `RenovationEstimate` - Renovation cost projections

#### Enums
- `Tier` - UNICORN, CONTENDER, PASS
- `Orientation` - NORTH, EAST, SOUTH, WEST, UNKNOWN
- `SewerType` - CITY, SEPTIC, UNKNOWN
- `SolarStatus` - OWNED, LEASED, NONE, UNKNOWN
- `RiskLevel` - LOW, MEDIUM, HIGH, CRITICAL
- `FloodZone` - X, A, AE, VE, etc.
- `CrimeRiskLevel` - VERY_LOW, LOW, MODERATE, HIGH, VERY_HIGH, UNKNOWN

**Design Decisions:**
- Entities are mutable dataclasses (modified during pipeline)
- Value objects are frozen (immutable)
- Enums provide type safety for categorical data

### 2. Service Layer (`src/phx_home_analysis/services/`)

**Purpose:** Implement business logic and coordinate domain operations.

**Service Modules:**

#### kill_switch/
- `KillSwitch` (abstract base class)
- `KillSwitchFilter` (orchestrator)
- Hard criteria: `NoHoaKillSwitch`, `MinBedroomsKillSwitch`, `MinBathroomsKillSwitch`
- Soft criteria: `CitySewerKillSwitch`, `MinGarageKillSwitch`, `LotSizeKillSwitch`, `NoNewBuildKillSwitch`

#### scoring/
- `PropertyScorer` (orchestrator applying all strategies)
- `ScoringStrategy` (abstract base class)
- Location strategies (8): School, Quietness, Crime, Supermarket, Parks, Orientation, Flood, WalkTransit, AirQuality
- Systems strategies (5): Roof, Backyard, Plumbing, Pool, CostEfficiency
- Interior strategies (7): Kitchen, Master, Light, Ceilings, Fireplace, Laundry, Aesthetics

#### cost_estimation/
- `CostEstimator` - Calculate monthly ownership costs
- `ArizonaCostRates` - AZ-specific cost rates and constants

#### image_extraction/
- `ImageExtractionOrchestrator` - Coordinate multi-source extraction
- `Deduplicator` - Perceptual hash-based dedup
- `Standardizer` - Image resizing and normalization
- `StateManager` - Resume capability for long-running extractions
- Extractors: `ZillowExtractor`, `RedfinExtractor`, `PhoenixMLSExtractor`, `MaricopaAssessorExtractor`

#### data_integration/
- `FieldMapper` - Map fields across different data sources
- `MergeStrategy` - Strategies for handling conflicts during merge
- `EnrichmentMerger` - Merge CSV + JSON + API data

#### quality/
- `QualityMetrics` - Calculate data completeness and accuracy scores
- `LineageTracker` - Track data provenance (which source provided which field)
- `ConfidenceScorer` - Assign confidence scores to enriched fields

**Design Decisions:**
- Strategy pattern allows easy addition of new scoring criteria
- Services are composable and testable in isolation
- State management enables crash recovery for long-running extractions

### 3. Repository Layer (`src/phx_home_analysis/repositories/`)

**Purpose:** Abstract data persistence to decouple from storage mechanism.

**Components:**

#### Base Classes
- `PropertyRepository` (abstract) - Interface for property data access
- `EnrichmentRepository` (abstract) - Interface for enrichment data access

#### Implementations
- `CsvPropertyRepository` - Read/write CSV listings (`phx_homes.csv`)
- `JsonEnrichmentRepository` - Read/write JSON enrichment (`enrichment_data.json`)

**Methods:**
```python
class PropertyRepository(ABC):
    def load_all() -> list[Property]
    def load_by_address(address: str) -> Property | None
    def save_all(properties: list[Property]) -> None

class EnrichmentRepository(ABC):
    def load_all() -> list[dict]  # enrichment_data.json is a LIST!
    def save_all(data: list[dict]) -> None
    def find_by_address(address: str) -> dict | None
```

**Design Decisions:**
- Repository pattern enables future database migration without changing business logic
- LIST-based JSON structure chosen for simplicity (iterable, no key collisions)
- All file I/O happens through repositories (testable with mocks)

### 4. Pipeline Layer (`src/phx_home_analysis/pipeline/`)

**Purpose:** Orchestrate the complete analysis workflow.

**Components:**

#### AnalysisPipeline
Main orchestrator coordinating all phases:

```python
class AnalysisPipeline:
    def __init__(self,
        property_repo: PropertyRepository,
        enrichment_repo: EnrichmentRepository,
        kill_switch_filter: KillSwitchFilter,
        scorer: PropertyScorer,
        tier_classifier: TierClassifier
    )

    def run(self) -> PipelineResult:
        """Execute complete pipeline: load → enrich → filter → score → classify"""

        # Phase 1: Load
        properties = self.property_repo.load_all()

        # Phase 2: Enrich
        enrichment_data = self.enrichment_repo.load_all()
        properties = self.merge_enrichment(properties, enrichment_data)

        # Phase 3: Filter (Kill-Switch)
        passed_properties = []
        for prop in properties:
            verdict = self.kill_switch_filter.evaluate(prop)
            if verdict in [Verdict.PASS, Verdict.WARNING]:
                passed_properties.append(prop)

        # Phase 4: Score
        for prop in passed_properties:
            prop.score_breakdown = self.scorer.score(prop)

        # Phase 5: Classify
        for prop in passed_properties:
            prop.tier = self.tier_classifier.classify(prop.score_breakdown.total)

        return PipelineResult(properties, passed_properties)
```

#### PipelineResult
Container for pipeline output with summary statistics.

**Design Decisions:**
- Pipeline is sequential for clarity (future: parallelize scoring)
- Dependency injection for all services (testable)
- Immutable result object (prevents accidental mutation)

### 5. Validation Layer (`src/phx_home_analysis/validation/`)

**Purpose:** Ensure data quality and consistency.

**Components:**

#### schemas.py
Pydantic schemas for strict data validation:
- `PropertySchema` - Validate property data
- `EnrichmentSchema` - Validate enrichment data
- `ListingSchema` - Validate listing fields
- `LocationSchema` - Validate location fields

#### validators.py
Custom validation logic:
- `AddressValidator` - Validate and normalize addresses
- `PriceValidator` - Validate price formats
- `DateValidator` - Validate dates and year_built

#### normalizer.py
Data normalization functions:
- `normalize_address()` - Standardize address format
- `infer_type()` - Infer data types from strings
- `clean_whitespace()` - Remove extra whitespace

#### deduplication.py
Hash-based duplicate detection:
- `AddressHasher` - Hash addresses for dedup
- `ImageHasher` - Perceptual hashing for image dedup

**Design Decisions:**
- Pydantic provides strong type checking at runtime
- Normalization happens before validation
- Deduplication uses hashing for O(1) lookups

### 6. Reporting Layer (`src/phx_home_analysis/reporters/`)

**Purpose:** Format and output analysis results.

**Components:**

- `ConsoleReporter` - Print results to terminal
- `CsvReporter` - Export to CSV (ranked list)
- `HtmlReporter` - Generate interactive HTML reports
- `DealSheetGenerator` - Per-property summary sheets

**Design Decisions:**
- Reporter pattern allows multiple output formats from same data
- Jinja2 templates for HTML generation
- CSV format matches input format for easy comparison

---

## Multi-Agent Orchestration

### Claude Code Multi-Agent System

The `.claude/` directory defines a multi-agent AI system for parallel data extraction:

#### Agent Definitions (`.claude/agents/`)

1. **listing-browser.md** (Claude Haiku)
   - **Purpose:** Extract listing data from Zillow/Redfin
   - **Tools:** Stealth browsers (nodriver), HTTP clients
   - **Outputs:** Price, beds, baths, HOA, images
   - **Duration:** ~30-60s per property
   - **Skills:** listing-extraction, property-data, state-management

2. **map-analyzer.md** (Claude Haiku)
   - **Purpose:** Geographic analysis
   - **Tools:** Google Maps API, GreatSchools, crime data
   - **Outputs:** School ratings, safety scores, orientation, distances
   - **Duration:** ~45-90s per property
   - **Skills:** map-analysis, property-data, arizona-context

3. **image-assessor.md** (Claude Sonnet 4.5)
   - **Purpose:** Visual scoring of interior quality
   - **Tools:** Claude Vision (multimodal)
   - **Outputs:** Section C scores (kitchen, master, light, etc.)
   - **Duration:** ~2-5 min per property
   - **Skills:** image-assessment, property-data, arizona-context-lite
   - **Prerequisites:** Phase 1 complete, images downloaded

#### Skill Modules (`.claude/skills/`)

Skills provide reusable domain expertise:

- `property-data/` - Load/query/update property data
- `state-management/` - Checkpointing and crash recovery
- `kill-switch/` - Buyer criteria validation
- `scoring/` - 600-point scoring system
- `county-assessor/` - Maricopa County API
- `arizona-context/` - AZ-specific factors
- `listing-extraction/` - Browser automation
- `map-analysis/` - Geographic data extraction
- `image-assessment/` - Visual scoring rubrics
- `deal-sheets/` - Report generation
- `visualizations/` - Charts and plots

#### Phase Dependencies

```
Phase 0: County API (independent)
    ↓
Phase 1a: listing-browser ┐
Phase 1b: map-analyzer     ├─ (parallel)
    ↓                      ↓
    └──────┬───────────────┘
           ↓
    [Prerequisites validation]
           ↓
Phase 2: image-assessor (requires Phase 1 complete)
    ↓
Phase 3: Synthesis (scoring, tier, verdict)
    ↓
Phase 4: Reports
```

**Critical Rule:** ALWAYS validate prerequisites before spawning Phase 2 agents using `scripts/validate_phase_prerequisites.py`.

---

## Data Architecture

### Data Storage Strategy

#### Files
- `data/phx_homes.csv` - Source listing data (address, price, beds, baths)
- `data/enrichment_data.json` - Enriched property data (LIST of dicts!)
- `data/work_items.json` - Pipeline state tracking
- `data/field_lineage.json` - Data provenance tracking

#### Data Flow

```
CSV Listings (phx_homes.csv)
    ↓
CsvPropertyRepository.load_all()
    ↓
Property entities (domain)
    ↓
Merge with enrichment_data.json
    ↓
Enriched Property entities
    ↓
Kill-Switch Filter
    ↓
Property Scorer
    ↓
Tier Classifier
    ↓
Reporters (CSV, HTML, Console)
```

### Critical Data Structure: enrichment_data.json

**IMPORTANT:** `enrichment_data.json` is a **LIST** of property dictionaries, NOT a dict keyed by address!

```json
[
  {
    "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
    "lot_sqft": 10500,
    "year_built": 2006,
    "listing": {
      "price": 475000,
      "beds": 4,
      "baths": 2.0
    },
    "location": {
      "school_rating": 8,
      "orientation": "north"
    }
  },
  {
    "full_address": "Another Address...",
    ...
  }
]
```

**Access Pattern:**
```python
# CORRECT
data = json.load(open('data/enrichment_data.json'))  # List[Dict]
prop = next((p for p in data if p["full_address"] == address), None)

# WRONG
prop = data[address]  # TypeError: list indices must be integers
```

### State Management Files

#### work_items.json Structure
```json
{
  "session": {
    "session_id": "abc123...",
    "started_at": "2025-12-03T10:00:00Z",
    "current_phase": "phase2_images",
    "mode": "all"
  },
  "work_items": [
    {
      "address": "4732 W Davis Rd, Glendale, AZ 85306",
      "phases": {
        "phase0_county": {
          "status": "completed",
          "completed_at": "..."
        },
        "phase1_listing": {
          "status": "completed",
          "completed_at": "..."
        },
        "phase2_images": {
          "status": "in_progress",
          "started_at": "..."
        }
      },
      "last_updated": "..."
    }
  ],
  "summary": {
    "total": 50,
    "completed": 35,
    "in_progress": 10,
    "failed": 5
  }
}
```

---

## Scoring System Architecture

### 600-Point Weighted System

#### Section A: Location & Environment (250 pts)

**Strategy Pattern Implementation:**

```python
class ScoringStrategy(ABC):
    @abstractmethod
    def score(self, property: Property) -> float:
        """Return score 0-10 (strategy calculates raw, weight applied by scorer)"""
        pass

# Example: School District Scorer
class SchoolDistrictScorer(ScoringStrategy):
    def score(self, property: Property) -> float:
        if property.school_rating is None:
            return 5.0  # Neutral default
        return property.school_rating  # Already 0-10 scale (GreatSchools)

# Scorer applies weight: 42 pts max
raw_score = SchoolDistrictScorer().score(prop)  # 8.0
weighted_score = raw_score * (42 / 10)  # 33.6 pts
```

**Location Strategies:**
1. `SchoolDistrictScorer` (42pts) - GreatSchools rating × 4.2
2. `QuietnessScorer` (30pts) - Distance to highways
3. `CrimeIndexScorer` (47pts) - 60% violent + 40% property crime
4. `SupermarketScorer` (23pts) - Distance to grocery
5. `ParksWalkabilityScorer` (23pts) - Parks, sidewalks, trails
6. `OrientationScorer` (25pts) - Sun orientation impact
7. `FloodRiskScorer` (23pts) - FEMA flood zones
8. `WalkTransitScorer` (22pts) - Walk/Transit/Bike Score
9. `AirQualityScorer` (15pts) - EPA AQI

#### Section B: Lot & Systems (170 pts)

**Systems Strategies:**
1. `RoofConditionScorer` (45pts) - Age-based condition
2. `BackyardUtilityScorer` (35pts) - Usable backyard space
3. `PlumbingElectricalScorer` (35pts) - Age-based infrastructure
4. `PoolConditionScorer` (20pts) - Pool equipment age
5. `CostEfficiencyScorer` (35pts) - Monthly cost vs target

#### Section C: Interior & Features (180 pts)

**Interior Strategies:**
1. `KitchenLayoutScorer` (40pts) - Visual inspection
2. `MasterSuiteScorer` (35pts) - Bedroom, closet, bathroom
3. `NaturalLightScorer` (30pts) - Windows, skylights
4. `HighCeilingsScorer` (25pts) - Ceiling height
5. `FireplaceScorer` (20pts) - Presence and quality
6. `LaundryAreaScorer` (20pts) - Location and quality
7. `AestheticsScorer` (10pts) - Overall visual appeal

### Tier Classification

```python
class TierClassifier:
    def classify(self, total_score: float) -> Tier:
        if total_score > 480:  # 80% of 600
            return Tier.UNICORN
        elif total_score >= 360:  # 60-80% of 600
            return Tier.CONTENDER
        else:  # < 60% of 600
            return Tier.PASS
```

---

## Kill-Switch Architecture

### Two-Tier Filtering System

#### Hard Criteria (Instant Fail)
```python
class NoHoaKillSwitch(KillSwitch):
    def evaluate(self, property: Property) -> bool:
        if property.hoa_fee is None:
            return True  # Assume no HOA if missing
        return property.hoa_fee == 0  # MUST be $0

class MinBedroomsKillSwitch(KillSwitch):
    def evaluate(self, property: Property) -> bool:
        return property.beds >= 4  # MUST have 4+ bedrooms

class MinBathroomsKillSwitch(KillSwitch):
    def evaluate(self, property: Property) -> bool:
        return property.baths >= 2.0  # MUST have 2+ bathrooms
```

#### Soft Criteria (Severity Accumulation)
```python
class CitySewerKillSwitch(KillSwitch):
    def evaluate(self, property: Property) -> bool:
        return property.sewer_type == SewerType.CITY

    def severity(self, property: Property) -> float:
        if self.evaluate(property):
            return 0.0  # Passes, no severity
        return 2.5  # Septic adds 2.5 severity

class MinGarageKillSwitch(KillSwitch):
    def evaluate(self, property: Property) -> bool:
        if property.garage_spaces is None:
            return True  # Assume has garage if missing
        return property.garage_spaces >= 2

    def severity(self, property: Property) -> float:
        if self.evaluate(property):
            return 0.0
        return 1.5  # < 2 spaces adds 1.5 severity
```

### Verdict Logic
```python
class KillSwitchFilter:
    def evaluate(self, property: Property) -> KillSwitchVerdict:
        # Check HARD criteria first
        for switch in self.hard_switches:
            if not switch.evaluate(property):
                return KillSwitchVerdict.FAIL  # Instant fail

        # Accumulate SOFT severity
        total_severity = 0.0
        for switch in self.soft_switches:
            total_severity += switch.severity(property)

        # Apply threshold
        if total_severity >= 3.0:  # SEVERITY_FAIL_THRESHOLD
            return KillSwitchVerdict.FAIL
        elif total_severity >= 1.5:  # SEVERITY_WARNING_THRESHOLD
            return KillSwitchVerdict.WARNING
        else:
            return KillSwitchVerdict.PASS
```

---

## Image Extraction Architecture

### Stealth Browser Automation

#### Problem: Bot Detection
Zillow and Redfin use PerimeterX to detect automated browsers. Standard Playwright is detected and blocked.

#### Solution: Stealth Stack
1. **nodriver** - Stealth Chrome automation (bypasses PerimeterX)
2. **curl-cffi** - HTTP client with browser TLS fingerprinting
3. **Playwright** - Fallback for Realtor.com (less aggressive detection)

#### Architecture

```
┌────────────────────────────────────────┐
│  ImageExtractionOrchestrator           │
│  - Coordinates multi-source extraction │
│  - Manages extraction state            │
│  - Handles retries and errors          │
└─────────┬──────────────────────────────┘
          │
          ├─→ ZillowExtractor (nodriver)
          ├─→ RedfinExtractor (nodriver)
          ├─→ PhoenixMLSExtractor (Playwright)
          └─→ MaricopaAssessorExtractor (HTTP)
                  ↓
          ┌───────▼──────────┐
          │  Deduplicator    │
          │  - Perceptual    │
          │    hash (pHash)  │
          │  - Hamming dist  │
          └───────┬──────────┘
                  ↓
          ┌───────▼──────────┐
          │  Standardizer    │
          │  - Resize 1024px │
          │  - PNG format    │
          └───────┬──────────┘
                  ↓
          data/property_images/processed/
```

#### Deduplication Strategy

**Perceptual Hashing (pHash):**
```python
import imagehash
from PIL import Image

def compute_hash(image_path: Path) -> str:
    image = Image.open(image_path)
    phash = imagehash.phash(image)
    return str(phash)

def is_duplicate(hash1: str, hash2: str, threshold: int = 8) -> bool:
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    hamming_distance = h1 - h2
    return hamming_distance <= threshold
```

**Why pHash?**
- Robust to resizing, compression, color adjustments
- Fast comparison (64-bit hashes, Hamming distance)
- Threshold of 8 allows minor variations

#### State Management

**Resume Capability:**
```json
{
  "4732 W Davis Rd, Glendale, AZ 85306": {
    "status": "in_progress",
    "sources": {
      "zillow": {
        "status": "completed",
        "images_downloaded": 45,
        "last_updated": "2025-12-03T10:15:00Z"
      },
      "redfin": {
        "status": "in_progress",
        "images_downloaded": 12,
        "last_updated": "2025-12-03T10:20:00Z"
      }
    }
  }
}
```

Extraction can resume after crashes by checking state file.

---

## State Management

### work_items.json - Pipeline Progress Tracking

**Purpose:** Track multi-phase pipeline execution across sessions.

**Key Features:**
- Session metadata (ID, start time, mode)
- Per-property phase status (pending, in_progress, completed, failed, skipped)
- Summary counters (total, completed, in_progress, failed)
- Last updated timestamps

**Access Pattern:**
```python
import json

work_items = json.load(open('data/work_items.json'))
session = work_items['session']
items = work_items['work_items']

# Find property
prop = next((w for w in items if w['address'] == address), None)

# Check phase status
if prop['phases']['phase1_listing']['status'] == 'completed':
    # Ready for Phase 2
    pass

# Update status
prop['phases']['phase2_images']['status'] = 'in_progress'
prop['last_updated'] = datetime.now().isoformat()
json.dump(work_items, open('data/work_items.json', 'w'), indent=2)
```

### Staleness Protocol

**Problem:** Stale state files lead to incorrect assumptions about what work is complete.

**Solution:** Timestamp-based staleness checks.

```python
from datetime import datetime, timedelta

def is_stale(timestamp_str: str, threshold_hours: int = 24) -> bool:
    timestamp = datetime.fromisoformat(timestamp_str)
    age = datetime.now() - timestamp
    return age.total_seconds() > (threshold_hours * 3600)

# Check before using state
if is_stale(prop['last_updated'], threshold_hours=12):
    print(f"WARNING: State is stale ({prop['last_updated']})")
    # Prompt user to refresh or proceed with caution
```

### Crash Recovery

**Timeout Detection:**
```python
for prop in work_items['work_items']:
    for phase, data in prop['phases'].items():
        if data['status'] == 'in_progress':
            if 'started_at' in data:
                if is_stale(data['started_at'], threshold_hours=0.5):  # 30 min timeout
                    print(f"⚠️  Resetting stuck {phase} for {prop['address']}")
                    data['status'] = 'pending'
```

---

## Integration Points

### External APIs

#### Maricopa County Assessor API
- **Purpose:** Lot size, year built, garage spaces, pool
- **Authentication:** Bearer token (`MARICOPA_ASSESSOR_TOKEN`)
- **Rate Limit:** Unknown (conservative: 1 req/sec)
- **Client:** `src/phx_home_analysis/services/county_data/assessor_client.py`

#### GreatSchools API
- **Purpose:** School ratings (1-10 scale)
- **Authentication:** API key
- **Rate Limit:** 1000 req/day (free tier)
- **Client:** `src/phx_home_analysis/services/schools/`

#### Google Maps API
- **Purpose:** Geocoding, distances, orientation
- **Authentication:** API key
- **Rate Limit:** Pay-as-you-go
- **Client:** Used by map-analyzer agent

#### FEMA Flood API
- **Purpose:** Flood zone classification
- **Authentication:** None (public)
- **Client:** `src/phx_home_analysis/services/flood_data/`

#### WalkScore API
- **Purpose:** Walk/Transit/Bike Scores
- **Authentication:** API key
- **Rate Limit:** 5000 req/day (free tier)
- **Client:** `src/phx_home_analysis/services/walkscore/`

### Web Scraping (Stealth)

#### Zillow
- **Method:** nodriver (stealth Chrome)
- **Detection:** PerimeterX bot detection
- **Bypass:** TLS fingerprinting, human behavior simulation
- **Data:** Images, price, beds, baths, description

#### Redfin
- **Method:** nodriver (stealth Chrome)
- **Detection:** Cloudflare bot detection
- **Bypass:** Similar to Zillow
- **Data:** Images, listing details

#### Realtor.com
- **Method:** Playwright (less aggressive detection)
- **Detection:** Minimal
- **Data:** Listing details

---

## Security Architecture

### Credential Management

**Environment Variables:**
```bash
# API Keys
MARICOPA_ASSESSOR_TOKEN=<secret>
GOOGLE_MAPS_API_KEY=<secret>
WALKSCORE_API_KEY=<secret>

# Proxy (optional)
PROXY_SERVER=host:port
PROXY_USERNAME=<secret>
PROXY_PASSWORD=<secret>
```

**Never in Code:**
- No hardcoded API keys
- No credentials in Git history
- `.env` file gitignored

### Pre-Commit Hooks

**Credential Protection Hook:**
```bash
# .claude/hooks/env_file_protection_hook.py
# Blocks commits that add API keys or credentials
```

**Runs on:** `git commit`
**Prevents:** Accidental credential commits

### Proxy Support

**Purpose:** Rotate IP addresses to avoid rate limiting/blocking.

**Configuration:**
```python
from src.phx_home_analysis.config.settings import StealthExtractionConfig

config = StealthExtractionConfig.from_env()
proxy_url = config.proxy_url  # http://user:pass@host:port
```

**Proxy Extension:**
```python
# src/phx_home_analysis/services/infrastructure/proxy_extension_builder.py
# Builds Chrome extension for proxy authentication
```

---

## Deployment Architecture

### Local Development

**Requirements:**
- Python 3.11+
- Chrome/Chromium (for stealth automation)
- Virtual display (optional, for browser isolation)

**Setup:**
```bash
# Install dependencies
uv sync

# Set environment variables
export MARICOPA_ASSESSOR_TOKEN=<token>

# Run pipeline
python scripts/phx_home_analyzer.py
```

### Production Considerations

**If scaling to production:**

1. **Database Migration**
   - Replace JSON/CSV with PostgreSQL
   - Implement connection pooling
   - Add database migrations (Alembic)

2. **API Layer**
   - Add REST API (FastAPI)
   - Add authentication (JWT)
   - Add rate limiting

3. **Async Processing**
   - Use Celery for background tasks
   - Add Redis for task queue
   - Implement retry logic

4. **Monitoring**
   - Add structured logging (Logstash)
   - Add metrics (Prometheus)
   - Add alerting (PagerDuty)

5. **Deployment**
   - Containerize with Docker
   - Orchestrate with Kubernetes
   - Add CI/CD (GitHub Actions)

---

## Architecture Decisions

### Why DDD?

**Pros:**
- Clear separation of concerns
- Business logic independent of infrastructure
- Testable in isolation

**Cons:**
- More boilerplate than simpler approaches
- Requires discipline to maintain boundaries

**Verdict:** Worth it for a complex system with evolving requirements.

### Why Strategy Pattern for Scoring?

**Pros:**
- Easy to add new scoring criteria
- Each strategy testable independently
- Composable (can enable/disable strategies)

**Cons:**
- More classes than a single monolithic scorer

**Verdict:** Essential for maintainability and extensibility.

### Why LIST for enrichment_data.json?

**Pros:**
- Simple iteration
- No key collision issues
- Easy to append new properties

**Cons:**
- O(n) lookup by address (not O(1) like dict)

**Verdict:** Acceptable for small datasets (<1000 properties). Migrate to database for production scale.

### Why Multi-Agent AI?

**Pros:**
- Parallel execution (faster than sequential)
- Specialized models (Haiku for speed, Sonnet for vision)
- Crash recovery (restart failed phases only)

**Cons:**
- More complex orchestration
- Higher Claude API costs

**Verdict:** Worth it for time savings and quality of visual analysis.

---

**Document Version:** 1.0
**Generated:** 2025-12-03
**Last Updated:** 2025-12-03
