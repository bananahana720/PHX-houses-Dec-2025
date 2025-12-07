---
last_updated: 2025-12-07T22:37:37Z
updated_by: agent
staleness_hours: 24
flags: []
---
# scripts/lib

## Purpose
Compatibility shims and legacy support modules for transitioning scripts to service layer architecture.

## Contents
| Path | Purpose |
|------|---------|
| `kill_switch.py` | Compatibility shim wrapping `services/kill_switch/`; delegates to service layer |
| `__init__.py` | Package initialization (empty) |

## Key Patterns
- **Deprecation layer**: Provides backward compatibility while migration completes
- **Delegation**: Re-exports service layer classes/functions without duplication
- **Zero logic**: No business logic; pure wrapper for import compatibility

## Tasks
- [ ] Remove `kill_switch.py` after all scripts migrated to direct service imports `P:M`
- [ ] Verify no direct imports from `scripts.lib` in codebase `P:M`

## Learnings
- **Compatibility shims**: Enable gradual migration without breaking existing scripts
- **Single source of truth**: Service layer at `src/phx_home_analysis/services/kill_switch/` is canonical
- **Scheduled removal**: This directory planned for deletion post-migration

## Refs
- Service layer: `src/phx_home_analysis/services/kill_switch/`
- Consumer scripts: `scripts/phx_home_analyzer.py`, legacy deal sheets

## Deps
← imports: `src/phx_home_analysis/services/kill_switch/`
→ used by: `scripts/phx_home_analyzer.py` (legacy), deprecated consumers
