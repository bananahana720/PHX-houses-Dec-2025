# Comprehensive Gap Analysis: PHX Houses Pipeline
**Analysis Date**: 2025-12-03
**Status**: Complete Wave 1 Deep-Dive Synthesis
**Total Gaps Identified**: 47
**Critical Gaps**: 8 | **High**: 12 | **Medium**: 18 | **Low**: 9

---

## Executive Summary

This gap analysis synthesizes findings from 4 parallel deep-dive analyses across 6 buckets + cross-cutting themes. The project has strong architectural fundamentals (AI/Claude integration, clean domain design) but faces significant operational challenges in image pipeline scalability, data explainability, and system autonomy.

**Key Insight**: The system achieves 80% alignment with vision but lacks execution infrastructure for production use. Image extraction is a critical bottleneck (blocks 30+ minutes, no background jobs, no concurrency, no visibility).

---

## Section 1: Gap Inventory Table

### Bucket 1+2: Vision & Buy-Box (Target 95% | Achieved 80%)

| Gap ID | Gap Description | Severity | Effort (days) | Impact | Root Cause |
|--------|-----------------|----------|---------------|--------|-----------|
| VB-01 | No interpretability: scores without explanation | HIGH | 3 | Users can't trust/understand scores | Missing score reasoning generation |
| VB-02 | Kill-switch too binary: all-or-nothing verdicts | MEDIUM | 2 | No nuance; unfixable properties marked FAIL | Severity accumulation logic is rigid |
| VB-03 | Missing foundation assessment: no structural eval | HIGH | 5 | Critical info gap for purchase decision | Service layer incomplete |
| VB-04 | No commute cost monetization | MEDIUM | 3 | Can't quantify time→money impact | Cost estimation service missing |
| VB-05 | No zoning/growth risk assessment | MEDIUM | 4 | Can't evaluate neighborhood upside | Risk assessment service incomplete |
| VB-06 | Weak energy efficiency modeling: no solar ROI | MEDIUM | 3 | Solar lease treated as liability only | Constants need expansion |
| VB-07 | Missing renovation ROI analysis | LOW | 4 | Can't evaluate fix-up properties | Renovation service framework exists, not integrated |
| VB-08 | No flood insurance cost estimation | LOW | 2 | Hidden cost not quantified | Cost estimation service gap |

**Summary**: Vision is 80% complete. Missing features are all in downstream analysis (interpretation, enrichment, monetization) rather than core filtering/scoring.

---

### Bucket 3+4: Claude/AI Architecture (Target 100% | Achieved 95%)

| Gap ID | Gap Description | Severity | Effort (days) | Impact | Root Cause |
|--------|-----------------|----------|---------------|--------|-----------|
| CA-01 | Auto-CLAUDE.md creation hooks designed but not implemented | MEDIUM | 2 | Directories without context docs | discovery_protocol defined but no hook |
| CA-02 | Staleness checks documented but not enforced at runtime | MEDIUM | 2 | Stale data used without warning | staleness_protocol in KB but no CI/CD gate |
| CA-03 | Tool violation linter missing | LOW | 2 | Bash find/grep still possible in comments | No pre-commit hook for tool compliance |
| CA-04 | Skill discovery is manual | LOW | 1 | No "ls skills" CLI command | `.claude/skills/` manually enumerated in docs |
| CA-05 | Knowledge graph schemas not validated on load | LOW | 1 | Malformed JSON could be loaded silently | No Pydantic schema for toolkit.json/context-management.json |

**Summary**: Architecture is 95% complete. Remaining gaps are automation/tooling rather than design issues.

---

### Bucket 5+6: Image Pipeline & Scraping (Target 95% | Achieved 40%)

