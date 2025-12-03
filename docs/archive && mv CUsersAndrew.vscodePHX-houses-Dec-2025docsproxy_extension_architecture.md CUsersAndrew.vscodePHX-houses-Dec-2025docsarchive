# PHX Houses Scoring System Improvement - Architecture Overview

**Version:** 1.0
**Date:** 2025-12-01
**Status:** Planning Phase

## Executive Summary

This document provides a comprehensive architectural overview of the multi-phase improvement project for the PHX Houses real estate analysis system. The project transforms the kill-switch logic from a rigid "all must pass" model to a weighted threshold system, introduces cost estimation as a scoring criterion, and establishes a robust data quality architecture targeting >95% accuracy.

### Key Goals

1. **Kill-Switch Redesign**: Weighted severity threshold (3 HARD + 4 SOFT criteria)
2. **Cost Estimation Module**: New 40-point scoring criterion + monthly cost display
3. **Data Quality Architecture**: 5-layer validation system
4. **Scoring Redistribution**: Maintain 600 pts total, rebalance sections

### Scope

- 7 implementation waves across multiple sessions
- 13 files modified, 8 new modules created
- Backward-compatible migration path
- Comprehensive test coverage additions

---

## System Context Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PHX HOUSES ANALYSIS SYSTEM                       │
│                                                                       │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐            │
│  │   Phase 0    │   │   Phase 1    │   │   Phase 2    │            │
│  │   County     │──>│  Listing +   │──>│   Image      │            │
│  │   Assessor   │   │  Map Data    │   │  Assessment  │            │
│  └──────────────┘   └──────────────┘   └──────────────┘            │
│         │                    │                   │                   │
│         └────────────────────┴───────────────────┘                   │
│                              │                                       │
│                              v                                       │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │          DATA QUALITY LAYER (NEW)                        │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│       │
│  │  │ Pydantic │  │    AI    │  │ Lineage  │  │ Quality ││       │
│  │  │Validation│─>│  Triage  │─>│ Tracking │─>│ Metrics ││       │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────┘│       │
│  └─────────────────────────────────────────────────────────┘       │
│                              │                                       │
│                              v                                       │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │          KILL-SWITCH FILTER (ENHANCED)                   │       │
│  │  ┌──────────────┐         ┌──────────────┐             │       │
│  │  │     HARD     │         │     SOFT     │             │       │
│  │  │   Criteria   │         │   Weighted   │             │       │
│  │  │ (3 instant)  │         │  Threshold   │             │       │
│  │  └──────────────┘         └──────────────┘             │       │
│  │         │                          │                     │       │
│  │         └──────────┬───────────────┘                     │       │
│  │                    v                                     │       │
│  │          Verdict: PASS / WARNING / FAIL                 │       │
│  └─────────────────────────────────────────────────────────┘       │
│                              │                                       │
│                  ┌───────────┴───────────┐                          │
│                  v                       v                          │
│  ┌──────────────────────┐   ┌──────────────────────┐              │
│  │  COST ESTIMATION     │   │  SCORING ENGINE      │              │
│  │  (NEW MODULE)        │   │  (ENHANCED)          │              │
│  │                      │   │                      │              │
│  │ • Mortgage           │   │  Section A: 230 pts  │              │
│  │ • Insurance          │   │  Section B: 180 pts  │              │
│  │ • Property Tax       │   │    + Cost (40 NEW)   │              │
│  │ • Utilities          │   │  Section C: 190 pts  │              │
│  │ • Maintenance        │   │                      │              │
│  │ • Pool (if present)  │   │  Tier Classification │              │
│  └──────────────────────┘   └──────────────────────┘              │
│             │                            │                          │
│             └────────────┬───────────────┘                          │
│                          v                                          │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │               DEAL SHEETS / REPORTS                      │       │
│  │  • Kill-switch verdict badges (H/S markers)             │       │
│  │  • Monthly cost display + $4k warning                   │       │
│  │  • Enhanced score breakdown                             │       │
│  │  • Data quality confidence indicators                   │       │
│  └─────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. Data Quality Layer (NEW)

