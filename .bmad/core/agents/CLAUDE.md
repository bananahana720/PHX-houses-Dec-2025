---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# .bmad/core/agents

## Purpose
Agent definitions for BMAD orchestration framework. Implements persona-based agent executors with activation workflows, menu routing, and handler systems for task/workflow dispatch. Supports both markdown and XML agent formats.

## Contents
| Path | Purpose |
|------|---------|
| `bmad-master.md` | Master orchestrator agent (4.9 KB): persona, activation steps, menu handlers, rule system, TTS integration |
| `bmad-web-orchestrator.agent.xml` | Web orchestration agent (6.1 KB): XML-based orchestrator for distributed workflows |

## Tasks
- [x] Implement persona-based agent activation `P:H`
- [x] Create menu-driven command routing `P:H`
- [x] Integrate file-based task execution (exec="path.md") `P:H`
- [ ] Add async/parallel agent execution `P:M`
- [ ] Implement inter-agent communication protocol `P:M`

## Learnings
- **Activation workflow:** Agents load config.yaml variables, initialize rules, display menu before accepting commands
- **Handler dispatch:** Menu items map to handlers (action|exec|workflow) with attribute-based routing
- **Persona system:** Agent XML embeds behavioral rules, communication style, and execution constraints
- **File-based execution:** exec handler loads markdown/text files and executes content (implements deterministic behavior)
- **TTS voice:** Agents call bmad-speak.sh hook for voice output (supports multilingual communication)

## Refs
- Master agent activation: `bmad-master.md:10-30` (initialization steps)
- Menu handler system: `bmad-master.md:30-45` (action, exec, workflow routing)
- Agent rules: `bmad-master.md:46-60` (communication rules, TTS integration)

## Deps
← Imports from:
  - `.bmad/core/config.yaml` (configuration variables)
  - `.claude/hooks/bmad-speak.sh` (TTS voice output)
  - Task/workflow files referenced via exec="path"

→ Imported by:
  - BMAD framework (agent orchestration)
  - User interface (menu command selection)
  - Multi-agent workflows