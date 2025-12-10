---
last_updated: 2025-12-10T12:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# create-story

## Purpose
Story creation workflow generating implementation-ready story files from epic breakdowns. Templates include orchestration metadata for wave planning, model tier selection, and cross-layer validation.

## Contents
| Path | Purpose |
|------|---------|
| `workflow.yaml` | Workflow config (variables, inputs, output paths) |
| `instructions.xml` | Step-by-step story creation instructions |
| `template.md` | Story template with orchestration metadata |
| `checklist.md` | Definition of Done validation checklist |

## Template Features (Added E3.S0)

| Feature | Section | Purpose |
|---------|---------|---------|
| Orchestration Metadata | `## Orchestration Metadata` | model_tier, wave, dependencies, conflicts, parallelizable |
| Layer Touchpoints | In Dev Notes | layers_affected, integration_points table |
| Cross-Layer Validation | Before DoD | extraction→persistence, read-back, orchestration wiring, e2e trace |

## Tasks
- [x] Add orchestration metadata section to template `P:H` (E3.S0)
- [x] Add layer touchpoints section to template `P:H` (E3.S0)
- [x] Add cross-layer validation checklist `P:H` (E3.S0)
- [ ] Add automated template validation `P:M`

## Learnings
- **Cross-layer resonance critical:** E2 Retro revealed extraction/persistence/orchestration layers weren't communicating (L6)
- **Wave planning enables parallelization:** Stories with no conflicts can run simultaneously within waves
- **Model tier selection matters:** Haiku for docs, Sonnet for implementation, Opus for vision/architecture

## Refs
- Template: `template.md:1-132`
- E3.S0 Story: `docs/sprint-artifacts/stories/E3-S0-template-orchestration-metadata.md`
- E2 Retro: `docs/sprint-artifacts/epic-2-retro-supplemental-2025-12-07.md:106-116`

## Deps
← imports: `.bmad/bmm/config.yaml` (project variables)
→ used by: `dev-story` workflow, story validation
