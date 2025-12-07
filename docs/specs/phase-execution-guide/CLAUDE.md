---
last_updated: 2025-12-07T22:37:45Z
updated_by: agent
staleness_hours: 24
flags: []
---
# phase-execution-guide

## Purpose
Actionable execution guide for multi-phase scoring system improvement implementation across 7 waves with session planning, continuity rules, and troubleshooting.

## Contents
| Path | Purpose |
|------|---------|
| `index.md` | Table of contents |
| `executive-summary.md` | Overview, timeline (7 waves, 10-12 sessions) |
| `session-planning-matrix.md` | Entry/exit criteria per session |
| `wave-0-baseline-pre-processing.md` | Baseline setup and cleanup |
| `wave-1-kill-switch-threshold.md` | Kill-switch threshold updates |
| `wave-2-cost-estimation-module.md` | Cost estimation integration |
| `wave-3-data-validation-layer.md` | Data validation logic |
| `wave-4-ai-assisted-triage.md` | AI-powered triage |
| `wave-5-quality-metrics-lineage.md` | Quality metrics and lineage |
| `wave-6-documentation-integration.md` | Documentation updates |
| `cross-session-continuity.md` | State management across sessions |
| `troubleshooting-guide.md` | Common issues and resolutions |
| `success-metrics.md` | Acceptance criteria per wave |

## Key Patterns
- **Wave-based delivery**: 7 waves enable incremental testing and validation
- **Session planning critical**: Clear entry/exit states prevent mid-session corruption
- **Continuity rules**: Cross-session state management via work_items.json checkpoints
- **Rollback procedures**: Each wave documents rollback plan

## Tasks
- [ ] Sync wave guides with Epic 3 kill-switch implementation `P:M`
- [ ] Add troubleshooting entries for PhoenixMLS Search issues `P:L`
- [ ] Update success-metrics.md with actual Epic 1+2 results `P:L`

## Learnings
- **Entry/exit criteria prevent drift**: Session planning matrix enforces clean boundaries
- **Rollback safety nets**: Pre-wave backups enable safe experimentation
- **Incremental validation**: Test after each wave prevents compound failures
- **Cross-session continuity essential**: Long-running improvements span multiple sessions

## Refs
- Implementation specs: `../implementation-spec/`
- Work items schema: `../../schemas/work_items_schema.md`
- Sprint tracking: `../../sprint-artifacts/sprint-status.yaml`

## Deps
← imports: `../implementation-spec/` (wave definitions)
→ used by: agents, orchestrators, `/analyze-property` command
