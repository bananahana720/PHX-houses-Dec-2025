---
last_updated: 2025-12-06T12:00:00Z
updated_by: agent
staleness_hours: 168
line_target: 80
flags: []
---
# Orchestration Skill

## Purpose
Coordinate multi-agent workflows with parallel swarm waves (non-destructive) and sequential orchestrated waves (destructive). Main Agent delegates work to sub-agents.

## Contents
| File | Purpose |
|------|---------|
| `SKILL.md` | Core skill definition with process, rules, templates |
| `orchestration-patterns.yaml` | Comprehensive patterns (complexity, waves, agents, costs, errors, state) |
| `patterns/sdlc-patterns.yaml` | General SDLC workflow patterns |
| `patterns/bmad-patterns.yaml` | BMAD method workflow integrations |
| `examples/` | Workflow examples (bug-fix, TDD, PHX pipeline) |

## Key Patterns
- **Main Agent Pattern**: Orchestrator delegates, sub-agents execute, orchestrator aggregates
- **Wave Types**: Parallel swarm (non-destructive) vs sequential orchestrated (destructive)
- **Single Writer Rule**: Only orchestrators modify state files; sub-agents return data

## Model Selection
| Model | Model ID | Use When |
|-------|----------|----------|
| Haiku 4.5 | `claude-haiku-4-5-20251001` | Structured extraction, API calls, parsing, high-volume |
| Opus 4.5 | `claude-opus-4-5-20251101` | Visual analysis, subjective scoring, complex reasoning |

## Thinking Block Tags
| Tag | Purpose |
|-----|---------|
| `<orchestration_analysis>` | Deep task analysis (Step 1) |
| `<adaptation_notes>` | Post-wave learning analysis |
| `<next_steps>` | Wave progression instructions (outside thinking) |

## Refs
- Main SKILL.md: `SKILL.md:1-432`
- Patterns: `orchestration-patterns.yaml`
- Parent: `../../CLAUDE.md`

## Deps
<- imports: none (skill definition)
-> used by: all agents via `Skill(orchestration)`, Task() orchestration
