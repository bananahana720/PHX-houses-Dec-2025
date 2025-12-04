# DIAGRAM 3: TOOL HIERARCHY (Bucket 4)

```
                    TOOL SELECTION PYRAMID

                        ┌─────────────┐
                        │   NATIVE    │
                        │  (Tier 1)   │
              ┌─────────┼─────────────┼─────────┐
              │         │             │         │
            Read      Write          Edit     Glob
              │         │             │         │
              └─────────┼─────────────┼─────────┘
                        │             │
                      Grep ◄──────────┘
                        │
                        ▼
              ┌─────────────────────────┐
              │  PROJECT SCRIPTS (T2)   │
              ├─────────────────────────┤
              │ phx_home_analyzer.py    │
              │ extract_county_data.py  │
              │ extract_images.py       │
              │ validate_prerequisites  │
              │ [50+ utility scripts]   │
              └──────────┬──────────────┘
                         │
                         ▼
              ┌─────────────────────────┐
              │  SKILLS (Tier 3)        │
              ├─────────────────────────┤
              │ property-data           │
              │ kill-switch             │
              │ scoring                 │
              │ [18 total]              │
              └──────────┬──────────────┘
                         │
                         ▼
              ┌─────────────────────────┐
              │  TASK SUBAGENTS (T4)    │
              ├─────────────────────────┤
              │ Complex exploration     │
              │ Multi-step analysis     │
              │ (expensive - avoid!)    │
              └──────────┬──────────────┘
                         │
                         ▼
              ┌─────────────────────────┐
              │  SLASH COMMANDS (T5)    │
              ├─────────────────────────┤
              │ /analyze-property       │
              │ /commit                 │
              └──────────┬──────────────┘
                         │
                         ▼
              ┌─────────────────────────┐
              │  MCP TOOLS (Tier 6)     │
              ├─────────────────────────┤
              │ playwright (Realtor.com)│
              │ fetch                   │
              │ (Zillow/Redfin: AVOID)  │
              └─────────────────────────┘

═════════════════════════════════════════════════════════════
KEY PRINCIPLE: Use highest tier available
COST DIFFERENCE: Bash(python:*) vs Task ≈ 10x
VIOLATION RATE: 0% in documented patterns
═════════════════════════════════════════════════════════════
```

---
