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
| `__init__.py` | Package exports: PhaseCoordinator, ProgressReporter, Phase, PhaseResult |
| `phase_coordinator.py` | Phase sequencing, batch execution, state file integration (930 lines) |
| `progress.py` | Progress reporting with rich library, ETA calculation (259 lines) |
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

## Usage

```python
from phx_home_analysis.pipeline import PhaseCoordinator, ProgressReporter

reporter = ProgressReporter()
coordinator = PhaseCoordinator(progress_reporter=reporter)

# Process batch
addresses = ["123 Main St", "456 Oak Ave"]
results = await coordinator.execute_pipeline(properties=addresses)
```

## Tasks

- [x] Implement PhaseCoordinator with full phase sequencing `P:H`
- [x] Implement ProgressReporter with rich library integration `P:H`
- [x] Add work_items.json state persistence `P:H`
- [x] Document phase enum and execution flow `P:H`
- [ ] Add performance profiling for large batches P:M
- [ ] Implement distributed phase execution (multi-worker) P:L

## Learnings

- **Phase parallelism**: LISTING and MAP both phase 1 and execute parallel; must track separately
- **ETA accuracy**: Rolling average prevents outlier skew; need at least 3 samples for reliability
- **State file updates**: Atomic writes to work_items.json prevent corruption on crash
- **Progress tracking essential**: Large batches benefit from real-time feedback

## Refs

- Phase enum: `phase_coordinator.py:48-60`
- PhaseResult: `phase_coordinator.py:62-85`
- PropertyState: `phase_coordinator.py:87-110`
- PipelineStats: `progress.py:36-75`
- Coordinator execute: `phase_coordinator.py:200-400`
- State persistence: `phase_coordinator.py:450-550`

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