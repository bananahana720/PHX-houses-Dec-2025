# SECTION 2: CONTEXT MANAGEMENT PATTERNS

### Staleness Protocol Implementation

**Thresholds by Directory:**

| Directory | Critical? | Threshold | Trigger | Action |
|-----------|-----------|-----------|---------|--------|
| `data/` | **YES** | 12h | Session start, agent spawn | WARN_USER |
| `.claude/` | No | 168h | Before agent spawn | flag_for_review |
| `scripts/` | No | 48h | Before script execution | flag_for_review |
| `src/` | No | 72h | Before import | flag_for_review |
| `tests/` | No | 72h | Before test run | flag_for_review |
| `docs/` | No | 168h | Before documentation reference | flag_for_review |

**Implementation Status:** **Documented in context-management.json but not enforced in code.** Manual checks required before each agent spawn.

### State Files Management

**Critical State Files (12h staleness):**

1. **enrichment_data.json** - Master property data store (LIST of dicts)
   - Updated by: Phase 0 (county), Phase 1 (listing), Phase 1 (map), Phase 2 (images), Phase 3 (synthesis)
   - Accessed by: All scripts, all agents
   - **Common Error:** Treating as dict instead of list
   - **Fix Pattern:** Atomic write (tempfile + os.replace)

2. **work_items.json** - Pipeline progress tracking
   - Updated by: Orchestrator only
   - Accessed by: All agents (read-only)
   - **Common Error:** Race conditions (multiple writers)
   - **Fix Pattern:** Single orchestrator pattern

3. **address_folder_lookup.json** - Address → image folder mapping
   - Updated by: Phase 1 image extraction
   - Accessed by: Phase 2 image assessment
   - **Common Error:** Orphan entries (root level non-mappings)
   - **Fix Pattern:** Always use `lookup["mappings"][address]`

### Agent Handoff Protocol

**Required Reading Flow:**
```
Agent Spawn
  ↓
Read: .claude/AGENT_BRIEFING.md (5-sec state orientation)
  ↓
Load: data/work_items.json (get current phase + context)
  ↓
Load: data/enrichment_data.json (property data)
  ↓
Load: Relevant skill files (domain knowledge)
  ↓
Execute Phase
```

**AGENT_BRIEFING.md Content:**
- Quick state check commands (one-liners)
- Data structure reference (enrichment_data is LIST, work_items is dict, etc.)
- Common errors and fixes
- Key file locations with access patterns

**Observation:** Briefing provides **semantic shortcuts** - agents don't need to reverse-engineer data structures from reading JSON. Includes explicit WRONG/CORRECT code patterns.

### Update Triggers (Implemented)

| Event | Action | File Updated | Priority |
|-------|--------|--------------|----------|
| Agent completes work | Update pending_tasks, add key_learnings | CLAUDE.md | HIGH |
| Error discovered | Add to key_learnings section | CLAUDE.md | HIGH |
| New files created | Update contents_section | CLAUDE.md | MEDIUM |
| Session wrapping up | Update pending_tasks | CLAUDE.md | MEDIUM |
| UPDATE_ME flag detected | Prompt user to update | CLAUDE.md | HIGH |

**Status:** Triggers are **documented in context-management.json** but require manual adherence. No automated enforcement (yet).

---
