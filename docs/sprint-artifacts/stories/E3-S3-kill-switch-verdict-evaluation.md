# Story 3.3: Kill-Switch Verdict Evaluation

Status: done

---

## Orchestration Metadata

<!--
ORCHESTRATION METADATA FIELDS (Required for all stories)
These fields enable wave planning, parallelization analysis, and cross-layer validation.
Reference: Epic 2 Supplemental Retrospective (2025-12-07) - Lesson L6: Cross-layer resonance

Field Definitions:
- model_tier: AI model appropriate for story complexity
  - haiku: Simple tasks (documentation, templates, minor updates)
  - sonnet: Standard implementation (CRUD, integrations, business logic)
  - opus: Complex tasks requiring vision, architecture decisions, or deep reasoning
- wave: Execution wave number (0=foundation, 1+=implementation waves)
- parallelizable: Can this story run simultaneously with others in same wave?
- dependencies: Story IDs that must complete before this story starts
- conflicts: Story IDs that modify same files/data (cannot run in parallel)
-->

**Model Tier:** sonnet
- **Justification:** Standard implementation task involving dataclass creation, verdict formatting utilities, and integration with existing KillSwitchFilter. Does not require vision capabilities or complex architectural reasoning. Builds on well-established patterns from E3.S1 and E3.S2.

**Wave Assignment:** Wave 2
- **Dependencies:** E3.S1 (HARD Kill-Switch Criteria - provides KillSwitchVerdict enum, CriterionResult), E3.S2 (SOFT Severity System - provides SoftSeverityResult, severity evaluation)
- **Conflicts:** None - E3.S2 is complete, and E3.S4/E3.S5 depend on this story completing first
- **Parallelizable:** No - E3.S4 (Failure Explanations) depends on KillSwitchResult being available

---

## Layer Touchpoints

<!--
LAYER TOUCHPOINTS (Required for implementation stories)
Documents which system layers this story affects and their integration points.
Purpose: Prevent "extraction works but persistence doesn't" bugs (E2 Retrospective).

Layer Types:
- extraction: Data gathering from external sources (APIs, web scraping)
- persistence: Data storage and retrieval (JSON, database, cache)
- orchestration: Pipeline coordination, state management, agent spawning
- reporting: Output generation (deal sheets, visualizations, exports)
-->

**Layers Affected:** persistence, orchestration, reporting

**Integration Points:**
| Source Layer | Target Layer | Interface/File | Data Contract |
|--------------|--------------|----------------|---------------|
| orchestration | persistence | `src/phx_home_analysis/services/kill_switch/result.py` (NEW) | `KillSwitchResult` dataclass |
| orchestration | persistence | `src/phx_home_analysis/services/kill_switch/result.py` (NEW) | `FailedCriterion` dataclass |
| orchestration | reporting | `src/phx_home_analysis/services/kill_switch/formatting.py` (NEW) | `format_verdict()`, `format_result()` |
| orchestration | orchestration | `src/phx_home_analysis/services/kill_switch/filter.py` | Updated `evaluate_to_result()` method |

---

## Story

As a system user,
I want a clear verdict (PASS/FAIL/WARNING) for each property with comprehensive result details,
so that I can quickly filter properties and understand exactly why each was evaluated as it was.

## Acceptance Criteria

1. **AC1: KillSwitchResult Dataclass** - Result includes:
   - `verdict: KillSwitchVerdict` (PASS/WARNING/FAIL enum)
   - `failed_criteria: list[FailedCriterion]` (all failed criteria, not just first)
   - `severity_score: float` (accumulated SOFT severity)
   - `timestamp: datetime` (evaluation timestamp)
   - `property_address: str` (for identification in reports)

2. **AC2: FailedCriterion Dataclass** - Each failed criterion includes:
   - `name: str` (criterion identifier, e.g., "no_hoa")
   - `actual_value: Any` (what the property actually has)
   - `required_value: str` (human-readable requirement)
   - `is_hard: bool` (True for HARD criteria, False for SOFT)
   - `severity: float` (severity weight for SOFT criteria, 0.0 for HARD)

3. **AC3: Verdict Formatting** - Clear verdict display:
   - PASS = green circle + "PASS" (accessible)
   - WARNING = yellow circle + "WARNING" (accessible)
   - FAIL = red circle + "FAIL" (accessible)
   - Format: `format_verdict(verdict) -> str` returning emoji + text

4. **AC4: Result Formatting** - Full breakdown format:
   - `format_result(result) -> str` for complete human-readable output
   - Lists all failed criteria with actual vs required values
   - Highlights most impactful criteria (HARD failures first, then by severity)
   - Includes severity score and threshold comparison

