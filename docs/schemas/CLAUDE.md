---
last_updated: 2025-12-10
updated_by: agent
---

# schemas

## Purpose
JSON schema documentation for pipeline state management (work_items.json) and property scoring (score_breakdown). Defines structure, constraints, and serialization formats for data layer persistence.

## Contents
| Document | Purpose |
|----------|---------|
| `work_items_schema.md` | work_items.json structure (phases, checkpoints, recovery, validation) |
| `score_breakdown_schema.md` | ScoreBreakdown value object (605-point system, sections, criteria) |

## Key Patterns
- **Atomic writes**: Temp file + rename pattern prevents corruption on crash
- **State machine**: Explicit transitions (pending→in_progress→completed→failed)
- **Stale detection**: 30-min timeout auto-resets hung phases
- **Validation rules**: Structural (types, fields) + semantic (status transitions)
- **Backup retention**: Last 10 timestamped backups enable rollback

## Score System
| Section | Name | Max Points |
|---------|------|------------|
| A | Location & Environment | 250 |
| B | Lot & Systems | 175 |
| C | Interior & Features | 180 |
| **Total** | | **605** |

## Refs
- Work items state: `work_items_schema.md:122-158` (enum, transitions)
- Phase checkpoints: `work_items_schema.md:365-431` (API contract)
- Score breakdown: `score_breakdown_schema.md:22-42` (Score value object)
- Implementation: `../../src/phx_home_analysis/repositories/`

## Deps
← imports: none (documentation)
→ used by: WorkItemsRepository, orchestrators, validation
