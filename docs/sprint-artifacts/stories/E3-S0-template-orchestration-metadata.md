---
story_id: E3-S0
epic: epic-3-kill-switch-filtering-system
title: Template Orchestration Metadata
status: pending
priority: P0
points: 2
created: 2025-12-07
wave: 0
type: infrastructure
depends_on: []
---

# E3.S0: Template Orchestration Metadata

## Summary
Update story and epic templates with orchestration metadata fields to enable wave planning, parallelization analysis, and cross-layer validation BEFORE Epic 3 main work begins. This "story zero" establishes template infrastructure required for all subsequent Epic 3+ stories.

## Background
**From Epic 2 Supplemental Retrospective (2025-12-07):**
- **Key Lesson L6:** "Cross-layer resonance is critical" - extraction, persistence, and orchestration layers must align
- **Challenge C4:** Layers work individually but not together; integration seams hide bugs
- **Team Agreement TA4:** Story zero for infrastructure before main epic work

**Current State:** Story template (`.bmad/bmm/workflows/4-implementation/create-story/template.md`) and epic template (`.bmad/bmm/workflows/3-solutioning/create-epics-and-stories/epics-template.md`) lack orchestration metadata.

**Target State:** Templates include wave planning, model tier selection, parallelization, dependencies, and cross-layer validation.

## Acceptance Criteria

### AC1: Story Template Orchestration Metadata Block
- [ ] Add `## Orchestration Metadata` section after frontmatter YAML
- [ ] Include `model_tier` field (haiku | sonnet | opus) with justification rationale
- [ ] Include `wave` field (0-N, execution wave number)
- [ ] Include `parallelizable` field (true/false with conflict analysis)
- [ ] Include `dependencies` field (list of story IDs this depends on)
- [ ] Include `conflicts` field (list of story IDs that cannot run in parallel)

### AC2: Story Template Layer Touchpoints Section
- [ ] Add `## Layer Touchpoints` section in Dev Notes
- [ ] Include `layers_affected` field (extraction | persistence | orchestration | reporting)
- [ ] Include `integration_points` field (specific files/modules that connect layers)

### AC3: Story Template Cross-Layer Validation Checklist
- [ ] Add `## Cross-Layer Validation` section before Definition of Done
- [ ] Include extraction→persistence schema validation checkpoint
- [ ] Include persistence read-back validation checkpoint
- [ ] Include orchestration wiring validation checkpoint
- [ ] Include end-to-end trace test requirement

### AC4: Epic Template Wave Planning Section
- [ ] Add `## Wave Planning` section after epic overview
- [ ] Include wave breakdown with story groupings (Wave 0, Wave 1, etc.)
- [ ] Include model tier recommendation per wave
- [ ] Include parallelization opportunities analysis
- [ ] Include dependency tracking across waves
- [ ] Include conflicts documentation

### AC5: Epic Template Orchestration Summary
- [ ] Add `## Orchestration Summary` section before FR Coverage Matrix
- [ ] Include total wave count
- [ ] Include critical path stories identification
- [ ] Include parallelization opportunities summary

### AC6: Template Validation via E3.S1 Draft
- [ ] Create E3.S1 draft using new story template
- [ ] Verify all orchestration metadata fields are populated
- [ ] Verify cross-layer validation checklist is applicable
- [ ] Confirm template format is usable by development agents

## Technical Requirements

### Story Template Changes (template.md)

**File:** `.bmad/bmm/workflows/4-implementation/create-story/template.md`

**New Section 1: Orchestration Metadata (after frontmatter, before Story section)**
```markdown
## Orchestration Metadata

**Model Tier:** [haiku | sonnet | opus]
- **Justification:** [Why this model tier is appropriate for this story]

**Wave Assignment:** Wave [N]
- **Dependencies:** [List story IDs this depends on, or "None"]
- **Conflicts:** [List story IDs that cannot run in parallel, or "None"]
- **Parallelizable:** [Yes | No]

**Layer Touchpoints:**
- **Layers Affected:** [extraction | persistence | orchestration | reporting]
- **Integration Points:** [Specific files/modules that connect layers]
```

**New Section 2: Cross-Layer Validation (before Definition of Done)**
```markdown
## Cross-Layer Validation Checklist

- [ ] **Extraction → Persistence:** Output schema matches persistence input schema
- [ ] **Persistence Verification:** Write followed by read-back test validates data integrity
- [ ] **Orchestration Wiring:** Correct extractor/persister instantiation with proper config
- [ ] **End-to-End Trace:** Full pipeline test from input to persisted output
```

