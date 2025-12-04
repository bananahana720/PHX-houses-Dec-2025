# DIAGRAM 8: SKILL INHERITANCE & DEPENDENCIES

```
                  SKILL LOADING CHAIN

        Agent Spawned (e.g., image-assessor)
                    │
                    ▼
        Load from frontmatter:
        skills: property-data, state-management,
                image-assessment, arizona-context-lite, scoring
                    │
    ┌───────────────┼───────────────┬──────────────────┬───┐
    │               │               │                  │   │
    ▼               ▼               ▼                  ▼   ▼
property-data  state-mgmt    image-assessment  arizona-context-lite scoring
    │               │               │                  │
    │ Loads:        │ Loads:        │ Loads:           │ Loads:
    │ • CSV         │ • work_items  │ • Interior       │ • Pool age
    │ • JSON        │ • Phase status│   scoring        │ • HVAC age
    │ • Validation  │ • Checkpoints │ • Exterior       │ • Solar info
    │               │               │   scoring        │ • Orientation
    │               │               │ • Photo analysis │   context
    │               │               │                  │
    │ Uses tools:   │ Uses tools:   │ Uses tools:      │ Uses tools:
    │ Read, Grep    │ Bash(python)  │ Read (images)    │ None (pure
    │               │               │ Bash(python)     │  logic)
    │               │               │                  │
    └───────────────┴───────────────┴──────────────────┴───┘
                            │
                            ▼
                    Agent has all capabilities
                    Can query data, manage state,
                    assess images, and score


SKILL DISCOVERY: .claude/skills/{name}/SKILL.md
TOOL SCOPING: Each skill declares allowed-tools
COMBINATION: Skills are composable (no conflicts)

═════════════════════════════════════════════════════════════
BENEFIT: Domain knowledge + tool access without tool bloat
═════════════════════════════════════════════════════════════
```

---
