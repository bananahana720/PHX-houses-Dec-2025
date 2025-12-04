---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# stories

## Purpose
User stories for BMAD sprint artifacts, capturing detailed requirements and acceptance criteria for implementation work. Each story represents a sized, ready-for-development task within a BMAD epic.

## Contents
| Path | Purpose |
|------|---------|
| `story-live-testing-infrastructure.md` | Live testing infrastructure for external API validation (E3.S1: 8pts, P1); validates mocked APIs against real endpoints to detect mock drift and reduce manual testing burden |

## Tasks
- [ ] Add story acceptance criteria tracking `P:M`
- [ ] Link completed story files to sprint-status.yaml burndown `P:H`
- [ ] Create story template with task decomposition schema `P:M`

## Learnings
- Story files capture full context (background, acceptance criteria, test plan) enabling async agent development
- Large story files (600+ lines) require careful section indexing for quick navigation
- Story status transitions (Draft → Ready → In Progress → Complete) should sync with sprint-status.yaml

## Refs
- Story format: `story-live-testing-infrastructure.md:1-50` (header, user story, background, pain points)
- BMAD epic definitions: `.bmad/bmm/workflows/create-epics-and-stories.md`
- Sprint tracking: `../sprint-status.yaml`
- Workflow status: `../workflow-status.yaml`

## Deps
← `../sprint-status.yaml` (epic/story progress tracking)
← `../workflow-status.yaml` (phase transition gates)
← `.bmad/` (story creation workflows)
→ Implementation agents (consume stories for dev tasks)
→ Sprint retrospectives (status validation)