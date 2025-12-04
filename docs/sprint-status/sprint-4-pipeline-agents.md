# Sprint 4: Pipeline & Agents

> **Epic**: E5
> **Objective**: Coordinate automated multi-phase analysis with specialized agents
> **Stories**: 6
> **PRD Coverage**: FR28-33

### Stories

#### E5.S1 - Pipeline Orchestrator CLI [CRITICAL PATH]

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E1.S4, E1.S5 |
| **FRs** | FR28, FR53, FR57 |

**Acceptance Criteria**:
- [ ] `/analyze-property --all` processes all properties
- [ ] `/analyze-property "123 Main St"` processes single property
- [ ] `--status` shows phase and property counts
- [ ] Progress display with ETA

**Definition of Done**:
- [ ] `.claude/commands/analyze-property.md` slash command
- [ ] Orchestrator in `src/phx_home_analysis/pipeline/orchestrator.py`
- [ ] rich library tables for status display
- [ ] Flags: --all, --test, --resume, --status, --strict, --skip-phase=N

---

#### E5.S2 - Sequential Phase Coordination

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E5.S1 |
| **FRs** | FR29 |

**Acceptance Criteria**:
- [ ] Phase sequence: 0 -> 1a+1b (parallel) -> 2 -> 3 -> 4
- [ ] Per-property phase tracking
- [ ] Failure handling: mark failed, skip subsequent phases for that property
- [ ] --skip-phase capability with dependency warnings

**Definition of Done**:
- [ ] PhaseCoordinator in `src/phx_home_analysis/pipeline/`
- [ ] Each phase independently executable
- [ ] Integration test for full sequence

---

#### E5.S3 - Agent Spawning with Model Selection

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E5.S2 |
| **FRs** | FR30 |

**Acceptance Criteria**:
- [ ] **listing-browser**: Haiku, skills: listing-extraction, property-data, state-management, kill-switch
- [ ] **map-analyzer**: Haiku, skills: map-analysis, property-data, state-management, arizona-context, scoring
- [ ] **image-assessor**: Sonnet (vision required), skills: image-assessment, property-data, state-management, arizona-context-lite, scoring
- [ ] Spawn failure handling with logging

**Definition of Done**:
- [ ] Agent files in `.claude/agents/`
- [ ] Model selection per Architecture: Haiku for data, Sonnet for vision
- [ ] Cost tracking per model

---

#### E5.S4 - Phase Prerequisite Validation

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E5.S3 |
| **FRs** | FR31 |

**Acceptance Criteria**:
- [ ] `scripts/validate_phase_prerequisites.py` executed before Phase 2
- [ ] Exit code 0 = can_spawn=true, proceed
- [ ] Exit code 1 = can_spawn=false, BLOCK
- [ ] JSON output: {can_spawn, missing_data[], reasons[]}
- [ ] **MANDATORY**: Never spawn Phase 2 without validation passing

**Definition of Done**:
- [ ] Prerequisite validation script
- [ ] Phase 2 requires: images downloaded, Phase 1 complete
- [ ] Phase 3 requires: Phase 2 complete for all properties

---

#### E5.S5 - Parallel Phase 1 Execution

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E5.S4 |
| **FRs** | FR32 |

**Acceptance Criteria**:
- [ ] listing-browser and map-analyzer run in parallel
- [ ] Atomic writes to work_items.json with file locking
- [ ] Wait for BOTH agents to complete before Phase 2
- [ ] Timeout warning after 10 minutes if stuck

**Definition of Done**:
- [ ] async/await for parallel execution
- [ ] File locking for state file
- [ ] Partial success handling
- [ ] 10-minute timeout per property

---

#### E5.S6 - Multi-Agent Output Aggregation

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E5.S5 |
| **FRs** | FR33 |

**Acceptance Criteria**:
- [ ] county_data from Phase 0
- [ ] listing_data from listing-browser
- [ ] location_data from map-analyzer
- [ ] image_assessment from image-assessor
- [ ] Conflict resolution: county > listing > image for physical attributes

**Definition of Done**:
- [ ] DataAggregator in `src/phx_home_analysis/pipeline/`
- [ ] Provenance preserved per section
- [ ] Atomic write on aggregation

---
