---
last_updated: 2025-12-10
updated_by: agent
staleness_hours: 24
---

# docs/epics

## Purpose
Epic repository organizing PHX Houses Analysis Pipeline into 7 epics with 50 stories. Transforms 62 FRs (100% coverage) into actionable development work with dependencies, critical path, and story-level acceptance criteria.

## Contents
| File | Purpose |
|------|---------|
| `index.md` | Master TOC and epic navigation |
| `overview.md` | Epic decomposition, critical path analysis |
| `epic-1-foundation-data-infrastructure.md` | Foundation: config, storage, provenance (6 stories) COMPLETE |
| `epic-2-property-data-acquisition.md` | Data acquisition: County API, images, extraction (13 stories) COMPLETE |
| `epic-3-kill-switch-filtering-system.md` | Filtering: HARD/SOFT criteria (6 stories) COMPLETE |
| `epic-4-property-scoring-engine.md` | Scoring: 605-point system (7 stories) |
| `epic-5-multi-agent-pipeline-orchestration.md` | Orchestration: agents, phases (6 stories) |
| `epic-6-visual-analysis-risk-intelligence.md` | Vision: image assessment, risks (6 stories) |
| `epic-7-deal-sheet-generation-reports.md` | Reports: deal sheets, exports (6 stories) |
| `fr-coverage-matrix.md` | FR-to-story traceability matrix (62 FRs -> 50 stories) |

## Status (2025-12-10)
| Metric | Status |
|--------|--------|
| Epics Complete | 3/7 (E1, E2, E3) |
| Stories Complete | 31/50 (62%) |
| FR Coverage | 62/62 (100%) |

## Key Patterns
- **Story structure**: User story -> Acceptance criteria -> Technical notes -> Definition of Done
- **Provenance**: All data sources tracked (0.95 County, 0.90 CSV, 0.75 web, 0.70 AI)
- **Atomic writes**: E1.S2 creates backups before JSON writes; E2.S4 content-addressed storage
- **Dependencies**: E1->E2->E4->E5->E7 critical path; E3/E6 parallel

## Critical Learnings
- **E1 patterns**: Repository pattern, atomic writes, provenance tracking, exponential backoff
- **E2 storage**: Content-addressed (`{hash[:8]}/{hash}.png`) not address-based folders
- **E2 blockers**: Zillow CAPTCHA (BLOCK-001), Redfin CDN 404 (BLOCK-002) mitigated
- **E3 kill-switch**: 5 HARD + 4 SOFT criteria; ConfigWatcher for hot-reload

## Refs
- Parent docs: `../CLAUDE.md` (project overview)
- PRD: `../prd/` (62 functional requirements)
- Sprint tracking: `../sprint-artifacts/sprint-status.yaml`
- Kill-switch: `../../src/phx_home_analysis/services/kill_switch/`

## Dependencies
<- PRD, Architecture, Story files | -> Sprint planning, dev workflows
