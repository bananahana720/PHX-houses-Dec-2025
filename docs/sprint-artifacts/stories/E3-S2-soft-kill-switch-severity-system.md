# Story 3.2: SOFT Kill-Switch Severity System

Status: done

---

## Orchestration Metadata

<!--
ORCHESTRATION METADATA FIELDS (Required for all stories)
These fields enable wave planning, parallelization analysis, and cross-layer validation.
Reference: Epic 2 Supplemental Retrospective (2025-12-07) - Lesson L6: Cross-layer resonance
-->

**Model Tier:** sonnet
- **Justification:** Standard implementation task involving business logic (SOFT severity evaluation), threshold-based verdicts, and CSV configuration loading. Does not require vision capabilities or complex architectural decisions. The implementation builds on existing patterns from E3.S1.

**Wave Assignment:** Wave 2
- **Dependencies:** E3.S1 (HARD Kill-Switch Criteria - must complete first for base classes and patterns)
- **Conflicts:** E3.S3 (Kill-Switch Verdict Evaluation) - both modify verdict calculation logic; run sequentially
- **Parallelizable:** No - E3.S3 depends on severity system being complete

---

## Layer Touchpoints

<!--
LAYER TOUCHPOINTS (Required for implementation stories)
Documents which system layers this story affects and their integration points.
-->

**Layers Affected:** persistence, orchestration

**Integration Points:**
| Source Layer | Target Layer | Interface/File | Data Contract |
|--------------|--------------|----------------|---------------|
| orchestration | persistence | `src/phx_home_analysis/services/kill_switch/severity.py` (NEW) | `SoftSeverityResult` dataclass |
| persistence | orchestration | `config/kill_switch.csv` (NEW) | CSV schema: name,type,operator,threshold,severity,description |
| orchestration | persistence | `src/phx_home_analysis/services/kill_switch/filter.py` | Updated to use `SoftSeverityEvaluator` |

---

## Story

As a system user,
I want a SOFT severity system for future flexibility,
so that I can add non-critical preferences that accumulate.

## Acceptance Criteria

1. **AC1: Severity Accumulation** - SOFT criteria accumulate severity scores when they fail; each failed SOFT criterion adds its severity weight to the running total
2. **AC2: Threshold-Based Verdicts** - Total severity determines verdict:
   - `>= 3.0` = FAIL (severity threshold exceeded)
   - `1.5 - 2.99` = WARNING (approaching threshold)
   - `< 1.5` = PASS (acceptable severity level)
3. **AC3: Current SOFT Criteria Active** - Per PRD and E3.S1, 4 SOFT criteria are currently active:
   - `city_sewer` (severity: 2.5) - City sewer required
   - `no_new_build` (severity: 2.0) - No new builds after 2023
   - `min_garage` (severity: 1.5) - Minimum 2 garage spaces
   - `lot_size` (severity: 1.0) - Lot size 7k-15k sqft
4. **AC4: Config-Driven Loading** - System can load SOFT criteria definitions from `config/kill_switch.csv` for future configuration without code changes
5. **AC5: SoftSeverityEvaluator Class** - Dedicated evaluator class that:
   - Accepts list of failed SOFT criteria with weights
   - Calculates total severity score
   - Returns verdict with breakdown

## Tasks / Subtasks

**NOTE: Severity system is PARTIALLY IMPLEMENTED in E3.S1. This story COMPLETES and ENHANCES.**

- [x] Task 1: Create SoftSeverityEvaluator class (AC: 1, 2, 5)
  - [x] 1.1 Create `src/phx_home_analysis/services/kill_switch/severity.py`
  - [x] 1.2 Implement `SoftSeverityEvaluator` class with `evaluate(soft_results: list[CriterionResult]) -> SoftSeverityResult`
  - [x] 1.3 Implement `SoftSeverityResult` dataclass with: total_severity, verdict, failed_criteria, breakdown
  - [x] 1.4 Implement threshold constants (already exist in constants.py: SEVERITY_FAIL_THRESHOLD=3.0, SEVERITY_WARNING_THRESHOLD=1.5)
