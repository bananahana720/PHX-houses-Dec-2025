# Action Items Matrix: PHX Houses Pipeline Enhancement

**Synthesis Date:** December 2024
**Status:** Complete
**Research Sources:** 9 Deep-Dive Reports (Market x3, Domain x3, Tech x3)
**Prior Analysis:** GAP_ANALYSIS_SYNTHESIS.md (47 gaps identified)

---

## 1. Action Items Overview

### Summary Statistics

| Metric | Count |
|--------|-------|
| **Total Action Items** | 68 |
| **From Research Reports** | 52 |
| **From Gap Analysis (Critical)** | 16 |
| **Configuration Changes** | 18 |
| **Code Changes** | 32 |
| **API Integrations** | 12 |
| **Process/Documentation** | 6 |

### Distribution by Priority

| Priority | Count | Effort (days) | Description |
|----------|-------|---------------|-------------|
| **P0 - Critical** | 8 | 28 | Must do immediately; blocks core functionality |
| **P1 - High** | 18 | 42 | Do next sprint; high ROI or risk mitigation |
| **P2 - Medium** | 26 | 48 | Important improvements; schedule within quarter |
| **P3 - Lower/Future** | 16 | 32 | Nice-to-have; backlog for future sprints |

### Distribution by Category

| Category | Count | Description |
|----------|-------|-------------|
| **CONFIG** | 18 | Constants, weights, thresholds (no code logic changes) |
| **CODE** | 32 | New services, strategies, or logic changes |
| **API** | 12 | External API integrations |
| **PROCESS** | 6 | Documentation, workflows, CI/CD |

---

## 2. Priority Matrix

### P0 - Critical (Do First)

These items address fundamental gaps that block production use or buyer decision accuracy.

| ID | Action | Category | Effort | Dependencies | Files Affected | Research Source |
|----|--------|----------|--------|--------------|----------------|-----------------|
| **P0-01** | Add Solar Lease as kill-switch criterion (HARD or SOFT 2.5) | CONFIG+CODE | 2d | None | `constants.py`, `kill_switch/criteria.py`, `schemas.py` | Market-Beta |
| **P0-02** | Implement job queue architecture for image extraction | CODE | 5d | None | `scripts/extract_images.py`, new `jobs/` module | Gap IP-01 |
| **P0-03** | Add progress visibility for long-running extractions | CODE | 2d | P0-02 | `extract_images.py`, `work_items.json` | Gap IP-04 |
| **P0-04** | Add scoring explanations (reasoning generation) | CODE | 3d | None | `services/scoring/scorer.py`, new `reasoning.py` | Gap XT-09 |
| **P0-05** | Add kill-switch verdict explanations with severity breakdown | CODE | 1d | None | `services/kill_switch/filter.py`, `verdict.py` | Gap XT-10 |
| **P0-06** | Implement field-level data lineage tracking | CODE | 4d | None | New `lineage/` service, `enrichment_data.json` schema | Gap XT-01 |
| **P0-07** | Add foundation/structural assessment service | CODE | 5d | None | New `services/foundation/` module | Gap VB-03, Domain-Alpha |
| **P0-08** | Update pool monthly cost to $250-400 range | CONFIG | 0.5d | None | `constants.py` | Market-Beta |

**P0 Critical Path:**
```
P0-02 (job queue) → P0-03 (progress visibility)
P0-04 (scoring explanations) ← P0-05 (kill-switch explanations)
All others: Independent
```

---

### P1 - High Priority

High-impact improvements that significantly enhance accuracy or user experience.

