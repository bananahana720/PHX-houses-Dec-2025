---
last_updated: 2025-12-05T00:00:00Z
updated_by: main
staleness_hours: 168
line_target: 80
flags: []
---
# Orchestration Skill

## Purpose
Coordinate multi-agent workflows with parallel swarm waves (non-destructive) and sequential orchestrated waves (destructive). Main Agent delegates work to sub-agents while enforcing quality standards.

## Contents
| File | Purpose |
|------|---------|
| `SKILL.md` | Core skill definition with process, rules, templates |
| `orchestration-patterns.yaml` | Comprehensive patterns (complexity, waves, agents, costs, errors, state) |
| `patterns/sdlc-patterns.yaml` | General SDLC workflow patterns |
| `patterns/bmad-patterns.yaml` | BMAD method workflow integrations |
| `examples/simple-bug-fix.yaml` | Bug fix workflow example |
| `examples/tdd-workflow.yaml` | TDD RED/GREEN/BLUE example |
| `examples/phx-full-pipeline.yaml` | PHX property analysis full pipeline |

## Key Patterns
- **Main Agent Pattern**: Orchestrator delegates, sub-agents execute, orchestrator aggregates
- **Wave Types**: Parallel swarm (non-destructive) vs sequential orchestrated (destructive)
- **Single Writer Rule**: Only orchestrators modify state files; sub-agents return data

## Quick Reference

### Mode Selection
| Mode | Token Threshold | Characteristics |
|------|-----------------|-----------------|
| Orchestration | >2000-3000 | Multiple components, parallel execution, SDLC workflows |
| Simple Workflow | <2000-3000 | Single component, straightforward, no parallelism |

### Model Selection
| Model | Use When |
|-------|----------|
| Haiku | Structured extraction, API calls, parsing, high-volume |
| Sonnet | Visual analysis, subjective scoring, complex reasoning |
| Opus | Architecture, novel problems, deep domain expertise |

### Thinking Block Tags
| Tag | Purpose |
|-----|---------|
| `<orchestration_analysis>` | Deep task analysis (Step 1) |
| `<adaptation_notes>` | Post-wave learning analysis |
| `<next_steps>` | Wave progression instructions (outside thinking) |

## Refs
- Main SKILL.md: `SKILL.md:1-432`
- Comprehensive patterns: `orchestration-patterns.yaml`
- SDLC patterns: `patterns/sdlc-patterns.yaml`
- BMAD patterns: `patterns/bmad-patterns.yaml`
- Parent CLAUDE.md: `../.claude/CLAUDE.md`

## Deps
<- imports: none (skill definition)
-> used by: all agents via `Skill(orchestration)`, Task() orchestration
