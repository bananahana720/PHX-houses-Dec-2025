---
last_updated: 2025-12-04
updated_by: Claude (Agent)
staleness_hours: 24
flags: []
---
# docs/sprint_artifacts

## Purpose

Sprint status tracking system for PHX Houses Analysis Pipeline. Contains YAML-based sprint state with epic and story progress tracking, serving as the source of truth for development workflow and CI/CD integration.

## Contents

| Path | Purpose |
|------|---------|
| `sprint-status.yaml` | YAML tracking file: epic statuses, story states, summary counts, timeline (7 epics, 42 stories) |

## Key Structure

**File Format:** YAML with:
- Metadata section (project, tracking system, story location)
- development_status section mapping all epics and stories to states
- summary section tracking totals and coverage

**Epic States:** backlog, contexted
**Story States:** backlog, drafted, ready-for-dev, in-progress, review, done

## Tasks

- [x] Document sprint tracking YAML structure and state machine
- [x] Map story status transitions: backlog → ready-for-dev → in-progress → review → done
- [x] Document epic status flow: backlog → contexted → (optional retrospective)
- [ ] Implement CI/CD gate to validate story transitions P:H
- [ ] Add automation to update summary counts on status changes P:M

## Learnings

- **State machine clarity:** Each story has well-defined states enabling workflow automation
- **Kill-switch for retrospective:** Epic retrospective is `optional` (not required) - only mandatory after epic complete
- **PRD coverage tracking:** Summary includes `fr_coverage` field (62/62 = 100%) for traceability
- **Atomic status updates:** Supports atomic transitions without race conditions via file-based locking

## Refs

- Status definitions: `sprint-status.yaml:119-137`
- Epic 1 config: `sprint-status.yaml:13-27` (6 stories + retrospective)
- Summary stats: `sprint-status.yaml:140-158` (total_stories: 42, p0_stories: 35)

## Deps

← Imports from:
  - `docs/stories/*.md` - Story definitions with acceptance criteria
  - `.claude/AGENT_BRIEFING.md` - Sprint execution context

→ Imported by:
  - CI/CD pipeline for gate checks
  - `/analyze-property` command for phase validation
  - Progress reporting dashboards
