---
last_updated: 2025-12-07T22:37:45Z
updated_by: agent
staleness_hours: 24
flags: []
---
# docs

## Purpose
Technical documentation hub for PHX Houses Analysis Pipeline containing architecture specs, product requirements, security audits, API references, and sprint artifacts.

## Contents
| Path | Purpose |
|------|---------|
| `prd/` | Product requirements (executive summary, scope, success criteria) |
| `specs/` | Implementation specs, phase guides, reference index |
| `schemas/` | JSON schema docs (work_items, enrichment_data) |
| `sprint-artifacts/` | Sprint status, stories, tech specs |
| `architecture/` | System design, schema evolution, consistency audits |
| `artifacts/` | Generated reports, deal sheets, implementation notes |
| `CONFIG_IMPLEMENTATION_GUIDE.md` | Configuration system reference |
| `SECURITY.md` | Security best practices |
| `MC-Assessor-API-Documentation.md` | Maricopa County API reference |

## Key Patterns
- **Dual CLAUDE.md structure**: Root docs/CLAUDE.md + child subdirectory CLAUDE.md files
- **Artifacts vs specs separation**: Intent (specs/) vs outcomes (artifacts/)
- **Quick ref files**: `.txt` files for fast scanning (e.g., SECURITY_QUICK_REFERENCE.txt)
- **Master indexes**: reference-index.md, CLEANUP_INDEX.md provide navigation

## Tasks
- [ ] Consolidate duplicate security audit reports `P:M`
- [ ] Archive old implementation-notes in artifacts/ `P:L`
- [ ] Sync test coverage docs with latest run `P:L`
- [ ] Update schema docs with enrichment_data.json `P:M`

## Learnings
- **Schema docs prevent corruption**: work_items_schema.md explains state machine, prevents invalid transitions
- **Tech specs bridge gap**: Convert story requirements to implementation guidance
- **Sprint artifacts track reality**: workflow-status.yaml, sprint-status.yaml show actual progress

## Refs
- Scoring: `../src/phx_home_analysis/services/scoring/`
- Kill-switch: `../src/phx_home_analysis/services/kill_switch/`
- Reports: `../scripts/deal_sheets/`
- Config: `../src/phx_home_analysis/config/`

## Deps
← imports: none (documentation hub)
→ used by: agents, commands, developers
