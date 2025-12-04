# DIAGRAM 1: CLAUDE.MD COVERAGE (Bucket 3)

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
