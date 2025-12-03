# Test Coverage Roadmap to 95%

## Current State (Baseline)

**Coverage:** 68% (3,746 of 5,515 statements)
**Passing Tests:** 749 of 752
**Failing Tests:** 3 (all fixable)
**Test Count:** 752 tests across 30 test files
**Test Code Size:** 9,470 LOC

## Gap Analysis

| Category | Current | Target | Gap | Statements | Priority |
|----------|---------|--------|-----|------------|----------|
| Core Business Logic | 97% | 95%+ | ✓ DONE | Kill-switches | P0 |
| Scoring Strategies | 95% | 95%+ | ✓ DONE | Interior, Location | P0 |
| Cost Estimation | 98% | 95%+ | ✓ DONE | Rates, Estimator | P0 |
| Pipeline Execution | 34% | 90%+ | 60 | **CRITICAL** | P0 |
| Property Analysis | 24% | 90%+ | 35 | **CRITICAL** | P0 |
| Tier Classification | 26% | 90%+ | 25 | **CRITICAL** | P0 |
| Data Integration | 85% | 90%+ | 12 | High | P1 |
| Enrichment Merge | 12% | 90%+ | 68 | **CRITICAL** | P1 |
| County API | 16% | 90%+ | 167 | Medium | P2 |
| Image Extraction | 10-28% | 80%+ | 400+ | Low | P2 |

## Phase-Based Roadmap

### Phase 0: Emergency Fixes (0.5 hours) - Week 1

**Objective:** Eliminate failing tests and low-hanging fruit

**Tasks:**
1. Fix confidence scorer assertions (test_score_inference_basic) - 20 min
2. Fix get_source_reliability test - 10 min
3. Fix deal_sheets CSV loading - 20 min

**Expected Coverage Gain:** 68% → 69%
**Effort:** 0.5 hours (1 developer)
**Owner:** Test automation engineer

**Deliverables:**
- All 752 tests passing
- No test failures in CI/CD

---

### Phase 1: Core Workflows (5 hours) - Week 1-2

**Objective:** Test main entry points and orchestration layers

**Tasks:**

1. **Pipeline Orchestrator (2 hours)**
   - File: `tests/integration/test_pipeline_orchestrator.py`
   - Tests:
     - `test_run_complete_workflow()` - Full pipeline execution
     - `test_run_with_empty_properties()` - Edge case
     - `test_run_with_mixed_valid_invalid_properties()` - Robustness
     - `test_run_preserves_property_data()` - Data integrity
     - `test_run_generates_output_csv()` - I/O
   - Coverage Impact: +26 percentage points (91 LOC)
   - Difficulty: Medium

2. **Property Analyzer (1.5 hours)**
   - File: `tests/services/test_property_analyzer.py`
   - Tests:
     - `test_analyze_property_full_workflow()` - Complete analysis
     - `test_analyze_property_no_enrichment_available()` - Graceful degradation
     - `test_analyze_property_failed_kill_switch_logs_failures()` - Error tracking
     - `test_analyze_batch_properties()` - Batch operations
   - Coverage Impact: +18 percentage points (46 LOC)
   - Difficulty: Medium

3. **Tier Classifier (1.5 hours)**
   - File: `tests/services/test_tier_classifier.py`
   - Tests:
     - Parametrized boundary tests (360, 480 points)
     - All tier ranges (PASS, CONTENDER, UNICORN)
     - Edge cases (0 score, 600 score)
   - Coverage Impact: +15 percentage points (34 LOC)
   - Difficulty: Low

**Expected Coverage Gain:** 69% → 82%
**Effort:** 5 hours (1 developer)
**Owner:** Test automation engineer

**Deliverables:**
- test_pipeline_orchestrator.py (350 LOC)
- test_property_analyzer.py (250 LOC)
- test_tier_classifier.py (200 LOC)
- CI/CD integration tests automated

---

### Phase 2: Data Integration (3 hours) - Week 2-3

**Objective:** Complete enrichment and data merging tests

**Tasks:**

1. **Enrichment Merger (2 hours)**
   - File: `tests/services/test_enrichment_merger_comprehensive.py`
   - Tests:
     - County assessor data merge
     - HOA & tax data merge
     - Location data merge (school, distances, commute)
     - AZ-specific features (solar, pool, roof/HVAC age)
     - Enum conversions (SewerType, Orientation, SolarStatus)
     - Batch operations with partial enrichment
     - Null value handling
   - Coverage Impact: +20 percentage points (77 LOC)
   - Difficulty: Low (straightforward merge operations)

