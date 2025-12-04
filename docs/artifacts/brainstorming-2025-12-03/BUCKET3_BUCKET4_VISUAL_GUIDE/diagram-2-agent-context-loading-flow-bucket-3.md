# DIAGRAM 2: AGENT CONTEXT LOADING FLOW (Bucket 3)

```
┌─────────────────────────────────────────────────────┐
│ AGENT SPAWNED                                       │
│ /analyze-property "123 Main St"                     │
└────────────────────┬────────────────────────────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ READ BRIEFING (5 sec)  │
        ├────────────────────────┤
        │ .claude/               │
        │ AGENT_BRIEFING.md      │
        │                        │
        │ ✓ Quick state commands │
        │ ✓ Data structures      │
        │ ✓ Common errors/fixes  │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ LOAD WORK_ITEMS (10s)  │
        ├────────────────────────┤
        │ data/                  │
        │ work_items.json        │
        │                        │
        │ ✓ Current phase        │
        │ ✓ Progress tracking    │
        │ ✓ Completed/blocked    │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ LOAD RELEVANT SKILLS   │
        ├────────────────────────┤
        │ .claude/skills/        │
        │ {name}/SKILL.md        │
        │                        │
        │ ✓ property-data        │
        │ ✓ kill-switch          │
        │ ✓ scoring              │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────┐
        │ READ PROTOCOLS (5 min) │
        ├────────────────────────┤
        │ .claude/protocols.md   │
        │                        │
        │ ✓ TIER 0: Mandatory    │
        │ ✓ TIER 1: Apply now    │
        │ ✓ TIER 1.5: Multi-agent│
        │ ✓ TIER 2: If context   │
        │ ✓ TIER 3: As needed    │
        └────────────┬───────────┘
                     │
                     ▼
        ┌────────────────────────────┐
        │ START EXECUTION            │
        ├────────────────────────────┤
        │ Use tool hierarchy:        │
        │ 1. Read/Write/Edit/Glob/   │
        │    Grep (native tools)     │
        │ 2. Bash(python:*) scripts  │
        │ 3. Skills for logic        │
        │ 4. Task subagents (rare)   │
        │ 5. MCP tools (fallback)    │
        └────────────────────────────┘

═════════════════════════════════════════════════════════════
CONTEXT COST: ~4300-5600 tokens per agent spawn
OVERLAP REDUCTION: Root docs cached, agents share briefing
═════════════════════════════════════════════════════════════
```

---