| ID | Action | Category | Effort | Dependencies | Files Affected | Research Source |
|----|--------|----------|--------|--------------|----------------|-----------------|
| **P1-01** | Add Owned Solar bonus (+5 pts to systems) | CONFIG+CODE | 1d | None | `scoring_weights.py`, new `solar_scorer.py` | Market-Beta |
| **P1-02** | Update commute cost baseline to $0.67-0.70/mile | CONFIG | 0.5d | None | `constants.py` | Market-Alpha |
| **P1-03** | Add septic system SOFT kill-switch (severity 2.5) - currently sewer only | CONFIG | 0.5d | None | `constants.py` - already has SEVERITY_WEIGHT_SEWER | Domain-Gamma |
| **P1-04** | Add roof material type differentiation (tile vs shingle scoring) | CODE | 2d | None | `services/scoring/strategies/systems.py` | Domain-Alpha |
| **P1-05** | Add tile roof underlayment age tracking (25-30 year lifespan) | CODE | 2d | P1-04 | `schemas.py`, `scoring/strategies/systems.py` | Domain-Alpha |
| **P1-06** | Integrate Phoenix Open Data crime API | API | 3d | None | New `services/crime_data/phoenix_api.py` | Tech-Beta |
| **P1-07** | Integrate FEMA NFHL flood zone API | API | 3d | None | `services/flood_data/` (may exist partially) | Tech-Alpha |
| **P1-08** | Add equipment replacement cost budget to deal sheets | CODE | 2d | None | `scripts/deal_sheets/`, `reporters/` | Domain-Alpha |
| **P1-09** | Add residential proxy integration (Smartproxy/IPRoyal) | CODE | 2d | None | `services/infrastructure/proxy.py` | Tech-Gamma |
| **P1-10** | Add retry logic with exponential backoff for extractions | CODE | 2d | P0-02 | `extract_images.py`, extraction services | Gap IP-06, IP-07 |
| **P1-11** | Add cost efficiency component breakdown in reports | CODE | 2d | P0-04 | `services/cost_estimation/`, reporters | Gap XT-11 |
| **P1-12** | Add HOA verification via County Recorder | API | 3d | None | New `services/hoa_verification/` | Domain-Beta |
| **P1-13** | Add solar lease detection from listing data | CODE | 2d | P0-01 | `listing-browser` agent, `schemas.py` | Domain-Beta |
| **P1-14** | Externalize kill-switch criteria to YAML config | CONFIG | 2d | None | New `config/kill_switch.yaml`, loader | Gap XT-05 |
| **P1-15** | Add scoring weight versioning | CODE | 2d | None | `scoring_weights.py`, run metadata | Gap XT-06 |
| **P1-16** | Validate/maintain $0 HOA hard kill-switch | PROCESS | 0.5d | None | Verify `constants.py` - confirmed correct | Market-Alpha |
| **P1-17** | Add water service area verification (DAWS) | API | 2d | None | New `services/water_service/` | Domain-Gamma |
| **P1-18** | Add Maricopa County GIS integration for lot validation | API | 3d | None | `services/county_data/gis.py` | Domain-Gamma |

**P1 Dependencies:**
```
P1-04 (roof material) → P1-05 (underlayment)
P0-02 (job queue) → P1-10 (retry logic)
P0-04 (explanations) → P1-11 (cost breakdown)
P0-01 (solar kill-switch) → P1-13 (solar detection)
```

---

### P2 - Medium Priority

Important enhancements that improve completeness and maintainability.

| ID | Action | Category | Effort | Dependencies | Files Affected | Research Source |
|----|--------|----------|--------|--------------|----------------|-----------------|
| **P2-01** | Add appreciation tier scoring by location | CODE | 3d | None | New `services/scoring/strategies/appreciation.py` | Market-Gamma |
| **P2-02** | Add emerging neighborhood tracking (Laveen, Buckeye, etc.) | CONFIG | 1d | P2-01 | `config/neighborhoods.yaml` | Market-Gamma |
| **P2-03** | Add pool equipment age as Systems subscore factor | CODE | 1d | None | `services/scoring/strategies/systems.py` | Market-Beta |
| **P2-04** | Add builder ROC complaints check for new construction | API | 3d | None | New `services/builder_verification/` | Domain-Beta |
| **P2-05** | Add zoning context lookup | API | 2d | P1-18 | `services/county_data/zoning.py` | Domain-Gamma |
| **P2-06** | Integrate EIA energy estimation API | API | 2d | None | New `services/energy_estimation/` | Tech-Beta |
| **P2-07** | Add energy estimation formula (sqft × region multiplier) | CODE | 1d | P2-06 | `services/cost_estimation/` | Tech-Beta |
| **P2-08** | Add circuit breaker pattern for extraction sources | CODE | 2d | P0-02 | `services/image_extraction/` (SourceCircuitBreaker exists) | Gap IP-08 |
| **P2-09** | Add crash-resilient extraction state | CODE | 3d | P0-02 | `extraction_state.json` handling | Gap IP-09 |
| **P2-10** | Add extraction metrics dashboard | CODE | 2d | P0-03 | New `reports/extraction_metrics.html` | Gap IP-10 |
| **P2-11** | Tune LSH deduplication for small datasets | CODE | 2d | None | `validation/deduplication.py` | Gap IP-11 |
| **P2-12** | Parallelize image standardizer | CODE | 2d | P0-02 | `services/image_extraction/standardizer.py` | Gap IP-12 |
| **P2-13** | Add schema versioning for data migrations | CODE | 3d | P0-06 | `services/schema/versioning.py` | Gap XT-02 |
| **P2-14** | Add mutation audit logging | CODE | 2d | P0-06 | Repositories, new `audit/` service | Gap XT-03 |
| **P2-15** | Index extraction run logs for querying | CODE | 1d | None | `run_history/` → indexed JSON | Gap XT-04 |
| **P2-16** | Add feature flag system for scoring strategies | CODE | 2d | P1-15 | New `config/feature_flags.py` | Gap XT-07 |
| **P2-17** | Move remaining constants to environment variables | CONFIG | 2d | None | `constants.py`, `.env.example` | Gap XT-08 |
| **P2-18** | Add "next tier" guidance to reports | CODE | 2d | P0-04 | `services/classification/`, reporters | Gap XT-12 |
| **P2-19** | Add commute cost monetization service | CODE | 3d | P1-02 | New `services/commute_cost/` | Gap VB-04 |
| **P2-20** | Add zoning/growth risk assessment | CODE | 4d | P2-05 | New `services/risk_assessment/zoning.py` | Gap VB-05 |
| **P2-21** | Enhance energy efficiency modeling (solar ROI) | CODE | 3d | P0-01, P2-06 | `services/cost_estimation/`, renovation service | Gap VB-06 |
| **P2-22** | Integrate renovation ROI service | CODE | 2d | None | Connect existing `renovation/` service | Gap VB-07 |
| **P2-23** | Add flood insurance cost estimation | CODE | 2d | P1-07 | `services/cost_estimation/` | Gap VB-08 |
| **P2-24** | Add WalkScore API rate limiting | CODE | 1d | None | `services/walkscore/` | Tech-Beta |
| **P2-25** | Validate 4+ bedroom requirement per demographics | PROCESS | 0.5d | None | Verify `constants.py` - confirmed correct | Market-Gamma |
| **P2-26** | Document Arizona HVAC lifespan (10-15 years) in deal sheets | PROCESS | 0.5d | None | Deal sheet templates, already in `constants.py` (12 years) | Domain-Alpha |