### Epic Template Changes (epics-template.md)

**File:** `.bmad/bmm/workflows/3-solutioning/create-epics-and-stories/epics-template.md`

**New Section 1: Wave Planning (after epic overview)**
```markdown
## Wave Planning

### Wave 0: Foundation
- **Stories:** [List story IDs]
- **Model Tier:** [haiku | sonnet | opus]
- **Parallelizable:** [Yes | No]
- **Purpose:** [Why these stories are foundation/prerequisites]

### Wave 1: Core Implementation
- **Stories:** [List story IDs]
- **Dependencies:** [Which waves must complete first]
- **Conflicts:** [Any stories that cannot run in parallel]
- **Model Tier:** [haiku | sonnet | opus]

[Additional waves as needed...]

## Orchestration Summary

- **Total Waves:** [N]
- **Critical Path:** [Story IDs that form the longest dependency chain]
- **Parallelization Opportunities:** [Number of stories that can run in parallel]
- **Estimated Execution Time:** [Based on wave structure and model tiers]
```

## Tasks/Subtasks

### Task 1: Update Story Template
- [ ] 1.1 Add Orchestration Metadata section with model tier, wave, dependencies, conflicts
- [ ] 1.2 Add Layer Touchpoints subsection in Dev Notes
- [ ] 1.3 Add Cross-Layer Validation checklist before Definition of Done
- [ ] 1.4 Add inline documentation explaining each field
- [ ] 1.5 Update template file header/comments

### Task 2: Update Epic Template
- [ ] 2.1 Add Wave Planning section after epic overview
- [ ] 2.2 Add Orchestration Summary section before FR Coverage Matrix
- [ ] 2.3 Add wave template structure (Wave 0-N)
- [ ] 2.4 Add inline documentation for wave planning
- [ ] 2.5 Update template file header/comments

### Task 3: Create E3.S1 Draft for Validation
- [ ] 3.1 Copy new story template to `E3-S1-hard-kill-switch-implementation-DRAFT.md`
- [ ] 3.2 Populate all orchestration metadata fields
- [ ] 3.3 Verify cross-layer validation checklist applies to E3.S1
- [ ] 3.4 Document any template issues discovered during population
- [ ] 3.5 Refine templates based on validation feedback

### Task 4: Documentation Updates
- [ ] 4.1 Update `.bmad/bmm/workflows/4-implementation/create-story/CLAUDE.md` to reference orchestration fields
- [ ] 4.2 Update `.bmad/bmm/workflows/3-solutioning/create-epics-and-stories/CLAUDE.md` to reference wave planning
- [ ] 4.3 Update `docs/sprint-artifacts/epic-2-retro-supplemental-2025-12-07.md` to mark A1/A2 complete
- [ ] 4.4 Document template changes in `CHANGELOG.md` or architecture docs

### Task 5: Validation
- [ ] 5.1 Verify template markdown syntax is valid
- [ ] 5.2 Verify E3.S1 draft is complete and follows new template
- [ ] 5.3 Get approval from SM/PM on template format
- [ ] 5.4 Run ruff/linters on any Python examples in templates (if applicable)

## Dependencies
- Epic 2 Supplemental Retrospective (docs/sprint-artifacts/epic-2-retro-supplemental-2025-12-07.md)
- Current story template (`.bmad/bmm/workflows/4-implementation/create-story/template.md`)
- Current epic template (`.bmad/bmm/workflows/3-solutioning/create-epics-and-stories/epics-template.md`)

## Dev Notes

### Orchestration Metadata Purpose
- **Model Tier:** Ensures appropriate AI model for task complexity (Haiku=simple, Sonnet=moderate, Opus=complex/vision)
- **Wave:** Groups stories by dependency and enables parallel execution planning
- **Parallelizable:** Identifies stories that can run simultaneously vs must be sequential
- **Dependencies:** Explicit story prerequisites prevent out-of-order execution
- **Conflicts:** Identifies stories that modify same files/data and cannot run in parallel