| Gap ID | Gap Description | Severity | Effort (days) | Impact | Root Cause |
|--------|-----------------|----------|---------------|--------|-----------|
| IP-01 | NO background jobs: blocks 30+ min per property | CRITICAL | 5 | Sequential extraction means 4+ hours for 8 properties | No job queue/worker architecture |
| IP-02 | NO job queue: concurrent requests dropped | CRITICAL | 4 | Can't parallelize across properties | ProcessPool exists but no queue abstraction |
| IP-03 | NO worker pool: single machine bottleneck | CRITICAL | 3 | Can't distribute to multi-machine | No task distribution layer |
| IP-04 | NO progress visibility: complete black box | CRITICAL | 2 | User sees nothing for 30 min, thinks broken | No real-time progress logging |
| IP-05 | NO job cancellation: must wait full run | HIGH | 2 | User forced to Ctrl+C; no graceful shutdown | No cancellation token pattern |
| IP-06 | NO retry logic for failed extractions | HIGH | 3 | Failed sources never re-attempted | ExtractionError caught but not queued for retry |
| IP-07 | NO rate limit adaptive backoff | HIGH | 2 | Hard-coded 1s/req; could use exponential backoff | RateLimitError detected but no adaptive strategy |
| IP-08 | Circuit breaker not integrated into orchestrator | MEDIUM | 2 | SourceCircuitBreaker exists but unused | Designed but not wired into extraction loop |
| IP-09 | Extraction state is not crash-resilient | MEDIUM | 3 | State loss on crash; can't resume mid-property | State persisted per-source but not atomically |
| IP-10 | No extraction metrics dashboard | MEDIUM | 2 | Can't diagnose why extraction slow | CaptchaMetrics exists but no rendering |
| IP-11 | LSH deduplication not tuned for small datasets | MEDIUM | 2 | False negatives on 20-image properties | min_df=2 inappropriate for small corpora |
| IP-12 | Image standardizer runs sequentially | MEDIUM | 2 | Resizing/compression blocks next extraction | No batch processing of standards |

**Summary**: Image pipeline is only 40% complete. Missing is the entire job management, concurrency, and operational visibility layer. This is the highest-risk bucket.

---

### Bucket 7: Cross-Cutting Themes

#### Traceability (Target 8/10 | Achieved 3/10)

| Gap ID | Gap Description | Severity | Effort (days) | Impact | Root Cause |
|--------|-----------------|----------|---------------|--------|-----------|
| XT-01 | NO field-level lineage: don't know data origins | CRITICAL | 4 | Can't audit enrichment quality | field_lineage.json structure exists but not populated |
| XT-02 | NO schema versioning for data migrations | HIGH | 3 | Can't evolve enrichment_data.json safely | schema/models.py incomplete |
| XT-03 | No audit log for data mutations | MEDIUM | 2 | Can't trace who changed what when | No mutation logging in repositories |
| XT-04 | Extraction run logs not indexed | MEDIUM | 1 | Logs created but not queryable | run_history/ exists as raw files |

**Summary**: Traceability is weak. Data provenance is partially designed but not enforced. This blocks compliance audits and root-cause analysis on data quality issues.

#### Evolvability (Target 8/10 | Achieved 5/10)

| Gap ID | Gap Description | Severity | Effort (days) | Impact | Root Cause |
|--------|-----------------|----------|---------------|--------|-----------|
| XT-05 | Hard-coded kill-switch criteria in constants.py | HIGH | 2 | Can't A/B test severity weights | Criteria in code; should be configurable |
| XT-06 | No scoring weight versioning | HIGH | 2 | Can't compare historical scores post-config change | scoring_weights.py not versioned |
| XT-07 | No feature flag system for scoring strategies | MEDIUM | 2 | Can't enable/disable scorers at runtime | Strategies loaded statically |
| XT-08 | Configuration not externalized to environment | MEDIUM | 1 | Must redeploy for config changes | Constants not from env vars |

**Summary**: Evolvability is 50%. System is not designed for A/B testing, feature flags, or configuration management.

#### Explainability (Target 8/10 | Achieved 4/10)

| Gap ID | Gap Description | Severity | Effort (days) | Impact | Root Cause |
|--------|-----------------|----------|---------------|--------|-----------|
| XT-09 | Scoring is a black box: no reasoning generation | CRITICAL | 3 | Users see "480/600" with no explanation | PropertyScorer.score() returns breakdown but no text explanations |
| XT-10 | Kill-switch reasons abbreviated: "sewer=Y" | HIGH | 1 | User doesn't understand severity weights | KillSwitchFilter returns verdict but not reasoning |
| XT-11 | Cost estimation opaque: no component breakdown | MEDIUM | 2 | User sees "$4500/mo" without knowing why | CostEstimator computes total but no detail report |
| XT-12 | No "why not <tier>" guidance | LOW | 2 | User can't see what would push property to next tier | TierClassifier only returns tier, not delta |