**P2 Dependencies:**
```
P1-18 (GIS) → P2-05 (zoning)
P2-05 (zoning) → P2-20 (zoning risk)
P0-02 (job queue) → P2-08, P2-09, P2-12
P0-06 (lineage) → P2-13, P2-14
P0-04 (explanations) → P2-18
P1-07 (FEMA API) → P2-23 (flood insurance)
P2-06 (EIA) → P2-07 (energy formula)
P0-01 (solar kill-switch) + P2-06 → P2-21 (solar ROI)
```

---

### P3 - Lower Priority / Future

Nice-to-have improvements for future consideration.

| ID | Action | Category | Effort | Dependencies | Files Affected | Research Source |
|----|--------|----------|--------|--------------|----------------|-----------------|
| **P3-01** | Add kill-switch severity bands (soft fail vs hard fail nuance) | CODE | 2d | P0-05 | `kill_switch/` service | Gap VB-02 |
| **P3-02** | Implement auto-CLAUDE.md creation hooks | CODE | 2d | None | Discovery protocol (designed, not implemented) | Gap CA-01 |
| **P3-03** | Add runtime staleness checks for data files | CODE | 2d | None | Context management hooks | Gap CA-02 |
| **P3-04** | Add tool violation linter (pre-commit) | PROCESS | 2d | None | `.pre-commit-config.yaml` | Gap CA-03 |
| **P3-05** | Add skill discovery CLI command | CODE | 1d | None | New CLI utility | Gap CA-04 |
| **P3-06** | Add knowledge graph schema validation | CODE | 1d | None | Pydantic schemas for `toolkit.json` | Gap CA-05 |
| **P3-07** | Add adaptive batch sizing for analysis | CODE | 1d | P0-02 | `analyze-property` command | Gap XT-14 |
| **P3-08** | Add self-healing for transient API failures | CODE | 3d | P1-10 | Extraction services | Gap XT-15 |
| **P3-09** | Add job cancellation support | CODE | 2d | P0-02 | Job queue infrastructure | Gap IP-05 |
| **P3-10** | Add worker pool for distributed extraction | CODE | 3d | P0-02 | New worker infrastructure | Gap IP-03 |
| **P3-11** | Add historical appreciation data by ZIP | API | 3d | P2-01 | `services/appreciation/` | Market-Gamma |
| **P3-12** | Add NeighborhoodScout crime data (enterprise) | API | 2d | Budget approval | Alternative to Phoenix Open Data | Tech-Beta |
| **P3-13** | Add CrimeOMeter API integration (address-level) | API | 2d | Budget approval | Alternative crime source | Tech-Beta |
| **P3-14** | Evaluate Celery migration (if RQ bottlenecks) | CODE | 5d | P0-02 proven insufficient | Migration from RQ | Tech-Gamma |
| **P3-15** | Add UtilityAPI/Arcadia for actual energy data | API | 4d | Budget approval | Enterprise energy data | Tech-Beta |
| **P3-16** | Add DOE Home Energy Score API integration | API | 3d | DOE Assessor credentials | Official energy scoring | Tech-Beta |