**Purpose**: Ensure >95% data quality through validation, inference, and lineage tracking.

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA QUALITY LAYER                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  LAYER 1: PYDANTIC VALIDATION                                │
│  ┌────────────────────────────────────────────────────┐     │
│  │  src/phx_home_analysis/validation/schemas.py       │     │
│  │  • Type enforcement (int, float, str, enums)       │     │
│  │  • Range validation (beds >= 0, baths >= 0)        │     │
│  │  • Cross-field checks (pool_age requires has_pool) │     │
│  └────────────────────────────────────────────────────┘     │
│                          │                                    │
│                          v                                    │
│  LAYER 2: AI-ASSISTED TRIAGE                                 │
│  ┌────────────────────────────────────────────────────┐     │
│  │  src/phx_home_analysis/services/ai_enrichment/     │     │
│  │       field_inferencer.py                          │     │
│  │  • Flag unpullable fields                          │     │
│  │  • Claude Haiku inference ($0.25/M tokens)         │     │
│  │  • Confidence scoring (high/medium/low)            │     │
│  └────────────────────────────────────────────────────┘     │
│                          │                                    │
│                          v                                    │
│  LAYER 3: DATA LINEAGE TRACKING                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  data/field_lineage.json                           │     │
│  │  {                                                  │     │
│  │    "address": "123 Main St",                       │     │
│  │    "lot_sqft": {                                   │     │
│  │      "value": 8500,                                │     │
│  │      "source": "maricopa_api",                     │     │
│  │      "confidence": "high",                         │     │
│  │      "timestamp": "2025-12-01T10:30:00Z"           │     │
│  │    }                                                │     │
│  │  }                                                  │     │
│  └────────────────────────────────────────────────────┘     │
│                          │                                    │
│                          v                                    │
│  LAYER 4: QUALITY METRICS                                    │
│  ┌────────────────────────────────────────────────────┐     │
│  │  scripts/quality_check.py                          │     │
│  │  • Completeness: % fields populated                │     │
│  │  • Confidence: % high-confidence sources           │     │
│  │  • Formula: (Completeness × 0.6) +                 │     │
│  │             (High Conf % × 0.4)                    │     │
│  │  • CI/CD gate: fail if <95%                        │     │
│  └────────────────────────────────────────────────────┘     │
│                          │                                    │
│                          v                                    │
│  LAYER 5: DUPLICATE DETECTION                                │
│  ┌────────────────────────────────────────────────────┐     │
│  │  src/phx_home_analysis/validation/normalizer.py    │     │
│  │  • Address normalization (St→Street, W→West)       │     │
│  │  • Hash-based deduplication                        │     │
│  │  • Fuzzy matching for near-duplicates              │     │
│  └────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

**Key Interfaces:**

```python
# Pydantic Schema (Layer 1)
class PropertyData(BaseModel):
    address: str
    beds: PositiveInt
    baths: PositiveFloat
    lot_sqft: Optional[PositiveInt] = None
    year_built: Optional[conint(ge=1800, le=2025)] = None
    hoa_fee: Optional[NonNegativeInt] = None

    @validator('pool_equipment_age')
    def validate_pool_age(cls, v, values):
        if v is not None and not values.get('has_pool'):
            raise ValueError('pool_equipment_age requires has_pool=True')
        return v

# AI Triage (Layer 2)
@dataclass
class FieldInference:
    field_name: str
    inferred_value: Any
    confidence: Literal['high', 'medium', 'low']
    reasoning: str
    model: str = 'claude-haiku'

# Lineage Tracking (Layer 3)
@dataclass
class FieldLineage:
    value: Any
    source: Literal['csv', 'api', 'manual', 'ai_inference', 'default']
    confidence: Literal['high', 'medium', 'low']
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

# Quality Metrics (Layer 4)
@dataclass
class QualityReport:
    total_fields: int
    populated_fields: int
    high_confidence_count: int
    completeness: float  # 0.0 - 1.0
    confidence_score: float  # 0.0 - 1.0
    quality_score: float  # 0.0 - 1.0 (combined)
    passing: bool  # quality_score >= 0.95
```

---

### 2. Kill-Switch Filter (ENHANCED)

**Current State**: All 7 criteria must pass (binary PASS/FAIL)

**Future State**: 3 HARD criteria (instant fail) + 4 SOFT criteria (weighted threshold)

