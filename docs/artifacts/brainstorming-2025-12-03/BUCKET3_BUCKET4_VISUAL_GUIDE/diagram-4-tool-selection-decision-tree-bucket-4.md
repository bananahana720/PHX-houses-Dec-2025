# DIAGRAM 4: TOOL SELECTION DECISION TREE (Bucket 4)

```
                    WHAT TOOL DO I USE?

                           START
                            │
                            ▼
                   File operation?
                    /          \
                  YES           NO
                  │              │
        ┌─────────┼─────────┐    │
        │         │         │    │
       READ    WRITE      EDIT   │
       (Read)  (Write)  (Edit)   │
                                 ▼
                      Search operation?
                        /          \
                      YES          NO
                      │             │
                 ┌─────┴─────┐      │
                 │           │      │
              Files      Content    │
              (Glob)     (Grep)     │
                                    ▼
                     Script/command?
                      /           \
                    YES            NO
                    │              │
                 BASH tool         │
              (python:*)           │
                                   ▼
                      Data operations?
                      /            \
                    YES             NO
                    │               │
                  SKILL            │
                (domain           │
                 logic)           │
                                   ▼
                    Complex work?
                     /          \
                   YES          NO
                   │            │
                  TASK       MCP Tools
              (subagent)    (fallback)

═════════════════════════════════════════════════════════════
DECISION POINT: "What's the minimum tier needed?"
RULE: Always choose highest (most restricted) tier available
═════════════════════════════════════════════════════════════
```

---