2. **Data Integration Gaps (1 hour)**
   - Fill remaining coverage gaps in merge_strategy.py
   - Parametrized tests for edge cases
   - Coverage Impact: +5 percentage points
   - Difficulty: Low

**Expected Coverage Gain:** 82% → 87%
**Effort:** 3 hours (1 developer)
**Owner:** Test automation engineer

**Deliverables:**
- test_enrichment_merger_comprehensive.py (300 LOC)
- Merge strategy parametrized tests
- All data integration tests passing

---

### Phase 3: External Services (4 hours) - Week 3-4

**Objective:** Mock-based tests for external APIs

**Tasks:**

1. **County Assessor Client with respx (2 hours)**
   - File: `tests/services/county_data/test_assessor_client_mock.py`
   - Tests:
     - Successful property data retrieval (mocked HTTP)
     - 404 handling (property not found)
     - 429 rate limiting
     - Malformed response handling
     - Batch operations
     - Authentication token validation
   - Coverage Impact: +15 percentage points (200 LOC)
   - Difficulty: Medium (requires respx + httpx mocking)
   - Pattern: Use respx.mock decorator and httpx.Response

2. **Image Extraction Basics (2 hours)**
   - File: `tests/services/image_extraction/test_extractors_mock.py`
   - Tests:
     - Zillow extractor with mocked page
     - Redfin extractor with mocked page
     - Image collection and deduplication
     - Timeout handling
   - Coverage Impact: +15 percentage points (150+ LOC)
   - Difficulty: Medium (async + browser automation)
   - Pattern: Mock Playwright page object with AsyncMock

**Expected Coverage Gain:** 87% → 92%
**Effort:** 4 hours (1 developer)
**Owner:** Test automation engineer

**Deliverables:**
- test_assessor_client_mock.py (250 LOC)
- test_extractors_mock.py (200 LOC)
- respx integration in conftest.py
- Async test patterns established

---

### Phase 4: Final Push (2 hours) - Week 4

**Objective:** Capture remaining edge cases and boundary conditions

**Tasks:**

1. **Negative Test Cases & Edge Cases (1.5 hours)**
   - Kill-switch boundary values (exactly at 7000 sqft, 15000 sqft)
   - Scoring with null/extreme values
   - Cost estimation with 0 sqft, negative prices
   - Enum conversion errors
   - Coverage Impact: +2 percentage points
   - Difficulty: Low

2. **Performance & Integration Finalization (0.5 hours)**
   - Verify all 752+ tests pass in <60 seconds
   - Check coverage report excludes test files
   - Update CI/CD coverage threshold to 95%
   - Coverage Impact: +1 percentage point
   - Difficulty: Low

**Expected Coverage Gain:** 92% → 95%+
**Effort:** 2 hours (1 developer)
**Owner:** Test automation engineer

**Deliverables:**
- test_edge_cases.py (150 LOC)
- Updated .coveragerc with 95% threshold
- CI/CD pipeline updated
- Coverage report (HTML)

---

## Implementation Schedule

### Week 1
- **Monday-Tuesday:** Phase 0 (emergency fixes)
- **Wednesday-Friday:** Phase 1, Part 1 (Pipeline tests)

### Week 2
- **Monday-Wednesday:** Phase 1, Part 2 (Property analyzer)
- **Thursday-Friday:** Phase 2, Part 1 (Enrichment merger)

### Week 3
- **Monday-Tuesday:** Phase 2, Part 2 + Phase 3, Part 1 (County API)
- **Wednesday-Friday:** Phase 3, Part 2 (Image extraction)

### Week 4
- **Monday-Tuesday:** Phase 4 (Edge cases)
- **Wednesday:** Final review and reporting
- **Thursday-Friday:** Follow-up fixes and optimization

**Total Calendar Time:** 4 weeks
**Total Development Hours:** ~14.5 hours (1 FTE)

---

## Success Criteria

### Coverage Metrics

| Metric | P0 | P1 | P2 | P3 | Final |
|--------|-----|-----|-----|-----|--------|
| **Overall Coverage** | 69% | 82% | 87% | 92% | 95% |
| **Critical Modules** | 50% | 80% | 90% | 95% | 95%+ |
| **Passing Tests** | 752 | 850+ | 920+ | 970+ | 1000+ |
| **Test Execution Time** | <60s | <90s | <120s | <150s | <180s |

### Quality Metrics

- [ ] Zero failing tests in all phases
- [ ] No test flakiness (100% deterministic)
- [ ] All tests run in < 3 minutes
- [ ] Coverage reports generated automatically
- [ ] Coverage badges in README.md
- [ ] CI/CD gates enforce 95% minimum