```
┌─────────────────────────────────────────────────────────────┐
│              KILL-SWITCH FILTER ARCHITECTURE                 │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  INPUT: Property Data                                        │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │  HARD CRITERIA (Instant Fail)                     │      │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │      │
│  │  │  Beds < 4   │  │  Baths < 2  │  │ HOA > $0 │  │      │
│  │  │  severity:  │  │  severity:  │  │severity: │  │      │
│  │  │   INSTANT   │  │   INSTANT   │  │ INSTANT  │  │      │
│  │  └─────────────┘  └─────────────┘  └──────────┘  │      │
│  │         │                │                │        │      │
│  │         └────────────────┴────────────────┘        │      │
│  │                      │                             │      │
│  │          ANY FAIL → VERDICT: FAIL (exit)          │      │
│  └───────────────────────────────────────────────────┘      │
│                      │                                        │
│             ALL PASS │                                        │
│                      v                                        │
│  ┌───────────────────────────────────────────────────┐      │
│  │  SOFT CRITERIA (Weighted Threshold)               │      │
│  │  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌────┐│      │
│  │  │  Septic  │  │  Garage  │  │  Year   │  │Lot ││      │
│  │  │  System  │  │  < 2-car │  │ >= 2024 │  │Size││      │
│  │  │severity: │  │severity: │  │severity:│  │Out ││      │
│  │  │   2.5    │  │   1.5    │  │   2.0   │  │1.0 ││      │
│  │  └──────────┘  └──────────┘  └─────────┘  └────┘│      │
│  │         │            │             │          │   │      │
│  │         └────────────┴─────────────┴──────────┘   │      │
│  │                      │                             │      │
│  │           SUM SEVERITY POINTS                      │      │
│  │                      │                             │      │
│  │         ┌────────────┴────────────┐                │      │
│  │         v                         v                │      │
│  │  severity >= 3.0          1.5 <= severity < 3.0   │      │
│  │  VERDICT: FAIL            VERDICT: WARNING        │      │
│  │                                                     │      │
│  │                                                     │      │
│  │         severity < 1.5                             │      │
│  │         VERDICT: PASS                              │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
│  OUTPUT: KillSwitchResult                                    │
│  {                                                            │
│    verdict: 'PASS' | 'WARNING' | 'FAIL',                    │
│    severity_score: float,                                    │
│    hard_failures: list[str],                                 │
│    soft_failures: list[tuple[str, float]],                  │
│    warnings: list[str]                                       │
│  }                                                            │
└─────────────────────────────────────────────────────────────┘
```

**Key Interfaces:**

```python
# Enhanced Kill-Switch Result
@dataclass
class KillSwitchResult:
    verdict: Literal['PASS', 'WARNING', 'FAIL']
    severity_score: float
    hard_failures: list[str]  # Instant disqualifications
    soft_failures: list[tuple[str, float]]  # (criterion, severity)
    warnings: list[str]  # Advisory notices

    @property
    def is_failed(self) -> bool:
        return self.verdict == 'FAIL'

    @property
    def has_warnings(self) -> bool:
        return self.verdict == 'WARNING' or len(self.warnings) > 0

# Criterion Definition (Enhanced)
@dataclass
class KillSwitchCriterion:
    name: str
    field: str
    check_fn: Callable[[Any], tuple[bool, str]]
    description: str
    requirement: str
    type: Literal['HARD', 'SOFT']
    severity: float  # INSTANT for HARD, 0.0-3.0 for SOFT

# Severity Weights (Constants)
HARD_SEVERITY = float('inf')  # Instant fail
SEVERITY_WEIGHTS = {
    'septic': 2.5,
    'garage': 1.5,
    'lot_size': 1.0,
    'year_built': 2.0
}
THRESHOLD_FAIL = 3.0
THRESHOLD_WARNING = 1.5
```

**Modified Files:**
- `scripts/lib/kill_switch.py` - Add weighted threshold logic
- `src/phx_home_analysis/services/kill_switch/filter.py` - Update filter orchestration
- `src/phx_home_analysis/services/kill_switch/criteria.py` - Add HARD/SOFT distinction

---

### 3. Cost Estimation Module (NEW)

