---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---

# docs/schemas/

## Purpose

JSON schema documentation for data structures used in the PHX Houses Analysis Pipeline. Documents the `work_items.json` state machine schema, including checkpoint operations, phase transitions, validation rules, and recovery patterns for multi-phase property analysis workflows.

## Contents

| Path | Purpose |
|------|---------|
| `work_items_schema.md` | Complete `work_items.json` structure (session, work items, phases, summary); state machine rules, checkpoint operations, backup/recovery, troubleshooting |

## Tasks

- [ ] Add `enrichment_data.json` schema documentation `P:M`
- [ ] Document property data validation rules `P:M`
- [ ] Add schema validation test suite `P:L`

## Learnings

- **Atomic writes prevent corruption**: `work_items.json` uses temp+rename pattern for reliability
- **State machine clarity**: Explicit transition rules (pending→in_progress→completed) prevent invalid state combinations
- **Stale detection enables recovery**: Phases hung >30 min are auto-reset to pending on load
- **Phase granularity drives orchestration**: 6 phases (county, listing, map, images, synthesis, report) enable fine-grained progress tracking
- **Backup retention provides safety**: Last 10 timestamped backups enable easy rollback on corruption

## Refs

- **State Machine**: `work_items_schema.md:122-158` (WorkItemStatus enum, transitions)
- **Phase Checkpoints**: `work_items_schema.md:365-431` (initialization, start, complete, error handling)
- **Validation Rules**: `work_items_schema.md:459-511` (structural, status transitions)
- **Implementation**: `src/phx_home_analysis/repositories/work_items_repository.py`
- **Enums**: `src/phx_home_analysis/domain/enums.py` (PhaseStatus, WorkItemStatus)

## Deps

← imports from: Pipeline orchestrators, agents, CLI tools
→ imported by: `.claude/commands/analyze-property.md`, `scripts/phx_home_analyzer.py`, phase agents