5. **AC5: Integration Method** - KillSwitchFilter gains:
   - `evaluate_to_result(property: Property) -> KillSwitchResult`
   - Returns complete result object with all metadata
   - Backward compatible (existing methods unchanged)

## Tasks / Subtasks

**NOTE: This story creates NEW dataclasses and formatting utilities. Builds on existing evaluation logic.**

- [x] Task 1: Create KillSwitchResult dataclass (AC: 1, 5)
  - [x] 1.1 Create `src/phx_home_analysis/services/kill_switch/result.py`
  - [x] 1.2 Implement `KillSwitchResult` dataclass with verdict, failed_criteria, severity_score, timestamp, property_address
  - [x] 1.3 Add `to_dict()` method for JSON serialization
  - [x] 1.4 Add `__str__()` method for quick summary display
  - [x] 1.5 Add `is_passing` property (True if verdict != FAIL)

- [x] Task 2: Create FailedCriterion dataclass (AC: 2)
  - [x] 2.1 Add `FailedCriterion` to `result.py` with name, actual_value, required_value, is_hard, severity
  - [x] 2.2 Add `to_dict()` method for JSON serialization
  - [x] 2.3 Add `__str__()` method for human-readable format

- [x] Task 3: Create verdict formatting utilities (AC: 3, 4)
  - [x] 3.1 Create `src/phx_home_analysis/services/kill_switch/formatting.py`
  - [x] 3.2 Implement `format_verdict(verdict: KillSwitchVerdict) -> str` with emoji + text
  - [x] 3.3 Implement `format_result(result: KillSwitchResult) -> str` for full breakdown
  - [x] 3.4 Add plain-text fallback mode for non-emoji environments (accessibility)

- [x] Task 4: Integrate evaluate_to_result into KillSwitchFilter (AC: 5)
  - [x] 4.1 Add `evaluate_to_result(property: Property) -> KillSwitchResult` method to filter.py
  - [x] 4.2 Build FailedCriterion list from existing evaluation logic
  - [x] 4.3 Include timestamp and property address in result
  - [x] 4.4 Ensure backward compatibility with existing evaluate methods

- [x] Task 5: Update package exports (AC: 1-5)
  - [x] 5.1 Update `__init__.py` to export KillSwitchResult, FailedCriterion
  - [x] 5.2 Update `__init__.py` to export format_verdict, format_result
  - [x] 5.3 Update module docstring with new usage examples

- [x] Task 6: Unit tests for result evaluation (AC: 1-5)
  - [x] 6.1 Test KillSwitchResult dataclass fields and serialization
  - [x] 6.2 Test FailedCriterion dataclass with HARD and SOFT examples
  - [x] 6.3 Test format_verdict for all three verdicts (PASS, WARNING, FAIL)
  - [x] 6.4 Test format_result output format and ordering
  - [x] 6.5 Test evaluate_to_result integration with existing filter
  - [x] 6.6 Test timestamp generation and property_address inclusion
  - [x] 6.7 Test is_passing property for all verdict types

## Dev Notes

### CRITICAL: This Story Creates NEW Components

**This story creates new dataclasses and formatting utilities to wrap existing evaluation logic.**

**Existing Code to Integrate With:**
- `filter.py:167-197` - `evaluate_with_severity()` returns (verdict, severity, failures)
- `filter.py:199-255` - `evaluate_with_explanation()` returns (verdict, severity, failures, explanation)
- `explanation.py:19-36` - `CriterionResult` dataclass (reuse for internal tracking)
- `base.py:47-53` - `KillSwitchVerdict` enum (PASS, WARNING, FAIL)

**New Files to Create:**
1. `result.py` - KillSwitchResult and FailedCriterion dataclasses
2. `formatting.py` - Verdict and result formatting utilities

### Architecture Reference

- **Pattern:** Wrap existing evaluation tuple return into rich result object
- **Location:** `src/phx_home_analysis/services/kill_switch/`
- **Reuse:** Leverage existing `CriterionResult` internally, expose `FailedCriterion` externally
- **Backward Compatible:** Existing methods remain unchanged, new method added

### Data Flow

```
Property -> KillSwitchFilter.evaluate_to_result()
         -> Internal: evaluate_with_severity() + criterion checks
         -> Build FailedCriterion list from failures
         -> KillSwitchResult(verdict, failed_criteria, severity, timestamp, address)
         -> format_result() for display
```

### Verdict Emoji Formatting

```python
VERDICT_FORMATS = {
    KillSwitchVerdict.PASS: "PASS",      # Green circle + PASS
    KillSwitchVerdict.WARNING: "WARNING", # Yellow circle + WARNING
    KillSwitchVerdict.FAIL: "FAIL",      # Red circle + FAIL
}
```

