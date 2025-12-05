---
last_updated: 2025-12-05T15:10:00Z
updated_by: agent
staleness_hours: 24
line_target: 80
flags: []
---
# .claude/plans

## Purpose
Multi-phase plan files documenting bug remediation and feature implementation workflows across epics. Tracks discovery → design → implementation → validation with checkpoints for crash recovery.

## Contents
| File | Purpose |
|------|---------|
| `memoized-brewing-gizmo.md` | E2.S4 image extraction: search result contamination bug, content-addressed storage, caching strategy |

## Key Patterns
- **Multi-phase workflow**: Discovery → Design → Implementation → Validation stages with clear acceptance criteria
- **Checkpoint recovery**: Atomic state files (extraction_state.json) enable resumable operations after crashes
- **Phase gates**: Validation before spawning dependent phases (Phase 1 → Phase 2 prerequisites)
- **Lineage tracking**: property_hash, created_by_run_id, content_hash enable full audit trail

## Tasks
- [ ] Document plan file naming conventions and structure `P:M`
- [ ] Create plan templates for E3 features `P:L`
- [ ] Archive completed E2 plans with learned lessons `P:L`

## Learnings
- **E2.S4 root cause**: Image extraction contaminated by search results; fixed via selector validation
- **Stealth extraction**: nodriver 0.48 required for PerimeterX anti-bot bypass (not Playwright)
- **State persistence**: Atomic writes (tempfile + os.replace()) prevent data corruption on crash
- **Phase dependencies**: Always validate prerequisites before Phase 2 spawn to avoid wasted resources

## Refs
- Memoized plan: `memoized-brewing-gizmo.md:1-200`
- State management: `../skills/state-management/SKILL.md:1-150`
- Listing browser agent: `../agents/listing-browser.md:1-200`
- Orchestrator: `src/phx_home_analysis/services/image_extraction/orchestrator.py:1-100`

## Deps
← imports from: BMAD workflow orchestration, Phase gates, Epic planning
→ used by: Epic implementation, Agent execution, Script workflows
