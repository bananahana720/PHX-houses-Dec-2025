# SECTION 6: TOKEN EFFICIENCY ANALYSIS

### Instruction Density Ratios

| File | Type | Lines | Instruction Ratio | Comment |
|------|------|-------|-------------------|---------|
| `protocols.md` | CRITICAL | 425 | 100% operational | No narrativ fluff |
| `AGENT_BRIEFING.md` | REFERENCE | 100+ | 90% dense code examples | Minimal explanation |
| `scripts/CLAUDE.md` | INVENTORY | 280 | 85% table + list | Organized by category |
| `src/CLAUDE.md` | REFERENCE | 258 | 80% schema + code | Includes design patterns |
| `data/CLAUDE.md` | CRITICAL | 269 | 95% code patterns + errors | WRONG/CORRECT emphasis |
| `tests/CLAUDE.md` | INVENTORY | 430 | 75% examples + tables | Comprehensive fixtures |
| `docs/CLAUDE.md` | INDEX | 231 | 70% links + status | Meta-documentation |

**Pattern:** Critical/reference files prioritize **instruction density** over prose. Non-critical files use tables and lists instead of narrative paragraphs.

### Knowledge Graph Design

**toolkit.json (366 lines):**
- Tier definitions (6 tiers)
- Native tools (18 tools with replaces + best_practices)
- Project scripts (5 main + 50+ utility)
- Agents (3 with model + skills)
- Skills (18 with purpose + tool scope)
- Relationships (11 dependency mappings)
- Phase dependencies (6 phases with requirements)
- Common mistakes (10 with fixes)

**context-management.json (395 lines):**
- Discovery protocol (hooks for auto-creation)
- Staleness protocol (thresholds by directory)
- Update triggers (5 events with actions)
- State files (3 critical files, schemas)
- Agent handoff (required reading + context)
- Spawn validation protocol (Phase 2 specific)
- Failure response protocols (structured error handling)
- Reference format (syntax for citations)
- CLAUDE.md sections (required/recommended/optional)
- Directory contexts (purpose + staleness for each)
- Session checklist (on_start, on_directory_enter, etc.)
- Validation rules (required files/directories)
- File organization rules (placement matrix)

**Observation:** Knowledge graphs serve as **semantic index** - agents can quickly discover tools, patterns, and dependencies without reading raw code.

---
