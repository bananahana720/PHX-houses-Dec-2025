---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
flags: []
---

# src/phx_home_analysis/pipeline

## Purpose

Pipeline orchestration layer for multi-agent property analysis. Provides phase coordination, progress tracking, resume capability, and crash recovery.

## Contents

| Path | Purpose |
|------|---------|
| `__init__.py` | Package exports: PhaseCoordinator, ProgressReporter, ResumePipeline |
| `phase_coordinator.py` | Phase sequencing, batch execution, work_items.json integration (930 lines) |
| `progress.py` | Rich progress bars, ETA calculation, tier statistics (259 lines) |
| `resume.py` | Crash recovery: stale reset, state validation, fresh start backup (371 lines) |
| `orchestrator.py` | Legacy orchestrator (backward compatibility) |

## Key Classes

| Class | Key Methods |
|-------|-------------|
| `PhaseCoordinator` | `execute_pipeline()`, batch checkpointing, error tracking |
| `ProgressReporter` | Rich progress bar, `PipelineStats` dataclass, ETA calculation |
| `ResumePipeline` | `can_resume()`, `reset_stale_items()`, `prepare_fresh_start()` |
| `StateValidationError` | Exception with details + suggestion attributes |

## Phase Enum

`COUNTY=0` | `LISTING=1` | `MAP=1` (parallel) | `IMAGES=2` | `SYNTHESIS=3` | `REPORT=4`

## Usage

```python
from phx_home_analysis.pipeline import PhaseCoordinator, ResumePipeline
from phx_home_analysis.repositories import WorkItemsRepository

# Resume or fresh start
repo = WorkItemsRepository("data/work_items.json")
resumer = ResumePipeline(repo)
if resumer.can_resume():
    resumer.load_and_validate()
    resumer.reset_stale_items()  # Resets >30min stale items
    pending = resumer.get_pending_addresses()
```

## Tasks

- [x] PhaseCoordinator with checkpointing `P:H`
- [x] ProgressReporter with rich integration `P:H`
- [x] ResumePipeline with crash recovery (E1.S5) `P:H`
- [ ] Performance profiling for large batches P:M

## Learnings

- **Phase parallelism:** LISTING and MAP both phase 1; track separately
- **Stale timeout:** 30 minutes (STALE_TIMEOUT_MINUTES) balances crash recovery vs false positives
- **MAX_RETRIES=3:** Failed items retry up to 3 times; previous errors preserved in `previous_error` field
- **Atomic writes:** work_items.json uses atomic save to prevent corruption

## Refs

- Phase enum: `phase_coordinator.py:48-60`
- ResumePipeline: `resume.py:69-371`
- StateValidationError: `resume.py:33-67`
- Stale reset: `resume.py:175-228`

## Deps

← `domain/`, `services/`, `repositories/`, `rich` 13.0+
→ `scripts/pipeline_cli.py`, `.claude/commands/analyze-property.md`, tests
