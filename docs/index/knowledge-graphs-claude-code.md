# Knowledge Graphs (Claude Code)

### Toolkit Knowledge Graph
**File:** `.claude/knowledge/toolkit.json`
**Purpose:** Machine-readable tool schemas, relationships, phase dependencies
**Key Sections:**
- `tool_tiers` - Tool priority hierarchy (native > scripts > agents > MCP)
- `native_tools` - Claude native tools (Read, Write, Edit, Grep, Glob, Bash, etc.)
- `project_scripts` - Analysis scripts (phx_home_analyzer.py, extract_*.py, etc.)
- `agents` - Agent definitions (listing-browser, map-analyzer, image-assessor)
- `skills` - Skill modules (property-data, scoring, kill-switch, etc.)
- `slash_commands` - Custom commands (/analyze-property, /commit)
- `mcp_tools` - MCP tool integrations (Playwright, fetch)
- `relationships` - Tool relationships (replaces, spawns, loads, etc.)
- `phase_dependencies` - Pipeline phase flow and spawn order
- `common_mistakes` - Frequent errors and fixes

[View Toolkit →](../.claude/knowledge/toolkit.json)

### Context Management Knowledge Graph
**File:** `.claude/knowledge/context-management.json`
**Purpose:** State management, staleness, handoff protocols
**Key Sections:**
- `discovery_protocol` - Auto-discover CLAUDE.md files in directories
- `staleness_protocol` - Check file freshness before use
- `update_triggers` - When to update context files
- `state_files` - Critical state files (work_items.json, enrichment_data.json)
- `agent_handoff` - Agent spawn and completion protocols
- `spawn_validation_protocol` - Pre-spawn validation (MANDATORY for Phase 2)
- `failure_response_protocols` - Structured error handling
- `directory_contexts` - Context for each major directory

[View Context Management →](../.claude/knowledge/context-management.json)

---