**Summary**: Explainability is 40%. System generates scores but not human-readable reasoning. This is a critical UX gap.

#### Autonomy (Target 8/10 | Achieved 8/10)

| Gap ID | Gap Description | Severity | Effort (days) | Impact | Root Cause |
|--------|-----------------|----------|---------------|--------|-----------|
| XT-13 | Serial processing only: no parallelization | MEDIUM | 4 | Properties processed one-at-a-time | No task parallelization in orchestrator.py |
| XT-14 | No adaptive batch sizing | LOW | 1 | Fixed batch size; can't optimize for available resources | analyze-property uses fixed --test (5) |
| XT-15 | No self-healing for transient failures | MEDIUM | 3 | Transient API errors cause full retry | retry_count exists but no exponential backoff |

**Summary**: Autonomy is 80%. Serial processing is acceptable for small batches but blocks scaling.

---

## Section 2: Gap Dependencies

### Critical Path (Blocking Other Fixes)

```
IP-01 (NO background jobs)
  ↓ BLOCKS
IP-02 (NO job queue)
  ↓ BLOCKS
IP-03 (NO worker pool)
  ↓ BLOCKS
IP-04 (NO progress visibility)
```

**Cannot proceed with IP-05 through IP-12 until IP-01→IP-04 resolved.**

```
XT-01 (NO field-level lineage)
  ↓ BLOCKS
XT-04 (Extraction logs not indexed)

VB-01 (No interpretability)
  ↓ REQUIRES
XT-09 (Scoring black box)
  ↓ REQUIRES
XT-10 (Kill-switch reasons)
```

**Cannot improve explainability without first implementing lineage and reasoning generation.**

```
CA-01 (Auto-CLAUDE.md not implemented)
  ↓ BLOCKS (optional, not critical)
CA-02 (Staleness not enforced)
```

### Parallel-Safe Fixes (Can Work Independently)

- VB-02 through VB-08 can be worked in parallel
- CA-01 through CA-05 can be worked in parallel
- XT-05 through XT-08 can be worked in parallel (evolvability)
- XT-13 through XT-15 can be worked in parallel (autonomy)

---

## Section 3: Gap Clusters

### Cluster A: Image Pipeline Infrastructure (12 gaps, IP-01 to IP-12)
**Severity**: 5 CRITICAL, 3 HIGH, 4 MEDIUM
**Total Effort**: 30 days
**Business Impact**: BLOCKING - System cannot handle batch processing >5 properties

**Dependencies**:
1. IP-01 (job queue architecture) - MUST do first
2. IP-02 (job queue implementation) - parallel to IP-01
3. IP-03 (worker pool) - after IP-01/IP-02
4. IP-04 (progress visibility) - parallel to IP-01

**Recommended Order**:
```
Week 1: IP-01, IP-02, IP-04 (foundation + visibility)
Week 2: IP-03 (worker pool), IP-05 (retries), IP-07 (backoff)
Week 3: IP-06, IP-08, IP-09 (resilience)
Week 4: IP-10, IP-11, IP-12 (optimization)
```

### Cluster B: Explainability & Reasoning (4 gaps, XT-09 to XT-12)
**Severity**: 1 CRITICAL, 2 HIGH, 1 LOW
**Total Effort**: 8 days
**Business Impact**: HIGH - UX blocker; users don't understand system output

**Dependencies**:
1. XT-01 (field lineage) - prerequisite for tracing score components
2. Score breakdown structures must be enhanced

**Recommended Order**:
```
Step 1: Enhance PropertyScorer to return reasoning text (3 days)
Step 2: Add KillSwitchFilter explanation generation (1 day)
Step 3: Add CostEstimator component breakdown (2 days)
Step 4: Add TierClassifier "next tier" guidance (2 days)
```

### Cluster C: Traceability & Audit (4 gaps, XT-01 to XT-04)
**Severity**: 1 CRITICAL, 1 HIGH, 2 MEDIUM
**Total Effort**: 10 days
**Business Impact**: MEDIUM - Compliance/audit gap; data quality concerns

**Dependencies**:
1. XT-01 (field lineage) must be done first; blocks XT-02/XT-03

