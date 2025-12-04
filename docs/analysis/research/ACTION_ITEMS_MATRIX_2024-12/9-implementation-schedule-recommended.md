# 9. Implementation Schedule (Recommended)

### Sprint 1 (Week 1-2): Foundation
**Goal:** Unblock batch processing + add explanations

| Day | Actions | Owner |
|-----|---------|-------|
| 1 | P0-08, P1-02 (quick wins) | Config |
| 2-3 | P0-02 (job queue design + implementation) | Infra |
| 4-5 | P0-03 (progress visibility) | Infra |
| 6-7 | P0-04 (scoring explanations) | Core |
| 8 | P0-05 (kill-switch explanations) | Core |
| 9-10 | P0-01 (solar kill-switch) + P1-01 (solar bonus) | Config+Core |

**Sprint 1 Deliverables:**
- [ ] Job queue operational (8 properties in <10 min)
- [ ] Progress visible in work_items.json
- [ ] Score explanations in English
- [ ] Solar lease detection and handling

### Sprint 2 (Week 3-4): Data Quality + APIs
**Goal:** Lineage tracking + critical API integrations

| Day | Actions | Owner |
|-----|---------|-------|
| 1-4 | P0-06 (field lineage) | Core |
| 5-7 | P1-06 (Phoenix crime API) | API |
| 8-10 | P1-07 (FEMA flood API) | API |

**Sprint 2 Deliverables:**
- [ ] All enriched fields have lineage tracking
- [ ] Crime data from Phoenix Open Data
- [ ] Flood zones from FEMA NFHL

### Sprint 3 (Week 5-6): Scoring Enhancements
**Goal:** Roof material scoring + infrastructure APIs

| Day | Actions | Owner |
|-----|---------|-------|
| 1-2 | P1-04 (roof material differentiation) | Core |
| 3-4 | P1-05 (underlayment tracking) | Core |
| 5-7 | P1-18 (Maricopa GIS) | API |
| 8-10 | P1-10, P2-08 (retry + circuit breaker) | Infra |

**Sprint 3 Deliverables:**
- [ ] Roof scoring includes material type
- [ ] Tile roofs track underlayment age
- [ ] GIS validation of lot sizes
- [ ] Robust retry with circuit breaker

### Sprint 4 (Week 7-8): Configuration + Polish
**Goal:** Externalize config + remaining P1 items

| Day | Actions | Owner |
|-----|---------|-------|
| 1-2 | P1-14 (externalize kill-switch config) | Config |
| 3-4 | P1-15 (scoring weight versioning) | Config |
| 5-6 | P1-11 (cost breakdown in reports) | Core |
| 7-8 | P1-08 (equipment costs in deal sheets) | Reports |
| 9-10 | P1-09 (proxy integration) | Infra |

**Sprint 4 Deliverables:**
- [ ] Kill-switch criteria in YAML
- [ ] Scoring versions tracked per run
- [ ] Cost breakdown visible in reports
- [ ] Equipment replacement budgets in deal sheets
- [ ] Proxy rotation working

---
