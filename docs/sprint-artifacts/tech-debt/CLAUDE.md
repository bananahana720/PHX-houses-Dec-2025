---
last_updated: 2025-12-07T19:00:00Z
updated_by: agent
staleness_hours: 168
---
# tech-debt

## Purpose
Tracks technical debt discovered during validation audits and retrospectives. Each ticket documents cleanup work with checklists and line references.

## Contents
| File | Purpose |
|------|---------|
| `kill-switch-consistency-cleanup.md` | 18+ files with old "7/8 HARD" → "5 HARD + 4 SOFT" |

## Ticket Format
- Background context
- Correct values/patterns
- File checklist with line numbers
- Acceptance criteria

## Priority Levels
| Priority | Timeline |
|----------|----------|
| HIGH | Before next epic |
| MEDIUM | During epic |
| LOW | Backlog |

## Refs
- Sprint: `../sprint-status.yaml`
- Stories: `../stories/`

## Deps
← Created by: Validation audits, retrospectives
→ Consumed by: Sprint planning
