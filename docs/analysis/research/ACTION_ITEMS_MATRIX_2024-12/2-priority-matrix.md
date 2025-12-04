# 2. Priority Matrix

### P0 - Critical (Do First)

These items address fundamental gaps that block production use or buyer decision accuracy.

| ID | Action | Category | Effort | Dependencies | Files Affected | Research Source |
|----|--------|----------|--------|--------------|----------------|-----------------|
| **P0-01** | Add Solar Lease as kill-switch criterion (HARD or SOFT 2.5) | CONFIG+CODE | 2d | None | `constants.py`, `kill_switch/criteria.py`, `schemas.py` | Market-Beta |
| **P0-02** | Implement job queue architecture for image extraction | CODE | 5d | None | `scripts/extract_images.py`, new `jobs/` module | Gap IP-01 |
| **P0-03** | Add progress visibility for long-running extractions | CODE | 2d | P0-02 | `extract_images.py`, `work_items.json` | Gap IP-04 |
| **P0-04** | Add scoring explanations (reasoning generation) | CODE | 3d | None | `services/scoring/scorer.py`, new `reasoning.py` | Gap XT-09 |
| **P0-05** | Add kill-switch verdict explanations with severity breakdown | CODE | 1d | None | `services/kill_switch/filter.py`, `verdict.py` | Gap XT-10 |
| **P0-06** | Implement field-level data lineage tracking | CODE | 4d | None | New `lineage/` service, `enrichment_data.json` schema | Gap XT-01 |
| **P0-07** | Add foundation/structural assessment service | CODE | 5d | None | New `services/foundation/` module | Gap VB-03, Domain-Alpha |
| **P0-08** | Update pool monthly cost to $250-400 range | CONFIG | 0.5d | None | `constants.py` | Market-Beta |

**P0 Critical Path:**
```
P0-02 (job queue) → P0-03 (progress visibility)
P0-04 (scoring explanations) ← P0-05 (kill-switch explanations)
All others: Independent
```

---

### P1 - High Priority

High-impact improvements that significantly enhance accuracy or user experience.

| ID | Action | Category | Effort | Dependencies | Files Affected | Research Source |
|----|--------|----------|--------|--------------|----------------|-----------------|
| **P1-01** | Add Owned Solar bonus (+5 pts to systems) | CONFIG+CODE | 1d | None | `scoring_weights.py`, new `solar_scorer.py` | Market-Beta |
| **P1-02** | Update commute cost baseline to $0.67-0.70/mile | CONFIG | 0.5d | None | `constants.py` | Market-Alpha |
| **P1-03** | Add septic system SOFT kill-switch (severity 2.5) - currently sewer only | CONFIG | 0.5d | None | `constants.py` - already has SEVERITY_WEIGHT_SEWER | Domain-Gamma |
| **P1-04** | Add roof material type differentiation (tile vs shingle scoring) | CODE | 2d | None | `services/scoring/strategies/systems.py` | Domain-Alpha |
| **P1-05** | Add tile roof underlayment age tracking (25-30 year lifespan) | CODE | 2d | P1-04 | `schemas.py`, `scoring/strategies/systems.py` | Domain-Alpha |
| **P1-06** | Integrate Phoenix Open Data crime API | API | 3d | None | New `services/crime_data/phoenix_api.py` | Tech-Beta |
| **P1-07** | Integrate FEMA NFHL flood zone API | API | 3d | None | `services/flood_data/` (may exist partially) | Tech-Alpha |
| **P1-08** | Add equipment replacement cost budget to deal sheets | CODE | 2d | None | `scripts/deal_sheets/`, `reporters/` | Domain-Alpha |
| **P1-09** | Add residential proxy integration (Smartproxy/IPRoyal) | CODE | 2d | None | `services/infrastructure/proxy.py` | Tech-Gamma |
| **P1-10** | Add retry logic with exponential backoff for extractions | CODE | 2d | P0-02 | `extract_images.py`, extraction services | Gap IP-06, IP-07 |
| **P1-11** | Add cost efficiency component breakdown in reports | CODE | 2d | P0-04 | `services/cost_estimation/`, reporters | Gap XT-11 |
| **P1-12** | Add HOA verification via County Recorder | API | 3d | None | New `services/hoa_verification/` | Domain-Beta |
| **P1-13** | Add solar lease detection from listing data | CODE | 2d | P0-01 | `listing-browser` agent, `schemas.py` | Domain-Beta |
| **P1-14** | Externalize kill-switch criteria to YAML config | CONFIG | 2d | None | New `config/kill_switch.yaml`, loader | Gap XT-05 |
| **P1-15** | Add scoring weight versioning | CODE | 2d | None | `scoring_weights.py`, run metadata | Gap XT-06 |
| **P1-16** | Validate/maintain $0 HOA hard kill-switch | PROCESS | 0.5d | None | Verify `constants.py` - confirmed correct | Market-Alpha |
| **P1-17** | Add water service area verification (DAWS) | API | 2d | None | New `services/water_service/` | Domain-Gamma |
| **P1-18** | Add Maricopa County GIS integration for lot validation | API | 3d | None | `services/county_data/gis.py` | Domain-Gamma |

