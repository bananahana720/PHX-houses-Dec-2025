# SECTION 8: RECOMMENDATIONS

### Priority 1: Enforce Current Patterns (Week 1)

**Objective:** Prevent regression and ensure consistency

1. **Add CI/CD checks** for CLAUDE.md coverage
   - Fail build if any directory missing CLAUDE.md
   - Validate frontmatter structure (name, purpose, contents)

2. **Add tool hierarchy linter** to pre-commit hooks
   - Reject bash cat/grep/find/ls in agent files
   - Allow only blessed tool + script patterns

3. **Implement staleness checks** in analyze-property orchestrator
   - Before spawning any Phase 2 agent, verify enrichment_data.json < 12h old
   - Warn user if work_items.json is stale

### Priority 2: Improve Developer Experience (Week 2-3)

**Objective:** Make patterns easier to follow

4. **Create CLAUDE.md templates** for each major directory type
   - Template for: scripts/, src/subsystems/, services/
   - Include standard sections, example content

5. **Build skill discovery CLI**
   - `python scripts/list_skills.py` → shows all 18 skills
   - `python scripts/show_skill.py SKILL_NAME` → detailed help

6. **Document hook implementation roadmap**
   - Timeline for auto-creation on directory enter
   - Dependencies (requires Python 3.11+, filesystem watching)

### Priority 3: Scale the Architecture (Month 2)

**Objective:** Support larger projects

7. **Implement context caching layer**
   - Cache parsed CLAUDE.md files
   - Invalidate on filesystem change
   - Saves repeated file reads

8. **Add context versioning**
   - Tag CLAUDE.md changes with git commit
   - Agents can reference "context as of commit X"
   - Enables reproducible runs

9. **Create context diff reports**
   - Show what changed in CLAUDE.md files since last run
   - Help agents understand recent architectural decisions

---
