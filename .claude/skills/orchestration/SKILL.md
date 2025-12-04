---
name: orchestration
description: Coordinate subagent workflows using parallel swarm waves (non-destructive) and sequential orchestrated waves (destructive). Main Agent delegates non-trivial work to subagents. Includes SDLC, TDD, and BMAD patterns. Use when user mentions using subagents, when you are planning on making a Task() tool call, managing complex multi-step tasks, spawning sub-agents, executing phased workflows, or orchestrating parallel work.
allowed-tools: Task, Read, Glob, Grep, Bash, TodoWrite, Skill
---

# Orchestration Skill

Coordinate multi-agent workflows with parallel swarm waves and sequential orchestrated waves.

## Core Principle: Main Agent Pattern

```
You are MAIN AGENT (orchestrator). User is CO-ARCHITECT.

RULES:
  → Delegate *ALL* non-trivial work to sub-agents
  → Only perform small R/W tasks yourself (~2k-3k tokens max)
  → Coordinate; don't execute heavy work

Task Types:
  • Non-destructive tasks → Parallel swarm waves
  • Destructive tasks → Sequential orchestrated waves
```

## First Steps (MANDATORY)

1. **Draft Orchestration Plan** - Enumerate phases, agents, dependencies
2. **Update TODO List** - Track with TodoWrite
3. **Begin Phased Execution** - You coordinate, sub-agents execute

## Workflow Selection

**Load pattern:** `Read .claude/skills/orchestration/examples/{pattern}.yaml`

## Wave Types

### Parallel Swarm Wave (Non-Destructive)

Use when tasks are for **reaserch, analysis, review, files that do not have dependency on one another**:
- Spawn multiple agents in **single message** (parallel)
- No shared state conflicts
- Example: Phase 1 listing-browser + map-analyzer

```python
# Launch in parallel (single message with multiple Task calls)
Task(agent="code-reviewer", prompt="Validate file...")
Task(agent="code-reviewer", prompt="Analyze schema...")
```

### Sequential Orchestrated Wave (Destructive)

Use when tasks **modify shared state**:
- Execute in strict order
- Validate between steps
- Example: Phase 2 → Phase 3 → Phase 4

```python
# Execute sequentially (separate messages)
result1 = Task(agent="explore", prompt="...")
validate(result1)  # Check before next
result2 = Task(agent="code-dev", prompt="...")
```

## Cost-Aware Model Selection

| Model | Strengths | Use When |
|-------|-----------|----------|
| Haiku | Speed, cost, structured tasks | Parsing, extraction, simple lookups, high-volume parallel |
| Sonnet | Nuance, vision, complex reasoning | Image analysis, subjective scoring, multi-factor decisions |
| Opus | Deep expertise, long-form, planning | Architecture, novel problems, extensive research |

**Model Selection Heuristics:**
```
1. Can I do this with 4-5 tool calls alone (Read/Grep/Glob)? → No agent needed
2. Is it a well-defined, repeatable task with clear inputs/outputs? → Haiku
3. Does it require judgment, interpretation, or ambiguity resolution? → Sonnet
4. Is it novel, requires deep domain expertise, or extensive planning? → Opus

Ask yourself:
- "Would a checklist suffice?" → Haiku
- "Does this need taste or judgment?" → Sonnet
- "Am I architecting something new or complex?" → Opus
```

## Agent & Workflow Catalog

### Built-in Task Agents
| Agent Type | Model | Use When | Skills to Pass |
|------------|-------|----------|----------------|
| Explore | Haiku | Codebase search, file discovery | - |
| general-purpose | Sonnet | Multi-step implementations | Relevant domain skills |
| code-reviewer | Sonnet | PR reviews, quality checks | - |
| debugger | Sonnet | Error investigation | - |

### Custom Agents (`.claude/agents/`)
| Agent | Model | Purpose | Skills |
|-------|-------|---------|--------|
| listing-browser | Haiku | Zillow/Redfin extraction | listing-extraction |
| map-analyzer | Haiku | Schools, safety, orientation | map-analysis |
| image-assessor | Sonnet | Interior/exterior scoring | image-assessment |

### BMAD Workflows (`/bmad:bmm:workflows/*`)
| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/bmad:bmm:workflows:create-story` | Generate implementation-ready stories | Before sprint work |
| `/bmad:bmm:workflows:dev-story` | Execute story with TDD | During implementation |
| `/bmad:bmm:workflows:code-review` | Adversarial code review | After PR ready |
| `/bmad:bmm:workflows:sprint-planning` | Generate sprint status tracking | Start of sprint |
| `/bmad:bmm:workflows:create-tech-spec` | Technical specification | Before complex features |

## Pre-Spawn Validation (MANDATORY for Phase 2+)

```bash
python scripts/validate_phase_prerequisites.py \
  --address "{ADDRESS}" --phase phase2_images --json

# Exit 0 = proceed
# Exit 1 = BLOCK - do not spawn
```

## State Management

### Single Writer Rule
```
CRITICAL: Only main agents/orchestrators modify state files.
Sub-agents MUST return data, NOT write files.
Orchestrator aggregates and writes atomically.
```

### Key State Files
| File | Purpose |
|------|---------|
| `data/work_items.json` | Pipeline progress |
| `data/enrichment_data.json` | Property data |
| `data/extraction_state.json` | Image pipeline |
| `docs/bmm-workflow-status.yaml` | BMAD workflow phase tracking |
| `docs/sprint-artifacts/sprint-status.yaml` | Sprint/epic/story progress |
| `docs/sprint-artifacts/workflow-status.yaml` | Current workflow state |

## Error Escalation

| Level | Condition | Action |
|-------|-----------|--------|
| 1 | Transient error | Auto-retry (3x) |
| 2 | Source blocked | Try alternate source |
| 3 | Non-critical fail | Skip phase, continue |
| 4 | Critical fail | Stop, escalate to user |

## Pattern Files

| File | Content |
|------|---------|
| `orchestration-patterns.yaml` | Comprehensive patterns (complexity tiers, wave types, agent catalog, cost-aware model selection, error escalation, state management) |
| `examples/simple-bug-fix.yaml` | Bug fix workflow |
| `examples/tdd-workflow.yaml` | TDD RED/GREEN/BLUE |
| `examples/phx-full-pipeline.yaml` | PHX property analysis |
| `patterns/sdlc-patterns.yaml` | General SDLC patterns |
| `patterns/bmad-patterns.yaml` | BMAD method workflows |

**Load pattern:** `Read .claude/skills/orchestration/orchestration-patterns.yaml`

## Agent Spawn Template

```python
prompt = f"""
You are {agent_name} for PHX Houses pipeline.

**Target:** {address}
**Prerequisites:** Phase 1 complete, {image_count} images
**Skills:** {skills_list}
**Output Budget:** max {token_budget} tokens

**Return Format:**
{{"status": "success|partial|failed", "data": {{...}}, "errors": []}}

**Pre-Work:** Read .claude/AGENT_BRIEFING.md
"""
```

## Best Practices

1. **Plan before spawn** - Draft orchestration plan first
2. **Track with TodoWrite** - Maintain visible progress
3. **Validate before dependent phases** - Use validation scripts
4. **Prefer Haiku** - Default to Haiku unless visual/subjective
5. **Checkpoint after each phase** - Update state files
6. **Single writer for shared state** - Aggregate, write once
7. **Set output token budgets** - Prevent context overflow
8. **Include context in prompts** - Pass property data to agents
