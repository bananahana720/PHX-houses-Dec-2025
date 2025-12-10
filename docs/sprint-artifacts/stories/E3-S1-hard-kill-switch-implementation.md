# Story 3.1: HARD Kill-Switch Criteria Implementation

Status: done

---

## Orchestration Metadata

<!--
ORCHESTRATION METADATA FIELDS (Required for all stories)
These fields enable wave planning, parallelization analysis, and cross-layer validation.
Reference: Epic 2 Supplemental Retrospective (2025-12-07) - Lesson L6: Cross-layer resonance
-->

**Model Tier:** sonnet
- **Justification:** Standard implementation task involving business logic (HARD criteria evaluation), type definitions, and test authoring. Does not require vision capabilities or complex architectural decisions that would warrant opus.

**Wave Assignment:** Wave 1
- **Dependencies:** E3.S0 (template orchestration metadata - must complete first to establish patterns)
- **Conflicts:** None - this is the foundation for E3 kill-switch work, no parallel stories modify same files
- **Parallelizable:** No - this is the core kill-switch foundation that E3.S2-S5 depend on

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
| orchestration | persistence | `src/phx_home_analysis/services/kill_switch/filter.py` | `CriterionResult` dataclass |
| orchestration | persistence | `src/phx_home_analysis/data/enrichment.py` | `KillSwitchResult` stored in `enrichment_data.json` |
| persistence | orchestration | `data/enrichment_data.json` | Property data with 8 kill-switch fields |

---

## Story

As a system user,
I want HARD kill-switch criteria that instantly reject properties,
so that non-negotiable deal-breakers are caught immediately.

## Acceptance Criteria

1. **AC1: HARD Criteria Implementation** - Any HARD criterion failing results in immediate "FAIL" verdict with specific criterion identified
2. **AC2: Short-Circuit Evaluation** - No further evaluation occurs after first HARD failure (short-circuit optimization)
3. **AC3: Five HARD Criteria** - Implement exactly 5 HARD criteria per Architecture:
   - `HOA = $0` (must have zero HOA)
   - `solar != lease` (solar must not be leased)
   - `beds >= 4` (minimum 4 bedrooms)
   - `baths >= 2` (minimum 2 bathrooms)
   - `sqft > 1800` (minimum 1800 square feet)
4. **AC4: Four SOFT Criteria** - Implement 4 SOFT criteria with severity accumulation:
   - `Sewer = city` (severity: 2.5)
   - `Year <= 2023` (severity: 2.0)
   - `Garage >= 2 indoor` (severity: 1.5)
   - `Lot 7k-15k sqft` (severity: 1.0)
5. **AC5: PASS Recording** - Passing all criteria results in "PASS" with all values recorded
6. **AC6: CriterionResult Output** - Each criterion returns `CriterionResult(passed: bool, value: Any, note: str)`

## Tasks / Subtasks

**NOTE: Implementation ALREADY EXISTS. Tasks focus on VALIDATION and ENHANCEMENT.**

- [x] Task 1: Validate KillSwitchFilter orchestrator (AC: 1, 2) - **VALIDATION** PASSED
  - [x] 1.1 Review `src/phx_home_analysis/services/kill_switch/filter.py` matches AC requirements
  - [x] 1.2 Verify short-circuit evaluation on first HARD failure (line ~175-187)
  - [x] 1.3 Confirm logging with trace IDs exists; add if missing
- [x] Task 2: Validate 5 HARD criterion implementations (AC: 3, 6) - **VALIDATION** PASSED
  - [x] 2.1 Verify `NoHoaKillSwitch` - fails if HOA > 0 (criteria.py:32-77)
  - [x] 2.2 Verify `NoSolarLeaseKillSwitch` - fails if solar leased (criteria.py:541-593)
  - [x] 2.3 Verify `MinBedroomsKillSwitch(min_beds=4)` - fails if beds < 4 (criteria.py:231-285)
  - [x] 2.4 Verify `MinBathroomsKillSwitch(min_baths=2.0)` - fails if baths < 2 (criteria.py:287-341)
  - [x] 2.5 Verify `MinSqftKillSwitch(min_sqft=1800)` - fails if sqft <= 1800 (criteria.py:343-402)
