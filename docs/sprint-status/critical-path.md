# Critical Path

The following stories form the critical path and must be completed in sequence:

```
E1.S1 (Config)
    → E1.S2 (Storage)
        → E1.S6 (Error Recovery)
            → E2.S7 (API Infrastructure)
                → E4.S1 (Scoring Engine)
                    → E5.S1 (Pipeline CLI)
                        → E7.S1 (Deal Sheets)
```

| Order | Story ID | Title | Reason |
|-------|----------|-------|--------|
| 1 | E1.S1 | Configuration System Setup | Foundation for all config loading |
| 2 | E1.S2 | Property Data Storage Layer | Foundation for all data persistence |
| 3 | E1.S6 | Transient Error Recovery | Required for reliable API integration |
| 4 | E2.S7 | API Integration Infrastructure | Foundation for all external API calls |
| 5 | E4.S1 | Three-Dimension Score Calculation | Core scoring engine |
| 6 | E5.S1 | Pipeline Orchestrator CLI | Primary user interface for pipeline |
| 7 | E7.S1 | Deal Sheet HTML Generation | Primary output deliverable |

---