**Recommended Order**:
```
Step 1: Implement field lineage population (3 days)
Step 2: Add schema versioning (2 days)
Step 3: Add mutation audit logging (2 days)
Step 4: Index extraction logs (1 day)
```

### Cluster D: Scoring Enrichment (8 gaps, VB-01 to VB-08)
**Severity**: 2 HIGH, 6 MEDIUM/LOW
**Total Effort**: 25 days
**Business Impact**: MEDIUM - Completeness; impacts property selection accuracy

**Dependencies**:
1. VB-01 (interpretability) requires XT-09 (scoring reasoning)
2. VB-03 (foundation assessment) can be done in parallel with others

**Recommended Order**:
```
Step 1: Implement foundation assessment service (3 days)
Step 2: Add commute cost monetization (2 days)
Step 3: Add zoning/growth risk service (3 days)
Step 4: Enhance energy efficiency (renovation ROI service exists, just integrate)
```

### Cluster E: Architecture Automation (5 gaps, CA-01 to CA-05)
**Severity**: All MEDIUM/LOW
**Total Effort**: 8 days
**Business Impact**: LOW - Nice-to-have; improves maintainability

**Dependencies**: None; can be done anytime

**Recommended Order**:
```
Sequential; low complexity:
Step 1: Implement auto-CLAUDE.md hooks (2 days)
Step 2: Enforce staleness checks (2 days)
Step 3: Add tool violation linter (1 day)
Step 4: Add skill discovery CLI (1 day)
Step 5: Add KB schema validation (1 day)
```

### Cluster F: Evolvability & Configuration (4 gaps, XT-05 to XT-08)
**Severity**: 2 HIGH, 2 MEDIUM
**Total Effort**: 7 days
**Business Impact**: MEDIUM - Blocks A/B testing, configuration management

**Dependencies**: None; can be done in parallel

**Recommended Order**:
```
Step 1: Externalize kill-switch criteria to YAML (1 day)
Step 2: Add scoring weight versioning (1 day)
Step 3: Implement feature flag system (2 days)
Step 4: Move all constants to env vars (2 days)
```

---

## Section 4: Root Cause Analysis (5 Whys)

### Root Cause 1: No Job Queue Architecture
**Problem**: Image extraction blocks 30+ minutes; users see black box
**Why 1**: Currently sequential `extract_images.py --all` processes properties one-at-a-time
**Why 2**: ProcessPool exists but not used; no queue abstraction
**Why 3**: Extraction is I/O-bound (waiting for Zillow API) but treated as CPU-bound
**Why 4**: Original design focused on correctness (dedup, state) not throughput
**Why 5**: **Root**: No background job framework designed (RQ, Celery, etc.) + no async/await pattern for HTTP calls

**Affects**: IP-01, IP-02, IP-03, IP-04, IP-05
**Fix**: Design job queue layer (Pydantic models for jobs, job states, retry policies)

---

### Root Cause 2: Scoring Black Box
**Problem**: Users see "480/600" but don't understand what contributes to score
**Why 1**: PropertyScorer.score() returns ScoreBreakdown (structured data) but no human text
**Why 2**: ScoreBreakdown is 600+ lines of numeric data with no narrative
**Why 3**: Reasoning generation not included in service layer
**Why 4**: Original focus was correctness (weighted calculation) not communication
**Why 5**: **Root**: No "explain myself" pattern in domain services; reasoning seen as post-hoc not core

**Affects**: XT-09, XT-10, XT-11, VB-01
**Fix**: Add ReasoningEngine service that traverses score breakdown and generates text explanations

---

### Root Cause 3: Hard-Coded Buyer Criteria
**Problem**: Kill-switch severity weights and tier thresholds in `constants.py`; can't A/B test
**Why 1**: Criteria is business logic, not configuration
**Why 2**: When changes needed, must edit source code
**Why 3**: No version control for which criteria set was used for each run
**Why 4**: Original design assumed fixed buyer profile; no multi-tenant use case
**Why 5**: **Root**: Configuration management not included in domain model; criteria treated as immutable code not variable settings

**Affects**: XT-05, XT-06, XT-08
**Fix**: Design BuyerProfile versioning (YAML config + version tracking in run metadata)

---