- [x] Task 3: Validate 4 SOFT criterion implementations (AC: 4, 6) - **VALIDATION** PASSED
  - [x] 3.1 Verify `CitySewerKillSwitch` - severity 2.5 (criteria.py:79-131)
  - [x] 3.2 Verify `NoNewBuildKillSwitch(max_year=2023)` - severity 2.0 (criteria.py:484-539)
  - [x] 3.3 Verify `MinGarageKillSwitch(min_spaces=2)` - severity 1.5 (criteria.py:133-229)
  - [x] 3.4 Verify `LotSizeKillSwitch(7000, 15000)` - severity 1.0 (criteria.py:404-482)
- [x] Task 4: Validate data contracts (AC: 5, 6) - **VALIDATION** PASSED
  - [x] 4.1 Review `CriterionResult` in explanation.py - verify passed, value, note fields
  - [x] 4.2 Review `KillSwitchVerdict` enum in base.py (PASS, WARNING, FAIL)
  - [x] 4.3 Review `VerdictExplanation` dataclass aggregating all criteria results
- [x] Task 5: Validate existing unit tests cover boundary cases (AC: 1-6) - **VALIDATION** PASSED
  - [x] 5.1 Review tests/unit/test_kill_switch.py for HARD boundary tests
  - [x] 5.2 Review SOFT severity accumulation tests (threshold >= 3.0)
  - [x] 5.3 Review short-circuit behavior tests
  - [x] 5.4 Review PASS verdict tests
- [x] Task 6: ADD cross-layer validation tests (AC: 1-6) - **ENHANCEMENT** (E2 Retro L6)
  - [x] 6.1 Fixed integration test conftest.py fixture with complete kill-switch fields
  - [x] 6.2 Verified type contract at KillSwitch->Property boundary
  - [x] 6.3 Verified CriterionResult schema matches persistence input schema

## Dev Notes

### CRITICAL: Existing Implementation Status

**The kill-switch system is ALREADY IMPLEMENTED. This story validates/enhances existing code.**

**Existing Code Location:** `src/phx_home_analysis/services/kill_switch/`

| File | Purpose | Lines |
|------|---------|-------|
| `filter.py` | KillSwitchFilter orchestrator | ~380 |
| `criteria.py` | 9 criterion implementations | ~593 |
| `base.py` | KillSwitch abstract class + KillSwitchVerdict enum | ~169 |
| `constants.py` | HARD/SOFT names, severity weights | ~89 |
| `explanation.py` | CriterionResult, VerdictExplanation | ~200 |

**Existing Tests:** `tests/unit/test_kill_switch.py` (75+ tests including boundary conditions)

### What the Dev Agent Should Do

1. **VALIDATE** existing implementation matches AC1-AC6
2. **ADD** any missing cross-layer validation tests per E2 Retro lesson L6
3. **VERIFY** CriterionResult output format alignment with persistence schema
4. **ENHANCE** if gaps found; DO NOT recreate existing code

### Architecture Reference

- **Architecture:** Per ADR-04 (All Kill-Switch Criteria Are HARD) - originally 8 HARD, now 5 HARD + 4 SOFT
- **Location:** Already implemented in `src/phx_home_analysis/services/kill_switch/`
- **Pattern:** Each criterion is a separate class implementing `KillSwitch` abstract base class
- **Data Source:** Property data from `enrichment_data.json` contains all 8 kill-switch fields via PhoenixMLS extraction
- **Severity Thresholds:** SOFT criteria total >= 3.0 = FAIL, 1.5-3.0 = WARNING, < 1.5 = PASS

### Existing Criterion Classes (Already Implemented)

**HARD Criteria (5):**
- `NoHoaKillSwitch` - fails if HOA > 0
- `NoSolarLeaseKillSwitch` - fails if solar is leased
- `MinBedroomsKillSwitch(min_beds=4)` - fails if beds < 4
- `MinBathroomsKillSwitch(min_baths=2.0)` - fails if baths < 2
- `MinSqftKillSwitch(min_sqft=1800)` - fails if sqft <= 1800

