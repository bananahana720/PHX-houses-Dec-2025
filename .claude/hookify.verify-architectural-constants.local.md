---
name: verify-architectural-constants
enabled: true
event: file
conditions:
  - field: new_text
    operator: regex_match
    pattern: (605\s*(pts|points)|8\s*HARD|7\s*HARD|kill[- ]?switch|UNICORN|CONTENDER|scoring\s*(system|weight)|tier\s*(threshold|classification))
---

⚠️ **Architectural Constant Referenced - Verify Against Canonical Source!**

You're writing content that references PHX Houses architectural constants.

**🛑 STOP and VERIFY against root CLAUDE.md:**

| Constant | Canonical Value | Source |
|----------|-----------------|--------|
| Kill-Switches | **5 HARD + 4 SOFT** (not 8 HARD!) | `CLAUDE.md:Kill-Switches` |
| Scoring Max | **605 pts** | `CLAUDE.md:Scoring` |
| Tiers | Unicorn >480, Contender 360-480, Pass <360 | `CLAUDE.md:Scoring` |

**Why this matters:**
- Brownfield project = docs drift from truth
- Derived docs (retros, specs) may have stale values
- Root CLAUDE.md is the **single source of truth**

**Before proceeding:**
1. Read the relevant section of root `CLAUDE.md`
2. Include `file:line` citation for any architectural constants
3. If inconsistency found → flag it, don't propagate it

**Canonical sources (in priority order):**
1. `CLAUDE.md` (project root)
2. `src/` implementation code
3. `config/*.yaml` configuration files
4. ❌ NOT: retros, specs, sprint artifacts (these are derived)
