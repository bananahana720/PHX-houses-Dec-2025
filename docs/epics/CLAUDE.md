---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# docs/epics

## Purpose
Epic repository organizing PHX Houses Analysis Pipeline work into 7 user-value-focused epics with 42 implementation-ready stories. Transforms 62 functional requirements (100% coverage) into story-driven development roadmap with clear dependencies and critical path.

## Contents
| Path | Purpose |
|------|---------|
| `overview.md` | Epic decomposition summary (7 epics, 42 stories, critical path) |
| `index.md` | Master TOC and navigation for all epics |
| `summary.md` | Executive summary with metrics |
| `epic-1-foundation-data-infrastructure.md` | Foundation: config, data storage, logging, validation (6 stories) |
| `epic-2-property-data-acquisition.md` | Acquisition: County API, image extraction, deduplication (7 stories) |
| `epic-3-kill-switch-filtering-system.md` | Filtering: HARD/SOFT criteria, severity system, verdicts (5 stories) |
| `epic-4-property-scoring-engine.md` | Scoring: Location/Systems/Interior strategies, 600pt system (6 stories) |
| `epic-5-multi-agent-pipeline-orchestration.md` | Orchestration: Haiku/Sonnet agents, state management, phase control (6 stories) |
| `epic-6-visual-analysis-risk-intelligence.md` | Analysis: Image assessment, risk scoring, visualizations (6 stories) |
| `epic-7-deal-sheet-generation-reports.md` | Reports: Deal sheets, property rankings, export formats (6 stories) |
| `fr-inventory-by-category.md` | 62 functional requirements indexed by feature area |
| `fr-coverage-matrix.md` | Traceability matrix linking FRs to stories |

## Tasks
- [x] Map 62 functional requirements to 7 epics `P:H`
- [x] Define critical path for sequential execution `P:H`
- [x] Organize stories with dependencies and acceptance criteria `P:H`
- [ ] Add story estimation (story points) across epics `P:M`
- [ ] Track epic completion % as stories are implemented `P:M`
- [ ] Create Gantt chart for timeline visualization `P:L`

## Learnings

### Epic Organization Pattern
- **User value-focused**: Each epic focuses on specific user outcome (e.g., "Kill-Switch Filtering System" solves deal-breaker elimination)
- **Cross-cutting stories**: Configuration, validation, logging cut across multiple epics but grouped in E1
- **Dependency-driven sequence**: Critical path (E1→E2→E4→E5→E7) ensures dependencies resolved before dependent work

### Story Structure Pattern
- **42 stories total**: 35 P0 (critical), 7 P1 (important)
- **Epic 1 blocking**: Foundation (config system, data storage) must complete before other epics
- **Parallel capability**: E2, E3, E4, E6 can execute in parallel once E1 complete
- **Stories are implementation-ready**: Each has user story statement, 6+ acceptance criteria, precise file:line technical tasks

### FR Coverage
- **62 FRs mapped**: 100% coverage of PRD requirements across 7 epics
- **Traceability maintained**: FR-to-story mapping enables verification that no requirement missed
- **Inventory by category**: FRs grouped by feature area (data, filtering, scoring, agents, reports)

### Critical Path Analysis
- **Shortest path to MVP**: E1.S1 (Config) → E1.S2 (Storage) → E1.S6 (Validation) → E2.S7 (Enrichment) → E4.S1 (Scoring) → E5.S1 (Orchestration) → E7.S1 (Deal Sheets)
- **Enables parallel work**: Once E1 complete, E2/E3/E4/E6 can execute concurrently
- **Dependency clarity**: Prevents blocked work and enables sprint planning

## Refs
- Epic overview: `overview.md:1-50` (7 epics, 42 stories, metrics)
- Critical path: `overview.md:24` (E1→E2→E4→E5→E7)
- Foundation epic: `epic-1-foundation-data-infrastructure.md:1-100` (config, storage, validation, logging)
- FR inventory: `fr-inventory-by-category.md:1-200` (62 requirements indexed by feature)
- Coverage matrix: `fr-coverage-matrix.md:1-300` (FR-to-story traceability)
- Story template: `../stories/` (user story statement, ACs, technical tasks)

## Deps
← Imports from:
  - PRD (62 functional requirements)
  - Architecture decisions (7 epic boundaries)
  - Story files in `../stories/` (detailed user stories derived from epics)

→ Imported by:
  - `.claude/AGENT_BRIEFING.md` - Epic context for agents
  - Sprint planning (`work_items.json` tracks story progress)
  - Roadmap documentation (external stakeholder communication)
  - Story decomposition (stories reference epic context)