- [x] Task 2: Create CSV configuration schema (AC: 4)
  - [x] 2.1 Create `config/kill_switch.csv` with columns: name, type, operator, threshold, severity, description
  - [x] 2.2 Populate with current 4 SOFT criteria from constants.py
  - [x] 2.3 Create `SoftCriterionConfig` Pydantic model for CSV row validation
  - [x] 2.4 Implement `load_soft_criteria_config(path: Path) -> list[SoftCriterionConfig]`
- [x] Task 3: Integrate SoftSeverityEvaluator into KillSwitchFilter (AC: 1, 2, 3)
  - [x] 3.1 Update `filter.py` to use SoftSeverityEvaluator for SOFT evaluation
  - [x] 3.2 Ensure backward compatibility with existing evaluate_with_severity() method
  - [x] 3.3 Update __init__.py exports to include new classes
- [x] Task 4: Unit tests for severity system (AC: 1-5)
  - [x] 4.1 Test severity accumulation (single SOFT failure, multiple SOFT failures)
  - [x] 4.2 Test threshold boundaries (exactly 1.5, 2.9, 3.0, 3.1)
  - [x] 4.3 Test PASS verdict (0.0, 0.5, 1.0, 1.4 severity)
  - [x] 4.4 Test WARNING verdict (1.5, 2.0, 2.5, 2.9 severity)
  - [x] 4.5 Test FAIL verdict (3.0, 3.5, 4.0, 7.0 severity)
  - [x] 4.6 Test CSV loading and validation
- [x] Task 5: Documentation for future additions (AC: 4)
  - [x] 5.1 Add docstrings explaining CSV schema and how to add new SOFT criteria
  - [x] 5.2 Document severity weight guidelines (how to choose appropriate weights)
  - [x] 5.3 Add example future SOFT criterion in comments (e.g., "Pool" with severity 0.5)

## Dev Notes

### CRITICAL: Partial Implementation Status

**The severity system is PARTIALLY implemented in E3.S1. This story creates a dedicated evaluator class and CSV configuration.**

**Existing Severity Code (from E3.S1):**
- `filter.py:137-155` - `_calculate_verdict()` method already handles severity thresholds
- `filter.py:157-187` - `evaluate_with_severity()` method calculates severity score
- `constants.py:46-51` - `SEVERITY_FAIL_THRESHOLD=3.0`, `SEVERITY_WARNING_THRESHOLD=1.5`
- `constants.py:85-98` - `SOFT_SEVERITY_WEIGHTS` dict with 4 criteria weights

**What This Story Adds:**
1. **SoftSeverityEvaluator** - Dedicated class (Single Responsibility Principle)
2. **CSV Configuration** - Future flexibility without code changes
3. **SoftSeverityResult** - Rich result object with breakdown
4. **Enhanced Documentation** - For future SOFT criteria additions

### Architecture Reference

- **Current Severity Logic Location:** `src/phx_home_analysis/services/kill_switch/filter.py:137-187`
- **Constants Location:** `src/phx_home_analysis/services/kill_switch/constants.py`
- **Config Constants Location:** `src/phx_home_analysis/config/constants.py:46-51`
- **Pattern:** Extract severity calculation into dedicated evaluator class

### Current SOFT Criteria (from E3.S1 / constants.py)

| Criterion | Severity Weight | Condition for Failure |
|-----------|-----------------|----------------------|
| `city_sewer` | 2.5 | Sewer type is not CITY |
| `no_new_build` | 2.0 | Year built > 2023 |
| `min_garage` | 1.5 | Garage spaces < 2 |
| `lot_size` | 1.0 | Lot outside 7k-15k sqft range |

### Severity Accumulation Examples

| Failed Criteria | Total Severity | Verdict |
|-----------------|----------------|---------|
| None | 0.0 | PASS |
| lot_size only | 1.0 | PASS |
| min_garage only | 1.5 | WARNING |
| lot_size + min_garage | 2.5 | WARNING |
| city_sewer only | 2.5 | WARNING |
| city_sewer + lot_size | 3.5 | FAIL |
| min_garage + no_new_build | 3.5 | FAIL |
| All 4 SOFT fail | 7.0 | FAIL |

