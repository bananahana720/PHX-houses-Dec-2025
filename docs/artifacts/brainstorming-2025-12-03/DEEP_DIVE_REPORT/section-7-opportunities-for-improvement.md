# SECTION 7: OPPORTUNITIES FOR IMPROVEMENT

### QUICK WINS (Minimal Effort)

#### 1. **Auto-create CLAUDE.md Hook**
**Status:** Designed but not implemented
**Effort:** Low (Python script to check on directory enter)

```python
# Pseudo-code
def ensure_claude_md(directory):
    claude_path = os.path.join(directory, "CLAUDE.md")
    if not os.path.exists(claude_path):
        with open(".claude/templates/CLAUDE.md.template") as f:
            template = f.read()
        with open(claude_path, "w") as f:
            f.write(template.replace("UPDATE_ME", f"Created: {date}"))
        return True
    return False
```

**Benefit:** Enforces Bucket 3 pattern across all directories automatically.

#### 2. **Staleness Check Before Agent Spawn**
**Status:** Documented protocol, not enforced
**Effort:** Low (shell script wrapper)

```bash
#!/bin/bash
# Pre-spawn validation
python scripts/validate_freshness.py
if [ $? -ne 0 ]; then
  echo "WARNING: State files are stale (>12h). Update before proceeding."
  exit 1
fi
```

**Benefit:** Prevents agents from working with outdated data.

#### 3. **Tool Violation Linter**
**Status:** Not implemented
**Effort:** Low (grep/regex checker)

```bash
# Check for tool violations in agent files
grep -r 'bash cat\|bash grep\|bash find\|bash ls' .claude/agents/
# Should return: 0 files (success)
```

**Benefit:** Catches tool hierarchy violations in CI/CD.

### MEDIUM EFFORT IMPROVEMENTS

#### 4. **Automated CLAUDE.md Updater**
**Status:** Manual process currently
**Effort:** Medium

Create post-agent-completion hook:
- Read work_items.json for completed phases
- Extract key_learnings from agent responses
- Update relevant CLAUDE.md files
- Mark UPDATE_ME sections as reviewed

**Benefit:** Context stays fresh without manual intervention.

#### 5. **Skill Discovery CLI**
**Status:** Manual skill loading
**Effort:** Medium

```bash
# Query available skills
python scripts/list_skills.py --category extraction
python scripts/list_skills.py --tool Bash

# Show skill details
python scripts/show_skill.py property-data
```

**Benefit:** Agents discover skills programmatically instead of reading documentation.

#### 6. **State File Versioning**
**Status:** Single version currently
**Effort:** Medium

Implement versioning for enrichment_data.json:
- Current: enrichment_data.json (v2.0.0)
- Historical: enrichment_data_v1.5.0.json (archived)
- Migration: Schema upgrade script

**Benefit:** Backward compatibility for agents expecting older structures.

### STRATEGIC IMPROVEMENTS

#### 7. **Middleware for Orchestration Axioms**
**Status:** Axioms documented but not enforced
**Effort:** High

Create enforcement layer:
- Axiom 1: Validate script preconditions
- Axiom 3: Reject Tier 4 agents for simple lookups
- Axiom 4: Check completeness gates before spawn
- Axiom 7: Enforce single writer pattern
- Axiom 9: Pattern-match failures for fail-fast

**Benefit:** Prevents expensive multi-agent mistakes automatically.

#### 8. **Context Compression for Large Projects**
**Status:** Full docs loaded each time
**Effort:** High

Implement progressive context loading:
- Agent gets 2KB summary (name, purpose, key files)
- Agent requests specific skills (loads 1-2KB each)
- Agent accesses full docs on-demand (Read tool)

**Benefit:** Saves tokens for very large projects (100+ agents).

---
