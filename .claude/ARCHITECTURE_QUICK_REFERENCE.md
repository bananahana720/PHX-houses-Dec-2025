# Claude/AI Architecture Quick Reference
**For:** Developers, Agents, Orchestrators
**Updated:** December 3, 2025
**Read Time:** 2-5 minutes

---

## WHAT IS THIS PROJECT'S ARCHITECTURE?

**Bucket 3 (Claude Architecture):** Directory-scoped context via CLAUDE.md files
**Bucket 4 (Tool Hierarchy):** Strict 6-tier tool selection (Tier 1 native tools → Tier 6 MCP)

---

## QUICK FACTS

| Fact | Value |
|------|-------|
| Directories with CLAUDE.md | 7/7 (100% coverage) |
| Skills available | 18 (property-data, scoring, kill-switch, etc.) |
| Agents designed | 3 (listing-browser, map-analyzer, image-assessor) |
| Protocol tiers | 4 (TIER 0 non-negotiable → TIER 3 standard) |
| Tool violation rate | 0% (zero bash cat/grep/find violations in docs) |
| Orchestration axioms | 10 (documented but partially enforced) |

---

## WHEN YOU SPAWN AN AGENT

**DO THIS (in order):**

1. **Read AGENT_BRIEFING.md** (mandatory, 5 seconds)
   - Quick state check commands
   - Data structure reference (enrichment_data.json is a LIST)
   - Common errors and fixes

2. **Read work_items.json** (mandatory, 10 seconds)
   - Check current phase
   - See what's completed vs in-progress
   - Get context about property being analyzed

3. **Load relevant skills** (conditional)
   - If extracting listings → load listing-extraction
   - If scoring properties → load scoring
   - If validating buyer criteria → load kill-switch