**Accessibility Note:** Always include text alongside emoji for screen reader compatibility.

### Example Output Format

```
Kill-Switch Verdict: FAIL

Property: 123 Main St, Phoenix, AZ
Timestamp: 2025-12-10T14:30:00

HARD Failures (Instant Fail):
  - no_hoa: Has HOA $150/month (required: $0)

SOFT Failures (Severity: 3.5 >= 3.0):
  - city_sewer (severity 2.5): Has septic (required: city sewer)
  - lot_size (severity 1.0): Lot 6000 sqft (required: 7000-15000 sqft)

Total Severity: 3.5 (threshold: 3.0)
Verdict: FAIL
```

### Project Structure Notes

**Existing Files (Enhance):**
- `src/phx_home_analysis/services/kill_switch/filter.py` - Add evaluate_to_result method
- `src/phx_home_analysis/services/kill_switch/__init__.py` - Add exports

**New Files (Create):**
- `src/phx_home_analysis/services/kill_switch/result.py` - KillSwitchResult, FailedCriterion
- `src/phx_home_analysis/services/kill_switch/formatting.py` - format_verdict, format_result
- `tests/unit/services/kill_switch/test_result.py` - Unit tests for result dataclasses
- `tests/unit/services/kill_switch/test_formatting.py` - Unit tests for formatting utilities

### Previous Story Intelligence (E3.S2)

**Patterns to Follow:**
- Dataclass with `to_dict()` method for JSON serialization (see SoftSeverityResult)
- `__str__()` for human-readable summary
- Comprehensive docstrings with usage examples
- Unit tests covering all boundary conditions

**Integration Pattern:**
- E3.S2 added `evaluate_soft_severity()` to KillSwitchFilter
- This story adds `evaluate_to_result()` following same pattern
- Import new classes at top of filter.py, implement method at bottom

### References

- [Source: docs/epics/epic-3-kill-switch-filtering-system.md#E3.S3] - Story requirements
- [Source: docs/sprint-artifacts/stories/E3-S2-soft-kill-switch-severity-system.md] - Previous story patterns
- [Source: CLAUDE.md#Kill-Switches] - 5 HARD + 4 SOFT criteria specification
- [Source: src/phx_home_analysis/services/kill_switch/filter.py:167-255] - Existing evaluation methods
- [Source: src/phx_home_analysis/services/kill_switch/explanation.py:19-36] - CriterionResult reference

---

## Cross-Layer Validation Checklist

<!--
CROSS-LAYER VALIDATION (Required before Definition of Done)
Ensures all affected layers communicate properly and data flows end-to-end.
Source: Epic 2 Supplemental Retrospective - Lesson L6, Team Agreement TA1

Complete ALL applicable checkpoints before marking story complete.
Mark N/A for layers not affected by this story.
-->

- [x] **Extraction -> Persistence:** N/A - No new extraction in this story
- [x] **Persistence Verification:** KillSwitchResult.to_dict() serializes correctly to JSON
- [x] **Orchestration Wiring:** evaluate_to_result() correctly builds from existing evaluation flow
- [x] **End-to-End Trace:** Full flow from Property -> KillSwitchResult -> format_result() validated
- [x] **Type Contract Tests:** FailedCriterion fields match CriterionResult source types

---

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debug issues encountered.

### Completion Notes List

- **All 45 new unit tests pass** (24 for result.py, 21 for formatting.py)
- **251 total kill-switch tests pass** (no regressions)
- **Linting clean** - ruff check and format pass
- **Type hints complete** - All functions have type annotations
- **Docstrings complete** - All public classes/methods documented with examples

### File List

**Existing Files (Enhance):**
- `src/phx_home_analysis/services/kill_switch/filter.py` - Add evaluate_to_result method
- `src/phx_home_analysis/services/kill_switch/__init__.py` - Add exports

**New Files (Create):**
- `src/phx_home_analysis/services/kill_switch/result.py` - KillSwitchResult, FailedCriterion dataclasses
- `src/phx_home_analysis/services/kill_switch/formatting.py` - Verdict and result formatting
- `tests/unit/services/kill_switch/test_result.py` - Unit tests for result dataclasses
- `tests/unit/services/kill_switch/test_formatting.py` - Unit tests for formatting

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-10 | Story created via create-story workflow. Status: ready-for-dev. Comprehensive context from E3.S1, E3.S2, and existing implementation incorporated. | PM Agent (create-story workflow) |
| 2025-12-10 | Story completed. All 6 tasks implemented, 45 new tests pass, 251 total kill-switch tests pass. | Dev Agent (Claude Opus 4.5) |
