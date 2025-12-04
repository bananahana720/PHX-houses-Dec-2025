# SECTION 4: SKILL SYSTEM MATURITY ANALYSIS

### Skills Inventory

**18 Skills Organized by Category:**

#### Data Management (2)
1. **property-data** - Load/query/update enrichment_data.json
   - Allowed tools: Read, Write, Bash(python:*), Grep
   - Use when: Any property data access pattern

2. **state-management** - Checkpointing & crash recovery
   - Critical for multi-phase workflows
   - Manages work_items.json state

#### Filtering & Validation (2)
3. **kill-switch** - Buyer criteria validation
   - Hard criteria (HOA, beds, baths)
   - Soft criteria with severity accumulation

4. **quality-metrics** - Data quality tracking
   - Lineage, completeness, accuracy scoring
   - Automated gates

#### Scoring & Economics (2)
5. **scoring** - 600-point weighted system
   - Location (230), Systems (180), Interior (190)
   - Tier classification (Unicorn/Contender/Pass)

6. **cost-efficiency** - Monthly cost projection
   - Mortgage, taxes, insurance, HOA, pool, solar lease

#### Data Extraction (4)
7. **county-assessor** - Maricopa County API
   - lot_sqft, year_built, garage_spaces

8. **listing-extraction** - Browser automation (stealth)
   - Zillow, Redfin via nodriver + curl_cffi

9. **map-analysis** - Geographic data
   - Schools, safety, orientation, distances

10. **image-assessment** - Visual scoring (Section C)
    - Interior + exterior scoring from photos

#### Domain Knowledge (3)
11. **arizona-context** - Full AZ context (solar, pool, HVAC)

12. **arizona-context-lite** - Image-only context (pool/HVAC age)

13. **inspection-standards** - Property inspection rubrics

#### Output Generation (3)
14. **deal-sheets** - Report generation
    - HTML deal sheets with scores + recommendations

15. **visualizations** - Charts & plots
    - Radar charts, value spotter, maps

16. **exterior-assessment** - Building exterior scoring
    - Roof, siding, condition assessment

#### Utilities (2)
17. **file-organization** - File placement standards
    - Protocol 9 enforcement

18. **_shared** - Shared tables & constants
    - Scoring tables, kill-switch references

### Skill Frontmatter Pattern

**Standardized Format:**
```yaml
---
name: property-data
description: Load, query, update, and validate property data...
allowed-tools: Read, Write, Bash(python:*), Grep
---
```

**Observation:** Each skill declares:
- **name:** Human-readable identifier
- **description:** When to use (1-2 sentences)
- **allowed-tools:** Tier 1 tools + specific Bash scopes

**Tool Scoping:** `Bash(python:*)` notation restricts Bash to Python scripts only - prevents unconstrained shell access.

### Skill Dependencies

**Skill Loading Chain:**
```
Agent spawned
  ↓
skills: property-data, state-management, kill-switch (from agent frontmatter)
  ↓
Load skill files from .claude/skills/{name}/SKILL.md
  ↓
Skill has allowed-tools restrictions
  ↓
Execute within tool constraints
```

**Observation:** Skills provide **domain expertise without expanding tool access.** kill-switch skill teaches evaluation logic without adding new tools.

---
