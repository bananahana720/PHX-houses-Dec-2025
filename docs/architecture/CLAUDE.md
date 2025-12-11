---
last_updated: 2025-12-10
updated_by: agent
---

# docs/architecture

## Purpose
System architecture documentation for PHX Houses pipeline, organized by domain concerns: data flow, kill-switches, scoring, state management, and integration maps.

## Contents
| Document | Purpose |
|----------|---------|
| `executive-summary.md` | Architecture overview (start here) |
| `core-architectural-decisions.md` | Key decisions and rationale |
| `component-architecture.md` | Service layer component breakdown |
| `integration-map-scoring.md` | Data flows between kill-switch, scoring, reporting |
| `data-architecture.md` | Data model definitions and lifecycle |
| `data-source-architecture.md` | Multi-source integration (Assessor, CSV, Web, AI) |
| `data-source-integration-architecture.md` | Source-specific patterns and reconciliation |
| `scoring-system-architecture.md` | 605-point scoring logic |
| `kill-switch-architecture.md` | 5 HARD + 4 SOFT kill-switch criteria |
| `state-management.md` | Comprehensive state protocol and recovery |

## Key Facts
| Aspect | Value |
|--------|-------|
| Scoring Total | 605 points (Location 250 + Systems 175 + Interior 180) |
| Kill-Switches | 5 HARD (instant fail) + 4 SOFT (severity accumulation) |
| Agent Models | Haiku 4.5 (extraction) + Opus 4.5 (vision) |
| Data Storage | JSON (state management), CSV (listings) |
| Browser Tech | nodriver (stealth), playwright (fallback) |

## Key Patterns
- **Data flow**: Load → Kill-switch → Score → Report
- **State machine**: Phase lifecycle with checkpoints and recovery
- **Multi-source**: Assessor (0.95) + CSV (0.90) + Web (0.75) + AI (0.70)
- **Atomic operations**: JSON with temp+rename for crash safety

## Refs
- PRD: `../prd/`
- Epics: `../epics/`
- Code: `../../src/phx_home_analysis/`

## Deps
← imports: PRD requirements
→ used by: implementation teams, agents, services
