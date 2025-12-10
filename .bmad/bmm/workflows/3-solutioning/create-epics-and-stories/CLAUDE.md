---
last_updated: 2025-12-10T12:00:00Z
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
| `workflow.yaml` | Workflow config (variables, input patterns, output paths) |
| `instructions.md` | Epic/story decomposition instructions |
| `epics-template.md` | Epic template with wave planning and orchestration metadata |

## Template Features (Added E3.S0)

| Feature | Section | Purpose |
|---------|---------|---------|
| Wave Planning | `## Wave Planning` | Groups stories by dependency into execution waves |
| Model Tiers | Per-wave field | haiku (docs) / sonnet (impl) / opus (vision) |
| Orchestration Summary | `## Orchestration Summary` | Total waves, critical path, parallelization count |
| Per-Story Block | Within each wave | Dependencies, conflicts, parallelizable flag |

## Tasks
- [x] Add wave planning section to epic template `P:H` (E3.S0)
- [x] Add orchestration summary section `P:H` (E3.S0)
- [x] Add per-story orchestration block `P:H` (E3.S0)
- [ ] Add automated FR coverage validation `P:M`

## Learnings
- **Story zero pattern:** Infrastructure before main epic work (Team Agreement TA4)
- **Wave planning enables parallelization:** Stories in same wave with no conflicts can run simultaneously
- **Model tier guidelines:** Haiku=simple docs/config, Sonnet=standard impl, Opus=complex/vision
- **Critical path identification:** Helps prioritize which stories block others

## Refs
- Epic template: `epics-template.md:1-162`
- E3.S0 Story: `docs/sprint-artifacts/stories/E3-S0-template-orchestration-metadata.md`
- E2 Retro: `docs/sprint-artifacts/epic-2-retro-supplemental-2025-12-07.md:144-152`

## Deps
← imports: `.bmad/bmm/config.yaml` (project variables)
→ used by: `create-story` workflow, sprint planning
