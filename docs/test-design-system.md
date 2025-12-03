# PHX Houses Analysis Pipeline - System Test Design

**Version:** 1.0
**Author:** Murat - Master Test Architect
**Date:** 2025-12-03
**Mode:** System-Level (Phase 3 - Solutioning)
**Status:** Draft

---

## Executive Summary

This document defines the comprehensive test strategy for the PHX Houses Analysis Pipeline, a personal decision support system that evaluates Phoenix-area residential properties against strict first-time homebuyer criteria.

**System Scope:**
- 7 Epics, 42 Stories, 62 Functional Requirements
- Multi-agent architecture with 4-phase pipeline
- 605-point scoring system (not 600 per reconciled Architecture)
- 7 HARD kill-switch criteria
- Target: 100+ properties/month, single user

**Test Strategy Summary:**
- **Unit Tests:** 65% (Domain logic, scoring, kill-switch)
- **Integration Tests:** 25% (Agent communication, APIs, file I/O)
- **E2E Tests:** 10% (Full pipeline runs, report generation)

---

## 1. Testability Assessment

### 1.1 Controllability

| Aspect | Assessment | Evidence | Status |
|--------|------------|----------|--------|
| State injection | PASS | `enrichment_data.json` and `work_items.json` are JSON files that can be seeded with test data | Ready |
| API mocking | PASS | Repository pattern enables mock implementations; external APIs abstracted via client classes | Ready |
| Configuration override | PASS | YAML/CSV configs externalized; `.env` for secrets; Pydantic validation | Ready |
| Phase isolation | PASS | Each phase independently executable via scripts; `--skip-phase` flag available | Ready |
| Kill-switch testing | PASS | Individual criterion classes; threshold constants in `constants.py` | Ready |
| Scoring strategy isolation | PASS | Strategy pattern with base class; each scorer testable in isolation | Ready |

**Controllability Assessment: PASS**

The architecture enables excellent test input control through:
- Repository pattern abstracts data persistence (mock CSV/JSON repositories)
- Dependency injection possible for services
- External API clients can be mocked at HTTP layer (httpx, respx)
- Configuration externalized to files (not hardcoded)

### 1.2 Observability

| Aspect | Assessment | Evidence | Status |
|--------|------------|----------|--------|
| State inspection | PASS | `work_items.json` tracks per-property phase status with timestamps | Ready |
| Logging | PASS | Centralized `logging_config.py` (6989 bytes); structured logging available | Ready |
| Score traceability | PASS | `ScoreBreakdown` dataclass tracks section subtotals; provenance metadata per field | Ready |
| Kill-switch explanations | PASS | `KillSwitchResult` includes `failed_criteria`, `details`, `evaluated_at` | Ready |
| Pipeline metrics | CONCERNS | Summary in `work_items.json` but no timing metrics per phase | Enhancement needed |
| Data quality metrics | PASS | Quality service tracks lineage, completeness, confidence scores | Ready |

**Observability Assessment: PASS with CONCERNS**

Strengths:
- Clear result containers (`KillSwitchResult`, `ScoreBreakdown`, `PipelineResult`)
- Provenance tracking with source, confidence, timestamp
- Checkpoint state preserved in JSON files

Concerns:
- No performance timing instrumentation in pipeline
- Console output not easily parseable for CI (consider JSON output mode)

**Recommendation:** Add timing metrics to `work_items.json` (phase duration, total runtime).

### 1.3 Reliability

| Aspect | Assessment | Evidence | Status |
|--------|------------|----------|--------|
| Test isolation | PASS | Repository pattern enables stateless tests; no shared mutable state | Ready |
| Deterministic scoring | PASS | Scoring strategies use pure functions on Property data | Ready |
| Crash recovery | PASS | Checkpoint after each phase; `--resume` flag; 30-min stuck detection | Ready |
| Atomic writes | PASS | Backup-before-modify pattern in repositories | Ready |
| External dependency isolation | CONCERNS | Stealth browser (nodriver) requires real Chrome; hard to mock | Requires test mode |
| Parallel safety | PASS | Single-user system; file-based state with atomic writes | Ready |

