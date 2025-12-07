# Story 3.1: HARD Kill-Switch Criteria Implementation

Status: drafted

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

- [ ] Task 1: Create KillSwitchFilter orchestrator class (AC: 1, 2)
  - [ ] 1.1 Define `KillSwitchFilter` class in `src/phx_home_analysis/services/kill_switch/filter.py`
  - [ ] 1.2 Implement short-circuit evaluation on first HARD failure
  - [ ] 1.3 Add comprehensive logging with trace IDs
- [ ] Task 2: Implement 5 HARD criterion classes (AC: 3, 6)
  - [ ] 2.1 Create `HoaCriterion` - fails if HOA > 0
  - [ ] 2.2 Create `SolarCriterion` - fails if solar is leased
  - [ ] 2.3 Create `BedroomsCriterion` - fails if beds < 4
  - [ ] 2.4 Create `BathroomsCriterion` - fails if baths < 2
  - [ ] 2.5 Create `SquareFootageCriterion` - fails if sqft <= 1800
- [ ] Task 3: Implement 4 SOFT criterion classes (AC: 4, 6)
  - [ ] 3.1 Create `SewerCriterion` - severity 2.5 if not city sewer
  - [ ] 3.2 Create `YearBuiltCriterion` - severity 2.0 if year > 2023
  - [ ] 3.3 Create `GarageCriterion` - severity 1.5 if garage < 2 indoor
  - [ ] 3.4 Create `LotSizeCriterion` - severity 1.0 if lot outside 7k-15k sqft
- [ ] Task 4: Define data contracts (AC: 5, 6)
  - [ ] 4.1 Create `CriterionResult` dataclass with passed, value, note fields
  - [ ] 4.2 Create `KillSwitchVerdict` enum (PASS, WARNING, FAIL)
  - [ ] 4.3 Create `KillSwitchResult` dataclass aggregating all criteria results
- [ ] Task 5: Write unit tests with boundary cases (AC: 1-6)
  - [ ] 5.1 Test each HARD criterion at boundary values
  - [ ] 5.2 Test SOFT severity accumulation (threshold >= 3.0)
  - [ ] 5.3 Test short-circuit behavior (no SOFT eval after HARD fail)
  - [ ] 5.4 Test PASS verdict with all criteria satisfied
- [ ] Task 6: Write integration test for full flow (AC: 1-6)
  - [ ] 6.1 Test with real property data from enrichment_data.json
  - [ ] 6.2 Verify results persist correctly to kill_switch section

## Dev Notes

- **Architecture:** Per ADR-04 (All Kill-Switch Criteria Are HARD) - originally 8 HARD, now 5 HARD + 4 SOFT
- **Location:** Implement in `src/phx_home_analysis/services/kill_switch/` directory
- **Pattern:** Each criterion is a separate class implementing `BaseCriterion` abstract class
- **Data Source:** Property data from `enrichment_data.json` contains all 8 kill-switch fields via PhoenixMLS extraction
- **Severity Threshold:** SOFT criteria total >= 3.0 = FAIL, 1.5-3.0 = WARNING, < 1.5 = PASS

### Project Structure Notes

- New directory: `src/phx_home_analysis/services/kill_switch/`
  - `__init__.py` - exports KillSwitchFilter, CriterionResult, KillSwitchResult
  - `filter.py` - orchestrator class
  - `criteria/` - individual criterion implementations
  - `models.py` - data contracts (CriterionResult, KillSwitchVerdict, KillSwitchResult)
- Tests: `tests/unit/services/kill_switch/` and `tests/integration/services/`

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

- [ ] **Extraction -> Persistence:** PhoenixMLS extraction outputs 8 kill-switch fields that match KillSwitchFilter input schema
- [ ] **Persistence Verification:** KillSwitchResult written to enrichment_data.json, read-back validates data integrity
- [ ] **Orchestration Wiring:** KillSwitchFilter correctly instantiated in pipeline orchestrator with proper config
- [ ] **End-to-End Trace:** Test from raw property data -> KillSwitchFilter -> persisted result with trace logging
- [ ] **Type Contract Tests:** CriterionResult field types match persistence schema (no string/enum mismatches)

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

**To Be Created:**
- `src/phx_home_analysis/services/kill_switch/__init__.py`
- `src/phx_home_analysis/services/kill_switch/filter.py`
- `src/phx_home_analysis/services/kill_switch/models.py`
- `src/phx_home_analysis/services/kill_switch/criteria/__init__.py`
- `src/phx_home_analysis/services/kill_switch/criteria/hard.py`
- `src/phx_home_analysis/services/kill_switch/criteria/soft.py`
- `tests/unit/services/kill_switch/test_filter.py`
- `tests/unit/services/kill_switch/test_criteria.py`
- `tests/integration/services/test_kill_switch_flow.py`

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-07 | Draft created using new orchestration metadata template (E3.S0 validation) | Dev Agent |