**Purpose**: Calculate monthly costs for scoring AND display warnings in reports.

```
┌─────────────────────────────────────────────────────────────┐
│                   COST ESTIMATION MODULE                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  INPUT: Property Data + External Rates                       │
│                                                               │
│  ┌───────────────────────────────────────────────────┐      │
│  │  DATA SOURCES                                     │      │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────┐   │      │
│  │  │  Mortgage  │  │ Insurance  │  │   Tax    │   │      │
│  │  │   Rates    │  │   Rates    │  │  (API)   │   │      │
│  │  │ (WebFetch) │  │ (WebFetch) │  │          │   │      │
│  │  └────────────┘  └────────────┘  └──────────┘   │      │
│  │  ┌────────────┐  ┌────────────┐  ┌──────────┐   │      │
│  │  │ Utilities  │  │Maintenance │  │   Pool   │   │      │
│  │  │(SRP/APS    │  │ (% home    │  │  (flat   │   │      │
│  │  │ rates)     │  │  value)    │  │  rate)   │   │      │
│  │  └────────────┘  └────────────┘  └──────────┘   │      │
│  └───────────────────────────────────────────────────┘      │
│                      │                                        │
│                      v                                        │
│  ┌───────────────────────────────────────────────────┐      │
│  │  COST CALCULATORS                                 │      │
│  │  ┌──────────────────────────────────────────┐    │      │
│  │  │  MortgageCalculator                      │    │      │
│  │  │  • Principal: price - down_payment       │    │      │
│  │  │  • Rate: current 30yr fixed (web fetch)  │    │      │
│  │  │  • Formula: P[r(1+r)^n]/[(1+r)^n - 1]    │    │      │
│  │  └──────────────────────────────────────────┘    │      │
│  │  ┌──────────────────────────────────────────┐    │      │
│  │  │  InsuranceCalculator                     │    │      │
│  │  │  • Base: $1,500-2,500/yr (AZ avg)        │    │      │
│  │  │  • Adjust by sqft, year_built, pool      │    │      │
│  │  └──────────────────────────────────────────┘    │      │
│  │  ┌──────────────────────────────────────────┐    │      │
│  │  │  UtilityCalculator                       │    │      │
│  │  │  • Electric: sqft × season × rate        │    │      │
│  │  │  • Water: $80-120/mo base                │    │      │
│  │  │  • Gas: $30-80/mo (if applicable)        │    │      │
│  │  └──────────────────────────────────────────┘    │      │
│  │  ┌──────────────────────────────────────────┐    │      │
│  │  │  MaintenanceCalculator                   │    │      │
│  │  │  • Formula: (price × 0.01) / 12          │    │      │
│  │  │  • Reserve fund for repairs              │    │      │
│  │  └──────────────────────────────────────────┘    │      │
│  │  ┌──────────────────────────────────────────┐    │      │
│  │  │  PoolCostCalculator                      │    │      │
│  │  │  • Service: $100-150/mo                  │    │      │
│  │  │  • Energy: +$50-100/mo (if pool)         │    │      │
│  │  └──────────────────────────────────────────┘    │      │
│  └───────────────────────────────────────────────────┘      │
│                      │                                        │
│                      v                                        │
│  ┌───────────────────────────────────────────────────┐      │
│  │  AGGREGATION                                      │      │
│  │  monthly_total = sum(all components)              │      │
│  └───────────────────────────────────────────────────┘      │
│                      │                                        │
│         ┌────────────┴────────────┐                          │
│         v                         v                          │
│  ┌──────────────┐        ┌───────────────────┐              │
│  │   SCORING    │        │  REPORT DISPLAY   │              │
│  │   (40 pts)   │        │  (Warning Badge)  │              │
│  │              │        │                   │              │
│  │ formula:     │        │  if total > $4k:  │              │
│  │ max(0,       │        │    show ⚠️ badge  │              │
│  │  10 - (cost  │        │  (informational)  │              │
│  │   - 3000)    │        │                   │              │
│  │   / 200)     │        │  NOT a threshold  │              │
│  └──────────────┘        │  trigger          │              │
│                          └───────────────────┘              │
│                                                               │
│  OUTPUT: MonthlyCostEstimate                                 │
│  {                                                            │
│    mortgage: float,                                          │
│    insurance: float,                                         │
│    property_tax: float,                                      │
│    utilities: float,                                         │
│    maintenance: float,                                       │
│    pool: float,                                              │
│    total: float,                                             │
│    exceeds_budget: bool  # > $4k                            │
│  }                                                            │
└─────────────────────────────────────────────────────────────┘
```