### Code Quality

- [ ] All new tests follow existing patterns
- [ ] Comprehensive docstrings on all test functions
- [ ] Parametrized tests for boundary conditions
- [ ] Mock/spy patterns documented
- [ ] pytest fixtures organized by concern

---

## Risk Mitigation

### Risk 1: Async Test Complexity
**Probability:** Medium
**Impact:** Delays image extraction tests
**Mitigation:** Start with synchronous mocks, gradually add async
**Fallback:** Focus on non-async extractors (standardizer, deduplicator)

### Risk 2: External API Mocking Issues
**Probability:** Low
**Impact:** 1-2 hour delay in county assessor tests
**Mitigation:** Use respx early in Phase 3, test setup before main tests
**Fallback:** Skip actual API tests, mock all responses

### Risk 3: Test Runtime Growth
**Probability:** Medium
**Impact:** CI/CD timeout if tests exceed 3 minutes
**Mitigation:** Profile slow tests, parallelize execution with pytest-xdist
**Fallback:** Split into fast/slow test suites

### Risk 4: Coverage Tool Issues
**Probability:** Low
**Impact:** Inaccurate coverage reporting
**Mitigation:** Use coverage.py exclusively, document thresholds
**Fallback:** Manual coverage spot-checks

---

## Tools & Dependencies

**Already Available:**
- pytest (test framework)
- pytest-cov (coverage measurement)
- pytest-asyncio (async test support)
- respx (HTTP mocking)
- unittest.mock (built-in mocking)

**Recommended Additions:**
- pytest-xdist (parallel test execution)
- pytest-benchmark (performance tests)
- coverage-badge (CI/CD integration)

**Optimization Commands:**
```bash
# Run tests in parallel (4 workers)
pytest -n 4

# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Run only fast tests
pytest -m "not slow"

# Profile test execution
pytest --durations=10
```

---

## Maintenance Plan (Post-95%)

Once 95% coverage is achieved, establish practices to maintain it:

1. **Coverage Gates in CI/CD**
   - Fail builds if coverage drops below 95%
   - Require new code to have 100% test coverage
   - Block PRs that reduce coverage

2. **Regular Coverage Audits**
   - Weekly coverage trend reports
   - Monthly deep-dives on new gaps
   - Quarterly retrospectives

3. **Test Maintenance**
   - Update tests when code changes
   - Refactor duplicated test patterns
   - Keep fixtures organized

4. **Documentation**
   - Maintain test README.md
   - Document complex test patterns
   - Update this roadmap quarterly

---

## Estimation Summary

| Phase | Hours | Calendar Days | Cumulative |
|-------|-------|----------------|-----------|
| P0 | 0.5 | 0.5 | 0.5 |
| P1 | 5.0 | 3 | 5.5 |
| P2 | 3.0 | 2 | 8.5 |
| P3 | 4.0 | 2.5 | 12.5 |
| P4 | 2.0 | 1 | 14.5 |
| **Total** | **14.5** | **9** | **14.5** |

**Assumptions:**
- 1 FTE developer
- 6-7 hours productive coding/day
- Code review + CI/CD integration included
- No major blockers or rework needed

---

## Approval & Sign-off

- [ ] Test Automation Lead: Approves roadmap
- [ ] Development Manager: Approves schedule
- [ ] Project Manager: Approves resource allocation
- [ ] QA Lead: Reviews test quality standards

---

## Related Documents

1. **TEST_COVERAGE_ANALYSIS.md** - Detailed coverage gaps and module analysis
2. **RECOMMENDED_TESTS.md** - Ready-to-implement test code
3. **.coverage** - Current coverage database (SQLite)
4. **htmlcov/index.html** - HTML coverage report

---

## Questions & Next Steps

### Q: Can we reach 95% in parallel work streams?
**A:** Yes - Phase 1 & 2 can be parallelized with 2 developers. Phase 3 requires integration knowledge, so 1 developer optimal.

### Q: What if we prioritize speed over coverage?
**A:** Focus on Phase 0 (emergency) + Phase 1 (core workflows). This gets to 82% in 5.5 hours, acceptable MVP.

### Q: Should we add performance tests?
**A:** Yes, in Phase 4 after functional coverage complete. Add to test_benchmarks/ directory.

### Q: How do we handle flaky async tests?
**A:** Use pytest-asyncio fixtures, mock external services, avoid real I/O in tests.

**Contact:** test-automation@project.local
**Last Updated:** December 2, 2025