---

## 3. Dependency Graph

### Critical Path Analysis

```
                                    ┌─────────────────────┐
                                    │ P0-02: Job Queue    │
                                    │ Architecture        │
                                    └─────────┬───────────┘
                                              │
              ┌───────────────────────────────┼───────────────────────────────┐
              │                               │                               │
              ▼                               ▼                               ▼
    ┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
    │ P0-03: Progress │           │ P1-10: Retry    │           │ P2-08: Circuit  │
    │ Visibility      │           │ Logic           │           │ Breaker         │
    └─────────────────┘           └─────────────────┘           └─────────────────┘
                                              │
                                              ▼
                                  ┌─────────────────┐
                                  │ P3-08: Self-    │
                                  │ Healing         │
                                  └─────────────────┘


    ┌─────────────────┐
    │ P0-04: Scoring  │
    │ Explanations    │◄────────┐
    └────────┬────────┘         │
             │                  │
             ▼                  │
    ┌─────────────────┐    ┌────┴────────────┐
    │ P1-11: Cost     │    │ P0-05: KillSwitch│
    │ Breakdown       │    │ Explanations    │
    └─────────────────┘    └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ P2-18: Next     │
    │ Tier Guidance   │
    └─────────────────┘


    ┌─────────────────┐
    │ P0-06: Field    │
    │ Lineage         │
    └────────┬────────┘
             │
             ├─────────────────┐
             ▼                 ▼
    ┌─────────────────┐   ┌─────────────────┐
    │ P2-13: Schema   │   │ P2-14: Audit    │
    │ Versioning      │   │ Logging         │
    └─────────────────┘   └─────────────────┘


    ┌─────────────────┐
    │ P0-01: Solar    │
    │ Kill-Switch     │
    └────────┬────────┘
             │
             ├─────────────────┐
             ▼                 ▼
    ┌─────────────────┐   ┌─────────────────┐
    │ P1-01: Solar    │   │ P1-13: Solar    │
    │ Bonus           │   │ Detection       │
    └─────────────────┘   └─────────────────┘
                               │
                               ▼
                          ┌─────────────────┐
                          │ P2-21: Solar    │
                          │ ROI Modeling    │
                          └─────────────────┘


    ┌─────────────────┐
    │ P1-18: GIS      │
    │ Integration     │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ P2-05: Zoning   │
    │ Lookup          │
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │ P2-20: Zoning   │
    │ Risk Assessment │
    └─────────────────┘
```

### Parallel Execution Opportunities

**Independent Streams (can run concurrently):**

1. **Infrastructure Stream:** P0-02 → P0-03 → P1-10 → P2-08, P2-09, P2-12
2. **Explainability Stream:** P0-04, P0-05 → P1-11 → P2-18
3. **Data Quality Stream:** P0-06 → P2-13, P2-14, P2-15
4. **Solar Stream:** P0-01 → P1-01, P1-13 → P2-21
5. **Location APIs Stream:** P1-06, P1-07, P1-17, P1-18 (all independent)
6. **Configuration Stream:** P1-14, P1-15 → P2-16, P2-17

---

## 4. Implementation Waves

### Wave 1: Configuration Updates (No Code Logic Changes)
**Effort:** 4 days | **Risk:** Low | **Impact:** Medium

| ID | Action | Current Value | New Value | File |
|----|--------|---------------|-----------|------|
| P0-08 | Pool monthly cost | $200 | $250-400 range | `constants.py` |
| P1-02 | Commute cost/mile | Unknown | $0.67-0.70 | `constants.py` |
| P1-03 | Septic severity | 2.5 (sewer) | Confirm covers septic | `constants.py` |
| P1-16 | HOA kill-switch | $0 hard | Validate maintained | `constants.py` |
| P2-25 | 4+ bedroom | 4 hard | Validate maintained | `constants.py` |
| P2-26 | HVAC lifespan doc | 12 years | Document in deal sheets | Templates |

