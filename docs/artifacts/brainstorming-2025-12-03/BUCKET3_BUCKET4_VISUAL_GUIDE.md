# Bucket 3 & 4 Visual Architecture Guide

**Purpose:** Visualize Claude/AI Architecture and Tool Hierarchy patterns
**Format:** ASCII diagrams + flow charts
**Level:** Reference/Teaching

---

## DIAGRAM 1: CLAUDE.MD COVERAGE (Bucket 3)

```
PHX-Houses-Dec-2025/
│
├─ CLAUDE.md ◄──────────── ROOT CONTEXT
│                           Purpose: Project overview + quick commands
│                           Lines: ~120
│                           Focus: Shallow entry point
│
├── .claude/
│   ├─ CLAUDE.md ◄──────── AGENT/SKILL HUB
│   │                       Purpose: Skill discovery + file navigation
│   │                       Lines: ~100
│   │                       Focus: Index to agents + skills
│   │
│   ├─ AGENT_BRIEFING.md ◄─ AGENT CONTEXT (mandatory reading)
│   │                       Quick state check + data structures
│   │                       5-second orientation
│   │
│   ├─ protocols.md ◄────── OPERATIONAL RULES
│   │                       TIER 0-3 protocols
│   │                       425 lines of do's/don'ts
│   │
│   ├─ knowledge/
│   │   ├─ toolkit.json ───── SEMANTIC INDEX (366 lines)
│   │   │                      Tools, Scripts, Skills, Relationships
│   │   │
│   │   └─ context-management.json (395 lines)
│   │                           State files, Staleness, Triggers
│   │
│   └─ agents/
│       ├─ listing-browser.md (Haiku)
│       ├─ map-analyzer.md (Haiku)
│       └─ image-assessor.md (Sonnet)
│
├── scripts/CLAUDE.md ◄──────── SCRIPT INVENTORY
│                               Purpose: Script catalog + usage patterns
│                               Lines: ~280
│                               Categories: 8 (core, viz, quality, etc.)
│
├── src/phx_home_analysis/CLAUDE.md ◄─── LIBRARY REFERENCE
│                                        Purpose: Domain models + services
│                                        Lines: ~258
│                                        Focus: Implementation architecture
│
├── data/CLAUDE.md ◄──────────── STATE FILE REFERENCE
│                                Purpose: Critical data structures
│                                Lines: ~269
│                                Staleness: 12h (CRITICAL)
│                                Focus: Access patterns + error fixes
│
├── tests/CLAUDE.md ◄──────────── TEST INFRASTRUCTURE
│                                 Purpose: Fixtures + test patterns
│                                 Lines: ~430
│                                 Focus: Comprehensive fixture documentation
│
└── docs/CLAUDE.md ◄──────────── DOCUMENTATION INDEX
                                 Purpose: Meta-documentation hub
                                 Lines: ~231
                                 Status: Links to 40+ documents

═══════════════════════════════════════════════════════════════
COVERAGE: 7/7 (100%)
STALENESS: 3 levels (12h critical, 48-72h normal, 168h reference)
═══════════════════════════════════════════════════════════════
```

---

## DIAGRAM 2: AGENT CONTEXT LOADING FLOW (Bucket 3)

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

## DIAGRAM 3: TOOL HIERARCHY (Bucket 4)

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

## DIAGRAM 4: TOOL SELECTION DECISION TREE (Bucket 4)

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

## DIAGRAM 5: MULTI-PHASE PIPELINE (Bucket 3/4 applied)

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

## DIAGRAM 6: KNOWLEDGE GRAPH STRUCTURE (Bucket 3)

