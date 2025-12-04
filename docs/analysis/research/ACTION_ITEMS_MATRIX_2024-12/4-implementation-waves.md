# 4. Implementation Waves

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