**Validation Checklist:**
- [x] `POOL_TOTAL_MONTHLY` = 200 (line 201) - **UPDATE NEEDED** to 300-350
- [x] Commute cost not in constants - **ADD NEEDED**
- [x] `SEVERITY_WEIGHT_SEWER` = 2.5 (line 61) - covers septic, confirmed
- [x] HOA hard kill-switch - in kill_switch logic, confirmed $0
- [x] 4+ bedrooms - in kill_switch hard criteria, confirmed
- [x] `HVAC_LIFESPAN_YEARS` = 12 (line 238) - correct per research (10-15 range)

---

### Wave 2: Kill-Switch Additions
**Effort:** 6 days | **Risk:** Medium | **Impact:** High

| ID | Action | Recommended Approach |
|----|--------|---------------------|
| P0-01 | Solar Lease kill-switch | **OPTION A (Recommended):** Add as HARD kill-switch (transfer liability too high) |
|       |                         | **OPTION B:** Add as SOFT with severity 2.5 (same as sewer) |
| P1-14 | Externalize kill-switch config | Move all criteria to `config/kill_switch.yaml` with versioning |

**Implementation Details for P0-01:**

```python
# constants.py addition (if SOFT):
SEVERITY_WEIGHT_SOLAR_LEASE: Final[float] = 2.5

# OR kill_switch/criteria.py addition (if HARD):
class SolarLeaseKillSwitch(HardKillSwitchCriterion):
    """Fail properties with solar lease (transfer liability)."""
    def evaluate(self, property: Property) -> bool:
        return property.solar_status == SolarStatus.LEASED
```

**Schema Updates Required:**
```python
# schemas.py - add solar_status field
class SolarStatus(str, Enum):
    OWNED = "owned"
    LEASED = "leased"
    NONE = "none"
    UNKNOWN = "unknown"
```

---

### Wave 3: Scoring Calibration
**Effort:** 12 days | **Risk:** Medium | **Impact:** High

| ID | Action | Points | Section | Implementation |
|----|--------|--------|---------|----------------|
| P1-01 | Owned Solar bonus | +5 pts | Systems | New `SolarSystemScorer` strategy |
| P1-04 | Roof material differentiation | Modify 45 pts | Systems | Enhance `RoofConditionScorer` |
| P1-05 | Tile underlayment tracking | Modify 45 pts | Systems | Add field, enhance scorer |
| P2-03 | Pool equipment age | Modify 20 pts | Systems | Enhance `PoolConditionScorer` |

**Scoring Weight Adjustments:**

Current Section B: 170 pts
- roof_condition: 45 pts
- backyard_utility: 35 pts
- plumbing_electrical: 35 pts
- pool_condition: 20 pts
- cost_efficiency: 35 pts

Proposed Section B: 175 pts (+5 for solar)
- Add `solar_system: 5 pts` - Owned = 5, None = 0, Leased = N/A (failed kill-switch)

**Roof Material Scoring Logic:**

```python
# Current: Age-based only (0-5 years = 45 pts, etc.)
# Proposed: Age + Material

ROOF_MATERIAL_MULTIPLIER = {
    "tile": 1.0,      # Full points (30-50 year life)
    "shingle": 0.8,   # 80% points (15-25 year life in AZ)
    "foam": 0.7,      # 70% points (10-15 year life)
    "unknown": 0.85,  # Conservative default
}

# For tile roofs: Track underlayment age (25-30 year life)
# If underlayment unknown and roof >20 years: Assume needs inspection
```

---

### Wave 4: New API Integrations
**Effort:** 18 days | **Risk:** High | **Impact:** High

| ID | API | Cost | Rate Limit | Data Provided |
|----|-----|------|------------|---------------|
| P1-06 | Phoenix Open Data Crime | Free | None stated | Address-level crime incidents |
| P1-07 | FEMA NFHL | Free | None stated | Flood zone classification |
| P1-12 | Maricopa County Recorder | Free | Unknown | HOA CC&R verification |
| P1-17 | DAWS Water Service | Free | Unknown | Water service area lookup |
| P1-18 | Maricopa GIS | Free | Unknown | Lot size, parcel data |
| P2-06 | EIA Energy Data | Free | 1000/hr | Regional energy statistics |

**Integration Priority Order:**
1. **P1-06 Phoenix Crime** - Direct Phoenix relevance, free, address-level
2. **P1-07 FEMA Flood** - High scoring impact (25 pts), free
3. **P1-18 Maricopa GIS** - Validates lot_sqft, free, enables P2-05
4. **P1-12 County Recorder** - HOA verification, reduces surprises
5. **P1-17 DAWS Water** - Important for unincorporated areas
6. **P2-06 EIA** - Energy estimation, lower priority

