---
last_updated: 2025-12-05T15:30:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# docs/epics

## Purpose
Epic repository organizing PHX Houses Analysis Pipeline into 7 epics with 42 stories. Transforms 62 FRs (100% coverage) into story-driven development with dependencies and critical path.

## Contents
| Path | Purpose |
|------|---------|
| `index.md` | Master TOC and navigation |
| `overview.md` | Epic decomposition summary, critical path |
| `epic-1-foundation-data-infrastructure.md` | Foundation: config, storage, provenance (6 stories) COMPLETE |
| `epic-2-property-data-acquisition.md` | Acquisition: APIs, images, extraction (7 stories) COMPLETE |
| `epic-3-kill-switch-filtering-system.md` | Filtering: HARD/SOFT criteria (5 stories) |
| `epic-4-property-scoring-engine.md` | Scoring: 605-point system (6 stories) |
| `epic-5-multi-agent-pipeline-orchestration.md` | Orchestration: agents, phases (6 stories) |
| `epic-6-visual-analysis-risk-intelligence.md` | Vision: image assessment, risks (6 stories) |
| `epic-7-deal-sheet-generation-reports.md` | Reports: deal sheets, exports (6 stories) |
| `fr-coverage-matrix.md` | FR-to-story traceability matrix |

## Current Status (2025-12-05)
| Metric | Value |
|--------|-------|
| Stories Complete | 19/42 (45%) |
| Epics Complete | 2/7 (E1, E2) |
| FR Coverage | 62/62 (100%) |
| Active Blockers | 2 (BLOCK-001, BLOCK-002) |

## Tasks
- [x] Map 62 FRs to 7 epics `P:H`
- [x] Define critical path (E1-E2-E4-E5-E7) `P:H`
- [x] Complete Epic 1 implementation `P:H`
- [x] Complete Epic 2 implementation `P:H`
- [ ] Run Epic 2 retrospective `P:H`
- [ ] Begin Epic 3 Kill-Switch `P:M`
- [ ] Address BLOCK-001/002 blockers `P:H`

## Learnings
- **E1 patterns**: Repository pattern, atomic writes, provenance tracking, exponential backoff
- **E2 major change**: E2.S4 uses content-addressed storage (`{hash[:8]}/{hash}.png`) not address folders
- **Blockers discovered**: Zillow CAPTCHA (BLOCK-001), Redfin CDN 404 (BLOCK-002) in live testing
- **Critical path**: E1-E2-E4-E5-E7 enables parallel work on E3/E6

## Refs
- Critical path: `overview.md:24`
- E1 implementation: `epic-1-foundation-data-infrastructure.md:109-137`
- E2 blockers: `epic-2-property-data-acquisition.md:200-210`
- FR coverage: `fr-coverage-matrix.md`

## Deps
- PRD (`../prd/`) - 62 functional requirements
- Architecture (`../architecture.md`) - 7 epic boundaries
- Stories (`../sprint-artifacts/stories/`) - 42 story files
- Sprint tracking (`../sprint-artifacts/sprint-status.yaml`)
