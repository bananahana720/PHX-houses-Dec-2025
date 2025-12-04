# Section 1: Gap Inventory Table

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