**Reliability Assessment: PASS with CONCERNS**

Strengths:
- Pure domain logic enables deterministic unit tests
- State management supports crash recovery testing
- Repository abstraction enables test isolation

Concerns:
- nodriver stealth browser requires real browser binary
- Image extraction depends on network availability
- Rate limiting in external APIs may cause flaky tests

**Recommendation:** Implement test fixtures for browser automation; mock HTTP responses with respx.

---

## 2. Architecturally Significant Requirements (ASRs)

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

## 3. Test Levels Strategy

### 3.1 Recommended Split

Based on the DDD architecture with strong domain isolation:

| Level | Target | Rationale |
|-------|--------|-----------|
| **Unit Tests** | 65% | Domain entities, scoring strategies, kill-switch criteria, value objects, repositories |
| **Integration Tests** | 25% | Pipeline orchestration, API clients, file I/O, agent communication |
| **E2E Tests** | 10% | Full pipeline runs, CLI commands, report generation |

### 3.2 Unit Tests (65%)

**Focus Areas:**
- Kill-switch criteria (7 individual criterion classes)
- Scoring strategies (22 strategy classes)
- Tier classification logic
- Address normalization
- Data validation (Pydantic schemas)
- Configuration loading
- Repository CRUD operations (with mock data)
- Error handling utilities

**Framework:** pytest
**Coverage Target:** 80% line coverage for `src/phx_home_analysis/`

**Example Test Categories:**

| Component | Test Count | Est. Hours |
|-----------|------------|------------|
| Kill-switch criteria (7 classes x 5 tests) | 35 | 8 |
| Scoring strategies (22 classes x 4 tests) | 88 | 20 |
| Tier classifier | 10 | 2 |
| Repository operations | 25 | 6 |
| Configuration loading | 15 | 4 |
| Validation schemas | 20 | 5 |
| **Total Unit** | ~200 | ~45 |

### 3.3 Integration Tests (25%)

**Focus Areas:**
- Pipeline phase coordination
- County Assessor API client (mocked HTTP)
- Listing extraction (mocked responses)
- Map analysis service
- State management (work_items.json manipulation)
- Data aggregation from multiple sources
- Agent spawning coordination

**Framework:** pytest + respx (HTTP mocking) + pytest-asyncio
**Coverage Target:** Critical paths fully covered

**Example Test Categories:**

| Component | Test Count | Est. Hours |
|-----------|------------|------------|
| Pipeline orchestration | 15 | 10 |
| API client integration (mocked) | 20 | 8 |
| State management | 15 | 6 |
| Data aggregation/merge | 12 | 5 |
| Phase coordination | 10 | 6 |
| **Total Integration** | ~70 | ~35 |

### 3.4 E2E Tests (10%)

**Focus Areas:**
- Full pipeline run (--test mode with 5 properties)
- CLI command validation
- Deal sheet generation
- Resume from checkpoint
- Report output verification

**Framework:** pytest + subprocess for CLI
**Environment:** Isolated test directory with fixtures

**Example Test Categories:**

| Component | Test Count | Est. Hours |
|-----------|------------|------------|
| CLI smoke tests | 5 | 3 |
| Full pipeline (--test) | 3 | 5 |
| Resume capability | 3 | 3 |
| Report generation | 5 | 4 |
| **Total E2E** | ~16 | ~15 |

---

## 4. NFR Testing Approach

### 4.1 Security Testing

| Requirement | Test Method | Tools | Priority |
|-------------|-------------|-------|----------|
| NFR25: Secrets in .env only | Git hook scanning | pre-commit + detect-secrets | P0 |
| NFR26: No PII in logs | Log audit tests | pytest + log capture | P0 |
| NFR27: No high/critical vulnerabilities | Dependency scanning | pip-audit | P0 (CI gate) |
| API token not exposed in errors | Error message audit | Unit tests | P1 |

**Test Cases:**
- `test_secrets_not_in_codebase`: grep for API key patterns in tracked files
- `test_logs_no_pii`: capture log output, assert no addresses/names
- `test_error_messages_sanitized`: verify 401 errors don't expose tokens