### Root Cause 4: No Data Lineage
**Problem**: Can't trace where a field's value came from; don't know if it's enriched or canonical
**Why 1**: enrichment_data.json populated incrementally by phases but no source tracking
**Why 2**: field_lineage.json structure designed but never populated
**Why 3**: Agents/scripts update properties but don't call lineage.record()
**Why 4**: Original design focused on data correctness not provenance
**Why 5**: **Root**: No lineage middleware in repository layer; lineage is optional not mandatory

**Affects**: XT-01, XT-03, XT-04, Traceability cluster
**Fix**: Add LineageRecorder service; make all repository writes log source/timestamp/confidence

---

### Root Cause 5: No Kill-Switch Interpretability
**Problem**: User sees "FAIL: sewer=Y, year=2020" but doesn't understand severity model
**Why 1**: KillSwitchFilter.evaluate() returns bool (pass/fail) + list of failures; no explanation
**Why 2**: Severity weights exist (constants.py) but not surfaced to user
**Why 3**: User doesn't see: "sewer adds 2.5, year adds 2.0, total 4.5 >= 3.0 threshold = FAIL"
**Why 4**: Original verdict design: just yes/no; interpretation seen as separate concern
**Why 5**: **Root**: Kill-switch verdict objects don't include "reasoning" field; calculation ephemeral not preserved

**Affects**: XT-10, VB-02, Explainability cluster
**Fix**: Enhance KillSwitchVerdict dataclass with explanation text and severity breakdown

---

## Section 5: Quick Wins (Low Effort, High Impact)

| Gap ID | Gap | Effort | Impact | Why Quick Win |
|--------|-----|--------|--------|----------------|
| CA-03 | Tool violation linter | 2d | HIGH | Pre-commit hook; prevents Bash grep | Simple regex scan |
| CA-04 | Skill discovery CLI | 1d | MEDIUM | UX improvement | Just enumerate files + format |
| XT-04 | Index extraction logs | 1d | MEDIUM | Query runs without grepping files | Add JSON index to run_history/ |
| XT-08 | Move constants to env vars | 2d | HIGH | Config without redeploy | Use python-dotenv for missing vars |
| XT-12 | Add "next tier" guidance | 2d | MEDIUM | UX improvement | Simple math: score delta to next tier |
| VB-08 | Flood insurance cost | 2d | LOW | Completeness | FEMA zone → $X/month lookup table |
| CA-02 | Runtime staleness check | 2d | MEDIUM | Data quality gate | Add check_freshness() before agent spawn |

**Recommended Quick Win Order** (7 days total):
```
Day 1: CA-03 (linter) + CA-04 (skill CLI) + XT-04 (log indexing)
Day 2-3: XT-08 (env config) + XT-12 (next tier guidance)
Day 4: CA-02 (runtime staleness)
Day 5: VB-08 (flood insurance)
```

**Expected Wins**: +3 UX improvements, -1 data quality risk, +1 operational capability

---

## Section 6: Technical Debt Assessment

### Debt 1: No Job Queue (IP-01-05 cluster)
**Current Cost**: 30 min per 8 properties = 375 min per 100 properties = Can't handle production volume
**Interest (per month)**: Blocks scaling; users wait 6+ hours for full batch
**Payoff Timeline**: 5 days to design/build; worth it after property #15
**Should Fix**: YES (blocks production use)

### Debt 2: Scoring Black Box (XT-09 cluster)
**Current Cost**: Low - system works correctly, just not understandable
**Interest (per month)**: UX complaints; distrust of system
**Payoff Timeline**: 3 days to implement reasoning; high user value
**Should Fix**: YES (UX blocker)

### Debt 3: Hard-Coded Configuration (XT-05-08 cluster)
**Current Cost**: Medium - requires code change + redeploy for any adjustment
**Interest (per month)**: Blocks A/B testing buyer profiles
**Payoff Timeline**: 4 days to externalize; enables future testing
**Should Fix**: MAYBE (nice-to-have, not blocking)

### Debt 4: No Data Lineage (XT-01-04 cluster)
**Current Cost**: Medium - can't audit data quality, can't debug enrichment issues
**Interest (per month)**: Data quality erosion; trust issues
**Payoff Timeline**: 4 days to implement; prevents future data corruption
**Should Fix**: YES (compliance/audit gap)

