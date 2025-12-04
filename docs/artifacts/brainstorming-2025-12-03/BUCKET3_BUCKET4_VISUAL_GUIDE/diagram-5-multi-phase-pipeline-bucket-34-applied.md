# DIAGRAM 5: MULTI-PHASE PIPELINE (Bucket 3/4 applied)

```
                   PROPERTY ANALYSIS PIPELINE

    ┌─────────────────────────────────────────────────────┐
    │ PHASE 0: County Data (Parallel, No Dependencies)    │
    ├─────────────────────────────────────────────────────┤
    │ Script: extract_county_data.py (Tier 2 Bash)        │
    │ Output: lot_sqft, year_built, garage_spaces         │
    │ Update: enrichment_data.json                        │
    │ Time: ~2min all properties                          │
    └────────────────────┬────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
  ┌────────────────┐          ┌────────────────┐
  │ PHASE 1a:      │          │ PHASE 1b:      │
  │ Listings       │          │ Maps           │
  │ (Parallel)     │          │ (Parallel)     │
  ├────────────────┤          ├────────────────┤
  │ Agent:         │          │ Agent:         │
  │ listing-browser│          │ map-analyzer   │
  │ (Haiku)        │          │ (Haiku)        │
  │                │          │                │
  │ Script:        │          │ No script,     │
  │ extract_images │          │ pure agent     │
  │                │          │                │
  │ Output:        │          │ Output:        │
  │ Images         │          │ Schools,       │
  │ Price, HOA     │          │ Safety,        │
  │                │          │ Orientation    │
  └────────┬───────┘          └────────┬───────┘
           │                           │
           └───────────────┬───────────┘
                           │
                           ▼
        ┌──────────────────────────────────┐
        │ VALIDATE PREREQUISITES (Axiom 4) │
        ├──────────────────────────────────┤
        │ Script: validate_prerequisites.py│
        │ Check: Phase 1 listing complete? │
        │ Check: Image folder exists?      │
        │ Exit 0 = Can spawn, 1 = Blocked  │
        └──────────────┬───────────────────┘
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
         Can Spawn?         BLOCKED
            │                  │
            ▼                  ▼
    ┌─────────────────┐   WARN USER
    │ PHASE 2:        │   DO NOT SPAWN
    │ Image Assess    │   Fix Phase 1
    │ (Sequential)    │
    ├─────────────────┤
    │ Agent:          │
    │ image-assessor  │
    │ (Sonnet 4.5)    │
    │                 │
    │ Skill:          │
    │ image-assessment│
    │                 │
    │ Output:         │
    │ Interior score  │
    │ Exterior score  │
    └────────┬────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ PHASE 3: Synthesis       │
    ├──────────────────────────┤
    │ Script: phx_home_analyzer│
    │ Calculate: Total score   │
    │ Determine: Tier          │
    │ Evaluate: Kill-switches  │
    │ Output: Ranked CSV       │
    └────────┬─────────────────┘
             │
             ▼
    ┌──────────────────────────┐
    │ PHASE 4: Reports         │
    ├──────────────────────────┤
    │ Scripts: deal_sheets/    │
    │          visualizations  │
    │ Output: HTML reports     │
    │ Output: Maps, charts     │
    └──────────────────────────┘

═════════════════════════════════════════════════════════════
KEY PATTERN: Validation gates (Axiom 4) prevent agent spam
SEQUENCE: 0,1a,1b parallel → validate → 2 → 3 → 4
TOOLS: Scripts (Tier 2) + Agents (Tier 4) + Skills (Tier 3)
═════════════════════════════════════════════════════════════
```

---
