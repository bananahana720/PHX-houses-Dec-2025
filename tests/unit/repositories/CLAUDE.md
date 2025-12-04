---
last_updated: 2025-12-04
updated_by: Claude Code
staleness_hours: 72
flags: []
---
# tests/unit/repositories/

## Purpose

Unit tests for the repository layer, validating data persistence, state management, and checkpoint recovery patterns. Tests `WorkItemsRepository` which manages pipeline progress tracking across multi-phase property analysis workflows.

## Contents

| Path | Purpose |
|------|---------|
| `test_work_items_repository.py` | WorkItemsRepository lifecycle, phase checkpointing, state transitions, stale detection, backup management (12 test classes, ~140 tests) |

## Test Coverage

**Test Classes (12):**
- `TestWorkItemsRepositoryInitialization` - Repo init, empty file handling
- `TestSessionInitialization` - Batch/single mode, session ID generation
- `TestWorkItemCreation` - Required fields, pipeline phases, 8-char hex IDs
- `TestPhaseCheckpointing` - Phase start/complete, success/failure, multi-phase workflows
- `TestStateTransitions` - Invalid transitions, completion blocking, failed phase retry
- `TestWorkItemStatusUpdate` - Auto-status updates (pending→in_progress→completed/failed)
- `TestStaleItemDetection` - 30-minute timeout reset to pending, freshness checks
- `TestSummaryCalculation` - Totals by status, completion percentage
- `TestBackupManagement` - Pre-save backup creation, old backup cleanup
- `TestErrorHandling` - Invalid JSON, unknown addresses
- `TestQueryMethods` - get_pending_items(), get_incomplete_items()
- `TestAtomicWrites` - File existence post-save, no temp files

**Coverage:** 140+ tests covering initialization, session management, phase lifecycle, state validation, recovery, and cleanup patterns.

## Key Patterns

- **Phase checkpointing:** Start (pending→in_progress) and complete (in_progress→completed/failed with errors)
- **Severity tracking:** Retry counters increment on failures; failed phases can be retried
- **Atomic operations:** Temp file writes prevent corruption; backups created before state changes
- **State validation:** Strict transitions prevent invalid state paths (e.g., complete without start)
- **Timeout recovery:** Stale phases (>30min in_progress) auto-reset to pending for crash recovery

## Tasks

- [x] Map WorkItemsRepository test coverage `P:H`
- [x] Document phase checkpointing patterns `P:H`
- [ ] Add concurrent checkpoint stress tests `P:M`
- [ ] Extend backup cleanup verification `P:M`

## Learnings

- State file corruption prevented via atomic writes + backups; tests validate both patterns
- Phase transitions are strictly enforced; invalid paths raise ValueError immediately
- Stale detection relies on 30-minute timeout; tests cover both fresh and expired states
- Backup cleanup tracks MAX_BACKUPS; tests verify old files deleted, recent preserved

## Refs

- WorkItemsRepository implementation: `src/phx_home_analysis/repositories/work_items.py`
- Base repository class: `src/phx_home_analysis/repositories/base.py:1-50`
- Work item state schema: `src/phx_home_analysis/validation/schemas.py` (WorkItem model)
- Phase enum: `src/phx_home_analysis/domain/enums.py` (Phase names)

## Deps

← Imports from:
- pytest 9.0.1+ (fixtures, assertions, error testing)
- tempfile (tmp_path fixture for isolated file I/O)
- datetime, timezone (timestamp tracking, stale detection)
- conftest.py (shared fixtures)

→ Imported by:
- CI/CD pipeline (unit test suite, pre-merge gates)
- Integration tests (validate state persistence across phases)
- Pipeline orchestrator (work_items.json state validation)