4. **Read protocols.md** (if you'll be making decisions)
   - TIER 0: Never violate these (git safety, no deviation, tool usage)
   - TIER 1: Apply these during work (root cause, scope completeness, verification)
   - TIER 1.5: Apply for multi-agent (10 axioms)

5. **Call project scripts via Bash(python:*)** (Tier 2)
   - Never implement logic already in scripts/
   - Example: `python scripts/phx_home_analyzer.py`

---

## WHAT TOOL DO I USE?

**Decision Tree:**

```
Is this a file operation?
├─ Reading file? → Use Read tool
├─ Writing new file? → Use Write tool
├─ Modifying existing? → Use Edit tool (exact string replacement)
└─ Not a file? → Continue

Is this a search operation?
├─ Finding files by pattern? → Use Glob tool
├─ Searching file contents? → Use Grep tool
└─ Neither? → Continue

Is this a script or system command?
├─ git, npm, docker, python? → Use Bash
├─ (with restrictions: Bash(python:*) = python only)
└─ Neither? → Continue

Is this data analysis or complex work?
├─ Can be done with existing scripts? → Use Bash(python:*)
├─ Requires exploration/iteration? → Use Skill or Task subagent
└─ Neither? → Use MCP tools (low priority)
```

**DON'T DO THIS:**
- ❌ `bash cat file.json` → Use **Read tool**
- ❌ `bash grep pattern file` → Use **Grep tool**
- ❌ `bash find . -name "*.py"` → Use **Glob tool**
- ❌ `bash sed 's/old/new/g'` → Use **Edit tool**
- ❌ `bash ls -la /dir/` → Use **Glob tool**

---

## DATA STRUCTURES YOU'LL ENCOUNTER

### enrichment_data.json (LIST ← Important!)
```python
# CORRECT: It's a list
data = json.load(file)  # Returns list of dicts
prop = next((p for p in data if p["full_address"] == addr), None)

# WRONG: It's NOT a dict keyed by address
prop = data[addr]  # TypeError: list indices must be integers
prop = data.get(addr)  # AttributeError: 'list' object has no attribute 'get'
```

### work_items.json (Dict)
```python
# CORRECT: Dict with work_items list inside
data = json.load(file)  # Returns dict
work_items = data["work_items"]  # List of items
item = next((w for w in work_items if w["address"] == addr), None)
```

### address_folder_lookup.json (Dict with mappings key)
```python
# CORRECT
lookup = json.load(file)
mapping = lookup["mappings"][address]
folder = mapping["folder"]

# WRONG: Don't access root directly
mapping = lookup.get(address)  # May be wrong
```

---

## BEFORE SPAWNING PHASE 2 IMAGE ASSESSOR

**MANDATORY:**

```bash
# Validate prerequisites
python scripts/validate_phase_prerequisites.py \
  --address "123 Main St" \
  --phase phase2_images \
  --json
```

**Parse output:**
- `can_spawn: true` → OK to spawn agent
- `can_spawn: false` → DO NOT SPAWN, check `reason` field
- Exit code 0 → success
- Exit code 1 → error, handle accordingly

**If blocked:**
```
"reason": "Image folder not found",
"remediation": ["Run Phase 1 listing extraction", "Run extract_images.py"]
```

---

## SKILLS QUICK LOOKUP

| Skill | When to Use | Allowed Tools |
|-------|------------|---------------|
| **property-data** | Load/query/update enrichment_data.json | Read, Write, Bash(python:*), Grep |
| **state-management** | Track progress across phases | Bash(python:*) |
| **kill-switch** | Evaluate buyer criteria (HOA, beds, baths) | None (pure logic) |
| **scoring** | Calculate 600-point score | None (pure logic) |
| **county-assessor** | Extract lot_sqft, year_built | Bash(python:*), WebSearch |
| **listing-extraction** | Extract images from Zillow/Redfin | Bash(python:*) |
| **map-analysis** | Get schools, safety, orientation | Bash(python:*), WebSearch, Playwright |
| **image-assessment** | Score interior/exterior from photos | Read (images), Bash(python:*) |
| **arizona-context** | AZ-specific factors (pool, solar, HVAC) | None (pure domain knowledge) |
| **cost-efficiency** | Calculate monthly ownership cost | Bash(python:*) |

---

## THE 10 ORCHESTRATION AXIOMS

**When coordinating multi-agent work, follow these:**

1. **Dependency Verification** - Test script preconditions before spawning agents
2. **Output Constraints** - Specify format + length limits in subagent prompts
3. **Right-Sized Tools** - Use Grep for lookups; reserve agents for exploration (10x cost difference)
4. **Completeness Gates** - Check data availability before spawning dependent agents
5. **External State Respect** - Accept externally-modified state as authoritative
6. **Attempt Over Assume** - Try MCP calls; don't assume they're blocked
7. **Single Writer** - Only orchestrator modifies shared state (enrichment_data.json, work_items.json)
8. **Atomic State** - Use atomic writes (tempfile + os.replace) for concurrent access
9. **Fail Fast** - Pattern-match failures; propagate to skip redundant attempts
10. **Reuse Logic** - Call existing scripts; don't reimplement logic

---

## COMMON PATTERNS

### Load Property Data
```python
from pathlib import Path
import json

# Load enrichment data (list)
with open("data/enrichment_data.json") as f:
    properties = json.load(f)  # LIST

# Find specific property
target_addr = "123 Main St, Phoenix, AZ 85001"
prop = next((p for p in properties if p["full_address"] == target_addr), None)

# Access field
if prop:
    lot_size = prop.get("lot_sqft")  # May be None
    hoa = prop.get("hoa_fee", 0)    # Default 0
```

### Update Property (Atomic Write)
```python
import json, os, tempfile

# Load
with open("data/enrichment_data.json") as f:
    properties = json.load(f)

# Modify
idx = next((i for i, p in enumerate(properties) if p["full_address"] == addr), -1)
if idx >= 0:
    properties[idx]["new_field"] = value

# Atomic write
fd, temp = tempfile.mkstemp(dir="data", prefix="enrichment_", suffix=".tmp")
try:
    with os.fdopen(fd, 'w') as f:
        json.dump(properties, f, indent=2)
    os.replace(temp, "data/enrichment_data.json")
except:
    os.unlink(temp)
    raise
```

### Validate Phase Prerequisites
```bash
# Before spawning Phase 2 agent
STATUS=$(python scripts/validate_phase_prerequisites.py \
  --address "$ADDRESS" \
  --phase phase2_images \
  --json)

CAN_SPAWN=$(echo "$STATUS" | jq -r '.can_spawn')
if [ "$CAN_SPAWN" = "true" ]; then
  # Safe to spawn image-assessor agent
else
  # Extract error reason and handle
  REASON=$(echo "$STATUS" | jq -r '.reason')
  echo "Blocked: $REASON"
fi
```

---

## DIRECTORY STALENESS THRESHOLDS

| Directory | Threshold | Action |
|-----------|-----------|--------|
| `data/` | **12h** CRITICAL | WARN before agent spawn |
| `scripts/` | 48h | Flag for review |
| `src/` | 72h | Flag for review |
| `tests/` | 72h | Flag for review |
| `.claude/` | 168h | Flag for review |
| `docs/` | 168h | Flag for review |

**Before spawning Phase 2 agents:** Verify enrichment_data.json and work_items.json are < 12h old.

---

## THE 5 TIER 0 PROTOCOLS

**NEVER violate these:**

1. **Git Safety** - Never use `git commit --no-verify` or skip pre-commit hooks
2. **No Deviation** - Never switch technologies when encountering issues; fix the actual problem
3. **Tool Usage** - Never use bash for file ops; use Read/Write/Edit/Glob/Grep
4. **Root Cause Analysis** - Never fix symptoms; trace to root cause and fix all instances
5. **Scope Completeness** - Never assume first search found everything; verify count

---

## DEBUGGING CHECKLIST

**If enrichment_data.json breaks:**
1. Verify JSON syntax: `python -m json.tool data/enrichment_data.json`
2. Check recent updates: `git log -p data/enrichment_data.json | head -50`
3. Repair with reconciliation: `python scripts/validate_phase_prerequisites.py --reconcile --repair`

**If agent fails:**
1. Check work_items.json for previous errors
2. Review agent's phase prerequisites
3. Read AGENT_BRIEFING.md data structure reference
4. Check console output for specific error message

**If tool selection is unclear:**
1. Refer to decision tree at top of this document
2. When in doubt: Read tool (for files), Grep tool (for search)
3. Use Bash(python:*) only for project scripts

---

## RECOMMENDED READING ORDER

1. **First time ever:** This document + AGENT_BRIEFING.md (10 min)
2. **Before spawning agents:** protocols.md TIER 0-1 sections (5 min)
3. **Working with data:** data/CLAUDE.md (10 min)
4. **Implementing features:** src/phx_home_analysis/CLAUDE.md (15 min)
5. **Debugging:** AGENT_BRIEFING.md "Common Errors and Fixes" (5 min)

---

## ONE-LINE REFERENCE

- **What's my current state?** → `python -c "import json; w=json.load(open('data/work_items.json')); print(f\"Phase: {w['session']['current_phase']}, Progress: {w['summary']['completed']}/{w['session']['total_items']}\")"`
- **Is Phase 2 ready?** → `python scripts/validate_phase_prerequisites.py --address "ADDRESS" --phase phase2_images --json | jq '.can_spawn'`
- **List all incomplete?** → `jq '.work_items[] | select(.status != "complete") | .address' data/work_items.json`
- **Find property by address?** → `jq '.[] | select(.full_address | contains("SUBSTRING"))' data/enrichment_data.json`
- **Show recent commits?** → `git log --oneline -10`

---

**Print this page. Tape it to your monitor. Refer often.**
