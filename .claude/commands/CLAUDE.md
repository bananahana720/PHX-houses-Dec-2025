---
last_updated: 2025-12-04
updated_by: Claude (Agent)
staleness_hours: 24
flags: []
---

# .claude/commands

## Purpose

Custom slash commands for Claude Code that orchestrate multi-agent property analysis workflows. Commands provide CLI-like interfaces for pipeline execution, git operations, and agent coordination.

## Contents

| Path | Purpose |
|------|---------|
| `analyze-property.md` | Multi-agent property analysis orchestrator (364 lines) - phases 0-4 with progress/ETA |
| `commit.md` | Git commit helper with conventional commit format |

## Key Command: analyze-property

**Arguments:** `<address>` or `--all` or `--test` with optional `--strict`, `--skip-phase=N`, `--resume`, `--fresh`

**Phases Orchestrated:**
- Phase 0: County API (extract_county_data.py)
- Phase 1a/1b: Listing + Map analysis (parallel)
- Phase 2: Image assessment (image-assessor agent)
- Phase 3: Synthesis (scoring pipeline)
- Phase 4: Reports (deal sheets)

**Integration:** Calls `scripts/pipeline_cli.py` for CLI execution with rich progress bars.

## Tasks

- [x] Implement analyze-property command with all flags `P:H`
- [x] Add CLI integration via pipeline_cli.py `P:H`
- [ ] Add batch progress persistence across sessions `P:M`
- [ ] Implement parallel property processing `P:L`

## Learnings

- **Slash commands are prompts:** Expanded at runtime, not executable scripts
- **Tool restrictions:** `allowed-tools` frontmatter limits which tools the command can use
- **Argument injection:** `$ARGUMENTS` placeholder receives user-provided args

## Refs

- analyze-property phases: `analyze-property.md:260-280`
- Pre-spawn validation: `analyze-property.md:171-210`
- State management: `analyze-property.md:253-260`

## Deps

<- Imports from:
  - `scripts/pipeline_cli.py` - CLI backend
  - `scripts/validate_phase_prerequisites.py` - Phase 2 validation
  - `.claude/skills/` - Domain expertise modules

-> Imported by:
  - User via `/analyze-property` command
  - Multi-agent orchestration workflows
