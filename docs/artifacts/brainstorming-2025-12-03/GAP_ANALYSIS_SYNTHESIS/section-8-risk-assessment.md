# Section 8: Risk Assessment

### Risk 1: Image Pipeline Redesign Impacts Existing Functionality
**Probability**: MEDIUM
**Impact**: CRITICAL (blocks all batch processing)
**Mitigation**:
- Design job queue as new layer, don't refactor existing orchestrator
- Use feature flags to enable/disable job queue gradually
- Comprehensive integration tests before rollout

### Risk 2: Explanation Generation Creates Inconsistency
**Probability**: LOW
**Impact**: MEDIUM (user confusion)
**Mitigation**:
- Use templating for explanations (consistent text)
- Test explanations against expected scores (regression tests)
- User acceptance testing with at least 20 properties

### Risk 3: Data Lineage Backfill Reveals Quality Issues
**Probability**: HIGH
**Impact**: MEDIUM (surprise data problems)
**Mitigation**:
- Expect to find gaps; plan for backfill reconciliation
- Create "unknown source" fallback for unmapped data
- Run lineage backfill in staging first

### Risk 4: Hard-Coded Tests Break When Configuration Changes
**Probability**: MEDIUM
**Impact**: MEDIUM (test maintenance burden)
**Mitigation**:
- Use parameterized tests with config fixtures
- Test both default and custom configurations
- Document test assumptions in code comments

---
