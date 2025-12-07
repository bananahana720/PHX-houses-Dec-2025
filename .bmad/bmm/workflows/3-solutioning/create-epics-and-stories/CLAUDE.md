---
last_updated: 2025-12-07T12:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# create-epics-and-stories

## Purpose
Epic and story breakdown workflow that decomposes PRD requirements into implementable epics and stories. Templates include wave planning for orchestration, parallelization analysis, and dependency tracking.

## Contents
| Path | Purpose |
|------|---------|
| `workflow.yaml` | Workflow configuration and variables |
| `instructions.xml` | Epic/story decomposition instructions |
| `epics-template.md` | Epic template with wave planning |
| `checklist.md` | FR coverage validation checklist |

## Template Structure (Updated 2025-12-07)

The epic template includes these key sections:

### Wave Planning Section
Added per E3.S0 (Epic 2 Retro action item A2):
- **Wave 0:** Foundation/infrastructure stories (templates, schemas, setup)
- **Wave 1+:** Implementation waves with dependency ordering
- **Per Wave Fields:**
  - Stories list
  - Model tier (haiku | sonnet | opus)
  - Dependencies (which waves must complete first)
  - Conflicts (stories that cannot run in parallel)
  - Parallelizable flag

### Orchestration Summary Section
Provides at-a-glance metrics for sprint planning:
- Total wave count
- Critical path (longest dependency chain)
- Parallelization opportunities
- Model distribution (Haiku/Sonnet/Opus counts)
- Estimated execution time

### Per-Story Orchestration Block
Each story within an epic now includes:
- Wave assignment
- Model tier
- Parallelizable flag
- Dependencies and conflicts
- Layer touchpoints

## Tasks
- [x] Add wave planning section to epic template `P:H` (E3.S0)
- [x] Add orchestration summary section `P:H` (E3.S0)
- [x] Add per-story orchestration block `P:H` (E3.S0)
- [ ] Add automated FR coverage validation `P:M`

## Learnings
- **Story zero pattern:** Infrastructure before main epic work (Team Agreement TA4)
- **Wave planning enables parallelization:** Stories in same wave with no conflicts can run simultaneously
- **Model tier guidelines:** Haiku=simple docs/config, Sonnet=standard implementation, Opus=complex/vision
- **Critical path identification:** Helps prioritize which stories block others

## Refs
- Epic template: `epics-template.md:1-162`
- E3.S0 Story: `docs/sprint-artifacts/stories/E3-S0-template-orchestration-metadata.md`
- E2 Retro: `docs/sprint-artifacts/epic-2-retro-supplemental-2025-12-07.md:144-152`
- E3 Wave Planning Example: `docs/epics/epic-3-kill-switch-filtering-system.md:10-27`

## Deps
<- imports: `.bmad/bmm/config.yaml` (project variables)
-> used by: `create-story` workflow, sprint planning
