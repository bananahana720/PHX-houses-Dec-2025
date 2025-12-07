---
last_updated: 2025-12-06T12:00:00Z
updated_by: agent
staleness_hours: 168
bmad_phase: phase_2_solutioning
---
# docs/architecture

## Purpose
System architecture documentation for PHX Houses pipeline, organized by BMAD SDLC phases.

## Contents
| Document | Purpose |
|----------|---------|
| `executive-summary.md` | Architecture overview (start here) |
| `core-architectural-decisions.md` | Key decisions and rationale |
| `data-architecture.md` | Data model definitions |
| `scoring-system-architecture.md` | 605-point scoring logic |
| `kill-switch-architecture.md` | 7 HARD kill-switch criteria |
| `multi-agent-architecture.md` | Agent design (Haiku 4.5 + Opus 4.5) |
| `state-management.md` | Comprehensive state protocol |
| `phase-orchestration/` | Phase-by-phase implementation guides |

## Key Architecture Facts
| Aspect | Value |
|--------|-------|
| Scoring Total | 605 points |
| Unicorn Tier | >=484 pts (80%) |
| Contender Tier | 363-483 pts |
| Kill-Switch Count | 7 HARD criteria |
| Agent Models | Haiku 4.5 + Opus 4.5 |
| Storage | JSON (LIST-based) |
| Browser | nodriver (stealth) |

## Document Hierarchy
- **Authoritative**: executive-summary, core-decisions, data, scoring, kill-switch
- **Reference**: state-management, phase-orchestration/, component-architecture
- **Derived**: state-management-architecture (summary), index.md

## Quick Commands
```bash
Read docs/architecture/executive-summary.md      # Overview
Read docs/architecture/scoring-system-architecture.md  # Scoring
ls docs/architecture/phase-orchestration/        # Pipeline phases
```

## Refs
- PRD: `../prd/`
- Epics: `../epics/`
- Sprint Status: `../sprint-status/`

## Deps
<- imports: PRD requirements
-> used by: implementation teams, agents