### Cross-Layer Validation Context
From Epic 2 Retrospective Lesson L6:
> "Code awareness and ensuring functional and software resonance is lacking. The different layers of the system (extraction, persistence, orchestration) weren't communicating properly. Extraction code worked perfectly in isolation, persistence code worked perfectly in isolation, but the connection between them had bugs that only surfaced in production."

**Examples of Cross-Layer Bugs from E2:**
- String vs enum type mismatch in ImageProcessor (E2.R1 Wave 2)
- 37 fields extracted, only 10 persisted (E2.R2)
- Kill-switch metadata not auto-persisted to enrichment_data.json (E2.R1 Wave 3)

### Wave Planning Guidelines
- **Wave 0:** Infrastructure/templates/foundation (this story)
- **Wave 1:** Core implementation with no dependencies
- **Wave 2+:** Dependent stories or extensions
- **Parallelization:** Stories in same wave with `parallelizable: true` and no conflicts can run simultaneously

### Project Structure Notes

**Template Locations:**
- Story template: `.bmad/bmm/workflows/4-implementation/create-story/template.md`
- Epic template: `.bmad/bmm/workflows/3-solutioning/create-epics-and-stories/epics-template.md`

**Example Story Files to Reference:**
- `docs/sprint-artifacts/stories/E2-R3-phoenixmls-extended-extraction.md` (has YAML frontmatter)
- `docs/sprint-artifacts/stories/E2-S1-batch-analysis-cli.md` (detailed task breakdown)

**Epic Files to Reference:**
- `docs/epics/epic-3-kill-switch-filtering-system.md` (includes Wave 0 section)

### References

- [Retro Source: docs/sprint-artifacts/epic-2-retro-supplemental-2025-12-07.md:43-56] - Action Items A1/A2
- [Retro Source: docs/sprint-artifacts/epic-2-retro-supplemental-2025-12-07.md:86-104] - Cross-layer resonance challenge
- [Epic 3 Wave 0: docs/epics/epic-3-kill-switch-filtering-system.md:10-26] - Wave 0 precedent
- [Story Template: .bmad/bmm/workflows/4-implementation/create-story/template.md] - Current format
- [Epic Template: .bmad/bmm/workflows/3-solutioning/create-epics-and-stories/epics-template.md] - Current format
- [Cross-Layer Validation Guide: docs/development-guide/cross-layer-validation-guide.md] - Validation checklist (Action Item A8)

## Dev Agent Record

### Context Reference

- Epic 2 Supplemental Retrospective: `docs/sprint-artifacts/epic-2-retro-supplemental-2025-12-07.md`
- Story template: `.bmad/bmm/workflows/4-implementation/create-story/template.md`
- Epic template: `.bmad/bmm/workflows/3-solutioning/create-epics-and-stories/epics-template.md`

### Agent Model Used

Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

### Debug Log References

None (template creation task)

### Completion Notes List

- This is a meta-story: it updates the templates used to create future stories
- E3.S1 draft creation validates the new template format
- Template changes are documentation-only (no code changes)
- Cross-layer validation checklist addresses Epic 2's key lesson about layer integration

### File List

**Modified:**
- `.bmad/bmm/workflows/4-implementation/create-story/template.md` - Add orchestration metadata, layer touchpoints, cross-layer validation
- `.bmad/bmm/workflows/3-solutioning/create-epics-and-stories/epics-template.md` - Add wave planning, orchestration summary

**Created:**
- `docs/sprint-artifacts/stories/E3-S1-hard-kill-switch-implementation-DRAFT.md` - Template validation

**Updated:**
- `.bmad/bmm/workflows/4-implementation/create-story/CLAUDE.md` - Reference orchestration fields
- `.bmad/bmm/workflows/3-solutioning/create-epics-and-stories/CLAUDE.md` - Reference wave planning

## Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-12-07 | Story created per Epic 2 Supplemental Retro action items A1/A2 | Claude |

## Definition of Done Checklist

- [ ] Story template updated with orchestration metadata section
- [ ] Story template updated with cross-layer validation checklist
- [ ] Epic template updated with wave planning section
- [ ] Epic template updated with orchestration summary section
- [ ] E3.S1 draft created using new templates to validate format
- [ ] CLAUDE.md files updated to reference new template sections
- [ ] Templates committed to repository
- [ ] Epic 2 Supplemental Retro action items A1/A2 marked complete
- [ ] Sprint-status.yaml updated to show E3.S0 complete
- [ ] All documentation changes reviewed and approved
