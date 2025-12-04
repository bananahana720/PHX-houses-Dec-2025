# Quick Win Recommendations (Prioritized)

### P0 - Critical (Fix immediately)

1. **Fix 3 failing tests** (30 minutes)
   - `test_score_inference_basic` - Update assertion to match 0.9025
   - `test_get_source_reliability` - Similar fix
   - `test_load_ranked_csv_with_valid_data` - Fix path handling

2. **Add Pipeline Orchestrator tests** (2 hours)
   - Tests for `run()`, `analyze_single()`, error handling
   - Impact: +26 percentage points coverage

3. **Add Property Analyzer tests** (1.5 hours)
   - Test enrichment merge, filtering, scoring workflow
   - Impact: +18 percentage points coverage

### P1 - High (Next sprint)

4. **Add Tier Classifier tests** (1 hour)
   - Boundary condition tests (360, 480 point thresholds)
   - Impact: +15 percentage points coverage

5. **Add Enrichment Merger tests** (2 hours)
   - All merge scenarios (county data, AZ-specific, conversions)
   - Impact: +20 percentage points coverage

6. **Mock-based County Assessor tests** (2 hours)
   - Use respx for HTTP mocking
   - Impact: +15 percentage points coverage

### P2 - Medium (Future)

7. **Image extraction async tests** (3 hours)
   - Mock browser pages, test extraction logic
   - Impact: +18 percentage points coverage

8. **Negative test cases** (2 hours)
   - Boundary values, null handling, error paths
   - Impact: +8 percentage points coverage

---
