---
last_updated: 2025-12-05T18:00:00Z
updated_by: agent
staleness_hours: 24
---

# docs

## Purpose
Technical documentation hub for PHX Houses Analysis Pipeline. Contains architecture, specs, security audits, API refs, and generated artifacts.

## Contents
| Path | Purpose |
|------|---------|
| `architecture/` | System design (scoring-improvement-architecture.md) |
| `specs/` | Implementation specs, phase guides, reference-index.md |
| `prd/` | Product requirements document |
| `epics/` | Epic and story definitions |
| `artifacts/` | Generated reports, deal sheets, implementation notes |
| `sprint-artifacts/` | Sprint status and workflow tracking |
| `templates/` | Jinja2 HTML report templates |
| `analysis/research/` | Domain and tech research (~10 subdocs) |
| `development-guide/` | Developer onboarding |
| `AI_TECHNICAL_SPEC/` | Complete project recreation guide for AI |

## Key Documents
| Document | Purpose |
|----------|---------|
| `CONFIG_IMPLEMENTATION_GUIDE.md` | Configuration system reference |
| `SECURITY.md` | Security best practices |
| `TEST_COVERAGE_ANALYSIS/` | Comprehensive coverage report |
| `MC-Assessor-API-Documentation.md` | Maricopa County API reference |
| `CLEANUP_INDEX.md` | Cleanup task tracking |

## Tasks
- [ ] Consolidate duplicate security audit reports `P:M`
- [ ] Archive old implementation-notes in artifacts/ `P:L`
- [ ] Sync test coverage docs `P:L`

## Learnings
- **Master indexes critical**: `reference-index.md`, `CLEANUP_INDEX.md` provide navigable entry points
- **Quick refs save time**: `.txt` files faster to scan than full `.md`
- **Separate specs from artifacts**: Intent separate from outcomes

## Refs
- Scoring: `../src/phx_home_analysis/services/scoring/`
- Kill-switch: `../src/phx_home_analysis/services/kill_switch/`
- Reports: `../scripts/deal_sheets/`
- Config: `../src/phx_home_analysis/config/`

## Deps
- Parent: `../CLAUDE.md` (project root)
- Agents: `../.claude/` (agent configuration)
