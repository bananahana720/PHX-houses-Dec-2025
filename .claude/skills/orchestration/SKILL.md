---
name: orchestration
description: Coordinate subagent workflows using parallel swarm waves (non-destructive) and sequential orchestrated waves (destructive). Main Agent delegates non-trivial work to subagents. Includes SDLC, TDD, and BMAD patterns. Use when user mentions using subagents, when you are planning on making a Task() tool call, managing complex multi-step tasks, spawning sub-agents, executing phased workflows, or orchestrating parallel work.
allowed-tools: Task, Read, Glob, Grep, Bash, TodoWrite, Skill
---

# Orchestration Skill

Coordinate multi-agent workflows with parallel swarm waves and sequential orchestrated waves.

## Workflow Selection

| Complexity | Agents | Pattern | Example |
|------------|--------|---------|---------|
| Simple | 2-3 | sequential | bug-fix-flow |
| Moderate | 3-5 | mixed | tdd-red-green-blue |
| Complex | 5+ | waves | phx-full-analysis |

**Load pattern:** `Read .claude/skills/orchestration/examples/{pattern}.yaml`

## Core Principle: Main Agent Pattern

```
You are MAIN AGENT (orchestrator). User is CO-ARCHITECT.

RULES:
  → Delegate ALL non-trivial work to sub-agents
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

## Wave Types

### Parallel Swarm Wave (Non-Destructive)

Use when tasks write to **independent locations**:
- Spawn multiple agents in **single message** (parallel)
- No shared state conflicts
- Example: Phase 1 listing-browser + map-analyzer

```python
# Launch in parallel (single message with multiple Task calls)
Task(agent="listing-browser", prompt="Extract listing...")
Task(agent="map-analyzer", prompt="Analyze location...")
```

### Sequential Orchestrated Wave (Destructive)

Use when tasks **modify shared state**:
- Execute in strict order
- Validate between steps
- Example: Phase 2 → Phase 3 → Phase 4

```python
# Execute sequentially (separate messages)
result1 = Task(agent="image-assessor", prompt="...")
validate(result1)  # Check before next
result2 = Task(agent="scorer", prompt="...")
```

## Cost-Aware Model Selection

| Task Type | Model | Cost/1M tokens | Use When |
|-----------|-------|----------------|----------|
| Structured extraction | Haiku | $0.25 in | Parsing, API calls |
| Geographic analysis | Haiku | $0.25 in | Schools, maps |
| Visual assessment | Sonnet | $3.00 in | Image scoring |
| Complex reasoning | Sonnet | $3.00 in | Multi-factor decisions |

**Decision Tree:**
```
Is task visual or subjective? → Sonnet
Is task structured extraction? → Haiku
Does task require nuance? → Sonnet
Is task simple lookup? → Grep (no agent)
```

## Agent Catalog (PHX Houses)

| Agent | Model | Phase | Purpose |
|-------|-------|-------|---------|
| listing-browser | Haiku | 1 | Zillow/Redfin extraction |
| map-analyzer | Haiku | 1 | Schools, safety, orientation |
| image-assessor | Sonnet | 2 | Interior/exterior scoring |

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
CRITICAL: Only orchestrators modify state files.
Sub-agents MUST return data, NOT write files.
Orchestrator aggregates and writes atomically.
```

### Key State Files
| File | Purpose |
|------|---------|
| `work_items.json` | Pipeline progress |
| `enrichment_data.json` | Property data |
| `extraction_state.json` | Image pipeline |

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
