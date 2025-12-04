# 2. Architecturally Significant Requirements (ASRs)

The following requirements pose significant testability challenges or drive architecture decisions.

### High-Priority ASRs (Score >= 6)

| ASR ID | Requirement | Category | Prob | Impact | Score | Priority | Mitigation |
|--------|-------------|----------|------|--------|-------|----------|------------|
| ASR-01 | Kill-switch accuracy must be 100% - zero false passes | BUS | 3 | 3 | 9 | P0 | Exhaustive unit tests for all 7 criteria with boundary conditions |
| ASR-02 | Scoring consistency within +/-5 points on re-run | DATA | 2 | 3 | 6 | P0 | Deterministic scoring tests with fixed input data |
| ASR-03 | Batch processing 20 properties in <=30 minutes | PERF | 2 | 3 | 6 | P1 | Performance benchmarks with timing assertions |
| ASR-04 | Crash recovery resume without data loss | OPS | 3 | 2 | 6 | P0 | Interrupt simulation tests; state validation |
| ASR-05 | Stealth browser bypasses PerimeterX detection | TECH | 3 | 2 | 6 | P1 | Integration test mode with mock servers |
| ASR-06 | API credentials never logged or exposed | SEC | 2 | 3 | 6 | P0 | Secret scanning in CI; log audit tests |
| ASR-07 | enrichment_data.json schema integrity | DATA | 2 | 3 | 6 | P0 | Pydantic schema validation on every write |

### Medium-Priority ASRs (Score 3-5)

| ASR ID | Requirement | Category | Prob | Impact | Score | Priority | Mitigation |
|--------|-------------|----------|------|--------|-------|----------|------------|
| ASR-08 | Phase prerequisite validation blocks invalid spawns | OPS | 2 | 2 | 4 | P1 | Unit tests for `validate_phase_prerequisites.py` |
| ASR-09 | Re-scoring 100 properties in <=5 minutes | PERF | 2 | 2 | 4 | P1 | Performance test with cached data |
| ASR-10 | Deal sheets render correctly on mobile | BUS | 2 | 2 | 4 | P2 | Visual regression tests (optional) |
| ASR-11 | API rate limits handled with exponential backoff | TECH | 2 | 2 | 4 | P1 | Retry decorator unit tests |
| ASR-12 | Arizona-specific factors applied (HVAC, pool, orientation) | BUS | 2 | 2 | 4 | P1 | Unit tests for AZ constants usage |
| ASR-13 | Multi-agent parallel Phase 1 execution | TECH | 2 | 2 | 4 | P1 | State file locking tests |
| ASR-14 | Tier thresholds calibrated to 605-point scale | DATA | 1 | 3 | 3 | P1 | Tier boundary tests at 484, 363 thresholds |

### Low-Priority ASRs (Score 1-2)

| ASR ID | Requirement | Category | Prob | Impact | Score | Priority | Mitigation |
|--------|-------------|----------|------|--------|-------|----------|------------|
| ASR-15 | CLI help documents all flags | BUS | 1 | 2 | 2 | P2 | Manual review; argparse --help validation |
| ASR-16 | Image cache cleanup after 14 days | OPS | 1 | 1 | 1 | P3 | Unit test for cleanup logic |
| ASR-17 | Proxy rotation for anti-bot detection | TECH | 2 | 1 | 2 | P2 | Integration test with mock proxy |

### ASR Risk Distribution

| Category | Count | Description |
|----------|-------|-------------|
| DATA | 3 | Schema integrity, scoring consistency, tier calibration |
| BUS | 4 | Kill-switch accuracy, mobile rendering, AZ factors, CLI usability |
| TECH | 4 | Stealth browser, rate limits, parallel execution, proxy rotation |
| OPS | 3 | Crash recovery, phase validation, cache cleanup |
| SEC | 1 | Credential protection |
| PERF | 2 | Batch timing, re-scoring speed |

---
