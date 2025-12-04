# Epic 5: Multi-Agent Pipeline Orchestration

**User Value:** Coordinate automated multi-phase property analysis using specialized Claude agents with appropriate model selection, parallel execution, and reliable state management.

**PRD Coverage:** FR28-33
**Architecture References:** Multi-Agent Architecture, Phase Dependencies

---

### E5.S1: Pipeline Orchestrator CLI

**Priority:** P0 | **Dependencies:** E1.S4, E1.S5 | **FRs:** FR28, FR53, FR57

**User Story:** As a system user, I want to execute the complete pipeline via single CLI command, so that I can analyze properties without manual phase coordination.

**Acceptance Criteria:** `/analyze-property --all` processes all CSV properties through all phases with progress and ETA. Specific address processes single property. `--status` shows current phase, property counts by status, elapsed time, and ETA.

**Technical Notes:** Implement in `.claude/commands/analyze-property.md`. Orchestrator in `src/phx_home_analysis/pipeline/orchestrator.py`. Status via `rich` tables. Flags: `--all`, `--test`, `--resume`, `--status`, `--strict`, `--skip-phase=N`.

**Definition of Done:** analyze-property command | Orchestrator | Progress with ETA | Status query | Unit tests

---

### E5.S2: Sequential Phase Coordination

**Priority:** P0 | **Dependencies:** E5.S1 | **FRs:** FR29

**User Story:** As a system user, I want phases to execute in proper sequence, so that each phase has the data it needs from previous phases.

**Acceptance Criteria:** **Sequence:** Phase 0 (County) → Phase 1 (Listing + Map) → Phase 2 (Images) → Phase 3 (Synthesis). Failed property marked "failed", subsequent phases skipped for that property, others continue. `--skip-phase` validates dependencies and warns about incomplete data.

**Technical Notes:** Phase sequence: 0 → 1a+1b (parallel) → 2 → 3 → 4. Implement `PhaseCoordinator`. Each phase independently executable.

**Definition of Done:** PhaseCoordinator | Per-property tracking | Failure handling | Skip capability | Full sequence integration test

---

### E5.S3: Agent Spawning with Model Selection

**Priority:** P0 | **Dependencies:** E5.S2 | **FRs:** FR30

**User Story:** As a system user, I want specialized agents spawned with appropriate Claude models, so that I get optimal cost-capability balance.

**Acceptance Criteria:** **listing-browser:** Haiku + skills: listing-extraction, property-data, state-management, kill-switch. **map-analyzer:** Haiku + skills: map-analysis, property-data, state-management, arizona-context, scoring. **image-assessor:** Sonnet (vision) + skills: image-assessment, property-data, state-management, arizona-context-lite, scoring. Spawn failures logged with property marked failed; no automatic retry.

**Technical Notes:** Agent definitions in `.claude/agents/`. Model: Haiku for data, Sonnet for vision. Spawn via Claude Code CLI or Task tool.

**Definition of Done:** Agent files with model selection | Skill loading | Error handling | Cost tracking | Integration test

---

### E5.S4: Phase Prerequisite Validation

**Priority:** P0 | **Dependencies:** E5.S3 | **FRs:** FR31

**User Story:** As a system user, I want mandatory prerequisite validation before agent spawning, so that agents have the data they need to succeed.

**Acceptance Criteria:** Before Phase 2, `validate_phase_prerequisites.py` runs. Exit 0 = proceed, Exit 1 = BLOCK. Failures list missing data with reasons; agent NOT spawned. Passes confirm all required data present.

**Technical Notes:** Output JSON: `{"can_spawn": bool, "missing_data": [], "reasons": []}`. Phase 2 requires images downloaded + Phase 1 complete. MANDATORY: Never spawn Phase 2 without validation.

**Definition of Done:** Validation script | JSON output | Phase-specific requirements | Blocking on failure | Integration test

---

### E5.S5: Parallel Phase 1 Execution

**Priority:** P0 | **Dependencies:** E5.S4 | **FRs:** FR32

**User Story:** As a system user, I want Phase 1 sub-tasks to run in parallel, so that listing and map analysis happen concurrently.

**Acceptance Criteria:** listing-browser and map-analyzer run in parallel with atomic writes to work_items.json. Phase 2 waits for BOTH agents. Timeout warning after 10 minutes if stuck. One failing preserves partial data with warning, Phase 2 may proceed.

**Technical Notes:** Async/await for parallel execution. File locking for atomic writes. Phase 1a: listing-browser, 1b: map-analyzer. Coordination via shared state.

**Definition of Done:** Parallel spawning | Completion sync | Partial success handling | Timeout detection | Integration test

---

### E5.S6: Multi-Agent Output Aggregation

**Priority:** P0 | **Dependencies:** E5.S5 | **FRs:** FR33

**User Story:** As a system user, I want multi-agent outputs aggregated into unified records, so that all data is consolidated per property.

**Acceptance Criteria:** Sections: county_data (Phase 0), listing_data (listing-browser), location_data (map-analyzer), image_assessment (image-assessor). Conflicts: county preferred for lot_sqft/year_built/garage_spaces; listing for price/beds/baths/sqft. Conflicts logged. Atomic write with backup; metadata includes last_updated and pipeline_version.

**Technical Notes:** Implement `DataAggregator`. Merge strategy per Architecture. Each section retains original source provenance.

**Definition of Done:** DataAggregator | Conflict resolution | Provenance preservation | Atomic write | Unit tests for merge

---
