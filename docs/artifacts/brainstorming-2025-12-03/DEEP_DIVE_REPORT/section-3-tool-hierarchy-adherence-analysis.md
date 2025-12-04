# SECTION 3: TOOL HIERARCHY ADHERENCE ANALYSIS

### Tool Tier System (Documented)

**From toolkit.json:**

```
Tier 1: Claude Native Tools (HIGHEST PRIORITY)
  ├─ Read (replaces: bash cat, head, tail)
  ├─ Write (replaces: bash echo >, cat <<EOF)
  ├─ Edit (replaces: bash sed, awk)
  ├─ Glob (replaces: bash find, ls -R)
  ├─ Grep (replaces: bash grep, rg)
  ├─ Bash (for git, npm, docker, builds)
  └─ TodoWrite (multi-step task tracking)

Tier 2: Project Scripts (HIGH PRIORITY)
  ├─ phx_home_analyzer.py
  ├─ extract_county_data.py
  ├─ extract_images.py
  ├─ validate_phase_prerequisites.py
  └─ [50+ analysis/reporting/utility scripts]

Tier 3: Agent Skills (MEDIUM PRIORITY)
  ├─ property-data
  ├─ state-management
  ├─ kill-switch
  ├─ scoring
  └─ [13+ domain skills]

Tier 4: Task-Based Subagents (MEDIUM PRIORITY)
  └─ For complex exploration work

Tier 5: Slash Commands (LOW PRIORITY)
  └─ /analyze-property, /commit

Tier 6: MCP Tools (LOWEST PRIORITY)
  ├─ playwright (Realtor.com only, NOT Zillow/Redfin)
  └─ fetch
```

### Actual Adherence Scan

**Tool Usage in Agent Files:**

#### listing-browser.md (Zillow/Redfin extraction)
```
CORRECT PATTERNS FOUND:
✓ "Use the **Read** tool" (explicit, repeated)
✓ "Use the **Glob** tool" (explicit for metadata checks)
✓ "Use the **Grep** tool for searching"

INHERITED RULES SECTION:
"These rules from CLAUDE.md apply regardless of examples below:
- Use `Read` tool for files (NOT `bash cat`)
- Use `Glob` tool for listing (NOT `bash ls`)
- Use `Grep` tool for searching (NOT `bash grep`)"
```

**Assessment:** Agent file **explicitly teaches** tool usage. Headers reinforce protocols.

#### analyze-property.md (Multi-agent orchestrator)
```
CORRECT PATTERNS FOUND:
✓ "Use the **Read** tool to load work_items.json"
✓ "Use the **Glob** tool for listing metadata"
✓ Skill invocation: /Skill property-data

BASH USAGE:
  python scripts/phx_home_analyzer.py (Tier 2 project script)
  python scripts/extract_county_data.py --all (Tier 2 project script)
  python scripts/extract_images.py --all (Tier 2 project script)
```

**Assessment:** Correctly uses Tier 2 project scripts. No inappropriate bash.

#### scripts/ execution patterns
```
TOOL HIERARCHY OBSERVED:
1. Load data with Read (enrichment_data.json, work_items.json)
2. List images/files with Glob (property_images/metadata/)
3. Search content with Grep (log files, extracted fields)
4. Execute scripts with Bash(python:*) (CLI tool invocation)
```

**Assessment:** Follows hierarchical pattern consistently.

### Tool Violations Scan (Using Grep)

Let me check for common violations:
- No `bash cat FILE` patterns found in agent files
- No `bash grep PATTERN` in documented examples
- No `bash find` in recent agent code
- No `bash ls` in critical paths

**Assessment:** **Zero violations in critical agent/skill documentation.** Project demonstrates strong tool discipline.

---
