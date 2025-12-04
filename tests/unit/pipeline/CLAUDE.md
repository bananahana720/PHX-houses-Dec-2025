---
last_updated: 2025-12-04
updated_by: Claude (Agent)
staleness_hours: 24
flags: []
---

# tests/unit/pipeline

## Purpose

Unit tests for pipeline orchestration and resume/checkpoint modules. Covers phase coordination, progress tracking, CLI argument parsing, and crash recovery/state management. Enables fast iteration on pipeline architecture and ensures state-based recovery mechanisms work correctly.

## Contents

| Path | Purpose |
|------|---------|
| `test_phase_coordinator.py` | Phase execution, sequencing, state transitions (264 lines, ~28 tests) |
| `test_progress.py` | Progress reporting, stats calculation, ETA estimation (235 lines, ~26 tests) |
| `test_cli.py` | CLI argument parsing, typer integration, help text (226 lines, ~23 tests) |
| `test_resume.py` | Resume/checkpoint logic, state validation, crash recovery (474 lines, 33 tests) |
| `__init__.py` | Package init (empty) |

## Test Coverage Summary

**Total Test Classes:** 13 classes across 4 modules
**Total Test Methods:** ~110 tests (28 + 26 + 23 + 33)

### Phase Coordinator Tests (test_phase_coordinator.py, ~28 tests)
- **Phase class**: Enum validation (COUNTY=0, LISTING=1, MAP=1, IMAGES=2, SYNTHESIS=3, REPORT=4)
- **PhaseResult dataclass**: Success/error tracking with duration, data fields
- **Phase sequencing**: Validates parallel phases (LISTING + MAP execute concurrently)
- **Error handling**: Phase failure, retry logic, state recovery
- **Work items integration**: JSON state file updates on phase completion

### Progress Reporter Tests (test_progress.py, ~26 tests)
- **PipelineStats dataclass**: Total, pending, in_progress, complete, failed, tier counts
- **Progress bar**: Rich progress integration, percentage/ETA calculation
- **Status table**: Property counts, tier breakdown summary, formatting
- **ETA calculation**: Rolling average of phase durations for estimation
- **Tier tracking**: UNICORN, CONTENDER, PASS counts and statistics

### CLI Tests (test_cli.py, ~23 tests)
- **Typer integration**: Argument parsing, option validation, help text
- **Commands**: `--all`, `--test`, `--status`, single address, `--resume`, `--fresh`, `--strict`, `--skip-phase`
- **Output**: Console formatting with rich library
- **Error handling**: Invalid arguments, missing files, subprocess errors
- **Exit codes**: 0=success, 1=error, 2=usage

### Resume/Checkpoint Tests (test_resume.py, 33 tests, 11 test classes)

**Test Classes:**

| Class | Purpose | Coverage |
|-------|---------|----------|
| `TestStateValidationError` | Custom exception with details/suggestions | Error message, details dict, suggestion field, defaults |
| `TestResumePipelineInitialization` | ResumePipeline constructor and setup | Repository injection, fresh flag state |
| `TestCanResume` | Resume eligibility checks | Valid state detection, empty state, fresh flag override |
| `TestLoadAndValidate` | Load and validate saved state | State loading, validation rules, error detection |
| `TestResetStaleItems` | Mark stale items for retry | Timestamp comparison, recency threshold, state updates |
| `TestGetPendingAddresses` | Query pending work items | Address filtering, status checks, ordering |
| `TestGetCompletedAddresses` | Query completed work items | Address filtering, completion tracking |
| `TestGetResumeSummary` | Generate resume summary report | Stats aggregation, progress reporting, ETA estimation |
| `TestPrepareFreshStart` | Reset state for fresh run | State cleanup, archive old state, initialization |
| `TestEstimateDataLoss` | Calculate potential data loss on resume | Incomplete phase detection, in-progress item recovery |
| `TestVersionCompatibility` | Check state file version compatibility | Format validation, migration detection, legacy handling |

**Key Features Tested:**
- **State validation**: JSON schema, required fields, type checking
- **Timestamp handling**: Stale detection (>1 hour old), timezone awareness
- **Recovery logic**: Resume from partial completion, restart incomplete phases
- **Data integrity**: Atomic writes, backup creation, rollback capability
- **Progress tracking**: Work item status transitions, completion verification
- **Error recovery**: Graceful handling of corrupted/missing state files

## Test Architecture

### State Management Pattern
```
can_resume() → load_and_validate() → (reset_stale_items|prepare_fresh_start) → get_resume_summary()
```

### Key Test Patterns

**Boundary Testing:**
- Stale item threshold (59m 59s vs 60m 0s old)
- Time zone handling (UTC vs local)
- State file versions (current vs legacy)

**Error Paths:**
- Missing work_items.json
- Corrupted JSON structure
- Invalid phase states
- Incomplete session data

**Integration Points:**
- WorkItemsRepository interaction
- State persistence (atomic writes)
- Timestamp tracking
- Progress resumption

## Tasks

- [x] Populate test_phase_coordinator.py documentation `P:H`
- [x] Populate test_progress.py documentation `P:H`
- [x] Populate test_cli.py documentation `P:H`
- [x] Add test_resume.py documentation (33 tests for ResumePipeline) `P:H`
- [ ] Add parametrized tests for all phase transitions P:M
- [ ] Add performance benchmarks for large batches (500+ properties) P:L
- [ ] Add integration tests for complete resume workflow (spawn agent, modify state, resume) P:M

## Learnings

- **Phase sequencing important**: LISTING and MAP both phase 1 value but execute parallel; tests validate no serial bottleneck
- **Rich library integration**: Console output mocking requires testing Display class without terminal
- **State file updates**: Phase completion writes to work_items.json; must validate atomic writes and recovery
- **ETA accuracy**: Phase durations need rolling average to avoid outlier skew
- **Resume state complexity**: Stale item detection, version compatibility, and data loss estimation require comprehensive test coverage
- **Timestamp handling critical**: Must account for timezone, stale thresholds, and clock skew in recovery logic
- **State file corruption**: Tests must validate graceful error handling for malformed JSON and missing required fields

## Refs

- Phase coordinator: `src/phx_home_analysis/pipeline/phase_coordinator.py:1-100`
- Progress reporter: `src/phx_home_analysis/pipeline/progress.py:1-80`
- Resume pipeline: `src/phx_home_analysis/pipeline/resume.py:1-200`
- CLI entry point: `scripts/pipeline_cli.py:1-100`
- Phase enum: `src/phx_home_analysis/pipeline/phase_coordinator.py:48-60`
- PhaseResult: `src/phx_home_analysis/pipeline/phase_coordinator.py:62-85`
- WorkItemsRepository: `src/phx_home_analysis/repositories/work_items_repository.py:1-150`

## Deps

← Imports from:
  - `src/phx_home_analysis/pipeline/` - Phase, PhaseResult, PhaseCoordinator, ProgressReporter, ResumePipeline, StateValidationError
  - `src/phx_home_analysis/repositories/` - WorkItemsRepository
  - `tests/conftest.py` - Shared fixtures
  - pytest 9.0.1+, rich 13.0+, typer 0.9+

→ Imported by:
  - CI/CD pipeline (pytest command)
  - Pre-merge validation
  - Pipeline initialization flows