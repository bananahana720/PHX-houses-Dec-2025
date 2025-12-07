# Story {{epic_num}}.{{story_num}}: {{story_title}}

Status: drafted

---

## Orchestration Metadata

<!--
ORCHESTRATION METADATA FIELDS (Required for all stories)
These fields enable wave planning, parallelization analysis, and cross-layer validation.
Reference: Epic 2 Supplemental Retrospective (2025-12-07) - Lesson L6: Cross-layer resonance

Field Definitions:
- model_tier: AI model appropriate for story complexity
  - haiku: Simple tasks (documentation, templates, minor updates)
  - sonnet: Standard implementation (CRUD, integrations, business logic)
  - opus: Complex tasks requiring vision, architecture decisions, or deep reasoning
- wave: Execution wave number (0=foundation, 1+=implementation waves)
- parallelizable: Can this story run simultaneously with others in same wave?
- dependencies: Story IDs that must complete before this story starts
- conflicts: Story IDs that modify same files/data (cannot run in parallel)
-->

**Model Tier:** [haiku | sonnet | opus]
- **Justification:** [Why this model tier is appropriate for this story's complexity]

**Wave Assignment:** Wave [N]
- **Dependencies:** [List story IDs this depends on, or "None"]
- **Conflicts:** [List story IDs that cannot run in parallel due to shared resources, or "None"]
- **Parallelizable:** [Yes | No - based on conflicts analysis]

---

## Layer Touchpoints

<!--
LAYER TOUCHPOINTS (Required for implementation stories)
Documents which system layers this story affects and their integration points.
Purpose: Prevent "extraction works but persistence doesn't" bugs (E2 Retrospective).

Layer Types:
- extraction: Data gathering from external sources (APIs, web scraping)
- persistence: Data storage and retrieval (JSON, database, cache)
- orchestration: Pipeline coordination, state management, agent spawning
- reporting: Output generation (deal sheets, visualizations, exports)
-->

**Layers Affected:** [extraction | persistence | orchestration | reporting] (list all that apply)

**Integration Points:**
| Source Layer | Target Layer | Interface/File | Data Contract |
|--------------|--------------|----------------|---------------|
| [layer] | [layer] | [file path or module] | [schema or type] |

---

## Story

As a {{role}},
I want {{action}},
so that {{benefit}}.

## Acceptance Criteria

1. [Add acceptance criteria from epics/PRD]

## Tasks / Subtasks

- [ ] Task 1 (AC: #)
  - [ ] Subtask 1.1
- [ ] Task 2 (AC: #)
  - [ ] Subtask 2.1

## Dev Notes

- Relevant architecture patterns and constraints
- Source tree components to touch
- Testing standards summary

### Project Structure Notes

- Alignment with unified project structure (paths, modules, naming)
- Detected conflicts or variances (with rationale)

### References

- Cite all technical details with source paths and sections, e.g. [Source: docs/<file>.md#Section]

---

## Cross-Layer Validation Checklist

<!--
CROSS-LAYER VALIDATION (Required before Definition of Done)
Ensures all affected layers communicate properly and data flows end-to-end.
Source: Epic 2 Supplemental Retrospective - Lesson L6, Team Agreement TA1

Complete ALL applicable checkpoints before marking story complete.
Mark N/A for layers not affected by this story.
-->

- [ ] **Extraction -> Persistence:** Output schema matches persistence input schema (types, field names, enums)
- [ ] **Persistence Verification:** Write followed by read-back test validates data integrity
- [ ] **Orchestration Wiring:** Correct extractor/persister/processor instantiation with proper config
- [ ] **End-to-End Trace:** Full pipeline test from input to persisted output with trace logging
- [ ] **Type Contract Tests:** Boundary types validated (no string/enum mismatches at integration seams)

---

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

## Change Log

| Date | Change | Author |
|------|--------|--------|
| {{date}} | Story created | {{author}} |