**API Integration Template:**

```python
# services/{api_name}/client.py
class {ApiName}Client:
    BASE_URL = "..."

    def __init__(self, api_key: str | None = None):
        self.session = requests.Session()
        self.api_key = api_key or os.getenv("{API_NAME}_API_KEY")

    @retry(max_attempts=3, backoff=exponential)
    def fetch(self, address: Address) -> dict:
        ...

# services/{api_name}/service.py
class {ApiName}Service:
    def __init__(self, client: {ApiName}Client, cache: Cache):
        ...

    def get_data(self, property: Property) -> {ApiData}:
        ...
```

---

### Wave 5: Infrastructure Improvements
**Effort:** 20 days | **Risk:** High | **Impact:** Critical

| ID | Component | Current State | Target State |
|----|-----------|---------------|--------------|
| P0-02 | Job queue | None (blocking) | RQ with job persistence |
| P0-03 | Progress visibility | None | Real-time logging + work_items.json |
| P1-09 | Proxy infrastructure | Manual | Smartproxy integration |
| P1-10 | Retry logic | Basic | Exponential backoff with jitter |
| P2-08 | Circuit breaker | Designed, unused | Integrated into extraction loop |
| P2-09 | Crash resilience | Partial | Full checkpoint/resume |

**Job Queue Architecture (P0-02):**

```python
# jobs/models.py
from pydantic import BaseModel
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExtractionJob(BaseModel):
    id: str
    address: str
    sources: list[str]
    status: JobStatus
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    progress: float  # 0.0 - 1.0
    error: str | None

# jobs/queue.py
from rq import Queue
from redis import Redis

class ExtractionQueue:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = Redis.from_url(redis_url)
        self.queue = Queue(connection=self.redis)

    def enqueue(self, job: ExtractionJob) -> str:
        ...

    def get_status(self, job_id: str) -> JobStatus:
        ...

    def get_progress(self, job_id: str) -> float:
        ...
```

**Progress Visibility (P0-03):**

```python
# Progress updates to work_items.json
{
    "extraction_progress": {
        "job_id": "ext-123",
        "address": "123 Main St",
        "status": "running",
        "progress": 0.45,
        "current_source": "zillow",
        "images_downloaded": 12,
        "estimated_remaining": "2m 30s"
    }
}
```

---

## 5. Risk Register

| Action ID | Risk | Probability | Impact | Mitigation | Rollback Plan |
|-----------|------|-------------|--------|------------|---------------|
| P0-01 | Solar lease data unavailable in listings | Medium | High | Add "unknown" handling; use disclosure detection | Skip scoring if uncertain |
| P0-02 | RQ integration complexity | Low | Critical | Start simple; expand incrementally | Fall back to sequential processing |
| P0-04 | Explanations inconsistent with scores | Medium | Medium | Template-based generation; regression tests | Disable explanations, show raw scores |
| P0-06 | Lineage tracking performance overhead | Medium | Low | Batch writes; async logging | Make lineage optional via config |
| P1-04 | Roof material detection inaccurate | Medium | Medium | Conservative defaults; manual override | Fall back to age-only scoring |
| P1-06 | Phoenix crime API unavailable (noted Sep 2025) | High | Medium | Use FBI CDE as fallback | Default to city-level averages |
| P1-07 | FEMA API rate limiting | Low | Low | Cache responses; batch requests | Use cached zone data |
| P1-09 | Proxy costs exceed budget | Low | Medium | Start with IPRoyal; upgrade if needed | Direct requests with delays |
| P1-14 | Config migration breaks existing logic | Medium | High | Comprehensive test coverage; feature flags | Revert to hardcoded constants |
| P2-21 | Solar ROI calculation complexity | Medium | Low | Simplify to payback period only | Show raw data without calculation |

---

## 6. Quick Wins

Items completable in <30 minutes with high impact:

| ID | Action | Time | Impact | How |
|----|--------|------|--------|-----|
| P0-08 | Update pool cost | 15m | Medium | Edit `constants.py` line 201: `POOL_TOTAL_MONTHLY = 325` |
| P1-02 | Add commute cost | 15m | Medium | Add to `constants.py`: `COMMUTE_COST_PER_MILE = 0.685` |
| P1-16 | Validate HOA kill-switch | 10m | High | Verify in `kill_switch/criteria.py` - confirmed correct |
| P2-25 | Validate 4+ bedrooms | 10m | High | Verify in `kill_switch/criteria.py` - confirmed correct |
| P2-26 | Document HVAC lifespan | 20m | Low | Add note to deal sheet templates |
| P2-15 | Index extraction logs | 30m | Medium | Add JSON index to `run_history/` |