### 4.2 Performance Testing

| Requirement | Test Method | Tools | Priority |
|-------------|-------------|-------|----------|
| NFR1: 20 properties in <=30 min | Timing benchmark | pytest-benchmark | P1 |
| NFR2: Re-score 100 in <=5 min | Timing benchmark | pytest-benchmark | P1 |
| NFR4: Prerequisite validation <=5s | Unit test with timing | pytest | P2 |
| Memory usage reasonable | Profiling | memory_profiler (optional) | P3 |

**Test Cases:**
- `test_scoring_performance`: score 100 cached properties, assert <300s
- `test_kill_switch_performance`: evaluate 1000 properties, assert <10s
- `test_prerequisite_validation_speed`: run validation, assert <5s

### 4.3 Reliability Testing

| Requirement | Test Method | Tools | Priority |
|-------------|-------------|-------|----------|
| NFR5: 100% kill-switch accuracy | Exhaustive boundary tests | pytest | P0 |
| NFR6: Scoring consistency +/-5 pts | Deterministic re-run tests | pytest | P0 |
| NFR7: 95%+ resume success | Interrupt simulation | pytest + signal handling | P1 |
| NFR8: 100% schema validation | Pydantic enforcement | pytest | P0 |
| NFR9: Atomic checkpoint writes | Concurrent write tests | pytest | P1 |

**Test Cases:**
- `test_kill_switch_boundary_conditions`: HOA=0 vs HOA=1, beds=3 vs beds=4
- `test_scoring_deterministic`: same input produces identical output
- `test_resume_after_interrupt`: simulate SIGTERM, verify state integrity
- `test_schema_validation_rejects_invalid`: malformed JSON raises ValidationError

### 4.4 Maintainability Testing

| Requirement | Test Method | Tools | Priority |
|-------------|-------------|-------|----------|
| NFR10: Config externalized | Code audit | grep + pytest | P1 |
| NFR11: 80%+ docstring coverage | Documentation check | interrogate | P2 |
| NFR12: Actionable error messages | Error message audit | pytest | P1 |
| NFR13: Config schema validation | Unit tests | pytest | P1 |

**Test Cases:**
- `test_no_hardcoded_thresholds`: grep for magic numbers in scoring/kill-switch
- `test_config_validation_error_messages`: invalid config produces clear errors
- `test_docstring_coverage`: interrogate reports >=80%

---

## 5. Test Environment Requirements

### 5.1 Fixtures

| Fixture | Purpose | Location |
|---------|---------|----------|
| `sample_property.json` | Single property with all fields populated | `tests/fixtures/` |
| `sample_enrichment_data.json` | 5-property enrichment dataset | `tests/fixtures/` |
| `sample_work_items.json` | Pipeline state at various phases | `tests/fixtures/` |
| `kill_switch_edge_cases.csv` | Boundary condition test data | `tests/fixtures/` |
| `scoring_scenarios.json` | Pre-calculated scoring test cases | `tests/fixtures/` |

### 5.2 Mocks

| Mock | Purpose | Implementation |
|------|---------|----------------|
| `MockCountyAssessorClient` | Bypass County API in tests | respx fixture |
| `MockGreatSchoolsClient` | Bypass GreatSchools API | respx fixture |
| `MockGoogleMapsClient` | Bypass Google Maps API | respx fixture |
| `MockBrowserExtractor` | Bypass stealth browser | Mock class returning fixture data |
| `MockImageDownloader` | Bypass image downloads | Return pre-cached test images |

### 5.3 Configuration

| Config | Test Value | Production Value |
|--------|------------|------------------|
| `MARICOPA_ASSESSOR_TOKEN` | `test-token-123` | (from .env) |
| `GOOGLE_MAPS_API_KEY` | `test-key-456` | (from .env) |
| Test data directory | `tests/fixtures/data/` | `data/` |
| Cache TTL | 0 (disabled) | 7 days |

### 5.4 Test Directory Structure

