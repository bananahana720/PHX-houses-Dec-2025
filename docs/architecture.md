# PHX Houses - Architecture Documentation

**Generated:** 2025-12-05
**Project Type:** Backend Data Pipeline
**Architecture Pattern:** Domain-Driven Design (DDD)

---

## Architectural Overview

PHX Houses Analysis Pipeline implements a **Domain-Driven Design** architecture with clear separation between:

- **Domain Layer** - Business entities, value objects, enums
- **Service Layer** - Business logic, scoring, filtering
- **Repository Layer** - Data persistence abstraction
- **Pipeline Layer** - Orchestration and coordination
- **Infrastructure Layer** - Cross-cutting concerns (HTTP, browser, proxy)

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │
│  │ scripts/*.py│  │.claude/agents│  │ Typer CLI  │                 │
│  └─────────────┘  └─────────────┘  └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PIPELINE LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                   PhaseCoordinator                            │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │  │
│  │  │Phase 0  │→│Phase 1  │→│Phase 2  │→│Phase 3  │→│Phase 4  │ │  │
│  │  │County   │ │Listing  │ │Images   │ │Synthesis│ │Reports  │ │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │ ProgressReporter│  │  ResumePipeline │  │AnalysisPipeline │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         SERVICE LAYER                               │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    ANALYSIS SERVICES                         │   │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │   │
│  │ │KillSwitch   │ │PropertyScorer│ │TierClassifier          │ │   │
│  │ │Filter       │ │(18 strategies)│ │(Unicorn/Contender/Pass)│ │   │
│  │ └─────────────┘ └─────────────┘ └─────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    DATA SERVICES                             │   │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐ │   │
│  │ │Schools   │ │GoogleMaps│ │FloodData │ │ImageExtraction   │ │   │
│  │ │Client    │ │Client    │ │Client    │ │Orchestrator      │ │   │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DOMAIN LAYER                                │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │    Property     │  │  ScoreBreakdown │  │   Enums         │     │
│  │  (Aggregate     │  │  (Value Object) │  │ Tier, Orientation│    │
│  │   Root)         │  │   605 points    │  │ SolarStatus...  │     │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      REPOSITORY LAYER                               │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│  │CsvPropertyRepo  │  │JsonEnrichmentRepo│  │WorkItemsRepo    │    │
│  │(phx_homes.csv)  │  │(enrichment.json) │  │(work_items.json)│    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                             │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐   │
│  │ StealthHTTP   │  │ BrowserPool   │  │ ProxyManager          │   │
│  │ Client        │  │ (Playwright)  │  │ (Residential Proxies) │   │
│  └───────────────┘  └───────────────┘  └───────────────────────┘   │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────────────┐   │
│  │ nodriver      │  │ curl-cffi     │  │ File Lock             │   │
│  │ (Zillow)      │  │ (Anti-detect) │  │ (Concurrent Safety)   │   │
│  └───────────────┘  └───────────────┘  └───────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline Phases

The analysis pipeline executes in **5 phases** with checkpointing:

### Phase 0: County Data
- **Source:** Maricopa County Assessor API
- **Data:** Lot size, year built, garage spaces, sewer type
- **Output:** Updates `enrichment_data.json`

### Phase 1: Listing + Maps (Parallel)
- **Listing:** Zillow/Redfin extraction via nodriver
- **Maps:** Google Maps distance calculations
- **Schools:** GreatSchools API ratings
- **Output:** Images, HOA, school ratings, distances

### Phase 2: Image Analysis
- **Source:** Downloaded property images
- **Analysis:** Exterior assessment (roof, pool, HVAC)
- **Scoring:** Interior scoring via Claude Vision
- **Output:** Section C scores (180 points)

### Phase 3: Synthesis
- **Kill-Switch:** Apply 8 HARD criteria
- **Scoring:** Calculate 605-point score
- **Classification:** Assign tier (Unicorn/Contender/Pass)
- **Output:** Final property rankings

### Phase 4: Reports
- **Deal Sheets:** Per-property HTML summaries
- **Dashboards:** Interactive maps and charts
- **Exports:** CSV rankings

---

## Domain Model

### Aggregate Root: Property

```python
@dataclass
class Property:
    # Address (5 fields)
    street: str
    city: str
    state: str
    zip_code: str
    full_address: str

    # Listing (6 fields)
    price: str
    price_num: int | None
    beds: int
    baths: float
    sqft: int
    price_per_sqft_raw: float

    # County Data (5 fields)
    lot_sqft: int | None
    year_built: int | None
    garage_spaces: int | None
    sewer_type: SewerType | None
    tax_annual: float | None

    # Analysis Results
    kill_switch_passed: bool
    kill_switch_failures: list[str]
    score_breakdown: ScoreBreakdown | None
    tier: Tier | None
```

### Value Objects

| Object | Purpose | Immutable |
|--------|---------|-----------|
| `Address` | Normalized address | Yes |
| `Score` | Weighted score with percentage | Yes |
| `ScoreBreakdown` | 605-point breakdown (A/B/C) | Yes |
| `RiskAssessment` | Risk level and description | Yes |
| `PerceptualHash` | Image deduplication hash | Yes |

### Enums

| Enum | Values | Purpose |
|------|--------|---------|
| `Tier` | UNICORN, CONTENDER, PASS | Classification |
| `Orientation` | N, NE, E, SE, S, SW, W, NW | Sun exposure |
| `SolarStatus` | OWNED, LEASED, NONE | Solar panel status |
| `SewerType` | CITY, SEPTIC, UNKNOWN | Sewer connection |
| `FloodZone` | X, A, AE, AH, VE | FEMA flood zones |

---

## Kill-Switch Architecture

All 8 criteria are **HARD** (instant fail):

```python
class KillSwitchFilter:
    criteria = [
        HOACriterion(),      # hoa_fee == 0
        BedsCriterion(),     # beds >= 4
        BathsCriterion(),    # baths >= 2
        SqftCriterion(),     # sqft > 1800
        LotCriterion(),      # lot_sqft > 8000
        GarageCriterion(),   # garage_spaces >= 1
        SewerCriterion(),    # sewer_type == CITY
        YearCriterion(),     # year_built <= 2024
    ]

    def evaluate(self, property: Property) -> KillSwitchResult:
        failures = []
        for criterion in self.criteria:
            if not criterion.passes(property):
                failures.append(criterion.failure_message())
        return KillSwitchResult(
            passed=len(failures) == 0,
            failures=failures
        )
```

---

## Scoring Architecture

### Strategy Pattern (18 Strategies)

```python
class PropertyScorer:
    strategies = {
        # Section A: Location (250 pts)
        'school_rating': SchoolRatingStrategy(max_pts=50),
        'crime_safety': CrimeSafetyStrategy(max_pts=40),
        'orientation': OrientationStrategy(max_pts=30),
        'walk_score': WalkScoreStrategy(max_pts=30),
        # ... 3 more

        # Section B: Systems (175 pts)
        'roof_condition': RoofConditionStrategy(max_pts=40),
        'hvac_age': HVACStrategy(max_pts=35),
        # ... 2 more

        # Section C: Interior (180 pts)
        'kitchen_quality': KitchenStrategy(max_pts=40),
        'master_suite': MasterSuiteStrategy(max_pts=30),
        # ... 5 more
    }

    def score(self, property: Property) -> ScoreBreakdown:
        section_a = sum(s.score(property) for s in self.section_a_strategies)
        section_b = sum(s.score(property) for s in self.section_b_strategies)
        section_c = sum(s.score(property) for s in self.section_c_strategies)
        return ScoreBreakdown(
            section_a=section_a,  # max 250
            section_b=section_b,  # max 175
            section_c=section_c,  # max 180
            total=section_a + section_b + section_c  # max 605
        )
```

---

## Repository Pattern

### Base Interface

```python
class PropertyRepository(Protocol):
    def load_all(self) -> list[Property]: ...
    def save_all(self, properties: list[Property]) -> None: ...
    def find_by_address(self, address: str) -> Property | None: ...
```

### Implementations

| Repository | File Format | Purpose |
|------------|-------------|---------|
| `CsvPropertyRepository` | CSV | Listing data |
| `JsonEnrichmentRepository` | JSON | Enrichment data |
| `WorkItemsRepository` | JSON | Pipeline state |

---

## Error Handling

### Classification

```python
def is_transient_error(error: Exception) -> bool:
    """Classify errors as transient (retryable) or permanent."""
    transient_types = (
        httpx.TimeoutException,
        httpx.ConnectError,
        RateLimitError,
    )
    return isinstance(error, transient_types)
```

### Retry Decorator

```python
@retry_with_backoff(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    exponential=True
)
async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```

---

## Configuration

### AppConfig

```python
@dataclass
class AppConfig:
    # Paths
    base_dir: Path
    data_dir: Path
    reports_dir: Path

    # Scoring
    scoring_weights: ScoringWeights
    tier_thresholds: TierThresholds

    # Kill-switch
    kill_switch_criteria: list[str]

    # External APIs
    assessor_token: str | None
    greatschools_api_key: str | None
```

### Environment Overrides

```bash
# .env file
MARICOPA_ASSESSOR_TOKEN=...
GREATSCHOOLS_API_KEY=...
PROXY_HOST=...
PROXY_USER=...
PROXY_PASS=...
```

---

## Testing Strategy

| Test Type | Location | Purpose |
|-----------|----------|---------|
| Unit | `tests/unit/` | Individual component tests |
| Integration | `tests/integration/` | Cross-component tests |
| Live | `tests/live/` | Real API tests (skipped by default) |

### Test Markers

```python
@pytest.mark.live      # Requires network
@pytest.mark.smoke     # Quick validation
@pytest.mark.slow      # Long-running tests
```

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| API Keys | Environment variables, never committed |
| Proxy Credentials | Encrypted in .env |
| Scraping Detection | nodriver + curl-cffi for stealth |
| Rate Limiting | Built-in rate limiter per client |
| Data Validation | Pydantic schemas for all input |
