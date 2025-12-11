---
last_updated: 2025-12-10T18:00:00Z
updated_by: agent
staleness_hours: 24
line_target: 80
flags: []
---
# .claude

## Purpose
Claude Code configuration: agents, skills, commands, hooks, hookify rules, and operational protocols for PHX Houses pipeline.

## Contents
| Path | Purpose |
|------|---------|
| `protocols.md` | Operational protocols (TIER 0-3) |
| `mcp-reference.md` | MCP tool docs (Context7, Playwright, Fetch) |
| `agents/` | Subagent definitions (3 agents: listing-browser, map-analyzer, image-assessor) |
| `commands/` | Slash commands (analyze-property, commit) |
| `skills/` | Domain expertise modules (12 skills) |
| `hooks/` | Pre/post execution hooks (18 Python scripts) |
| `hookify.*.local.md` | 40 hookify rules (orchestration, safety, quality) |
| `settings.json` | Claude Code settings |

## Key Patterns
- **Skills loading**: Agents declare `skills:` in frontmatter YAML
- **Hooks**: Python scripts in `hooks/` run pre/post tool execution
- **Hookify rules**: Markdown rules in `.local.md` files for behavior enforcement
- **Model tiers**: Haiku 4.5 (extraction), Opus 4.5 (vision/assessment)
- **Orchestration**: Main agent delegates, subagents implement

## Available Skills
| Skill | Use When |
|-------|----------|
| property-data | Any property data access |
| state-management | Multi-phase workflows, crash recovery |
| kill-switch | Filtering properties (5 HARD + 4 SOFT criteria) |
| scoring | Calculating 605-point scores/tiers |
| county-assessor | Phase 0 Maricopa County API |
| arizona-context | AZ-specific: solar, pool, HVAC |
| listing-extraction | Phase 1 Zillow/Redfin automation |
| map-analysis | Phase 1 schools, safety, distances |
| image-assessment | Phase 2 visual scoring (Section C) |
| orchestration | Multi-agent workflow coordination |
| visualizations | Charts & plots |

## Quick Commands
```bash
/analyze-property --test          # First 5 properties
/analyze-property --all           # Full batch
/analyze-property "123 Main St"   # Single property
```

## Hookify Rules (40 total)
| Category | Count | Key Rules |
|----------|-------|-----------|
| Orchestration | 8 | enforce-orchestrator-role, enforce-task-delegation, track-subagent-completions |
| Safety | 10 | block-playwright-zillow, block-secrets-commit, block-data-file-edits |
| Quality | 12 | require-tests-before-stop, verify-test-execution, precommit-hygiene |
| Documentation | 6 | require-claude-md-update, detect-stale-documentation |
| Architecture | 4 | enforce-ddd-layers, validate-repository-pattern |

## Refs
- Parent: `../CLAUDE.md` (full project docs)
- Protocols: `protocols.md` (TIER 0-3 rules)
- MCP: `mcp-reference.md` (Context7, Playwright, Fetch)
- Hookify format: `hookify.*.local.md` files

## Deps
<- imports: none (config directory)
-> used by: all agents, all skills, all commands
