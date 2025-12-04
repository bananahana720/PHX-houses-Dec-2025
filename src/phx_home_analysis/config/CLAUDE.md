---
last_updated: 2025-12-04
updated_by: main
staleness_hours: 24
flags: []
---
# config

## Purpose
Configuration module for PHX home analysis pipeline. Provides scoring weights (605-point system), kill-switch buyer criteria, file paths, Arizona-specific context, and YAML-based configuration loading with backward compatibility.

## Contents
| Path | Purpose |
|------|---------|
| `__init__.py` | Package exports; docstring shows 250pts Location section (updated) |
| `scoring_weights.py` | 605-point system definition (Section A: 250, B: 175, C: 180) |
| `constants.py` | Kill-switch thresholds, file paths, buyer profile constants |
| `settings.py` | Dataclasses: `AppConfig`, `BuyerProfile`, `ProjectPaths`, `ArizonaContext` |
| `loader.py` | ConfigLoader for YAML-based configuration; `get_config()` singleton |
| `README.md` | Module documentation |

## Tasks
- [x] Docstring updated to show 250pts (Location section clarified)
- [ ] Migrate deprecated dataclasses to YAML config P:M

## Learnings
- Location section correctly 250pts (not 230), documented in __init__.py line 15
- ConfigLoader pattern supports YAML with validation; legacy dataclasses available for backward compatibility

## Refs
- Docstring: `__init__.py:1-20`
- Scoring weights: `scoring_weights.py:1-50`
- Kill-switch constants: `constants.py:1-89`
- ConfigLoader: `loader.py:1-100`

## Deps
← Imports from:
  - `phx_home_analysis.domain` (Property, Score enums)
  - `pydantic`, `yaml`, `pathlib` (std lib)

→ Imported by:
  - `phx_home_analysis.__init__.py` (package root)
  - `services/`, `pipeline/`, scripts
  - Tests (unit/integration)