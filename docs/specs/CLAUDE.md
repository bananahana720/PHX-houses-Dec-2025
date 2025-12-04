---
last_updated: 2025-12-04
updated_by: main
staleness_hours: 168
flags: []
---

# docs/specs

## Purpose

Centralized repository for implementation specifications, phase execution guides, reference documentation, and operational procedures for the PHX Houses Analysis Pipeline. Provides detailed technical requirements, step-by-step execution frameworks, cross-reference materials, and user-facing documentation for pipeline operations and resume capabilities.

## Contents

| Path | Purpose |
|------|---------|
| `implementation-spec/` | Detailed technical specifications organized by implementation wave (0-6); defines architecture, data models, validation logic, quality metrics, and integration requirements |
| `phase-execution-guide/` | Actionable execution guide for multi-phase pipeline runs; includes session planning, troubleshooting, continuity rules, and success metrics |
| `reference-index/` | Master reference catalog with links to research, rubrics, code architecture, testing references, and related documents; serves as single source of truth |
| `pipeline-resume-guide.md` | User documentation (E1.S5) for pipeline resume capability; covers quick start, CLI usage, state validation, and recovery procedures |

## Tasks

- [x] Create CLAUDE.md for top-level specs directory `P:H`
- [ ] Keep reference-index synchronized with new specifications `P:M`
- [ ] Update phase-execution-guide when implementation specs change `P:M`

## Learnings

- **Wave-based structure**: Implementation divided into 6 waves enables incremental delivery and testing (Wave 0=baseline, 1-5=features, 6=docs)
- **Separation of concerns**: `implementation-spec/` (WHAT), `phase-execution-guide/` (HOW), `reference-index/` (WHERE/WHY) prevents duplication
- **Resume capability critical**: `pipeline-resume-guide.md` documents essential feature for long-running batch operations (crash recovery, continuity)
- **Session planning essential**: `phase-execution-guide/session-planning-matrix.md` prevents mid-session state corruption by enforcing clear entry/exit states

## Refs

- Wave structure definition: `implementation-spec/index.md:1-20`
- Phase execution entry point: `phase-execution-guide/index.md:1-25`
- Resume capability guide: `pipeline-resume-guide.md:1-100`
- Session planning matrix: `phase-execution-guide/session-planning-matrix.md:1-50`
- Reference index catalog: `reference-index/index.md:1-50`

## Deps

← Imported by:
  - `docs/CLAUDE.md` - References specs/ as core implementation documentation
  - `../.claude/commands/analyze-property.md` - Uses phase-execution-guide for orchestration
  - `../.claude/AGENT_BRIEFING.md` - Links to phase-execution-guide for multi-agent workflow

→ Imports from:
  - `src/phx_home_analysis/pipeline/` - Implementation modules match Wave structure
  - `src/phx_home_analysis/config/` - Constants and scoring weights referenced in specs
  - `scripts/` - CLI scripts implement phase-execution-guide procedures