**SOFT Criteria (4):**
- `CitySewerKillSwitch` - severity 2.5 if not city sewer
- `NoNewBuildKillSwitch(max_year=2023)` - severity 2.0 if year > 2023
- `MinGarageKillSwitch(min_spaces=2, indoor_required=True)` - severity 1.5 if garage < 2
- `LotSizeKillSwitch(min_sqft=7000, max_sqft=15000)` - severity 1.0 if lot outside range

### Project Structure Notes

**EXISTING STRUCTURE (Already Implemented):**
- `src/phx_home_analysis/services/kill_switch/`
  - `__init__.py` - exports KillSwitchFilter, KillSwitchVerdict, criteria classes
  - `filter.py` - KillSwitchFilter orchestrator class
  - `criteria.py` - All 9 criterion implementations (5 HARD + 4 SOFT)
  - `base.py` - KillSwitch abstract base class, KillSwitchVerdict enum
  - `constants.py` - HARD_CRITERIA_NAMES, SOFT_SEVERITY_WEIGHTS, thresholds
  - `explanation.py` - CriterionResult, VerdictExplanation, VerdictExplainer

**EXISTING TESTS:**
- `tests/unit/test_kill_switch.py` - 75+ unit tests including boundary conditions
- `tests/integration/test_kill_switch_chain.py` - Severity accumulation system validation

### References

- [Source: docs/epics/epic-3-kill-switch-filtering-system.md#E3.S1] - Story requirements
- [Source: docs/architecture/kill-switch-architecture.md] - Kill-switch design decisions
- [Source: CLAUDE.md#Kill-Switches] - 5 HARD + 4 SOFT criteria specification
- [Source: docs/sprint-artifacts/epic-2-retro-supplemental-2025-12-07.md] - Cross-layer validation requirements

---

## Cross-Layer Validation Checklist

<!--
CROSS-LAYER VALIDATION (Required before Definition of Done)
Ensures all affected layers communicate properly and data flows end-to-end.
-->

- [x] **Extraction -> Persistence:** PhoenixMLS extraction outputs 8 kill-switch fields that match KillSwitchFilter input schema - VALIDATED via integration tests
- [x] **Persistence Verification:** Property data flows correctly through KillSwitchFilter - VALIDATED via 115 tests
- [x] **Orchestration Wiring:** KillSwitchFilter correctly instantiated with proper config - VALIDATED via filter.py review
- [x] **End-to-End Trace:** Integration tests validate full filter -> verdict flow - 26 chain tests pass
- [x] **Type Contract Tests:** Fixed integration conftest.py to include SewerType, SolarStatus enums - type safety confirmed

---

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Template validation: This draft validates E3.S0 story template orchestration metadata format
- All orchestration metadata fields populated (model_tier, wave, dependencies, conflicts, parallelizable)
- Layer touchpoints documented with integration points table
- Cross-layer validation checklist applicable to kill-switch implementation

### File List

**EXISTING FILES (Validate/Enhance):**
- `src/phx_home_analysis/services/kill_switch/__init__.py` - Package exports
- `src/phx_home_analysis/services/kill_switch/filter.py` - KillSwitchFilter orchestrator
- `src/phx_home_analysis/services/kill_switch/base.py` - Abstract base class, enums
- `src/phx_home_analysis/services/kill_switch/criteria.py` - All 9 criterion implementations
- `src/phx_home_analysis/services/kill_switch/constants.py` - Thresholds, weights
- `src/phx_home_analysis/services/kill_switch/explanation.py` - CriterionResult, explanations
- `tests/unit/test_kill_switch.py` - 75+ unit tests
- `tests/integration/test_kill_switch_chain.py` - Integration tests

**MAY BE ADDED (Cross-Layer Validation - E2 Retro L6):**
- `tests/integration/test_kill_switch_cross_layer.py` - Extraction->persistence trace tests

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-07 | Draft created using new orchestration metadata template (E3.S0 validation) | Dev Agent |
| 2025-12-10 | Status: drafted -> ready-for-dev. Tasks revised to VALIDATION scope (existing impl found). Added cross-layer validation tasks per E2 Retro L6. | PM Agent (create-story workflow) |
| 2025-12-10 | Status: ready-for-dev -> done. All 6 tasks validated. Fixed integration test conftest.py (missing kill-switch fields). Fixed base.py type annotation (any -> Any). 115 tests passing (89 unit + 26 integration). | Dev Agent (dev-story workflow) |
