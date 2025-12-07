# PHX Houses Analysis Pipeline - System Architecture

## BMAD Phase 2: Solutioning Architecture

This directory contains the authoritative system architecture for the PHX Houses Analysis Pipeline, organized for BMAD SDLC workflow integration.

---

## Quick Start

| Goal | Document |
|------|----------|
| Understand the system | [Executive Summary](executive-summary.md) |
| See key decisions | [Core Architectural Decisions](core-architectural-decisions.md) |
| Learn scoring logic | [Scoring System Architecture](scoring-system-architecture.md) |
| Understand kill-switches | [Kill-Switch Architecture](kill-switch-architecture.md) |
| Review pipeline phases | [Phase Orchestration](phase-orchestration/index.md) |

---

## Core Architecture Documents

### System Design

- [Executive Summary](executive-summary.md) - Architecture overview & key goals
- [System Overview](system-overview.md) - High-level system context
- [Core Architectural Decisions](core-architectural-decisions.md) - ADR summary

### Domain Architecture

- [Scoring System Architecture](scoring-system-architecture.md) - 605-point weighted scoring
- [Kill-Switch Architecture](kill-switch-architecture.md) - 5 HARD + 4 SOFT criteria filtering

### Technical Architecture

- [Data Architecture](data-architecture.md) - JSON-based storage design
- [Component Architecture](component-architecture.md) - Service/module design
- [Multi-Agent Architecture](multi-agent-architecture.md) - Haiku + Sonnet agents
- [Integration Architecture](integration-architecture.md) - External APIs & browsers
- [State Management Architecture](state-management-architecture.md) - State file overview

### Infrastructure

- [Security Architecture](security-architecture.md) - Security controls
- [Deployment Architecture](deployment-architecture.md) - Deployment strategy

### Validation

- [Architecture Validation](architecture-validation.md) - Validation criteria

---

## Implementation Guides

### Pipeline Orchestration

Detailed phase execution guides: [Phase Orchestration](phase-orchestration/index.md)

| Phase | Document |
|-------|----------|
| Dependencies | [Phase Dependencies](phase-orchestration/phase-dependencies.md) |
| Phase 0 | [County Data](phase-orchestration/phase-0-county-data.md) |
| Phase 0.5 | [Cost Estimation](phase-orchestration/phase-05-cost-estimation.md) |
| Phase 1 | [Data Collection](phase-orchestration/phase-1-data-collection-parallel.md) |
| Phase 2A | [Exterior Assessment](phase-orchestration/phase-2a-exterior-assessment.md) |
| Phase 2B | [Interior Assessment](phase-orchestration/phase-2b-interior-assessment.md) |
| Phase 3 | [Synthesis & Scoring](phase-orchestration/phase-3-synthesis-scoring.md) |
| Phase 4 | [Report Generation](phase-orchestration/phase-4-report-generation.md) |
| Batch | [Batch Processing](phase-orchestration/batch-processing-protocol.md) |
| Recovery | [Crash Recovery](phase-orchestration/crash-recovery-protocol.md) |

### State Management

- [State Management Protocol](state-management.md) - Comprehensive 320-line guide

---

## Reference

- [Appendix A: Action Items](appendix-a-action-items.md) - Historical actions
- [CLAUDE.md](CLAUDE.md) - Directory documentation & BMAD alignment

---

## Key Facts

| Metric | Value |
|--------|-------|
| Total Scoring Points | 605 |
| Unicorn Tier Threshold | ≥484 (80%) |
| Contender Tier Threshold | 363-483 (60-80%) |
| Kill-Switch Criteria | 5 HARD + 4 SOFT |
| Agent Models | Haiku (extraction) + Sonnet (vision) |
| Storage Format | JSON (LIST-based) |

---

*Generated from sharding of `architecture.md` (1500 lines) - Original archived at `docs/archive/architecture.md`*