**P1 Dependencies:**
```
P1-04 (roof material) → P1-05 (underlayment)
P0-02 (job queue) → P1-10 (retry logic)
P0-04 (explanations) → P1-11 (cost breakdown)
P0-01 (solar kill-switch) → P1-13 (solar detection)
```

---

### P2 - Medium Priority

Important enhancements that improve completeness and maintainability.

| ID | Action | Category | Effort | Dependencies | Files Affected | Research Source |
|----|--------|----------|--------|--------------|----------------|-----------------|
| **P2-01** | Add appreciation tier scoring by location | CODE | 3d | None | New `services/scoring/strategies/appreciation.py` | Market-Gamma |
| **P2-02** | Add emerging neighborhood tracking (Laveen, Buckeye, etc.) | CONFIG | 1d | P2-01 | `config/neighborhoods.yaml` | Market-Gamma |
| **P2-03** | Add pool equipment age as Systems subscore factor | CODE | 1d | None | `services/scoring/strategies/systems.py` | Market-Beta |
| **P2-04** | Add builder ROC complaints check for new construction | API | 3d | None | New `services/builder_verification/` | Domain-Beta |
| **P2-05** | Add zoning context lookup | API | 2d | P1-18 | `services/county_data/zoning.py` | Domain-Gamma |
| **P2-06** | Integrate EIA energy estimation API | API | 2d | None | New `services/energy_estimation/` | Tech-Beta |
| **P2-07** | Add energy estimation formula (sqft × region multiplier) | CODE | 1d | P2-06 | `services/cost_estimation/` | Tech-Beta |
| **P2-08** | Add circuit breaker pattern for extraction sources | CODE | 2d | P0-02 | `services/image_extraction/` (SourceCircuitBreaker exists) | Gap IP-08 |
| **P2-09** | Add crash-resilient extraction state | CODE | 3d | P0-02 | `extraction_state.json` handling | Gap IP-09 |
| **P2-10** | Add extraction metrics dashboard | CODE | 2d | P0-03 | New `reports/extraction_metrics.html` | Gap IP-10 |
| **P2-11** | Tune LSH deduplication for small datasets | CODE | 2d | None | `validation/deduplication.py` | Gap IP-11 |
| **P2-12** | Parallelize image standardizer | CODE | 2d | P0-02 | `services/image_extraction/standardizer.py` | Gap IP-12 |
| **P2-13** | Add schema versioning for data migrations | CODE | 3d | P0-06 | `services/schema/versioning.py` | Gap XT-02 |
| **P2-14** | Add mutation audit logging | CODE | 2d | P0-06 | Repositories, new `audit/` service | Gap XT-03 |
| **P2-15** | Index extraction run logs for querying | CODE | 1d | None | `run_history/` → indexed JSON | Gap XT-04 |
| **P2-16** | Add feature flag system for scoring strategies | CODE | 2d | P1-15 | New `config/feature_flags.py` | Gap XT-07 |
| **P2-17** | Move remaining constants to environment variables | CONFIG | 2d | None | `constants.py`, `.env.example` | Gap XT-08 |
| **P2-18** | Add "next tier" guidance to reports | CODE | 2d | P0-04 | `services/classification/`, reporters | Gap XT-12 |
| **P2-19** | Add commute cost monetization service | CODE | 3d | P1-02 | New `services/commute_cost/` | Gap VB-04 |
| **P2-20** | Add zoning/growth risk assessment | CODE | 4d | P2-05 | New `services/risk_assessment/zoning.py` | Gap VB-05 |
| **P2-21** | Enhance energy efficiency modeling (solar ROI) | CODE | 3d | P0-01, P2-06 | `services/cost_estimation/`, renovation service | Gap VB-06 |
| **P2-22** | Integrate renovation ROI service | CODE | 2d | None | Connect existing `renovation/` service | Gap VB-07 |
| **P2-23** | Add flood insurance cost estimation | CODE | 2d | P1-07 | `services/cost_estimation/` | Gap VB-08 |
| **P2-24** | Add WalkScore API rate limiting | CODE | 1d | None | `services/walkscore/` | Tech-Beta |
| **P2-25** | Validate 4+ bedroom requirement per demographics | PROCESS | 0.5d | None | Verify `constants.py` - confirmed correct | Market-Gamma |
| **P2-26** | Document Arizona HVAC lifespan (10-15 years) in deal sheets | PROCESS | 0.5d | None | Deal sheet templates, already in `constants.py` (12 years) | Domain-Alpha |