### Debt 5: Foundation Assessment Missing (VB-03)
**Current Cost**: High - missing critical decision factor
**Interest (per month)**: Bad property selections; structural problems discovered late
**Payoff Timeline**: 5 days to build assessment service
**Should Fix**: YES (business logic gap)

---

## Section 7: Implementation Roadmap

### Phase 1: Production Readiness (Weeks 1-4) - FIX BLOCKING ISSUES
**Goals**: Image pipeline operational, scoring explainable, data traceable

```
Week 1: Image Pipeline Foundation (IP-01, IP-02, IP-04, CA-02)
├── Design job queue abstraction (1 day)
├── Implement Pydantic job models (1 day)
├── Wire job queue into orchestrator (1 day)
├── Add progress logging (1 day)
└── Add runtime staleness checks (1 day)
Effort: 5 days | Team: 1 engineer

Week 2: Explanation Layer (XT-09, XT-10, VB-01)
├── Design reasoning generation service (1 day)
├── Implement score explanation templates (1 day)
├── Add kill-switch verdict reasons (1 day)
├── Test with 10 properties (1 day)
└── User acceptance testing (1 day)
Effort: 5 days | Team: 1 engineer

Week 3: Data Lineage (XT-01, XT-02, XT-03)
├── Design lineage recorder service (1 day)
├── Implement field_lineage population (1 day)
├── Add mutation audit logging (1 day)
├── Add schema versioning framework (1 day)
└── Backfill lineage for existing data (1 day)
Effort: 5 days | Team: 1 engineer

Week 4: Scoring Enrichment (VB-03, VB-04, VB-05)
├── Implement foundation assessment (2 days)
├── Add commute cost monetization (1 day)
├── Add zoning/growth risk service (1 day)
└── Integration testing (1 day)
Effort: 5 days | Team: 1 engineer

**End of Phase 1**: System production-ready for batch processing. Can handle 30+ properties with explanations and full audit trail.
```

### Phase 2: Scale & Optimize (Weeks 5-8) - HANDLE LARGE BATCHES
**Goals**: Image extraction parallelized, configuration flexible, autonomous

```
Week 5: Worker Pool (IP-03, IP-05, IP-07)
├── Design worker pool abstraction (1 day)
├── Implement retry logic with backoff (1 day)
├── Integrate rate limit adaptive strategy (1 day)
└── Load testing with 100 properties (2 days)
Effort: 5 days | Team: 1 engineer

Week 6: Configuration Management (XT-05, XT-06, XT-08)
├── Externalize kill-switch criteria to YAML (1 day)
├── Implement criteria versioning (1 day)
├── Move constants to env vars (1 day)
├── Add feature flag system (1 day)
└── Test config hot-reload (1 day)
Effort: 5 days | Team: 1 engineer

Week 7: Foundation Enhancements (VB-06, VB-07, IP-11, IP-12)
├── Enhance energy efficiency modeling (1 day)
├── Integrate renovation ROI service (1 day)
├── Tune LSH deduplication (1 day)
├── Parallelize image standardizer (1 day)
└── Performance benchmarking (1 day)
Effort: 5 days | Team: 1 engineer

Week 8: Architecture Automation (CA-01, CA-04, XT-04, XT-15)
├── Implement auto-CLAUDE.md hooks (1 day)
├── Add skill discovery CLI (0.5 days)
├── Index extraction logs (0.5 days)
├── Add self-healing for transient failures (1 day)
└── Documentation + training (1.5 days)
Effort: 5 days | Team: 1 engineer

**End of Phase 2**: System scales to 1000+ properties. Configuration-driven. Self-healing.
```

### Phase 3: Analytics & Insights (Weeks 9-12) - MOVE FROM FILTERING TO GUIDANCE
**Goals**: Complete scoring enrichment, property recommendations, portfolio analysis

```
Week 9-10: Remaining VB Gaps
├── VB-02: Kill-switch nuance (severity bands, recommendations)
├── VB-08: Flood insurance cost (FEMA zone lookup table)
Effort: 4 days

Week 11: API & Reporting
├── REST API for property analysis
├── Portfolio comparison dashboard
Effort: 5 days

Week 12: Documentation & Knowledge Transfer
├── Architecture documentation
├── Runbooks for operations
├── Training for end users
Effort: 5 days

**End of Phase 3**: System complete. Ready for public release.
```

