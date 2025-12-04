# DIAGRAM 6: KNOWLEDGE GRAPH STRUCTURE (Bucket 3)

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
