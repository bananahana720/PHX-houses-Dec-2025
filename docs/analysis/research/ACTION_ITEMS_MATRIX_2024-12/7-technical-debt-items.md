# 7. Technical Debt Items

Items that improve code quality without adding features:

| ID | Description | Effort | Benefit |
|----|-------------|--------|---------|
| TD-01 | Consolidate scoring constants between `constants.py` and `scoring_weights.py` | 2d | Single source of truth |
| TD-02 | Add type hints to all service methods | 3d | IDE support, fewer bugs |
| TD-03 | Increase test coverage for scoring strategies (currently ~60%) | 4d | Regression prevention |
| TD-04 | Refactor extraction services to use common interface | 2d | Easier to add new sources |
| TD-05 | Add Pydantic schemas for all API responses | 2d | Type safety, validation |
| TD-06 | Document all constants with source citations | 1d | Traceability |
| TD-07 | Add pre-commit hooks for code quality | 1d | Consistent formatting |
| TD-08 | Migrate from print() to structured logging | 2d | Better observability |

**Technical Debt vs Feature Work:**
- Current technical debt: ~17 days
- Recommendation: Allocate 20% of sprint capacity to debt (1 day/week)

---
