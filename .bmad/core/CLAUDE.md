---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---
# .bmad/core

## Purpose
BMAD (Behavioral Multi-Agent Distributed) core module providing agent/task/workflow orchestration, configuration management, and menu-driven execution framework for multi-agent pipelines. Implements persona-based agent activation with embedded XML rules and dynamic command routing.

## Contents
| Path | Purpose |
|------|---------|
| `config.yaml` | Core configuration: bmad_folder, user_name, language, output paths, version 6.0.0-alpha.13 |
| `agents/` | Agent definitions (bmad-master.md orchestrator, bmad-web-orchestrator.agent.xml) |
| `tasks/` | Task definitions and implementations |
| `resources/` | Shared resources for agents and tasks |
| `workflows/` | Workflow definitions and pipelines |
| `tools/` | Tool integrations and utilities |

## Tasks
- [x] Load core configuration on agent activation `P:H`
- [x] Parse and route menu-based commands `P:H`
- [ ] Add multi-workflow orchestration support `P:M`
- [ ] Implement agent scaling for parallel execution `P:L`
- [ ] Add persistence for long-running workflows `P:L`

## Learnings
- **Config injection:** config.yaml variables ({user_name}, {communication_language}, {bmad_folder}) injected into agent activation steps
- **Agent persona system:** Agents load activation XML with mandatory initialization steps before menu display
- **Menu handler routing:** Menu items dispatch to action|exec|workflow handlers with attribute extraction
- **File-based execution:** exec="path.md" loads entire file and executes as instructions (prevents improvisation)
- **TTS integration:** Agents call .claude/hooks/bmad-speak.sh for voice output after responses

## Refs
- Configuration: `config.yaml:6-11` (user_name, communication_language, output_folder)
- Master agent: `agents/bmad-master.md:1-50` (activation steps, menu handlers)
- Agent XML structure: `agents/bmad-master.md:8-50` (persona, rules, handlers)

## Deps
← Imports from:
  - `.bmad/core/config.yaml` (configuration variables)
  - `.claude/hooks/` (TTS, speech integration)

→ Imported by:
  - `agents/bmad-master.md` (master orchestrator)
  - `agents/bmad-web-orchestrator.agent.xml` (web orchestration)
  - User interface (menu-driven command routing)