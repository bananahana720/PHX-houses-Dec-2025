# SECTION 1: CLAUDE.md COVERAGE ANALYSIS

### Current State

| Directory | CLAUDE.md | Status | Staleness Threshold | Lines |
|-----------|-----------|--------|---------------------|-------|
| `.` (root) | ✓ | Current | N/A | ~120 |
| `.claude/` | ✓ | Current | 168h | ~100 |
| `scripts/` | ✓ | Current | 48h | ~280 |
| `src/phx_home_analysis/` | ✓ | Current | 72h | ~258 |
| `data/` | ✓ | Current | **12h** (CRITICAL) | ~269 |
| `tests/` | ✓ | Current | 72h | ~430 |
| `docs/` | ✓ | Current | 168h | ~231 |

**Coverage Score: 7/7 (100%)**

---

### BUCKET 3 PATTERN ANALYSIS: CLAUDE.md Structure

Each CLAUDE.md follows a **consistent token-efficient format**:

#### Root CLAUDE.md (`CLAUDE.md`)
**Purpose:** Project-wide orientation
**Contents:**
- Quick commands (bash examples)
- Kill-switch criteria table
- Arizona specifics
- Multi-agent pipeline phases
- State file references
- Environment variables

**Observation:** Deliberately **shallow** - points to more detailed docs elsewhere. Average reader loads this once per session.

#### `.claude/CLAUDE.md`
**Purpose:** Agent/skill navigation hub
**Contents:**
- Directory tree with annotations
- Skills system overview + usage examples
- Quick links to key files
- "Essential Files (Do Not Condense)" section

**Observation:** Acts as **skill discovery mechanism** - prevents agents from rediscovering available skills. Links to `AGENT_BRIEFING.md` and `protocols.md` as required reading.

#### `scripts/CLAUDE.md`
**Purpose:** Script inventory and execution patterns
**Contents:**
- Core pipeline scripts (5 main + descriptions)
- Visualization scripts (7 types)
- Quality & utility scripts (8)
- Reporting scripts (3)
- Data management scripts (7)
- Analysis & batch scripts (6+)
- CLI patterns and exit codes
- Common operations (full workflows)
- Dependencies (internal + external)

**Pattern Insight:** **Categorizes by purpose, not alphabetically.** Lists scripts agents might call via Bash(python:*), with usage examples and exit code semantics.

#### `src/phx_home_analysis/CLAUDE.md`
**Purpose:** Core library navigation
**Contents:**
- Package-level architecture (8 subdirectories)
- Services breakdown (15+ services with roles)
- Key files matrix (with line counts)
- Design patterns (Repository, Strategy, DDD, Orchestration)
- Scoring system (600pt breakdown)
- Kill-switch architecture (hard + soft criteria)
- Data flow pipeline
- Integration points (Used By / Uses)
- Key learnings (3 sections: Scoring, Kill-Switch, Arizona-Specific)

**Pattern Insight:** Combines **code reference with domain knowledge.** Scoring system breakdown is comprehensive enough that agents don't need to read the source file.

#### `data/CLAUDE.md`
**Purpose:** Critical state file documentation
**Contents:**
- WARNING header (12h staleness threshold)
- Critical state files table (enrichment_data.json, work_items.json, etc.)
- Structure definitions (JSON schemas)
- Access patterns (code examples for CORRECT/WRONG)
- Subdirectories (property_images/, archive/, raw_exports/)
- Data schemas (PropertyEnrichment v2.0.0, WorkItems v1)
- Access patterns with Python code
- Common errors and fixes

**Pattern Insight:** **Focuses on integrity and access patterns.** Includes explicit WRONG/CORRECT code to prevent common errors. Highest criticality (12h staleness).

#### `tests/CLAUDE.md`
**Purpose:** Test infrastructure and fixtures
**Contents:**
- Directory structure (unit, integration, services, benchmarks)
- Key files (conftest.py with 638 lines)
- Running tests (6 example patterns)
- Test categories (unit, integration, service, benchmark)
- Fixtures deep dive (property, enrichment, config fixtures)
- Kill-switch testing reference
- Scoring system testing
- Writing new tests (AAA pattern examples)

**Pattern Insight:** **Fixtures-centric documentation.** Describes available test data before test patterns. Kill-switch boundary testing explicitly documented (lot size: 6,999 vs 7,000).

#### `docs/CLAUDE.md`
**Purpose:** Documentation hub
**Contents:**
- Key documents table (AI_TECHNICAL_SPEC, CODE_REFERENCE, DATA_ENGINEERING_AUDIT)
- Architecture & specifications
- Configuration & setup (7 docs)
- Security documentation (5 docs)
- Testing & quality (8 docs)
- API & integration (5 docs)
- Cleanup & maintenance (5 docs)
- Subdirectories (architecture/, specs/, artifacts/, templates/, risk_checklists/)

**Pattern Insight:** **Meta-documentation** - serves as index to 40+ documents. Includes status column (Current/Complete/Reference) to signal which docs are authoritative vs historical.

---

### HOOK-DRIVEN STUB PATTERN

**Implementation:** Auto-creation via excluded directories list

```json
// .claude/knowledge/context-management.json
"excluded_directories": [
  "node_modules", ".git", "__pycache__", ".venv", "venv",
  ".pytest_cache", ".mypy_cache", ".ruff_cache",
  "data/property_images/processed"
]
```

**Observation:** Hooks are defined but **not yet implemented as live hooks**. When entering a directory without CLAUDE.md:
- Currently: Manual creation with UPDATE_ME flag
- Intended: Auto-create placeholder + flag for review

**Gap:** No `.claude/templates/CLAUDE.md.template` found in current codebase. This would be next iteration.

---