```
tests/
+-- conftest.py                    # Shared fixtures
+-- unit/
|   +-- test_kill_switch.py        # Kill-switch criteria tests
|   +-- test_scorer.py             # Scoring strategy tests
|   +-- test_domain.py             # Entity/value object tests
|   +-- test_repositories.py       # Repository tests
|   +-- test_validation.py         # Schema validation tests
|   +-- services/
|       +-- test_job_queue.py      # Job queue tests
|       +-- test_zillow_extractor_validation.py
+-- integration/
|   +-- test_pipeline.py           # Pipeline orchestration
|   +-- test_kill_switch_chain.py  # Full kill-switch flow
|   +-- test_deal_sheets_simple.py # Report generation
+-- e2e/
|   +-- test_cli_commands.py       # CLI smoke tests (new)
|   +-- test_full_pipeline.py      # End-to-end runs (new)
+-- fixtures/
|   +-- sample_property.json
|   +-- sample_enrichment_data.json
|   +-- sample_work_items.json
|   +-- kill_switch_edge_cases.csv
+-- benchmarks/
    +-- test_lsh_performance.py
```

---

## 6. Risk-Based Test Priorities

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

## 7. Sprint 0 Recommendations

### 7.1 Test Framework Setup

| Action | Priority | Effort |
|--------|----------|--------|
| Configure pytest with coverage reporting | P0 | 2 hours |
| Set up pytest-asyncio for async tests | P0 | 1 hour |
| Install respx for HTTP mocking | P0 | 1 hour |
| Configure pytest-benchmark for performance tests | P1 | 1 hour |
| Set up pytest markers (unit, integration, e2e, slow) | P0 | 1 hour |
| Create conftest.py with shared fixtures | P0 | 4 hours |

**Total Setup:** 10 hours

### 7.2 Initial Test Suite Structure

```python
# pytest.ini or pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (requires fixtures)",
    "e2e: End-to-end tests (full pipeline)",
    "slow: Tests that take >10 seconds",
    "security: Security-related tests",
]
addopts = "--strict-markers -v"

[tool.coverage.run]
source = ["src/phx_home_analysis"]
branch = true
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
fail_under = 80
show_missing = true
```

### 7.3 CI/CD Test Integration

**Recommended GitHub Actions Workflow:**

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run unit tests
        run: pytest tests/unit -m unit --cov --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v4

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install uv
          uv sync
      - name: Run integration tests
        run: pytest tests/integration -m integration

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit
      - name: Run secret detection
        uses: gitleaks/gitleaks-action@v2