**Key Interfaces:**

```python
# Cost Estimator
class CostEstimator:
    def __init__(self, rate_provider: RateProvider):
        self.rate_provider = rate_provider
        self.mortgage_calc = MortgageCalculator()
        self.insurance_calc = InsuranceCalculator()
        self.utility_calc = UtilityCalculator()
        self.maintenance_calc = MaintenanceCalculator()
        self.pool_calc = PoolCostCalculator()

    def estimate(self, property: Property) -> MonthlyCostEstimate:
        """Calculate all monthly costs."""
        pass

# Monthly Cost Estimate
@dataclass
class MonthlyCostEstimate:
    mortgage: float
    insurance: float
    property_tax: float
    utilities: float
    maintenance: float
    pool: float

    @property
    def total(self) -> float:
        return sum([
            self.mortgage,
            self.insurance,
            self.property_tax,
            self.utilities,
            self.maintenance,
            self.pool
        ])

    @property
    def exceeds_budget(self) -> bool:
        return self.total > 4000.0

    def to_scoring_value(self) -> float:
        """Convert to 0-10 scale for CostEfficiencyScorer."""
        return max(0.0, 10.0 - ((self.total - 3000) / 200))
```

**New Files:**
- `src/phx_home_analysis/services/cost_estimation/estimator.py`
- `src/phx_home_analysis/services/cost_estimation/calculators.py`
- `src/phx_home_analysis/services/cost_estimation/rate_provider.py`

---

### 4. Scoring Engine (ENHANCED)

**Current State**: 600 pts (Section A: 250, Section B: 160, Section C: 190)

**Future State**: 600 pts (Section A: 230, Section B: 180, Section C: 190)

```
┌─────────────────────────────────────────────────────────────┐
│                      SCORING ENGINE                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  SECTION A: LOCATION & ENVIRONMENT (250 → 230 pts)          │
│  ┌───────────────────────────────────────────────────┐      │
│  │  School Rating:    50 → 50 pts (unchanged)        │      │
│  │  Quietness:        50 → 40 pts (REDUCED)          │      │
│  │  Safety:           50 → 50 pts (unchanged)        │      │
│  │  Grocery Distance: 40 → 30 pts (REDUCED)          │      │
│  │  Parks:            30 → 30 pts (unchanged)        │      │
│  │  Orientation:      30 → 30 pts (unchanged)        │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
│  SECTION B: LOT & SYSTEMS (160 → 180 pts)                   │
│  ┌───────────────────────────────────────────────────┐      │
│  │  Roof Condition:     50 → 50 pts (unchanged)      │      │
│  │  Backyard Utility:   40 → 40 pts (unchanged)      │      │
│  │  Plumbing/Electric:  40 → 40 pts (unchanged)      │      │
│  │  Pool Condition:     30 → 20 pts (REDUCED)        │      │
│  │  Cost Efficiency:     0 → 40 pts (NEW)            │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
│  SECTION C: INTERIOR (190 → 190 pts)                        │
│  ┌───────────────────────────────────────────────────┐      │
│  │  Kitchen:        40 → 40 pts (unchanged)          │      │
│  │  Master Suite:   40 → 40 pts (unchanged)          │      │
│  │  Natural Light:  30 → 30 pts (unchanged)          │      │
│  │  High Ceilings:  30 → 30 pts (unchanged)          │      │
│  │  Fireplace:      20 → 20 pts (unchanged)          │      │
│  │  Laundry:        20 → 20 pts (unchanged)          │      │
│  │  Aesthetics:     10 → 10 pts (unchanged)          │      │
│  └───────────────────────────────────────────────────┘      │
│                                                               │
│  TIER CLASSIFICATION (unchanged)                             │
│  ┌───────────────────────────────────────────────────┐      │
│  │  UNICORN:    > 480 pts (>80%)                     │      │
│  │  CONTENDER:  360-480 pts (60-80%)                 │      │
│  │  PASS:       < 360 pts (<60%)                     │      │
│  │  FAILED:     Kill-switch fail (any score)         │      │
│  └───────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

**Modified Files:**
- `src/phx_home_analysis/config/scoring_weights.py` - Update weight constants
- `src/phx_home_analysis/services/scoring/strategies/location.py` - Adjust quietness, grocery
- `src/phx_home_analysis/services/scoring/strategies/systems.py` - Add CostEfficiencyScorer, adjust pool

---

## Data Flow Diagram

### End-to-End Pipeline

```
┌──────────────┐
│  CSV Listing │
│     Data     │
└──────┬───────┘
       │
       v
