# Executive Summary

The PHX Houses codebase exhibits a well-organized domain-driven architecture but has accumulated significant technical debt through code duplication and oversized modules. This plan addresses the highest-impact refactoring opportunities.

### Key Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Kill-switch implementations | 3 locations | 1 location |
| Largest script file | 1,057 lines | <300 lines |
| Orchestrator file size | 693 lines | <300 lines |
| Code duplication (scoring) | ~150 lines | 0 lines |
| Test coverage | Good | Maintained |

### ROI Assessment

| Change | Business Value | Effort | Risk | Priority |
|--------|---------------|--------|------|----------|
| Consolidate kill-switches | 9/10 | 2-3 hours | Low | CRITICAL |
| Refactor deal_sheets.py | 7/10 | 4-6 hours | Medium | HIGH |
| Split orchestrator | 6/10 | 4-6 hours | Medium | HIGH |
| Unify scoring functions | 5/10 | 3-4 hours | Low | MEDIUM |

---
