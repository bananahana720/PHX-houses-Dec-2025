# 7. Strategic Recommendations

### Top 5 Immediate Actions (This Week)

| Priority | Action | Effort | Impact | Dependencies |
|----------|--------|--------|--------|--------------|
| **1** | Add solar lease as HARD kill-switch | 2 hours | CRITICAL | Update kill_switch.py, constants.py |
| **2** | Integrate FEMA NFHL flood zone API | 4 hours | HIGH | New script: extract_flood_zone.py |
| **3** | Recalibrate HVAC scoring for Arizona lifespan | 2 hours | HIGH | Update scoring_weights.py |
| **4** | Add pool cost factor to cost efficiency | 2 hours | MEDIUM | Update cost calculations |
| **5** | Add water service area verification | 4 hours | MEDIUM | ADWR DAWS list integration |

### Top 5 Medium-Term Improvements (This Month)

| Priority | Action | Effort | Impact | Dependencies |
|----------|--------|--------|--------|--------------|
| **1** | Integrate WalkScore API | 8 hours | HIGH | API key, scoring integration |
| **2** | Add Phoenix crime data integration | 8 hours | MEDIUM | Data pipeline, scoring integration |
| **3** | Implement foundation assessment factor | 16 hours | MEDIUM | Visual assessment rubric |
| **4** | Add septic system detection | 8 hours | MEDIUM | County database query |
| **5** | Implement owned solar bonus scoring | 4 hours | LOW | Detection logic |

### Risk Factors to Monitor

**Market Risks:**

| Risk | Probability | Impact | Monitoring Action |
|------|-------------|--------|-------------------|
| Interest rate spike >7.5% | Medium | High | Weekly Freddie Mac PMMS check |
| Phoenix market correction | Medium | Medium | Monthly Zillow HPI tracking |
| HOA inventory squeeze | Low | Medium | Quarterly listing count check |
| Solar company bankruptcies | High | Medium | Track major provider status |

**Technical Risks:**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| nodriver detection (~6 months) | High | High | Budget for commercial scraping solution |
| Zillow/Redfin ToS enforcement | Medium | Critical | Maintain commercial data provider backup |
| Proxy IP reputation degradation | Medium | Medium | Rotate providers, premium tiers |
| API rate limit changes | Low | Low | Implement adaptive throttling |

**Regulatory Risks:**

| Risk | Probability | Impact | Monitoring Action |
|------|-------------|--------|-------------------|
| Arizona water restrictions expansion | Medium | High | Track ADWR announcements |
| HOA law changes (fee caps, etc.) | Low | Low | Annual legislative review |
| Solar lease transfer law changes | Medium | Low | November 2025 AAR form release |

---