┌────────────────────────────────────────────────────────┐
│  Phase 0: County Assessor Data                         │
│  ┌──────────────────────────────────────────────┐     │
│  │  Maricopa County API                         │     │
│  │  • lot_sqft, year_built, garage_spaces       │     │
│  │  • has_pool, tax_annual, roof_type           │     │
│  └──────────────────────────────────────────────┘     │
└────────────────────────────┬───────────────────────────┘
                             │
                             v
┌────────────────────────────────────────────────────────┐
│  DATA QUALITY VALIDATION (NEW)                         │
│  1. Pydantic schema validation                         │
│  2. AI triage for missing fields                       │
│  3. Lineage tracking                                   │
└────────────────────────────┬───────────────────────────┘
                             │
                             v
┌────────────────────────────────────────────────────────┐
│  KILL-SWITCH FILTER (ENHANCED)                         │
│  ┌──────────────────────────────────────────────┐     │
│  │  HARD Check: Beds, Baths, HOA                │     │
│  │  SOFT Check: Septic, Garage, Lot, Year       │     │
│  │  Calculate severity score                     │     │
│  │  Verdict: PASS / WARNING / FAIL              │     │
│  └──────────────────────────────────────────────┘     │
└────────────────────────────┬───────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
        FAIL / WARNING                     PASS
              │                             │
              v                             v
    ┌─────────────────┐         ┌────────────────────────┐
    │  Store as       │         │  Phase 1: Listing +    │
    │  FAILED tier    │         │  Map Data Extraction   │
    │  (early exit)   │         │                        │
    └─────────────────┘         └──────────┬─────────────┘
                                           │
                                           v
                                ┌────────────────────────┐
                                │  Phase 2: Image        │
                                │  Assessment            │
                                │  (Visual Scoring)      │
                                └──────────┬─────────────┘
                                           │
                                           v
                                ┌────────────────────────┐
                                │  COST ESTIMATION (NEW) │
                                │  • Calculate monthly   │
                                │  • Check budget ($4k)  │
                                └──────────┬─────────────┘
                                           │
                                           v
                                ┌────────────────────────┐
                                │  SCORING ENGINE        │
                                │  • Section A: 230 pts  │
                                │  • Section B: 180 pts  │
                                │  •   (incl Cost 40)    │
                                │  • Section C: 190 pts  │
                                │  • Tier assignment     │
                                └──────────┬─────────────┘
                                           │
                                           v
                                ┌────────────────────────┐
                                │  Phase 4: Deal Sheets │
                                │  • Kill-switch badges  │
                                │  • Cost warning        │
                                │  • Score breakdown     │
                                │  • Quality indicators  │
                                └────────────────────────┘
```

---

## Integration Points

### 1. Data Repositories

**Current:**
- `src/phx_home_analysis/repositories/csv_repository.py` - CSV listings
- `src/phx_home_analysis/repositories/json_repository.py` - Enrichment data

**Integration:**
- Add Pydantic validation on load
- Track field lineage in metadata
- Integrate with AI triage for missing fields

### 2. Property Entity

**Current:**
```python
@dataclass
class Property:
    # Basic fields
    street: str
    beds: int
    baths: float
    # ...

    # Kill-switch results
    kill_switch_passed: bool
    kill_switch_failures: list[str]