**Recommended Quick Win Session (1 hour):**
1. P0-08: Update pool cost constant (15m)
2. P1-02: Add commute cost constant (15m)
3. P2-15: Create extraction log index (30m)

---

## 7. Technical Debt Items

Items that improve code quality without adding features:

| ID | Description | Effort | Benefit |
|----|-------------|--------|---------|
| TD-01 | Consolidate scoring constants between `constants.py` and `scoring_weights.py` | 2d | Single source of truth |
| TD-02 | Add type hints to all service methods | 3d | IDE support, fewer bugs |
| TD-03 | Increase test coverage for scoring strategies (currently ~60%) | 4d | Regression prevention |
| TD-04 | Refactor extraction services to use common interface | 2d | Easier to add new sources |
| TD-05 | Add Pydantic schemas for all API responses | 2d | Type safety, validation |
| TD-06 | Document all constants with source citations | 1d | Traceability |
| TD-07 | Add pre-commit hooks for code quality | 1d | Consistent formatting |
| TD-08 | Migrate from print() to structured logging | 2d | Better observability |

**Technical Debt vs Feature Work:**
- Current technical debt: ~17 days
- Recommendation: Allocate 20% of sprint capacity to debt (1 day/week)

---

## 8. Deferred Items

Items explicitly NOT recommended for now, with rationale:

| ID | Item | Rationale | Revisit When |
|----|------|-----------|--------------|
| DEF-01 | NeighborhoodScout integration ($5K/year) | Cost prohibitive for current scale | Processing >500 properties/month |
| DEF-02 | UtilityAPI integration (paid) | Requires customer authorization | B2B use case emerges |
| DEF-03 | Arcadia enterprise integration | Overkill for single-user pipeline | Multi-tenant deployment |
| DEF-04 | Celery migration | RQ sufficient for current scale | Queue backups >30 seconds consistent |
| DEF-05 | DOE Home Energy Score | Requires assessor certification | Professional service offering |
| DEF-06 | Multi-machine worker pool | Current workload fits single machine | >1000 properties/batch |
| DEF-07 | Real-time appreciation tracking | Historical data sufficient | Investment analysis feature request |
| DEF-08 | Machine learning price prediction | Complexity vs value unclear | After core pipeline stable |

---

## 9. Implementation Schedule (Recommended)

### Sprint 1 (Week 1-2): Foundation
**Goal:** Unblock batch processing + add explanations

| Day | Actions | Owner |
|-----|---------|-------|
| 1 | P0-08, P1-02 (quick wins) | Config |
| 2-3 | P0-02 (job queue design + implementation) | Infra |
| 4-5 | P0-03 (progress visibility) | Infra |
| 6-7 | P0-04 (scoring explanations) | Core |
| 8 | P0-05 (kill-switch explanations) | Core |
| 9-10 | P0-01 (solar kill-switch) + P1-01 (solar bonus) | Config+Core |

**Sprint 1 Deliverables:**
- [ ] Job queue operational (8 properties in <10 min)
- [ ] Progress visible in work_items.json
- [ ] Score explanations in English
- [ ] Solar lease detection and handling

### Sprint 2 (Week 3-4): Data Quality + APIs
**Goal:** Lineage tracking + critical API integrations

| Day | Actions | Owner |
|-----|---------|-------|
| 1-4 | P0-06 (field lineage) | Core |
| 5-7 | P1-06 (Phoenix crime API) | API |
| 8-10 | P1-07 (FEMA flood API) | API |

**Sprint 2 Deliverables:**
- [ ] All enriched fields have lineage tracking
- [ ] Crime data from Phoenix Open Data
- [ ] Flood zones from FEMA NFHL

### Sprint 3 (Week 5-6): Scoring Enhancements
**Goal:** Roof material scoring + infrastructure APIs

| Day | Actions | Owner |
|-----|---------|-------|
| 1-2 | P1-04 (roof material differentiation) | Core |
| 3-4 | P1-05 (underlayment tracking) | Core |
| 5-7 | P1-18 (Maricopa GIS) | API |
| 8-10 | P1-10, P2-08 (retry + circuit breaker) | Infra |

**Sprint 3 Deliverables:**
- [ ] Roof scoring includes material type
- [ ] Tile roofs track underlayment age
- [ ] GIS validation of lot sizes
- [ ] Robust retry with circuit breaker

