---
last_updated: 2025-12-10
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
| `artifacts/` | Generated reports, deal sheets, research |
| `epics/` | Epic definitions (E1-E7) |
| `sprint-change-proposal-2025-12-10.md` | Active sprint change proposal |
| `SECURITY.md` | Security best practices |

## Key Patterns
- **Dual CLAUDE.md structure**: Root docs/CLAUDE.md + child subdirectory CLAUDE.md files
- **Artifacts vs specs separation**: Intent (specs/) vs outcomes (artifacts/)
- **Quick ref files**: `.txt` files for fast scanning (e.g., SECURITY_QUICK_REFERENCE.txt)
- **Master indexes**: reference-index.md, CLEANUP_INDEX.md provide navigation

## Tasks
- [x] Complete Epic 3 retrospective `P:H`
- [x] Complete P1-P6 research tasks `P:H`
- [x] Implement E4.S0 infrastructure setup `P:H`
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
