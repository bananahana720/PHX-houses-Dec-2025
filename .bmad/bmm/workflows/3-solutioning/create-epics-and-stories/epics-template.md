# {{project_name}} - Epic Breakdown

**Author:** {{user_name}}
**Date:** {{date}}
**Project Level:** {{project_level}}
**Target Scale:** {{target_scale}}

---

## Overview

This document provides the complete epic and story breakdown for {{project_name}}, decomposing the requirements from the [PRD](./PRD.md) into implementable stories.

**Living Document Notice:** This is the initial version. It will be updated after UX Design and Architecture workflows add interaction and technical details to stories.

{{epics_summary}}

---

## Functional Requirements Inventory

{{fr_inventory}}

---

## FR Coverage Map

{{fr_coverage_map}}

---

## Wave Planning

<!--
WAVE PLANNING SECTION (Required for all epics)
Documents execution waves, dependencies, model tiers, and parallelization opportunities.
Reference: Epic 2 Supplemental Retrospective (2025-12-07) - Team Agreement TA4

Wave Definitions:
- Wave 0: Foundation/infrastructure stories (templates, schemas, setup)
- Wave 1+: Implementation waves with dependency ordering

Model Tier Guidelines:
- haiku: Simple tasks (documentation, templates, config)
- sonnet: Standard implementation (CRUD, integrations, business logic)
- opus: Complex tasks requiring vision, architecture decisions, or deep reasoning

Parallelization Rules:
- Stories in same wave CAN run in parallel if no conflicts
- Conflicts = stories modifying same files/data/state
- Dependencies = stories requiring outputs from previous waves
-->

### Wave 0: Foundation
- **Stories:** [List story IDs, e.g., E{{N}}.S0]
- **Model Tier:** [haiku | sonnet | opus]
- **Parallelizable:** [Yes | No]
- **Purpose:** [Why these stories are foundation/prerequisites before main epic work]

### Wave 1: Core Implementation
- **Stories:** [List story IDs, e.g., E{{N}}.S1, E{{N}}.S2]
- **Dependencies:** Wave 0 complete
- **Conflicts:** [Any stories that cannot run in parallel, or "None"]
- **Model Tier:** [haiku | sonnet | opus]
- **Purpose:** [Core functionality that subsequent waves depend on]

### Wave 2: Extensions
- **Stories:** [List story IDs]
- **Dependencies:** [Which waves/stories must complete first]
- **Conflicts:** [Any parallel restrictions]
- **Model Tier:** [haiku | sonnet | opus]
- **Parallelizable:** [Yes | No - stories within this wave]

<!-- Add additional waves as needed (Wave 3, Wave 4, etc.) -->

---

## Orchestration Summary

<!--
ORCHESTRATION SUMMARY (Computed from Wave Planning)
Provides at-a-glance orchestration metrics for sprint planning.
-->

- **Total Waves:** [N]
- **Critical Path:** [Story IDs that form the longest dependency chain]
- **Parallelization Opportunities:** [Count of stories that can run in parallel within waves]
- **Model Distribution:**
  - Haiku: [N] stories
  - Sonnet: [N] stories
  - Opus: [N] stories
- **Estimated Execution Time:** [Based on wave structure - sequential waves + parallel story counts]

---

<!-- Repeat for each epic (N = 1, 2, 3...) -->

## Epic {{N}}: {{epic_title_N}}

{{epic_goal_N}}

<!-- Repeat for each story (M = 1, 2, 3...) within epic N -->

### Story {{N}}.{{M}}: {{story_title_N_M}}

As a {{user_type}},
I want {{capability}},
So that {{value_benefit}}.

**Orchestration:**
- **Wave:** [N]
- **Model Tier:** [haiku | sonnet | opus]
- **Parallelizable:** [Yes | No]
- **Dependencies:** [Story IDs or "None"]
- **Conflicts:** [Story IDs or "None"]

**Acceptance Criteria:**

**Given** {{precondition}}
**When** {{action}}
**Then** {{expected_outcome}}

**And** {{additional_criteria}}

**Prerequisites:** {{dependencies_on_previous_stories}}

**Technical Notes:** {{implementation_guidance}}

**Layer Touchpoints:** [extraction | persistence | orchestration | reporting]

<!-- End story repeat -->

---

<!-- End epic repeat -->

---

## FR Coverage Matrix

{{fr_coverage_matrix}}

---

## Summary

{{epic_breakdown_summary}}

### Epic Orchestration Summary

| Epic | Total Stories | Waves | Critical Path Length | Parallel Opportunities |
|------|---------------|-------|----------------------|------------------------|
| Epic {{N}} | [count] | [wave count] | [longest dependency chain] | [parallel story count] |

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._

_This document will be updated after UX Design and Architecture workflows to incorporate interaction details and technical decisions._

_Wave planning enables parallel execution where safe, while maintaining dependency ordering and preventing conflicts._