```

**Enhanced:**
```python
@dataclass
class Property:
    # ... existing fields ...

    # Enhanced kill-switch results
    kill_switch_result: Optional[KillSwitchResult] = None

    # Cost estimation
    monthly_cost_estimate: Optional[MonthlyCostEstimate] = None

    # Data quality
    field_lineage: dict[str, FieldLineage] = field(default_factory=dict)
    quality_score: Optional[float] = None
```

### 3. Pipeline Orchestrator

**Current:**
```python
class AnalysisPipeline:
    def run(self, properties: list[Property]):
        # 1. Apply kill-switches
        # 2. Score passed properties
        # 3. Generate reports
```

**Enhanced:**
```python
class AnalysisPipeline:
    def run(self, properties: list[Property]):
        # 0. Quality baseline measurement
        # 1. Data validation (Pydantic)
        # 2. Apply kill-switches (weighted)
        # 3. Estimate costs (for passed properties)
        # 4. Score properties (including cost efficiency)
        # 5. Generate reports (with badges, warnings)
        # 6. Quality metrics reporting
```

### 4. Deal Sheets Renderer

**Current:**
- Simple PASS/FAIL kill-switch display
- Basic cost information from Property.monthly_costs

**Enhanced:**
- Kill-switch verdict badges with [H]/[S] markers
- Severity score display
- Monthly cost breakdown with ⚠️ if >$4k
- Cost efficiency score display (new 40-pt criterion)
- Data quality confidence indicators

---

## Technology Stack

### Core Dependencies (Unchanged)
- Python 3.11+
- Pydantic 2.x - Data validation
- Pandas - Data manipulation
- Requests - HTTP clients

### New Dependencies
- None (use existing libraries)

### External Services
- Maricopa County Assessor API - Authoritative property data
- Claude API (Haiku) - AI-assisted field inference ($0.25/M tokens)
- Web scraping (nodriver, curl_cffi) - Listing data extraction
- Rate data sources (web fetch) - Mortgage, insurance, utility rates

---

## Performance Considerations

### Batch Processing
- **Current**: ~25 properties, ~5 minutes total
- **Future**: +30 seconds for cost estimation, +10 seconds for validation
- **Total**: ~6 minutes for 25 properties

### Caching Strategy
- Cache rate data (mortgage, insurance, utilities) for 24 hours
- Cache county assessor results indefinitely (rarely changes)
- AI inference results cached per property hash

### Scalability
- Validation layer adds minimal overhead (<100ms per property)
- Cost estimation parallelizable (async/await for rate fetching)
- Quality metrics calculated once per batch (not per property)

---

## Security Considerations

### API Keys
- Maricopa County Assessor: `MARICOPA_ASSESSOR_TOKEN` (env var)
- Anthropic Claude: `ANTHROPIC_API_KEY` (env var)

### Data Privacy
- No PII stored beyond property addresses (public records)
- Field lineage tracks data sources but not user actions
- Quality reports aggregated, not per-user

### Rate Limiting
- County API: 1000 requests/day (sufficient for batch processing)
- Claude API: $5/day budget for inference (Haiku tier)

---

## Testing Strategy

### Unit Tests
- `tests/services/kill_switch/test_weighted_threshold.py`
- `tests/services/cost_estimation/test_calculators.py`
- `tests/validation/test_schemas.py`

### Integration Tests
- `tests/integration/test_kill_switch_pipeline.py`
- `tests/integration/test_cost_scoring_integration.py`
- `tests/integration/test_quality_validation.py`

### Regression Tests
- Baseline 25 properties scored with current system
- Re-score with new system, verify tier changes are intentional
- Validate backward compatibility (old enrichment_data.json still works)

---

## Backward Compatibility

### Data Migration
- Old kill-switch boolean results mapped to new verdict format
- Missing `monthly_cost_estimate` calculated on-demand
- Field lineage backfilled with `source: 'legacy'` for existing data

### API Compatibility
- `kill_switch_passed` property maintained (reads from `kill_switch_result.verdict`)
- `kill_switch_failures` property maintained (reads from `kill_switch_result.hard_failures + soft_failures`)

### Configuration
- Old scoring weights still valid (new weights opt-in via config flag)
- Gradual migration path: Wave 1-6 can be deployed incrementally

---

## Deployment Architecture

### Environment Setup
```bash
# Install new dependencies (none required beyond existing)
uv sync

