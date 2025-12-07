---
last_updated: 2025-12-07T22:37:45Z
updated_by: agent
staleness_hours: 24
flags: []
---
# schemas

## Purpose
JSON schema documentation for pipeline state management and property data structures used in multi-phase property analysis workflows.

## Contents
| Path | Purpose |
|------|---------|
| `work_items_schema.md` | Complete work_items.json structure (session, phases, checkpoints, recovery) |

## Key Patterns
- **Atomic writes prevent corruption**: Temp+rename pattern for work_items.json reliability
- **State machine clarity**: Explicit transitions (pending→in_progress→completed→failed) prevent invalid combinations
- **Stale detection**: Phases hung >30min auto-reset to pending on load
- **Phase granularity**: 6 phases (county, listing, map, images, synthesis, report) enable fine-grained tracking
- **Backup retention**: Last 10 timestamped backups enable rollback

## Tasks
- [ ] Add enrichment_data.json schema documentation `P:M`
- [ ] Document property data validation rules `P:M`
- [ ] Add schema validation test suite `P:L`

## Learnings
- **Checkpoint operations critical**: checkpoint_phase_start(), checkpoint_phase_complete() enforce valid transitions
- **Stale timeout prevents hangs**: 30min timeout recovers from crashed agents
- **Summary auto-calculated**: Never manually edit; recalculated on every save_state()
- **Retry count enables backoff**: Track retry_count per phase for exponential backoff

## Refs
- State machine: `work_items_schema.md:122-158` (WorkItemStatus enum, transitions)
- Phase checkpoints: `work_items_schema.md:365-431` (initialization, start, complete, error handling)
- Validation rules: `work_items_schema.md:459-511` (structural, status transitions)
- Implementation: `../../src/phx_home_analysis/repositories/work_items_repository.py`
- Enums: `../../src/phx_home_analysis/domain/enums.py`

## Deps
← imports: none (schema documentation)
→ used by: WorkItemsRepository, agents, orchestrators, CLI tools
