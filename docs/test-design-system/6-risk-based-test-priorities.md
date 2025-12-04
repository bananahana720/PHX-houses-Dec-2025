# 6. Risk-Based Test Priorities

### 6.1 P0 - Critical Path (Must Pass)

**Run on every commit. 100% pass rate required.**

| Test | Risk Link | Rationale |
|------|-----------|-----------|
| Kill-switch HOA criterion (0 vs >0) | ASR-01 | Instant fail criterion, zero tolerance |
| Kill-switch beds criterion (>=4) | ASR-01 | Hard criterion boundary |
| Kill-switch baths criterion (>=2) | ASR-01 | Hard criterion boundary |
| Kill-switch sqft criterion (>1800) | ASR-01 | Hard criterion boundary |
| Kill-switch lot criterion (>8000) | ASR-01 | Hard criterion boundary |
| Kill-switch garage criterion (>=1) | ASR-01 | Hard criterion boundary |
| Kill-switch sewer criterion (city) | ASR-01 | Hard criterion boundary |
| Scoring determinism test | ASR-02 | Score reproducibility |
| Schema validation (enrichment_data.json) | ASR-07 | Data integrity |
| Tier classification at thresholds | ASR-14 | 484/363 boundary correctness |
| Secrets not in codebase | ASR-06 | Security gate |
| State checkpoint atomic write | ASR-04 | Crash recovery integrity |

**Count:** 12 P0 tests
**Estimated Time:** 15 tests x 2 hours = 30 hours

### 6.2 P1 - High Value (Should Pass)

**Run on PR to main. 95% pass rate target.**

| Test | Risk Link | Rationale |
|------|-----------|-----------|
| All 22 scoring strategies | ASR-02 | Score calculation accuracy |
| Phase prerequisite validation | ASR-08 | Spawn safety |
| Resume from checkpoint | ASR-04 | Crash recovery |
| API retry with backoff | ASR-11 | Transient error handling |
| Arizona context application | ASR-12 | Domain correctness |
| Parallel Phase 1 state locking | ASR-13 | Concurrency safety |
| Data aggregation merge rules | ASR-07 | Conflict resolution |
| Configuration loading and validation | ASR-07 | Runtime safety |
| Repository CRUD operations | ASR-07 | Data layer reliability |
| Kill-switch severity accumulation | ASR-01 | Soft criteria logic |
| Pipeline phase coordination | ASR-04 | Workflow correctness |

**Count:** 45 P1 tests
**Estimated Time:** 45 tests x 1 hour = 45 hours

### 6.3 P2 - Coverage (Nice to Have)

**Run nightly or weekly. 90% pass rate target.**

| Test | Risk Link | Rationale |
|------|-----------|-----------|
| CLI --help documentation | ASR-15 | User experience |
| Error message clarity | ASR-11 | Developer experience |
| Docstring coverage audit | NFR11 | Maintainability |
| Visual regression (deal sheets) | ASR-10 | Output quality |
| API response caching | ASR-11 | Performance optimization |
| Image cache cleanup | ASR-16 | Resource management |
| Address normalization edge cases | ASR-07 | Data quality |
| Confidence level calibration | ASR-12 | Trust accuracy |

**Count:** 25 P2 tests
**Estimated Time:** 25 tests x 0.5 hours = 12.5 hours

### 6.4 P3 - Exploratory (On-Demand)

**Run manually or on-demand.**

| Test | Rationale |
|------|-----------|
| Performance benchmarks (timing) | Optimization validation |
| Memory profiling | Resource usage |
| Load testing (100+ properties) | Scale validation |
| Stealth browser detection testing | Anti-bot effectiveness |
| Cross-platform compatibility | Windows/Linux/macOS |

**Count:** 10 P3 tests
**Estimated Time:** 10 tests x 1 hour = 10 hours

---
