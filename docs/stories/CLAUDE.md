---
last_updated: 2025-12-04
updated_by: Claude (Agent)
staleness_hours: 24
flags: []
---
# docs/stories

## Purpose

User story repository for PHX Houses Analysis Pipeline. Stores implementation-ready stories with detailed acceptance criteria, technical tasks with file:line references, and dependencies enabling AI agents and developers to execute work without discovery phase.

## Contents

| Path | Purpose |
|------|---------|
| `sprint-0-architecture-prerequisites.md` | Foundational alignment: 605→600 point scoring, kill-switch HARD/SOFT clarification (P0, 8pts) |
| `e1-s1-configuration-system-setup.md` | Config externalization from YAML with env overrides, validation, hot-reload (P0, 8pts) |
| `e1-s2-property-data-storage-layer.md` | JSON storage with atomic writes, address normalization, backup/restore (P0, 5pts, depends E1.S1) |
| `e1-s6-transient-error-recovery.md` | Retry decorator with exponential backoff, error classification, work_items.json integration (P0, 5pts) |
| `E4.S1-three-dimension-scoring.md` | Three-dimension scoring refinement: cost efficiency, systems quality, interior condition (DONE, 13pts) |
| `e5-s1-pipeline-orchestrator-cli.md` | Pipeline orchestration with typer CLI, progress reporting with rich, phase coordination (NEW, 13pts) |

## Story Structure Pattern

**Metadata:** Status (Ready for Development/Review), Epic, Priority, Points, Dependencies
**User Story:** "As [role], I want [feature], so that [benefit]"
**Acceptance Criteria (6+):** Given-When-Then format with AC1-AC6 prefixes
**Technical Tasks:** File paths with line ranges, action steps, nested acceptance criteria
**Test Plan:** Unit/integration test suites with counts
**Dependencies:** Explicit story/epic blocking relationships

## Tasks

- [x] Extract sprint-0 prerequisites blocking all work
- [x] Document E1.S1 configuration system story with 8 technical tasks
- [x] Document E1.S2 property data storage story with 10 technical tasks
- [x] Document E1.S6 transient error recovery story with 8 technical tasks
- [x] Add given-when-then acceptance criteria to all stories
- [x] Create E4.S1 three-dimension scoring story (13pts) P:H
- [x] Create E5.S1 pipeline orchestrator CLI story (13pts) P:H
- [ ] Link stories to implementation files with line-level precision P:H
- [ ] Auto-generate acceptance test matrix from AC definitions P:M

## Learnings

- **Story precision enables AI handoff:** Each task includes exact file:line ranges (e.g., `src/phx_home_analysis/config/constants.py:19-23`), reducing discovery time from hours to minutes
- **AC format is executable:** Given-When-Then acceptance criteria map directly to unit/integration tests (AC1 → test_ac1_*)
- **Dependency chains prevent ordering errors:** E1.S1 blocks E1.S2 blocks E1.S3 explicitly documented, preventing parallel sprint hazards
- **Technical task nesting provides structure:** Each AC has corresponding technical task(s) with implementation code snippets, acceptance criteria, and file locations

## Refs

- Sprint 0 blocking work: `sprint-0-architecture-prerequisites.md:1-150`
- E1.S1 config system: `e1-s1-configuration-system-setup.md:1-100` (8 technical tasks)
- E1.S2 data storage: `e1-s2-property-data-storage-layer.md:1-150` (10 technical tasks)
- E1.S6 error recovery: `e1-s6-transient-error-recovery.md:1-200` (8 technical tasks, 81 tests)
- E4.S1 three-dimension scoring: `E4.S1-three-dimension-scoring.md:1-120` (DONE, 13pts)
- E5.S1 pipeline CLI: `e5-s1-pipeline-orchestrator-cli.md:1-180` (NEW, 13pts, PhaseCoordinator + ProgressReporter)
- Metadata example: `e1-s1-configuration-system-setup.md:1-6` (Status, Epic, Priority, Points)

## Deps

← Imports from:
  - `docs/epics/` - Stories derived from epic functional requirements
  - `.claude/AGENT_BRIEFING.md` - Shared story context for agents
  - `src/phx_home_analysis/config/` - Config system targets
  - `src/phx_home_analysis/domain/` - Domain model references

→ Imported by:
  - Sprint planning (`work_items.json` tracking)
  - Dev/PM agents for story execution
  - CI/CD acceptance test generation
  - `/analyze-property` prerequisite validation
