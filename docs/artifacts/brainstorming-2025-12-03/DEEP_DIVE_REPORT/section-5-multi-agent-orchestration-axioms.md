# SECTION 5: MULTI-AGENT ORCHESTRATION AXIOMS

### 10 Documented Axioms (protocols.md TIER 1.5)

| # | Axiom | Status | Implementation |
|---|-------|--------|-----------------|
| 1 | **Dependency Verification** | DOCUMENTED | Test script preconditions before workflow integration |
| 2 | **Output Constraints** | DOCUMENTED | Subagent prompts specify format + length limits |
| 3 | **Right-Sized Tools** | DOCUMENTED | Grep for lookups; agents for exploration (10x cost difference) |
| 4 | **Completeness Gates** | DOCUMENTED | Check data availability before spawning dependent agents |
| 5 | **External State Respect** | DOCUMENTED | Accept externally-modified state as authoritative |
| 6 | **Attempt Over Assume** | DOCUMENTED | Try MCP calls; don't assume blocked without evidence |
| 7 | **Single Writer** | DOCUMENTED | Orchestrator modifies shared state; agents return data |
| 8 | **Atomic State** | DOCUMENTED | Use locking/CAS for concurrent access |
| 9 | **Fail Fast** | DOCUMENTED | Detect pattern of failures; propagate to skip redundant attempts |
| 10 | **Reuse Logic** | DOCUMENTED | Call existing scripts; don't reimplement |

**Implementation Status:** Rules are clearly written but **enforcement is manual** - no middleware enforces these yet.

### Phase Dependency Graph (toolkit.json)

```
Phase 0: County API → lot_sqft, year_built, garage_spaces
  ↓ (no dependencies)

Phase 1a: Listing Browser → images, price, HOA
  ↓ (parallel with Phase 1b)

Phase 1b: Map Analyzer → schools, safety, orientation
  ↓ (both must complete)

Phase 2: Image Assessor (VALIDATES PREREQUISITES BEFORE SPAWN)
  ├─ Requires: Phase 1 listing complete
  ├─ Validates: image_folder exists, image_count > 0
  └─ Blocks: If prerequisites not met

Phase 3: Synthesis → total_score, tier, kill_switch_verdict
  └─ Requires: Phase 0, 1a, 1b, 2 all complete

Phase 4: Reports → deal_sheets, visualizations
  └─ Requires: Phase 3 complete
```

**Key Detail:** Phase 2 spawn **MUST** call `validate_phase_prerequisites.py` before Task dispatch. Exit code 0 = can proceed; exit code 1 = blocked.

---
