# Priority Matrix

### P0: Fix This Week (Blocking/Critical)

| Issue | Severity | Effort | Impact |
|-------|----------|--------|--------|
| Scoring display bug (500→600) | Critical | 1 day | User trust, decision accuracy |
| Hardcoded 2024 new-build filter | Critical | 4 hours | Time bomb (fails Jan 2025) |
| County data overwrites manual research | High | 2 days | Data loss, no audit trail |

### P1: Fix This Month (Important)

| Issue | Severity | Effort | Impact |
|-------|----------|--------|--------|
| Dead code removal (10 items) | Medium | 2 days | Maintainability, confusion |
| Duplicate schema definitions (3 models) | Medium | 1 day | DRY violation, sync issues |
| Unused LineageTracker infrastructure | High | 3 days | False sense of validation |
| Field name mismatches (county↔enrichment) | High | 2 days | 100% missing rates |
| Hardcoded buyer criteria | Medium | 2 days | Inflexibility |

### P2: Plan for Next Quarter (Nice-to-Have)

| Issue | Severity | Effort | Impact |
|-------|----------|--------|--------|
| Schema naming consistency (8 categories) | Low | 1 week | Developer experience |
| Orphaned metadata fields (19+) | Low | 3 days | Schema completeness |
| Dead code removal (11 medium-confidence) | Low | 2 days | Maintainability |
| Unused ArizonaContext fields | Low | 1 day | Configuration clarity |
| Hardcoded value zone thresholds | Low | 4 hours | Flexibility |

---