```
                   KNOWLEDGE GRAPHS

            ┌─────────────────────────────┐
            │  toolkit.json (366 lines)   │
            │  Semantic index of tools    │
            ├─────────────────────────────┤
            │                             │
            ├─ tool_tiers (6 tiers)       │
            │  ├─ Tier 1: Native tools    │
            │  ├─ Tier 2: Project scripts │
            │  ├─ Tier 3: Agent skills    │
            │  ├─ Tier 4: Task subagents  │
            │  ├─ Tier 5: Slash commands  │
            │  └─ Tier 6: MCP tools       │
            │                             │
            ├─ native_tools (18)          │
            │  ├─ read, write, edit       │
            │  ├─ glob, grep, bash        │
            │  ├─ websearch, webfetch     │
            │  └─ todowrite               │
            │                             │
            ├─ project_scripts (50+)      │
            │  ├─ analysis (5 main)       │
            │  ├─ validation (3)          │
            │  ├─ reporting (3)           │
            │  └─ utilities (40+)         │
            │                             │
            ├─ agents (3)                 │
            │  ├─ listing-browser (Haiku) │
            │  ├─ map-analyzer (Haiku)    │
            │  └─ image-assessor (Sonnet) │
            │                             │
            ├─ skills (18)                │
            │  ├─ data-management (2)     │
            │  ├─ filtering (2)           │
            │  ├─ scoring (2)             │
            │  ├─ extraction (4)          │
            │  ├─ domain-knowledge (3)    │
            │  ├─ output-generation (3)   │
            │  └─ utilities (2)           │
            │                             │
            ├─ relationships (11)         │
            │  ├─ Grep replaces bash grep │
            │  ├─ Read replaces bash cat  │
            │  ├─ Task spawns agents      │
            │  └─ Phase dependencies      │
            │                             │
            └─ phase_dependencies         │
               ├─ Phase 0: No deps        │
               ├─ Phase 1a,1b: No deps    │
               ├─ Phase 2: Requires Ph1   │
               ├─ Phase 3: Requires all   │
               └─ Phase 4: Requires Ph3   │

            ┌─────────────────────────────┐
            │ context-management.json     │
            │ (395 lines)                 │
            ├─────────────────────────────┤
            │                             │
            ├─ discovery_protocol         │
            │  └─ Auto-create CLAUDE.md   │
            │                             │
            ├─ staleness_protocol         │
            │  ├─ 12h critical            │
            │  ├─ 48-72h normal           │
            │  └─ 168h reference          │
            │                             │
            ├─ update_triggers (5)        │
            │  ├─ Agent completes work    │
            │  ├─ Error discovered        │
            │  ├─ New files created       │
            │  └─ Session wrapping up     │
            │                             │
            ├─ state_files (3)            │
            │  ├─ enrichment_data.json    │
            │  ├─ work_items.json         │
            │  └─ address_folder_lookup   │
            │                             │
            ├─ agent_handoff              │
            │  └─ Required reading flow   │
            │                             │
            ├─ spawn_validation_protocol  │
            │  └─ Phase 2 prerequisites   │
            │                             │
            ├─ failure_response_protocols │
            │  ├─ Prerequisite not met    │
            │  ├─ Data inconsistency      │
            │  └─ Agent timeout           │
            │                             │
            ├─ directory_contexts (6)     │
            │  ├─ scripts/                │
            │  ├─ src/                    │
            │  ├─ data/                   │
            │  ├─ tests/                  │
            │  ├─ .claude/                │
            │  └─ docs/                   │
            │                             │
            └─ session_checklist          │
               ├─ on_start (3)            │
               ├─ on_directory_enter (2)  │
               ├─ on_work_complete (3)    │
               └─ on_error (2)            │

═════════════════════════════════════════════════════════════
PURPOSE: Serve as semantic index for quick lookups
NOT LOADED DIRECTLY: Agents reference through skills
BENEFIT: Discover tools/patterns without reading raw code
═════════════════════════════════════════════════════════════
```

---

## DIAGRAM 7: DATA STRUCTURE RELATIONSHIPS

```
                   DATA FLOW & RELATIONSHIPS

              ┌──────────────────────────────┐
              │ phx_homes.csv (read-only)    │
              │ - street, city, zip, price   │
              │ - beds, baths, sqft          │
              └────────────┬──────────────────┘
                           │
                           │ Load via property-data skill
                           │
                           ▼
              ┌──────────────────────────────┐
              │ enrichment_data.json (LIST)  │
              │ - PRIMARY DATA STORE         │
              │                              │
              │ Phase 0 fields:              │
              │  lot_sqft, year_built        │
              │  garage_spaces               │
              │                              │
              │ Phase 1 fields:              │
              │  price, hoa_fee              │
              │  school_rating, orientation │
              │  safety_score               │
              │                              │
              │ Phase 2 fields:              │
              │  interior_total             │
              │  exterior_total             │
              │                              │
              │ Phase 3 fields:              │
              │  total_score, tier          │
              │  kill_switch_passed         │
              └───┬──────────┬──────────┬────┘
                  │          │          │
         ┌────────┘          │          └────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
   │ work_items   │  │ address_     │  │ extraction_  │
   │ .json        │  │ folder_      │  │ state.json   │
   │              │  │ lookup.json  │  │              │
   │ Progress     │  │              │  │ Image meta   │
   │ tracking     │  │ Maps addr→   │  │ Image status │
   │ Phase status │  │ image folder │  │ Run history  │
   │              │  │              │  │              │
   └──────────────┘  └──────────────┘  └──────────────┘
         │                   │                   │
         └───────────────────┼───────────────────┘
                             │
                             ▼
         ┌──────────────────────────────────┐
         │ phx_homes_ranked.csv (output)    │
         │ - All enrichment fields          │
         │ - Final scores and tier          │
         │ - Kill-switch verdict            │
         └──────────────────────────────────┘

CONSISTENCY RULES:
- enrichment_data.json is source of truth
- work_items.json tracks progress only
- address_folder_lookup.json is derived from Phase 1
- extraction_state.json is transient (can be regenerated)

═════════════════════════════════════════════════════════════
KEY: Use Read tool to load, property-data skill to manipulate
═════════════════════════════════════════════════════════════
```

---

## DIAGRAM 8: SKILL INHERITANCE & DEPENDENCIES

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

## KEY TAKEAWAYS

### Bucket 3 (Claude Architecture)
✓ **CLAUDE.md per directory** - 7/7 directories covered
✓ **Narrow context loading** - Each file loads only what its directory needs
✓ **Update triggers documented** - Staleness checks, auto-creation hooks
✓ **Knowledge graphs as indexes** - toolkit.json, context-management.json
✓ **Token-efficient format** - Lists/tables > prose, code examples > explanations

### Bucket 4 (Tool Hierarchy)
✓ **6-tier system implemented** - Native tools, scripts, skills, agents, slash commands, MCP
✓ **Zero violations** - No bash cat/grep/find in critical paths
✓ **Tool scoping** - Skills declare allowed-tools, restrictions enforced
✓ **Decision tree available** - Quick reference for tool selection
✓ **10 orchestration axioms** - Prevent common multi-agent failures

### Overall Maturity: 9/10
This is a **reference implementation** for Claude Code project organization.

---

*Generated: December 3, 2025*
*Print this guide. Reference often. Modify as your project evolves.*
