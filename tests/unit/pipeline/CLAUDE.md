---
last_updated: 2025-12-04
updated_by: Claude (Agent)
staleness_hours: 24
flags: []
---

# tests/unit/pipeline

## Purpose

Unit tests for pipeline orchestration modules (Phase coordinator, progress reporter, CLI). Tests verify phase sequencing, progress tracking, CLI argument parsing, and integration with data files. Enables fast iteration on pipeline architecture.

## Contents

| Path | Purpose |
|------|---------|
| `test_phase_coordinator.py` | Phase execution, sequencing, state transitions (264 lines, ~28 tests) |
| `test_progress.py` | Progress reporting, stats calculation, ETA estimation (235 lines, ~26 tests) |
| `test_cli.py` | CLI argument parsing, typer integration, help text (226 lines, ~23 tests) |
| `__init__.py` | Package init (empty) |

## Test Architecture

### Phase Coordinator Tests (test_phase_coordinator.py)
- **Phase class**: Enum validation (COUNTY=0, LISTING=1, MAP=1, IMAGES=2, SYNTHESIS=3, REPORT=4)
- **PhaseResult dataclass**: Success/error tracking with duration, data fields
- **Phase sequencing**: Validates parallel phases (LISTING + MAP execute concurrently)
- **Error handling**: Phase failure, retry logic, state recovery
- **Work items integration**: JSON state file updates on phase completion

### Progress Reporter Tests (test_progress.py)
- **PipelineStats dataclass**: Total, pending, in_progress, complete, failed, tier counts
- **Progress bar**: Rich progress integration, percentage/ETA calculation
- **Status table**: Property counts, tier breakdown summary, formatting
- **ETA calculation**: Rolling average of phase durations for estimation
- **Tier tracking**: UNICORN, CONTENDER, PASS counts and statistics

### CLI Tests (test_cli.py)
- **Typer integration**: Argument parsing, option validation, help text
- **Commands**: `--all`, `--test`, `--status`, single address, `--resume`, `--fresh`, `--strict`, `--skip-phase`
- **Output**: Console formatting with rich library
- **Error handling**: Invalid arguments, missing files, subprocess errors
- **Exit codes**: 0=success, 1=error, 2=usage

## Tasks

- [x] Populate test_phase_coordinator.py documentation `P:H`
- [x] Populate test_progress.py documentation `P:H`
- [x] Populate test_cli.py documentation `P:H`
- [ ] Add parametrized tests for all phase transitions P:M
- [ ] Add performance benchmarks for large batches (500+ properties) P:L

## Learnings

- **Phase sequencing important**: LISTING and MAP both phase 1 value but execute parallel; tests validate no serial bottleneck
- **Rich library integration**: Console output mocking requires testing Display class without terminal
- **State file updates**: Phase completion writes to work_items.json; must validate atomic writes and recovery
- **ETA accuracy**: Phase durations need rolling average to avoid outlier skew

## Refs

- Phase coordinator: `src/phx_home_analysis/pipeline/phase_coordinator.py:1-100`
- Progress reporter: `src/phx_home_analysis/pipeline/progress.py:1-80`
- CLI entry point: `scripts/pipeline_cli.py:1-100`
- Phase enum: `src/phx_home_analysis/pipeline/phase_coordinator.py:48-60`
- PhaseResult: `src/phx_home_analysis/pipeline/phase_coordinator.py:62-85`

## Deps

← Imports from:
  - `src/phx_home_analysis/pipeline/` - Phase, PhaseResult, PhaseCoordinator, ProgressReporter
  - `tests/conftest.py` - Shared fixtures
  - pytest 9.0.1+, rich 13.0+, typer 0.9+

→ Imported by:
  - CI/CD pipeline (pytest command)
  - Pre-merge validation