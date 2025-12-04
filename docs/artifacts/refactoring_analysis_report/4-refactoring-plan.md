# 4. Refactoring Plan

### Phase 1: Immediate Fixes (High Impact, Low Effort)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Extract shared data loaders | All | 2 hrs | HIGH |
| Centralize configuration | All | 2 hrs | HIGH |
| Fix value_spotter.py global execution | 1 | 0.5 hrs | MEDIUM |
| Add type hints to missing functions | 5 | 1 hr | MEDIUM |

### Phase 2: Structural Improvements (Medium Effort)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Extract HTML templates to files | 3 | 4 hrs | HIGH |
| Implement Repository pattern | All | 4 hrs | HIGH |
| Create RiskLevel enum | 1 | 1 hr | MEDIUM |
| Decompose long functions | 4 | 3 hrs | HIGH |

### Phase 3: Architecture Enhancement (Higher Effort)

| Task | Files | Effort | Impact |
|------|-------|--------|--------|
| Implement Strategy pattern for scoring | 1 | 4 hrs | MEDIUM |
| Create plugin system for kill switches | 1 | 2 hrs | LOW |
| Add comprehensive error handling | All | 3 hrs | MEDIUM |
| Add unit tests (target 80% coverage) | All | 8 hrs | HIGH |

---
