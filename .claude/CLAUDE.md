---
last_updated: 2025-12-05T18:30:00Z
updated_by: agent
staleness_hours: 24
line_target: 80
flags: []
---
# .claude

## Purpose
Claude Code configuration: agents, skills, commands, hooks, and operational protocols.

## Contents
| File/Dir | Purpose |
|----------|---------|
| `protocols.md` | Operational protocols (TIER 0-3) |
| `mcp-reference.md` | MCP tool docs (Context7, Playwright, Fetch) |
| `agents/` | Subagent definitions (listing-browser, map-analyzer) |
| `commands/` | Slash commands (analyze-property, commit) |
| `skills/` | Domain expertise modules (11 skills) |
| `hooks/` | Pre/post execution hooks (safety, linting) |
| `settings.json` | Claude Code settings |

## Key Patterns
- **Skills loading**: Agents declare `skills:` in frontmatter YAML
- **Hooks**: Python scripts in `hooks/` run pre/post tool execution
- **Protocols reference**: See `protocols.md` for TIER 0-3 rules

## Available Skills
| Skill | Use When |
|-------|----------|
| property-data | Any property data access |
| state-management | Multi-phase workflows, crash recovery |
| kill-switch | Filtering properties (8 HARD criteria) |
| scoring | Calculating 605-point scores/tiers |
| county-assessor | Phase 0 Maricopa County API |
| arizona-context | AZ-specific: solar, pool, HVAC |
| listing-extraction | Phase 1 Zillow/Redfin automation |
| map-analysis | Phase 1 schools, safety, distances |
| image-assessment | Phase 2 visual scoring (Section C) |
| deal-sheets | Phase 4 report generation |
| visualizations | Charts & plots |

## Quick Commands
```bash
/analyze-property --test          # First 5 properties
/analyze-property --all           # Full batch
/analyze-property "123 Main St"   # Single property
```

## Refs
- Parent: `../CLAUDE.md` (full project docs)
- Protocols: `protocols.md` (TIER 0-3 rules)
- MCP: `mcp-reference.md` (Context7, Playwright, Fetch)

## Deps
← imports: none (config directory)
→ used by: all agents, all skills, all commands
