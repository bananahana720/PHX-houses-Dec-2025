---
last_updated: 2025-12-06T12:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# phase-orchestration

## Purpose
Detailed phase-by-phase implementation guides for PHX property analysis pipeline (Phases 0-4).

## Contents
| File | Phase | Purpose |
|------|-------|---------|
| `phase-0-county-data.md` | 0 | County API extraction (lot, year, garage) |
| `phase-05-cost-estimation.md` | 0.5 | Cost calculation |
| `phase-1-data-collection-parallel.md` | 1 | Parallel listing + map extraction |
| `phase-2a-exterior-assessment.md` | 2A | Exterior visual analysis (Opus 4.5) |
| `phase-2b-interior-assessment.md` | 2B | Interior scoring (190 pts, Opus 4.5) |
| `phase-3-synthesis-scoring.md` | 3 | Score aggregation, tier assignment |
| `phase-4-report-generation.md` | 4 | Deal sheet output |
| `batch-processing-protocol.md` | - | Batch operations guide |
| `crash-recovery-protocol.md` | - | Recovery procedures |
| `phase-dependencies.md` | - | Inter-phase dependencies |

## Phase Flow
```
Phase 0 (County API) → Phase 1a/1b (Parallel) → [Validation] → Phase 2 (Sequential) → Phase 3 → Phase 4
```

## Key Rules
- Phase 2 requires Phase 1 complete + images downloaded
- Run `scripts/validate_phase_prerequisites.py` before Phase 2
- Use Opus 4.5 for visual assessment (model: opus)

## Refs
- Validation script: `scripts/validate_phase_prerequisites.py`
- Parent: `../CLAUDE.md`

## Deps
<- imports: architecture decisions
-> used by: orchestrator, agents