**P2 Dependencies:**
```
P1-18 (GIS) → P2-05 (zoning)
P2-05 (zoning) → P2-20 (zoning risk)
P0-02 (job queue) → P2-08, P2-09, P2-12
P0-06 (lineage) → P2-13, P2-14
P0-04 (explanations) → P2-18
P1-07 (FEMA API) → P2-23 (flood insurance)
P2-06 (EIA) → P2-07 (energy formula)
P0-01 (solar kill-switch) + P2-06 → P2-21 (solar ROI)
```

---

### P3 - Lower Priority / Future

Nice-to-have improvements for future consideration.

| ID | Action | Category | Effort | Dependencies | Files Affected | Research Source |
|----|--------|----------|--------|--------------|----------------|-----------------|
| **P3-01** | Add kill-switch severity bands (soft fail vs hard fail nuance) | CODE | 2d | P0-05 | `kill_switch/` service | Gap VB-02 |
| **P3-02** | Implement auto-CLAUDE.md creation hooks | CODE | 2d | None | Discovery protocol (designed, not implemented) | Gap CA-01 |
| **P3-03** | Add runtime staleness checks for data files | CODE | 2d | None | Context management hooks | Gap CA-02 |
| **P3-04** | Add tool violation linter (pre-commit) | PROCESS | 2d | None | `.pre-commit-config.yaml` | Gap CA-03 |
| **P3-05** | Add skill discovery CLI command | CODE | 1d | None | New CLI utility | Gap CA-04 |
| **P3-06** | Add knowledge graph schema validation | CODE | 1d | None | Pydantic schemas for `toolkit.json` | Gap CA-05 |
| **P3-07** | Add adaptive batch sizing for analysis | CODE | 1d | P0-02 | `analyze-property` command | Gap XT-14 |
| **P3-08** | Add self-healing for transient API failures | CODE | 3d | P1-10 | Extraction services | Gap XT-15 |
| **P3-09** | Add job cancellation support | CODE | 2d | P0-02 | Job queue infrastructure | Gap IP-05 |
| **P3-10** | Add worker pool for distributed extraction | CODE | 3d | P0-02 | New worker infrastructure | Gap IP-03 |
| **P3-11** | Add historical appreciation data by ZIP | API | 3d | P2-01 | `services/appreciation/` | Market-Gamma |
| **P3-12** | Add NeighborhoodScout crime data (enterprise) | API | 2d | Budget approval | Alternative to Phoenix Open Data | Tech-Beta |
| **P3-13** | Add CrimeOMeter API integration (address-level) | API | 2d | Budget approval | Alternative crime source | Tech-Beta |
| **P3-14** | Evaluate Celery migration (if RQ bottlenecks) | CODE | 5d | P0-02 proven insufficient | Migration from RQ | Tech-Gamma |
| **P3-15** | Add UtilityAPI/Arcadia for actual energy data | API | 4d | Budget approval | Enterprise energy data | Tech-Beta |
| **P3-16** | Add DOE Home Energy Score API integration | API | 3d | DOE Assessor credentials | Official energy scoring | Tech-Beta |

---
