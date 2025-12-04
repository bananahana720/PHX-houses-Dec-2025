# 5. Risk Register

| Action ID | Risk | Probability | Impact | Mitigation | Rollback Plan |
|-----------|------|-------------|--------|------------|---------------|
| P0-01 | Solar lease data unavailable in listings | Medium | High | Add "unknown" handling; use disclosure detection | Skip scoring if uncertain |
| P0-02 | RQ integration complexity | Low | Critical | Start simple; expand incrementally | Fall back to sequential processing |
| P0-04 | Explanations inconsistent with scores | Medium | Medium | Template-based generation; regression tests | Disable explanations, show raw scores |
| P0-06 | Lineage tracking performance overhead | Medium | Low | Batch writes; async logging | Make lineage optional via config |
| P1-04 | Roof material detection inaccurate | Medium | Medium | Conservative defaults; manual override | Fall back to age-only scoring |
| P1-06 | Phoenix crime API unavailable (noted Sep 2025) | High | Medium | Use FBI CDE as fallback | Default to city-level averages |
| P1-07 | FEMA API rate limiting | Low | Low | Cache responses; batch requests | Use cached zone data |
| P1-09 | Proxy costs exceed budget | Low | Medium | Start with IPRoyal; upgrade if needed | Direct requests with delays |
| P1-14 | Config migration breaks existing logic | Medium | High | Comprehensive test coverage; feature flags | Revert to hardcoded constants |
| P2-21 | Solar ROI calculation complexity | Medium | Low | Simplify to payback period only | Show raw data without calculation |

---