### Sprint 4 (Week 7-8): Configuration + Polish
**Goal:** Externalize config + remaining P1 items

| Day | Actions | Owner |
|-----|---------|-------|
| 1-2 | P1-14 (externalize kill-switch config) | Config |
| 3-4 | P1-15 (scoring weight versioning) | Config |
| 5-6 | P1-11 (cost breakdown in reports) | Core |
| 7-8 | P1-08 (equipment costs in deal sheets) | Reports |
| 9-10 | P1-09 (proxy integration) | Infra |

**Sprint 4 Deliverables:**
- [ ] Kill-switch criteria in YAML
- [ ] Scoring versions tracked per run
- [ ] Cost breakdown visible in reports
- [ ] Equipment replacement budgets in deal sheets
- [ ] Proxy rotation working

---

## 10. Success Metrics

### Phase 1 (Sprints 1-2) Success Criteria
- [ ] Image extraction: 8 properties in <10 minutes (was 30+ min)
- [ ] Each property has score explanation in natural language
- [ ] All data sources tracked in field lineage
- [ ] Crime data populated from Phoenix Open Data API
- [ ] Flood zones populated from FEMA API
- [ ] 100% of tests passing

### Phase 2 (Sprints 3-4) Success Criteria
- [ ] Roof scores differentiate tile vs shingle
- [ ] Lot sizes validated against GIS data
- [ ] Kill-switch config changes without code deployment
- [ ] Deal sheets include 5-year equipment replacement budgets
- [ ] Retry logic handles transient failures gracefully
- [ ] Proxy rotation achieving >90% success rate on Zillow

### Overall Metrics
| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| Properties/hour | 2 | 20 | Job queue + parallelization |
| Score explainability | 0% | 100% | Reasoning generation |
| Data lineage coverage | 0% | 95% | Field tracking |
| API success rate | ~70% | >95% | Proxy + retry |
| Configuration agility | Code deploy | Config reload | YAML externalization |

---

## Appendix A: File Reference Matrix

| File Path | Current Lines | Actions Affecting |
|-----------|---------------|-------------------|
| `src/phx_home_analysis/config/constants.py` | 601 | P0-08, P1-02, P1-03, P2-17 |
| `src/phx_home_analysis/config/scoring_weights.py` | 380 | P1-01, P1-04, P1-05, P2-03 |
| `src/phx_home_analysis/services/kill_switch/criteria.py` | ~200 | P0-01, P0-05, P1-14 |
| `src/phx_home_analysis/services/kill_switch/filter.py` | ~150 | P0-05 |
| `src/phx_home_analysis/services/scoring/scorer.py` | ~250 | P0-04, P1-15 |
| `src/phx_home_analysis/services/scoring/strategies/systems.py` | ~300 | P1-01, P1-04, P1-05, P2-03 |
| `src/phx_home_analysis/validation/schemas.py` | ~200 | P0-01, P1-05 |
| `scripts/extract_images.py` | ~500 | P0-02, P0-03, P1-10, P2-08 |
| `data/enrichment_data.json` | varies | P0-06, P2-13 |
| `data/work_items.json` | varies | P0-03 |

---

## Appendix B: Research Report Cross-Reference

| Report | Key Findings | Action Items Derived |
|--------|--------------|---------------------|
| Market-Alpha | HOA validated, 6.99% mortgage, $0.67/mile commute | P1-02, P1-16 |
| Market-Beta | Pool $250-400/mo, solar lease liability | P0-01, P0-08, P1-01, P1-13 |
| Market-Gamma | 4+ beds validated, emerging areas | P2-01, P2-02, P2-25 |
| Domain-Alpha | HVAC 10-15yr, tile vs shingle, foundation risk | P1-04, P1-05, P0-07, P1-08 |
| Domain-Beta | HOA verification, solar lease detection, ROC | P1-12, P1-13, P2-04 |
| Domain-Gamma | Septic severity, DAWS, GIS integration | P1-03, P1-17, P1-18, P2-05 |
| Tech-Alpha | FEMA NFHL, Assessor API confirmed | P1-07 |
| Tech-Beta | Phoenix crime API, WalkScore, EIA | P1-06, P2-06, P2-24 |
| Tech-Gamma | nodriver validated, Smartproxy, RQ | P1-09, P0-02, P1-10 |

---

**Document Status:** COMPLETE
**Last Updated:** December 2024
**Next Review:** After Sprint 1 completion

---

*This action items matrix provides a complete implementation roadmap. Each P0/P1 item includes sufficient detail for a developer to begin implementation immediately.*