```

### 7.4 Fixture Creation Priorities

| Fixture | Priority | Effort |
|---------|----------|--------|
| `tests/fixtures/sample_property.json` | P0 | 1 hour |
| `tests/fixtures/sample_enrichment_data.json` | P0 | 2 hours |
| `tests/fixtures/kill_switch_edge_cases.csv` | P0 | 1 hour |
| `tests/fixtures/scoring_scenarios.json` | P1 | 2 hours |
| `tests/fixtures/sample_work_items.json` | P1 | 1 hour |
| Mock HTTP response fixtures (County API) | P1 | 2 hours |
| Mock HTTP response fixtures (GreatSchools) | P2 | 1 hour |

**Total Fixture Creation:** 10 hours

---

## 8. Quality Gate Criteria

### 8.1 PR Gate (Merge to feature branch)

| Criterion | Threshold | Blocking |
|-----------|-----------|----------|
| Unit tests pass | 100% | Yes |
| Integration tests pass | 95% | Yes |
| Coverage (changed files) | >= 80% | Yes |
| No new security vulnerabilities | 0 high/critical | Yes |
| Linting (ruff) | 0 errors | Yes |
| Type checking (mypy) | 0 errors | Yes |

### 8.2 Merge Gate (PR to main)

| Criterion | Threshold | Blocking |
|-----------|-----------|----------|
| All P0 tests pass | 100% | Yes |
| All P1 tests pass | >= 95% | Yes |
| Overall coverage | >= 80% | Yes |
| No security vulnerabilities | 0 high/critical | Yes |
| pip-audit clean | 0 high/critical | Yes |
| No hardcoded secrets | 0 detections | Yes |

### 8.3 Release Gate (Tag creation)

| Criterion | Threshold | Blocking |
|-----------|-----------|----------|
| All tests pass (P0 + P1 + P2) | >= 95% | Yes |
| Coverage | >= 80% | Yes |
| Performance benchmarks | Within 10% of baseline | No (warning) |
| Documentation coverage | >= 80% docstrings | No (warning) |
| CHANGELOG updated | Required | Yes |

---

## 9. Summary

### 9.1 Key Metrics

| Metric | Value |
|--------|-------|
| **ASRs Identified** | 17 |
| **High-Priority ASRs (>=6)** | 7 |
| **Test Level Split** | Unit 65% / Integration 25% / E2E 10% |
| **P0 Test Count** | 12 |
| **P1 Test Count** | 45 |
| **P2 Test Count** | 25 |
| **P3 Test Count** | 10 |
| **Total Estimated Tests** | ~290 |
| **Sprint 0 Setup Effort** | 20 hours |
| **Total Test Development Effort** | ~95 hours (~12 days) |

### 9.2 Risk Mitigation Summary

| Risk Category | Count | Highest Score | Key Mitigation |
|---------------|-------|---------------|----------------|
| BUS (Business) | 4 | 9 (ASR-01) | Exhaustive kill-switch boundary tests |
| DATA | 3 | 6 (ASR-02, ASR-07) | Deterministic scoring tests, schema validation |
| TECH | 4 | 6 (ASR-05) | Mock servers for browser automation |
| OPS | 3 | 6 (ASR-04) | Interrupt simulation, state integrity checks |
| SEC | 1 | 6 (ASR-06) | Secret scanning, log auditing |
| PERF | 2 | 6 (ASR-03) | Timing benchmarks with assertions |

### 9.3 Next Steps

1. **Immediate (Sprint 0):**
   - Configure pytest with coverage and markers
   - Create initial fixture set (5 files)
   - Implement P0 kill-switch boundary tests
   - Set up CI/CD pipeline with test stages

2. **Sprint 1:**
   - Complete P0 test suite (12 tests)
   - Begin P1 scoring strategy tests
   - Implement mock HTTP fixtures for APIs

3. **Sprint 2:**
   - Complete P1 test suite (45 tests)
   - Add integration tests for pipeline
   - Performance benchmark baseline

4. **Ongoing:**
   - P2/P3 tests as capacity allows
   - Maintain coverage >= 80%
   - Update fixtures with new test data

---

## Appendix A: Existing Test Coverage Analysis

Based on `tests/` directory scan (41 test files found):

| Category | Files | Status |
|----------|-------|--------|
| Unit tests | 17 | Partial coverage |
| Integration tests | 5 | Basic coverage |
| Service tests | 5 | Good coverage |
| Benchmark tests | 1 | Performance only |
| Archived tests | 5 | Not running |

**Key Gaps:**
- No dedicated E2E CLI tests
- Kill-switch tests exist but may lack boundary coverage
- Scoring tests exist but strategy coverage unclear
- No explicit security tests

---

## Appendix B: References

### Architecture Documents
- `docs/architecture.md` - System architecture (1500 lines)
- `docs/prd.md` - Product requirements (1158 lines)
- `docs/epics.md` - 7 epics, 42 stories (2197 lines)

### Key Code References
- `src/phx_home_analysis/config/scoring_weights.py` - 605-point scoring system
- `src/phx_home_analysis/config/constants.py` - All configuration constants
- `src/phx_home_analysis/services/kill_switch/` - Kill-switch implementation
- `src/phx_home_analysis/services/scoring/` - Scoring strategies

### Test Framework Documentation
- pytest: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/
- respx: https://lundberg.github.io/respx/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/

---

**Generated by:** BMad TEA Agent - Test Architect Module
**Workflow:** `.bmad/bmm/workflows/testarch/test-design`
**Version:** 4.0 (BMad v6)
