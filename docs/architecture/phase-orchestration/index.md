# Phase Orchestration Protocol

## BMAD Phase 3: Implementation Reference

Detailed execution guides for each pipeline phase. Use during sprint implementation.

---

## Pipeline Flow

```
Phase 0 (County) → Phase 0.5 (Costs) → Phase 1 (Data) → Phase 2A/2B (Visual) → Phase 3 (Score) → Phase 4 (Reports)
```

---

## Phase Documents

### Prerequisites

- [Phase Dependencies](phase-dependencies.md) - Inter-phase requirements

### Data Acquisition

| Phase | Document | Purpose |
|-------|----------|---------|
| 0 | [County Data](phase-0-county-data.md) | Maricopa Assessor API extraction |
| 0.5 | [Cost Estimation](phase-05-cost-estimation.md) | Monthly cost calculations |
| 1 | [Data Collection](phase-1-data-collection-parallel.md) | Parallel listing + map extraction |

### Visual Analysis

| Phase | Document | Purpose |
|-------|----------|---------|
| 2A | [Exterior Assessment](phase-2a-exterior-assessment.md) | Roof, pool, HVAC visual |
| 2B | [Interior Assessment](phase-2b-interior-assessment.md) | Section C scoring (190 pts) |

### Synthesis & Output

| Phase | Document | Purpose |
|-------|----------|---------|
| 3 | [Synthesis & Scoring](phase-3-synthesis-scoring.md) | Score aggregation, tier assignment |
| 4 | [Report Generation](phase-4-report-generation.md) | Deal sheet creation |

### Operations

| Protocol | Document | Purpose |
|----------|----------|---------|
| Batch | [Batch Processing](batch-processing-protocol.md) | Multi-property processing |
| Recovery | [Crash Recovery](crash-recovery-protocol.md) | Resume from failures |

---

## Key Commands

```bash
# Run full pipeline
/analyze-property --all

# Single property
/analyze-property "123 Main St"

# Test mode (first 5)
/analyze-property --test
```

---

*Parent: [Architecture Index](../index.md)*
