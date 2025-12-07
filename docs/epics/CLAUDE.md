---
last_updated: 2025-12-07
updated_by: agent
staleness_hours: 24
---

# docs/epics

## Purpose
Epic repository organizing PHX Houses Analysis Pipeline into 7 epics with 42 stories. Transforms 62 FRs (100% coverage) into actionable development work with dependencies, critical path, and story-level acceptance criteria.

## Contents
| File | Purpose |
|------|---------|
| `index.md` | Master TOC and epic navigation |
| `overview.md` | Epic decomposition, critical path analysis |
| `epic-1-foundation-data-infrastructure.md` | Foundation: config, storage, provenance (6 stories) ✅ COMPLETE |
| `epic-2-property-data-acquisition.md` | Data acquisition: County API, images, extraction (7 stories) ✅ COMPLETE |
| `epic-3-kill-switch-filtering-system.md` | Filtering: HARD/SOFT criteria (5 stories) |
| `epic-4-property-scoring-engine.md` | Scoring: 605-point system (6 stories) |
| `epic-5-multi-agent-pipeline-orchestration.md` | Orchestration: agents, phases (6 stories) |
| `epic-6-visual-analysis-risk-intelligence.md` | Vision: image assessment, risks (6 stories) |
| `epic-7-deal-sheet-generation-reports.md` | Reports: deal sheets, exports (6 stories) |
| `fr-coverage-matrix.md` | FR-to-story traceability matrix (62 FRs → 42 stories) |

## Status (2025-12-07)
| Metric | Status |
|--------|--------|
| Epics Complete | 2/7 (E1, E2) |
| Stories Complete | 19/42 (45%) |
| FR Coverage | 62/62 (100%) |

## Key Patterns
- **Story structure**: User story → Acceptance criteria → Technical notes → Definition of Done
- **Provenance**: All data sources tracked (0.95 confidence for County, 0.90 for CSV, 0.75 web, 0.70 AI)
- **Atomic writes**: E1.S2 creates backups before JSON writes; E2.S4 uses content-addressed storage
- **Dependencies**: E1→E2→E4→E5→E7 critical path; E3/E6 parallel

## Critical Learnings
- **E1 patterns**: Repository pattern, atomic writes, provenance tracking, exponential backoff
- **E2 storage**: Content-addressed (`{hash[:8]}/{hash}.png`) not address-based folders
- **E2 blockers**: Zillow CAPTCHA (BLOCK-001), Redfin CDN 404 (BLOCK-002) documented
- **Rate limiting**: County API ~0.5s/req, exponential backoff on 429 errors

## Refs
- Parent docs: `../CLAUDE.md` (project overview)
- PRD: `../prd/` (62 functional requirements)
- Architecture: `../architecture.md` (7 epic boundaries)
- Sprint tracking: `../sprint-artifacts/sprint-status.yaml`

## Dependencies
← PRD, Architecture, Story files | → Sprint planning, dev workflows
