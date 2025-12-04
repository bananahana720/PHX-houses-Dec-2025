---
last_updated: 2025-12-04
updated_by: Claude (Agent)
staleness_hours: 24
flags: []
---

# src/phx_home_analysis/pipeline

## Purpose

Pipeline orchestration layer for multi-agent property analysis. Provides phase coordination, progress tracking, and state management for executing analysis phases (County API, listing extraction, image assessment, scoring, reporting) across property batches.

## Contents

| Path | Purpose |
|------|---------|
| `__init__.py` | Package exports: PhaseCoordinator, ProgressReporter, Phase, PhaseResult, ResumePipeline |
| `phase_coordinator.py` | Phase sequencing, batch execution, state file integration (930 lines) |
| `progress.py` | Progress reporting with rich library, ETA calculation (259 lines) |
| `resume.py` | Pipeline resume capability with crash recovery, state validation (371 lines) |
| `orchestrator.py` | Legacy orchestrator (kept for compatibility) |

## Architecture

### Phase Coordinator (phase_coordinator.py)
- **Phase enum**: COUNTY=0, LISTING=1, MAP=1, IMAGES=2, SYNTHESIS=3, REPORT=4
- **PhaseResult dataclass**: Tracks success, duration, error, data for each phase
- **PropertyState dataclass**: Status (pending/in_progress/complete/failed), tier, score
- **Batch execution**: Processes multiple properties with checkpointing
- **Error handling**: Phase failure tracking, retry logic, state recovery
- **Work items integration**: Reads/writes `data/work_items.json` for state persistence

### Progress Reporter (progress.py)
- **PipelineStats dataclass**: Total, pending, in_progress, complete, failed, tier counts
- **Rich integration**: Progress bar with percentage, ETA, status table
- **ETA calculation**: Rolling average of phase durations
- **Tier tracking**: UNICORN, CONTENDER, PASS counts and statistics
- **Console output**: Formatted property status, batch summary

### Resume Pipeline (resume.py)
- **ResumePipeline class**: Manages crash recovery and pipeline resumption
  - Loads and validates state from work_items.json
  - Resets items stuck in 'in_progress' for >30 minutes (STALE_TIMEOUT_MINUTES)
  - Provides pending/completed address lists for continued execution
  - Backs up state on fresh start to prevent data loss
- **StateValidationError exception**: Custom error with details + actionable suggestions
  - Schema version compatibility checking
  - Required field validation (session, work_items)
  - Detailed error context for debugging
- **Recovery features**:
  - Detects stale in_progress items and resets to pending
  - Preserves previous error messages for debugging
  - Supports max 3 retries per failed item (MAX_RETRIES)
  - Estimates data loss before fresh start
  - Validates session continuity

## Usage

```python
from phx_home_analysis.pipeline import PhaseCoordinator, ProgressReporter, ResumePipeline
from phx_home_analysis.repositories import WorkItemsRepository

# Standard execution
reporter = ProgressReporter()
coordinator = PhaseCoordinator(progress_reporter=reporter)
addresses = ["123 Main St", "456 Oak Ave"]
results = await coordinator.execute_pipeline(properties=addresses)

# Resume from checkpoint
repo = WorkItemsRepository("data/work_items.json")
resumer = ResumePipeline(repo)
if resumer.can_resume():
    state = resumer.load_and_validate()
    reset_count = len(resumer.reset_stale_items())
    pending = resumer.get_pending_addresses()
    summary = resumer.get_resume_summary()
    results = await coordinator.execute_pipeline(properties=pending)
else:
    # Fresh start
    resumer.prepare_fresh_start(addresses)
```

## Tasks

- [x] Implement PhaseCoordinator with full phase sequencing `P:H`
- [x] Implement ProgressReporter with rich library integration `P:H`
- [x] Add work_items.json state persistence `P:H`
- [x] Document phase enum and execution flow `P:H`
- [x] Implement ResumePipeline with crash recovery `P:H` (E1.S5)
- [x] Add StateValidationError with detailed context `P:H` (E1.S5)
- [ ] Add performance profiling for large batches P:M
- [ ] Implement distributed phase execution (multi-worker) P:L

## Learnings

- **Phase parallelism**: LISTING and MAP both phase 1 and execute parallel; must track separately
- **ETA accuracy**: Rolling average prevents outlier skew; need at least 3 samples for reliability
- **State file updates**: Atomic writes to work_items.json prevent corruption on crash
- **Progress tracking essential**: Large batches benefit from real-time feedback
- **Resume stale timeout**: 30-minute threshold (STALE_TIMEOUT_MINUTES) balances crash recovery vs. false positives
- **State validation critical**: Version compatibility + required fields prevent silent failures
- **Error preservation**: Stale resets keep previous error messages for debugging (moved to previous_error field)
- **Data loss prevention**: prepare_fresh_start() backs up state and warns about completed items being re-processed
- **Retry strategy**: MAX_RETRIES=3 allows transient failures recovery without infinite loops

## Refs

- Phase enum: `phase_coordinator.py:48-60`
- PhaseResult: `phase_coordinator.py:62-85`
- PropertyState: `phase_coordinator.py:87-110`
- PipelineStats: `progress.py:36-75`
- Coordinator execute: `phase_coordinator.py:200-400`
- State persistence: `phase_coordinator.py:450-550`
- ResumePipeline class: `resume.py:69-371`
- StateValidationError exception: `resume.py:33-67`
- Stale item reset: `resume.py:175-228`
- State validation: `resume.py:131-173`
- Resume summary: `resume.py:270-297`
- Fresh start backup: `resume.py:299-336`

## Deps

← Imports from:
  - `src/phx_home_analysis/domain/` - Property, Tier entities
  - `src/phx_home_analysis/services/` - Scoring, kill-switch services
  - `src/phx_home_analysis/repositories/` - CSV/JSON data access
  - `rich` 13.0+ - Progress bar, console output
  - `typing`, `asyncio`, `pathlib` - Standard library

→ Imported by:
  - `scripts/pipeline_cli.py` - CLI entry point
  - `.claude/commands/analyze-property.md` - Multi-agent orchestrator
  - Tests: `tests/unit/pipeline/`, `tests/integration/`