# Set environment variables
export MARICOPA_ASSESSOR_TOKEN="..."
export ANTHROPIC_API_KEY="..."

# Run quality baseline
python scripts/quality_baseline.py

# Run analysis with new system
python scripts/phx_home_analyzer.py
```

### Monitoring
- Quality score dashboard: `scripts/quality_check.py --report`
- Cost estimation accuracy: Compare against manual calculations
- Kill-switch verdict distribution: Track PASS/WARNING/FAIL ratios

---

## Future Enhancements

### Phase 2 Improvements (Post-Wave 6)
1. **Machine Learning Scoring**: Train model on historical buyer preferences
2. **Dynamic Thresholds**: Adjust severity weights based on market conditions
3. **Real-time Rate Updates**: Fetch mortgage/insurance rates on-demand
4. **Enhanced Image Analysis**: Use Vision API for construction quality assessment

### Scalability Improvements
1. **Database Backend**: Replace CSV/JSON with PostgreSQL
2. **API Service**: RESTful API for property analysis
3. **Web UI**: Interactive dashboard for property comparison
4. **Batch Automation**: Scheduled daily updates for tracked properties

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **Kill-Switch** | Binary criterion that auto-disqualifies properties if not met |
| **HARD Criterion** | Kill-switch that causes instant failure (Beds, Baths, HOA) |
| **SOFT Criterion** | Kill-switch with weighted severity (Septic, Garage, Lot, Year) |
| **Severity Score** | Sum of SOFT criterion penalties (0.0 - 7.0 range) |
| **Threshold** | Severity score boundary (3.0 = FAIL, 1.5 = WARNING) |
| **Cost Efficiency** | New 40-pt scoring criterion based on monthly cost estimate |
| **Field Lineage** | Metadata tracking data source and confidence for each field |
| **Quality Score** | Combined metric: (Completeness × 0.6) + (Confidence × 0.4) |
| **Triage Model** | AI-assisted inference for unpullable fields (Claude Haiku) |

---

## Appendix B: File Manifest

### New Files (8)
1. `src/phx_home_analysis/validation/schemas.py` - Pydantic models
2. `src/phx_home_analysis/validation/normalizer.py` - Data pre-processing
3. `src/phx_home_analysis/services/ai_enrichment/field_inferencer.py` - AI triage
4. `src/phx_home_analysis/services/cost_estimation/estimator.py` - Cost calculator
5. `src/phx_home_analysis/services/cost_estimation/calculators.py` - Component calculators
6. `src/phx_home_analysis/services/cost_estimation/rate_provider.py` - Rate data source
7. `scripts/quality_baseline.py` - Baseline measurement
8. `scripts/quality_check.py` - Quality metrics & CI gate

### Modified Files (13)
1. `scripts/lib/kill_switch.py` - Weighted threshold logic
2. `src/phx_home_analysis/services/kill_switch/filter.py` - Filter orchestration
3. `src/phx_home_analysis/services/kill_switch/criteria.py` - HARD/SOFT distinction
4. `src/phx_home_analysis/config/scoring_weights.py` - Weight redistribution
5. `src/phx_home_analysis/services/scoring/strategies/location.py` - Adjusted weights
6. `src/phx_home_analysis/services/scoring/strategies/systems.py` - CostEfficiencyScorer
7. `src/phx_home_analysis/domain/entities.py` - Enhanced Property entity
8. `src/phx_home_analysis/pipeline/orchestrator.py` - Pipeline updates
9. `scripts/deal_sheets/renderer.py` - Verdict badges, cost warnings
10. `scripts/deal_sheets/templates.py` - Template updates
11. `.claude/skills/kill-switch/SKILL.md` - Updated documentation
12. `.claude/skills/scoring/SKILL.md` - Cost efficiency documentation
13. `data/field_lineage.json` - NEW data file (lineage tracking)

---

**Document Version Control:**
- v1.0 (2025-12-01): Initial architecture specification
- Next Review: After Wave 0 completion

**Related Documents:**
- `docs/specs/implementation-spec.md` - Detailed implementation guide
- `docs/specs/phase-execution-guide.md` - Session-by-session execution
- `docs/specs/reference-index.md` - Research document catalog
