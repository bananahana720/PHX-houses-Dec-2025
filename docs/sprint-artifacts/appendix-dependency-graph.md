# Appendix: Dependency Graph

```
Sprint 0 (ARCH items)
    │
    ▼
Sprint 1: E1 (Foundation)
    ├── E1.S1 (Config) ──────────────────────────────────┐
    │       │                                            │
    │       ▼                                            │
    ├── E1.S2 (Storage) ─────────────────────────────────┤
    │       │                                            │
    │       ├──────────────────────┐                     │
    │       ▼                      ▼                     │
    ├── E1.S3 (Provenance)    E1.S4 (Checkpoint)         │
    │                              │                     │
    │                              ▼                     │
    │                         E1.S5 (Resume)             │
    │                              │                     │
    │                              ▼                     │
    └─────────────────────── E1.S6 (Error Recovery) ◄────┘
                                   │
                                   ▼
Sprint 2: E2 (Data Acquisition)
    ├── E2.S7 (API Infrastructure) ◄───────────────────── CRITICAL PATH
    │       │
    │       ├────────┬────────┬────────┐
    │       ▼        ▼        ▼        ▼
    ├── E2.S2    E2.S3    E2.S5    E2.S6
    │   (County) (Zillow) (Maps)   (Schools)
    │               │
    │               ▼
    └────────── E2.S4 (Images)
                   │
                   ▼
Sprint 3: E3+E4 (Kill-Switch & Scoring)
    ├── E3.S1 (HARD Criteria) ────────────────────────────┐
    │       │                                             │
    │       ▼                                             │
    ├── E3.S2 (SOFT System) ──► E3.S3 (Verdict)           │
    │                               │                     │
    │                               ▼                     │
    │                          E3.S4 (Explanations)       │
    │                                                     │
    └── E4.S1 (Score Calc) ◄────────────────────────────── CRITICAL PATH
            │
            ├────────────────────────┐
            ▼                        ▼
        E4.S2 (22 Strategies)   E4.S3 (Tiers)
            │                        │
            └────────┬───────────────┘
                     ▼
                E4.S4 (Breakdown) ──► E4.S5 (Re-score) ──► E4.S6 (Delta)
                                   │
                                   ▼
Sprint 4: E5 (Pipeline)
    ├── E5.S1 (Orchestrator) ◄──────────────────────────── CRITICAL PATH
    │       │
    │       ▼
    ├── E5.S2 (Phase Coord) ──► E5.S3 (Agent Spawn)
    │                               │
    │                               ▼
    ├── E5.S4 (Prerequisite Validation)
    │       │
    │       ▼
    ├── E5.S5 (Parallel Phase 1) ──► E5.S6 (Aggregation)
    │
    ▼
Sprint 5: E6 (Risk Intelligence)
    ├── E6.S1 (Image Assessment)
    │       │
    │       ├────────────────────────┐
    │       ▼                        ▼
    ├── E6.S2 (Warnings) ◄──── E6.S5 (Foundation)
    │       │
    │       ▼
    ├── E6.S3 (Consequence) ──► E6.S4 (Confidence) ──► E6.S6 (HVAC)
    │
    ▼
Sprint 6: E7 (Reports)
    ├── E7.S1 (Deal Sheet HTML) ◄──────────────────────── CRITICAL PATH
    │       │
    │       ▼
    ├── E7.S2 (Content Structure) ──► E7.S3 (Narratives)
    │
    ├── E7.S4 (Visualizations)
    │
    ├── E7.S5 (Checklists)
    │
    └── E7.S6 (Regeneration)
```

---

*Last Updated: 2025-12-03*
*Next Review: Sprint 0 completion*
