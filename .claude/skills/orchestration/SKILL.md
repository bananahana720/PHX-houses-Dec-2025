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

---

# Core Process

## Step 1: Deep Analysis

Analyze the task thoroughly inside `<orchestration_analysis>` tags within your thinking block. Work systematically through:

### Component Breakdown
List every atomic sub-task as a numbered list with brief descriptions. Write them out explicitly, one by one. It's OK for this section to be quite long - be thorough and comprehensive.

### Classification
Go through each numbered component and classify it as:
- **Destructive**: Modifies files, deletes content, structural changes, migrations, deployments
- **Non-destructive**: Read-only operations, analysis, drafting, testing without modifications, reviews

### Dependency Mapping
Identify which components must complete before others. Map the dependency chain explicitly by referencing the numbered components. Note which can run in parallel.

### Conflict Identification
Identify potential conflicts if components run in parallel. For each conflict note:
- Which components might conflict (reference by number)
- Nature of conflict (file-level, resource, logical)
- Whether it requires sequential execution

### SDLC Pattern Matching
Consider which pattern applies:
- **Feature Development**: Requirements/tech spec → Design/test plan → Implementation → Review/test → Integration
- **Bug Fix**: Log analysis/reproduction → Root cause → Fix with tests → Deploy/verify
- **Refactoring**: Code smell identification → Strategy → Staged transformations → Verification
- **Architecture Review**: Component analysis → Assessment → Recommendations → Implementation

*Load detailed patterns:* `Read .claude/skills/orchestration/patterns/sdlc-patterns.yaml`

### Risk Assessment
List ambiguities needing clarification, risks/unknowns requiring adaptive orchestration, areas where novel information might emerge.

### Success Criteria
Define what success looks like and key outputs/quality gates.

### Token Efficiency
Be thorough but avoid unnecessary repetition. Focus on critical analysis points.

---

## Step 2: Choose Mode

### Orchestration Mode
Use for tasks that:
- Require >2000-3000 tokens to complete
- Involve multiple distinct components
- Benefit from parallel execution
- Require specialized analysis before implementation
- Are standard SDLC workflows

### Simple Workflow Mode
Use for tasks that:
- Are straightforward and well-defined
- Can complete in <2000-3000 tokens
- Involve single component
- Don't require parallel execution

---

## Step 3: Execute Based on Mode

### Orchestration Mode

#### Select Models for Sub-Agents

| Model | Strengths | Use When |
|-------|-----------|----------|
| **Haiku** | Speed, cost, structured tasks | Parsing, extraction, simple lookups, high-volume parallel |
| **Sonnet** | Nuance, vision, complex reasoning | Image analysis, subjective scoring, multi-factor decisions |
| **Opus** | Deep expertise, long-form, planning | Architecture, novel problems, extensive research |

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

#### Present Orchestration Plan

```
<orchestration_plan>
Wave 1: [Name] - [Parallel/Sequential]
- Agent 1: [Role] - Model: [Haiku/Sonnet/Opus] - Rationale: [Why]
- Agent 2: [Role] - Model: [Haiku/Sonnet/Opus] - Rationale: [Why]
- Outputs: [What each produces]

Wave 2: [Name] - [Parallel/Sequential]
- Agent 1: [Role] - Model: [Haiku/Sonnet/Opus] - Rationale: [Why]
- Outputs: [What produces]

Dependencies: [Which waves depend on prior waves and why]
Risks: [Issues and mitigations]
</orchestration_plan>

<todo_list>
- [ ] Wave 1: [Description] - Status: Not Started
  - [ ] Agent 1: [Task]
  - [ ] Agent 2: [Task]
- [ ] Wave 2: [Description] - Status: Blocked by Wave 1
  - [ ] Agent 1: [Task]
</todo_list>

<first_wave_instructions>
Agent 1: [Complete instructions with context, task, output format, tools, acceptance criteria]
Agent 2: [Complete instructions with context, task, output format, tools, acceptance criteria]
</first_wave_instructions>
```

#### Execute and Adapt

After each wave, analyze responses for novel information inside `<adaptation_notes>` tags within your thinking block. Look for:
- Unexpected dependencies/blockers
- Risks not previously considered
- Incorrect assumptions
- Scope changes
- Technical constraints affecting feasibility

If novel information discovered:
1. Document it
2. Reassess plan
3. Identify affected waves
4. Adjust assignments/sequencing
5. Update TODO list