### CSV Schema for config/kill_switch.csv

```csv
name,type,operator,threshold,severity,description
city_sewer,SOFT,==,CITY,2.5,City sewer required (no septic)
no_new_build,SOFT,<=,2023,2.0,No new builds (year <= 2023)
min_garage,SOFT,>=,2,1.5,Minimum 2 garage spaces
lot_size,SOFT,range,7000-15000,1.0,Lot size 7k-15k sqft preferred
```

### Project Structure Notes

**Existing Files (Enhance):**
- `src/phx_home_analysis/services/kill_switch/filter.py` - Integrate SoftSeverityEvaluator
- `src/phx_home_analysis/services/kill_switch/constants.py` - Reference for weights
- `src/phx_home_analysis/services/kill_switch/__init__.py` - Add exports

**New Files (Create):**
- `src/phx_home_analysis/services/kill_switch/severity.py` - SoftSeverityEvaluator class
- `config/kill_switch.csv` - CSV configuration file

### References

- [Source: docs/epics/epic-3-kill-switch-filtering-system.md#E3.S2] - Story requirements
- [Source: docs/sprint-artifacts/stories/E3-S1-hard-kill-switch-implementation.md] - Previous story patterns
- [Source: CLAUDE.md#Kill-Switches] - 5 HARD + 4 SOFT criteria specification
- [Source: src/phx_home_analysis/services/kill_switch/filter.py:137-187] - Existing severity calculation
- [Source: src/phx_home_analysis/services/kill_switch/constants.py:85-98] - SOFT weights definition

---

## Cross-Layer Validation Checklist

<!--
CROSS-LAYER VALIDATION (Required before Definition of Done)
Ensures all affected layers communicate properly and data flows end-to-end.
Source: Epic 2 Supplemental Retrospective - Lesson L6, Team Agreement TA1
-->

- [x] **Extraction -> Persistence:** CSV config loads correctly into SoftCriterionConfig models
- [x] **Persistence Verification:** SoftSeverityResult correctly serializes for storage (to_dict method)
- [x] **Orchestration Wiring:** SoftSeverityEvaluator correctly instantiated in KillSwitchFilter
- [x] **End-to-End Trace:** Full SOFT evaluation flow from Property -> SoftSeverityResult
- [x] **Type Contract Tests:** Verify SoftSeverityResult fields match expected types

---

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debug issues encountered

### Completion Notes List

1. Created `severity.py` with SoftSeverityEvaluator class and SoftSeverityResult dataclass
2. Created `config/kill_switch.csv` with full schema and 4 SOFT + 5 HARD criteria
3. Integrated SoftSeverityEvaluator into KillSwitchFilter with `evaluate_soft_severity()` method
4. Added 54 unit tests covering all severity scenarios and boundary conditions
5. All tests pass (94 total in kill_switch module)
6. Documentation complete with severity weight guidelines and future addition examples

### File List

**Existing Files (Enhance):**
- `src/phx_home_analysis/services/kill_switch/filter.py` - Integrate SoftSeverityEvaluator
- `src/phx_home_analysis/services/kill_switch/__init__.py` - Add new exports

**New Files (Create):**
- `src/phx_home_analysis/services/kill_switch/severity.py` - SoftSeverityEvaluator, SoftSeverityResult
- `config/kill_switch.csv` - CSV configuration for SOFT criteria
- `tests/unit/services/kill_switch/test_severity.py` - Unit tests for severity evaluator

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-10 | Story created via create-story workflow. Status: ready-for-dev. Comprehensive context from E3.S1 and existing implementation incorporated. | PM Agent (create-story workflow) |
| 2025-12-10 | Story completed. All tasks implemented: SoftSeverityEvaluator class, CSV config schema, KillSwitchFilter integration, 54 unit tests, documentation. Status: done. | Dev Agent (Claude Opus 4.5) |