---

## Section 8: Risk Assessment

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

## Section 9: Success Metrics

### Phase 1 Success Criteria
- [ ] Image extraction completes 8 properties in <10 minutes (currently 30+ min)
- [ ] Each property has score explanation in natural language
- [ ] All data sources tracked in field_lineage.json
- [ ] 100% of tests passing
- [ ] Foundation assessment service deployed

### Phase 2 Success Criteria
- [ ] 100 properties processed in <30 minutes (parallelization working)
- [ ] Zero lost data on extraction interruption (crash-resilient)
- [ ] Configuration changes possible without redeployment
- [ ] Autonomous retries on transient failures
- [ ] 95%+ uptime on 24/7 batch runs

### Phase 3 Success Criteria
- [ ] 1000+ properties scorable in <2 hours
- [ ] Complete scoring enrichment (all VB gaps closed)
- [ ] User satisfaction >4/5 on explanation clarity
- [ ] Zero audit findings on data provenance
- [ ] API available for third-party integrations

---

## Section 10: Gap Summary by Bucket

```
BUCKET 1+2: Vision & Buy-Box
├── Implemented: 80% (5/8 core systems)
├── Gaps: 8 (2 HIGH, 6 MEDIUM/LOW)
├── Effort: 25 days
└── Risk: MEDIUM (nice-to-have enrichments)

BUCKET 3+4: Claude/AI Architecture
├── Implemented: 95% (well-designed, lacks automation)
├── Gaps: 5 (all MEDIUM/LOW)
├── Effort: 8 days
└── Risk: LOW (no core impact)

BUCKET 5+6: Image Pipeline & Scraping
├── Implemented: 40% (correctness good, operations missing)
├── Gaps: 12 (5 CRITICAL, 3 HIGH, 4 MEDIUM)
├── Effort: 30 days
└── Risk: CRITICAL (blocks production use)

CROSS-CUTTING: Explainability, Traceability, Evolvability
├── Implemented: 50% (designed but not enforced)
├── Gaps: 15 (1 CRITICAL, 5 HIGH, 9 MEDIUM)
├── Effort: 32 days
└── Risk: HIGH (data quality, UX, compliance)

TOTAL: 47 gaps | 4 CRITICAL | 8 HIGH | 18 MEDIUM | 9 LOW | 95 days effort
```

---

## Section 11: Appendix - Full Gap Glossary

### Image Pipeline Terminology
- **Job Queue**: Abstraction for distributing image extraction across workers
- **Worker Pool**: Multiple parallel processes handling extraction
- **Circuit Breaker**: Pattern that disables failing data sources temporarily
- **Progress Visibility**: Real-time logging of extraction status
- **Crash Resilience**: Ability to resume after unexpected interruption

### Scoring & Evaluation
- **Interpretability**: Users understand why property received score
- **Explainability**: System generates human-readable reasoning
- **Reasoning Generation**: NLP templates that convert numeric scores to prose
- **Black Box**: System that produces output without showing its logic

### Data & Configuration
- **Field Lineage**: Tracking of data provenance (source, timestamp, confidence)
- **Schema Versioning**: Version control for data structure changes
- **Hard-Coded**: Values in source code vs. configuration files
- **A/B Testing**: Running two configurations simultaneously to compare results

### Operational
- **Autonomy**: System's ability to self-recover from failures
- **Evolvability**: Ease of adding new features or changing behavior
- **Traceability**: Ability to audit and trace all system operations

---

## Conclusion

The PHX Houses Pipeline has strong architectural fundamentals (80% of vision + 95% of Claude/AI architecture implemented) but faces critical operational gaps that prevent production use.

**Top 3 Priority Fixes** (would unlock 90% of value):
1. **Job queue + worker pool** (IP-01-03) - Unblocks batch processing
2. **Scoring explanations** (XT-09) - Provides user confidence
3. **Foundation assessment** (VB-03) - Completes decision model

**Estimated total effort**: 95 days for 1-2 engineers over 12 weeks.
**ROI**: System moves from 40% operational (single property) to 100% operational (batch production).

---

**Document Status**: COMPLETE
**Last Updated**: 2025-12-03
**Next Review**: After Phase 1 completion (Week 4)
