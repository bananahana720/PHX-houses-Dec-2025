# docs/architecture/CLAUDE.md

---
last_updated: 2025-12-03
updated_by: Claude Code
staleness_hours: 168
bmad_phase: phase_2_solutioning
---

## Purpose

System architecture documentation for the PHX Houses Analysis Pipeline, organized according to BMAD SDLC phases. This directory contains the authoritative technical architecture that would be the output of `/bmad:bmm:workflows:create-architecture`.

## BMAD SDLC Alignment

### Phase 2: Solutioning - Core Architecture

These documents define the "HOW" of the system and map to BMAD architecture workflow outputs:

| Document | BMAD Artifact Type | Status |
|----------|-------------------|--------|
| `executive-summary.md` | Architecture Overview | Current |
| `system-overview.md` | System Context | Current |
| `core-architectural-decisions.md` | ADR Summary | Current |
| `data-architecture.md` | Data Layer Design | Current |
| `component-architecture.md` | Component Design | Current |
| `multi-agent-architecture.md` | Agent Design | Current |
| `scoring-system-architecture.md` | Domain Logic | Current |
| `kill-switch-architecture.md` | Domain Logic | Current |
| `integration-architecture.md` | Integration Design | Current |
| `security-architecture.md` | Security Design | Current |
| `deployment-architecture.md` | Deployment Design | Current |

### Phase 3: Implementation - Technical Reference

Detailed implementation guides for developers during sprint execution:

| Document | Purpose | Use When |
|----------|---------|----------|
| `state-management.md` | Comprehensive state protocol | Implementing state/recovery |
| `state-management-architecture.md` | State overview (sharded) | Quick reference |
| `phase-orchestration/` | Pipeline phase details | Implementing pipeline |
| `architecture-validation.md` | Validation criteria | Pre-implementation check |

### Phase Orchestration Subdirectory

Detailed phase-by-phase implementation guides (`phase-orchestration/`):

```
phase-orchestration/
├── index.md                      # Phase overview & navigation
├── phase-dependencies.md         # Inter-phase dependencies
├── phase-0-county-data.md       # County API extraction
├── phase-05-cost-estimation.md  # Cost calculation
├── phase-1-data-collection-parallel.md  # Parallel data collection
├── phase-2a-exterior-assessment.md      # Exterior visual analysis
├── phase-2b-interior-assessment.md      # Interior visual analysis
├── phase-3-synthesis-scoring.md         # Score aggregation
├── phase-4-report-generation.md         # Deal sheet output
├── batch-processing-protocol.md         # Batch operations
└── crash-recovery-protocol.md           # Recovery procedures
```

### Reference & Appendices

Supporting materials and action tracking:

| Document | Purpose | Status |
|----------|---------|--------|
| `appendix-a-action-items.md` | Historical action items | Reference |
| `table-of-contents.md` | Legacy TOC (from sharding) | Deprecated |
| `index.md` | Auto-generated TOC | Navigation |

## Document Hierarchy

```
AUTHORITATIVE (Source of Truth)
├── executive-summary.md          ← Start here for architecture overview
├── core-architectural-decisions.md ← Key decisions and rationale
├── data-architecture.md          ← Data model definitions
├── scoring-system-architecture.md ← 605-point scoring logic
└── kill-switch-architecture.md   ← Kill-switch criteria

DETAILED REFERENCE (Implementation Guides)
├── state-management.md           ← Comprehensive state protocol (320 lines)
├── phase-orchestration/          ← Phase-by-phase execution
└── component-architecture.md     ← Service/module design

DERIVED/SHARDED (From parent doc)
├── state-management-architecture.md ← Summary view (71 lines)
├── table-of-contents.md          ← Legacy, use index.md
└── index.md                      ← Navigation (auto-generated)
```

## Key Architecture Facts

| Aspect | Value | Source Document |
|--------|-------|-----------------|
| Scoring Total | 605 points | `scoring-system-architecture.md` |
| Unicorn Tier | ≥484 pts (80%) | `scoring-system-architecture.md` |
| Contender Tier | 363-483 pts | `scoring-system-architecture.md` |
| Kill-Switch Count | 7 HARD criteria | `kill-switch-architecture.md` |
| Agent Models | Haiku + Sonnet | `multi-agent-architecture.md` |
| Storage | JSON (LIST-based) | `data-architecture.md` |
| Browser | nodriver (stealth) | `integration-architecture.md` |

## BMAD Workflow Integration

### When to Update Architecture

```yaml
trigger_update:
  - PRD changes that affect system design
  - New integration requirements
  - Scoring/kill-switch criteria changes
  - Security requirement changes

update_workflow:
  command: /bmad:bmm:workflows:validate-architecture
  agent: architect
  output: architecture-validation-report.md
```

### Pre-Implementation Check

Before Phase 3 (Implementation), run:
```bash
/bmad:bmm:workflows:implementation-readiness
```

This validates architecture docs are complete and aligned with PRD/UX.

## Document Maintenance

### Sharded Files

These files were sharded from `docs/archive/architecture.md` (original at 1500 lines):

- All files in root except `state-management.md`
- Files in `phase-orchestration/` from `docs/archive/architecture/phase-orchestration.md`

### Reassembly

To reassemble the full architecture doc:
```bash
npx @kayvan/markdown-tree-parser assemble docs/architecture/ architecture-full.md
```

## Quick Reference

```bash
# Architecture overview
Read docs/architecture/executive-summary.md

# Key decisions
Read docs/architecture/core-architectural-decisions.md

# Scoring logic
Read docs/architecture/scoring-system-architecture.md

# Pipeline phases
ls docs/architecture/phase-orchestration/

# State management
Read docs/architecture/state-management.md
```

## Related Documents

| Resource | Location | Purpose |
|----------|----------|---------|
| PRD | `docs/prd/` (sharded) | Requirements source |
| UX Design | `docs/ux-design-specification/` (sharded) | UI requirements |
| Epics | `docs/epics/` (sharded) | Implementation stories |
| Sprint Status | `docs/sprint-status/` (sharded) | Progress tracking |
| Test Design | `docs/test-design-system/` (sharded) | Quality strategy |

---

**Navigation:**
- **Parent**: `docs/`
- **BMAD Status**: `docs/bmm-workflow-status.yaml`
- **Project Root**: `CLAUDE.md`