Present outside thinking:
```
<next_steps>
[Updated plan for next wave based on learnings. Instructions for next agents.]
</next_steps>
```

---

### Simple Workflow Mode

1. **Break down task** into sub-tasks. Use Task(Explore) for codebase questions.

2. **Create detailed plan** with TodoWrite:
```yaml
step: 1 - [Title]
  in: [file:line] - [Current state]
  do: [Exact changes]
  out: [file:line] - [Expected result]
  check: [Verification method]
  risk: [Failure modes and mitigations]
  needs: []
```

3. **Verify plan.** If ANY ambiguity exists, use AskUserQuestion before proceeding. Once approved, call ExitPlanMode.

4. **Pre-implementation checks:**
   - Task(Explore) to understand existing patterns
   - Validate syntax with mcp__context7 tools
   - Check CLAUDE.md for project rules

5. **Execute** step by step.

6. **Validate results** (see Quality Standards below).

---

## Step 4: Generate Completion Report

```yaml
completed: [Feature/task name]
  changed:
    - [file:line]
    - [file:line]
  tests: [Status - e.g., "All 23 tests passing"]
  docs: [Status - e.g., "Updated README, added inline comments"]
  verified: rg clean (no TODO/console.log), types pass, lint pass
```

---

# Quality Standards - Stop-the-Line Rules

🛑 **STOP and report** if you encounter:
- Preexisting errors (build/lint/test/type failures)
- Outdated/missing documentation
- <95% confidence (use AskUserQuestion)
- Placeholder code (TODO, mocks, console.log, commented code)
- Missing error handling or input validation
- Security issues (hardcoded secrets)

**Core Rules:**
- **Git Safety 💾**: Commit existing work BEFORE creating new TodoWrite (mandatory, atomic commits)
- **Docs-First 📚**: Update documentation BEFORE marking work complete
- **Read Entire Files 📖**: Read section-by-section for complete context (never skip with offset/limit)
- **Zero Shortcuts ❌**: No TODOs, placeholders, console.logs, commented code, hardcoded values, silent failures
- **Complete Implementations ✅**: Include error handling, validation, tests, types, timeouts/retries
- **Verify Before Assuming**: Use mcp__context7 tools for syntax verification
- **Single WIP**: Keep TODO synchronized in real-time
- **Post-Implementation**: Run `rg "TODO\|console\.log" src/` and verify empty; ensure tests/types/lint pass

---

# Mandatory Tools

| Tool | When to Use |
|------|-------------|
| **ExitPlanMode** | After plan approval, before implementation |
| **AskUserQuestion** | When confidence <95%, ambiguity exists, errors found, or before destructive ops |
| **mcp__context7__resolve-library-id** | Before syntax suggestions |
| **mcp__context7__get-library-docs** | To verify library APIs |
| **Task(Explore)** | For codebase exploration (specify quick/medium/very thorough) |
| **Task(general-purpose)** | For multi-step implementations (provide plan + acceptance criteria) |
| **TodoWrite** | For all planned work with extreme detail |

---

# File Safety

- Prefer edit over create
- NEVER delete until migration complete and data preserved
- Use full paths before modifications
- Confirm before destructive operations
- Separate mechanical from behavioral changes

---

# Communication

- Concise, evidence-based with file:line references
- Professional yet personable
- Prioritize technical accuracy
- Use emojis: 🎯 key points, 🛑 warnings, 🚀 celebrations
- Warn when <30% token budget remains; suggest /compact before large operations

---

# Wave Types

## Parallel Swarm Wave (Non-Destructive)

Use when tasks are for **research, analysis, review, files that do not have dependency on one another**:
- Spawn multiple agents in **single message** (parallel)
- No shared state conflicts
- Example: Phase 1 listing-browser + map-analyzer

```python
# Launch in parallel (single message with multiple Task calls)
Task(agent="code-reviewer", prompt="Validate file...")
Task(agent="code-reviewer", prompt="Analyze schema...")
```

## Sequential Orchestrated Wave (Destructive)

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

---

# Agent & Workflow Catalog

## Built-in Task Agents

| Agent Type | Model | Use When | Skills to Pass |
|------------|-------|----------|----------------|
| Explore | Haiku | Codebase search, file discovery | - |
| general-purpose | Sonnet | Multi-step implementations | Relevant domain skills |
| code-reviewer | Sonnet | PR reviews, quality checks | - |
| debugger | Sonnet | Error investigation | - |

