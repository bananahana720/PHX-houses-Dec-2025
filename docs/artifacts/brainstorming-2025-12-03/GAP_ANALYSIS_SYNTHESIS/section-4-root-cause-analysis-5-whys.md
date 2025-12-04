# Section 4: Root Cause Analysis (5 Whys)

### Root Cause 1: No Job Queue Architecture
**Problem**: Image extraction blocks 30+ minutes; users see black box
**Why 1**: Currently sequential `extract_images.py --all` processes properties one-at-a-time
**Why 2**: ProcessPool exists but not used; no queue abstraction
**Why 3**: Extraction is I/O-bound (waiting for Zillow API) but treated as CPU-bound
**Why 4**: Original design focused on correctness (dedup, state) not throughput
**Why 5**: **Root**: No background job framework designed (RQ, Celery, etc.) + no async/await pattern for HTTP calls

**Affects**: IP-01, IP-02, IP-03, IP-04, IP-05
**Fix**: Design job queue layer (Pydantic models for jobs, job states, retry policies)

---

### Root Cause 2: Scoring Black Box
**Problem**: Users see "480/600" but don't understand what contributes to score
**Why 1**: PropertyScorer.score() returns ScoreBreakdown (structured data) but no human text
**Why 2**: ScoreBreakdown is 600+ lines of numeric data with no narrative
**Why 3**: Reasoning generation not included in service layer
**Why 4**: Original focus was correctness (weighted calculation) not communication
**Why 5**: **Root**: No "explain myself" pattern in domain services; reasoning seen as post-hoc not core

**Affects**: XT-09, XT-10, XT-11, VB-01
**Fix**: Add ReasoningEngine service that traverses score breakdown and generates text explanations

---

### Root Cause 3: Hard-Coded Buyer Criteria
**Problem**: Kill-switch severity weights and tier thresholds in `constants.py`; can't A/B test
**Why 1**: Criteria is business logic, not configuration
**Why 2**: When changes needed, must edit source code
**Why 3**: No version control for which criteria set was used for each run
**Why 4**: Original design assumed fixed buyer profile; no multi-tenant use case
**Why 5**: **Root**: Configuration management not included in domain model; criteria treated as immutable code not variable settings

**Affects**: XT-05, XT-06, XT-08
**Fix**: Design BuyerProfile versioning (YAML config + version tracking in run metadata)

---

### Root Cause 4: No Data Lineage
**Problem**: Can't trace where a field's value came from; don't know if it's enriched or canonical
**Why 1**: enrichment_data.json populated incrementally by phases but no source tracking
**Why 2**: field_lineage.json structure designed but never populated
**Why 3**: Agents/scripts update properties but don't call lineage.record()
**Why 4**: Original design focused on data correctness not provenance
**Why 5**: **Root**: No lineage middleware in repository layer; lineage is optional not mandatory

**Affects**: XT-01, XT-03, XT-04, Traceability cluster
**Fix**: Add LineageRecorder service; make all repository writes log source/timestamp/confidence

---

### Root Cause 5: No Kill-Switch Interpretability
**Problem**: User sees "FAIL: sewer=Y, year=2020" but doesn't understand severity model
**Why 1**: KillSwitchFilter.evaluate() returns bool (pass/fail) + list of failures; no explanation
**Why 2**: Severity weights exist (constants.py) but not surfaced to user
**Why 3**: User doesn't see: "sewer adds 2.5, year adds 2.0, total 4.5 >= 3.0 threshold = FAIL"
**Why 4**: Original verdict design: just yes/no; interpretation seen as separate concern
**Why 5**: **Root**: Kill-switch verdict objects don't include "reasoning" field; calculation ephemeral not preserved

**Affects**: XT-10, VB-02, Explainability cluster
**Fix**: Enhance KillSwitchVerdict dataclass with explanation text and severity breakdown

---
