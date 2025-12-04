# Core Architectural Decisions

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