## Custom Agents (`.claude/agents/`)

| Agent | Model | Purpose | Skills |
|-------|-------|---------|--------|
| listing-browser | Haiku | Zillow/Redfin extraction | listing-extraction |
| map-analyzer | Haiku | Schools, safety, orientation | map-analysis |
| image-assessor | Sonnet | Interior/exterior scoring | image-assessment |

## BMAD Workflows (`/bmad:bmm:workflows/*`)

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/bmad:bmm:workflows:create-story` | Generate implementation-ready stories | Before sprint work |
| `/bmad:bmm:workflows:dev-story` | Execute story with TDD | During implementation |
| `/bmad:bmm:workflows:code-review` | Adversarial code review | After PR ready |
| `/bmad:bmm:workflows:sprint-planning` | Generate sprint status tracking | Start of sprint |
| `/bmad:bmm:workflows:create-tech-spec` | Technical specification | Before complex features |

*Load detailed BMAD patterns:* `Read .claude/skills/orchestration/patterns/bmad-patterns.yaml`

---

# Pre-Spawn Validation (MANDATORY for Phase 2+)

```bash
python scripts/validate_phase_prerequisites.py \
  --address "{ADDRESS}" --phase phase2_images --json

# Exit 0 = proceed
# Exit 1 = BLOCK - do not spawn
```

---

# State Management

## Single Writer Rule
```
CRITICAL: Only main agents/orchestrators modify state files.
Sub-agents MUST return data, NOT write files.
Orchestrator aggregates and writes atomically.
```

## Key State Files

| File | Purpose |
|------|---------|
| `data/work_items.json` | Pipeline progress |
| `data/enrichment_data.json` | Property data |
| `data/extraction_state.json` | Image pipeline |
| `docs/bmm-workflow-status.yaml` | BMAD workflow phase tracking |
| `docs/sprint-artifacts/sprint-status.yaml` | Sprint/epic/story progress |
| `docs/sprint-artifacts/workflow-status.yaml` | Current workflow state |

*Load detailed state management rules:* `Read .claude/skills/orchestration/orchestration-patterns.yaml` (Section 6)

---

# Error Escalation

| Level | Condition | Action |
|-------|-----------|--------|
| 1 | Transient error | Auto-retry (3x) |
| 2 | Source blocked | Try alternate source |
| 3 | Non-critical fail | Skip phase, continue |
| 4 | Critical fail | Stop, escalate to user |

*Load detailed error escalation matrix:* `Read .claude/skills/orchestration/orchestration-patterns.yaml` (Section 5)

---

# Pattern Files

| File | Content |
|------|---------|
| `orchestration-patterns.yaml` | Comprehensive patterns (complexity tiers, wave types, agent catalog, cost-aware model selection, error escalation, state management) |
| `examples/simple-bug-fix.yaml` | Bug fix workflow |
| `examples/tdd-workflow.yaml` | TDD RED/GREEN/BLUE |
| `examples/phx-full-pipeline.yaml` | PHX property analysis |
| `patterns/sdlc-patterns.yaml` | General SDLC patterns |
| `patterns/bmad-patterns.yaml` | BMAD method workflows |

**Load comprehensive patterns:** `Read .claude/skills/orchestration/orchestration-patterns.yaml`

---

# Agent Spawn Template

```python
prompt = f"""
You are {agent_name} for PHX Houses pipeline.

**Target:** {address}
**Prerequisites:** Phase 1 complete, {image_count} images
**Skills:** {skills_list}
**Output Budget:** max {token_budget} tokens

**Return Format:**
{{"status": "success|partial|failed", "data": {{...}}, "errors": []}}

**CRITICAL RULES:**
- DO NOT write to state files (read-only access)
- Return data to orchestrator for aggregation
- Include errors array even if empty

**Pre-Work:** Read .claude/AGENT_BRIEFING.md
"""
```

---

# Best Practices

1. **Plan before spawn** - Draft orchestration plan first
2. **Track with TodoWrite** - Maintain visible progress
3. **Validate before dependent phases** - Use validation scripts
4. **Prefer Haiku** - Default to Haiku unless visual/subjective
5. **Checkpoint after each phase** - Update state files
6. **Single writer for shared state** - Aggregate, write once
7. **Set output token budgets** - Prevent context overflow
8. **Include context in prompts** - Pass property data to agents
