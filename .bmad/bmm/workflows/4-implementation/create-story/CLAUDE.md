---
last_updated: 2025-12-07T12:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# create-story

## Purpose
Story creation workflow that generates implementation-ready story files from epic breakdowns. Templates include orchestration metadata for wave planning, model tier selection, and cross-layer validation.

## Contents
| Path | Purpose |
|------|---------|
| `workflow.yaml` | Workflow configuration and variables |
| `instructions.xml` | Step-by-step story creation instructions |
| `template.md` | Story template with orchestration metadata |
| `checklist.md` | Definition of Done validation checklist |

## Template Structure (Updated 2025-12-07)

The story template includes these key sections:

### Orchestration Metadata Section
Added per E3.S0 (Epic 2 Retro action item A1):
- **Model Tier:** haiku | sonnet | opus (with justification)
- **Wave Assignment:** Wave number (0=foundation, 1+=implementation)
- **Dependencies:** Story IDs this story depends on
- **Conflicts:** Story IDs that cannot run in parallel
- **Parallelizable:** Yes/No based on conflicts analysis

### Layer Touchpoints Section
Added per E3.S0 to document cross-layer integration:
- **Layers Affected:** extraction | persistence | orchestration | reporting
- **Integration Points:** Table mapping source/target layers to interfaces and data contracts

### Cross-Layer Validation Checklist
Added per E3.S0 (Epic 2 Retro Lesson L6):
- Extraction -> Persistence schema validation
- Persistence read-back verification
- Orchestration wiring validation
- End-to-End trace test requirement
- Type contract tests at boundaries

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
- Cross-Layer Guide: `docs/development-guide/cross-layer-validation-guide.md`

## Deps
<- imports: `.bmad/bmm/config.yaml` (project variables)
-> used by: `dev-story` workflow, story validation
