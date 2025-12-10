---
last_updated: 2025-12-10T12:00:00Z
updated_by: agent
staleness_hours: 24
flags: []
---
# stories

## Purpose
User stories (42 total across 7 epics) capturing detailed requirements and acceptance criteria for Phase 4 implementation. Each story represents a sized, ready-for-development task with test plan and success metrics.

## Contents

| Story | Epic | Status | Focus |
|-------|------|--------|-------|
| E1-S1 to E1-S6 | Epic 1 | ✅ Done | Configuration, storage, provenance, checkpoints, resume, retry |
| E2-S1 to E2-S7 | Epic 2 | ✅ Done | CLI, county API, Zillow/Redfin, images, maps, schools, HTTP infra |
| E2-R1 to E2-R3 | Epic 2 | ✅ Done | Zillow ZPID, PhoenixMLS full/extended extraction |
| E3-S0 | Epic 3 | ✅ Done | Template orchestration metadata (wave planning, cross-layer) |
| E3-S1 | Epic 3 | 📋 Draft | Hard kill-switch implementation |
| E4-S1 | Epic 4 | Backlog | Three-dimension scoring (605 pts) |
| E5-S1 | Epic 5 | Backlog | Pipeline orchestrator CLI |
| E7-S1 | Epic 7 | Backlog | Deal sheet HTML generation |

## Key Status (2025-12-10)

| Metric | Value |
|--------|-------|
| Epics Complete | 2/7 (E1, E2) |
| Stories Done | 20/42 (48%) |
| Latest Completed | E3.S0 - Template Orchestration Metadata |
| Next Up | E3.S1 - Hard Kill-Switch Implementation |

## Tasks
- [x] Complete E3.S0 template infrastructure `P:H`
- [ ] Finalize E3.S1 draft to ready-for-dev `P:H`
- [ ] Link E3 stories to kill-switch roadmap `P:H`
- [ ] Draft E4 scoring story specifications `P:M`

## Learnings
- **Story completeness critical**: Full context (AC, test plan, blockers) enables async agent development
- **Status synchronization vital**: Story completion requires updates to sprint-status.yaml
- **Orchestration metadata added**: E3.S0 added wave planning, model tiers, cross-layer validation to templates
- **Content-addressed storage**: E2.S4 approach prevents duplicate downloads

## Refs
- Sprint tracking: `../sprint-status.yaml`
- Workflow status: `../workflow-status.yaml`
- Story template: `.bmad/bmm/workflows/4-implementation/create-story/template.md`
- E3.S0 story: `E3-S0-template-orchestration-metadata.md`

## Deps
← `../sprint-status.yaml` (epic/story progress tracking)
← `../workflow-status.yaml` (phase gates, decisions)
← `.bmad/` (story creation workflows)
→ Implementation agents (dev-story workflow consumers)
→ Sprint retrospectives (completion validators)
