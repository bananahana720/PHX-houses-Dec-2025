# Failing Tests Analysis

### 1. test_deal_sheets_simple.py::TestDealSheetDataLoading::test_load_ranked_csv_with_valid_data

**Status:** FAILED
**Error:** CSV file not found or data loading issue
**Root Cause:** Deal sheet generator expects specific CSV structure
**Fix Priority:** MEDIUM - Path handling issue

### 2. test_ai_enrichment.py::TestConfidenceScorer::test_score_inference_basic

**Status:** FAILED
**Error:** `assert 0.9025 == 0.95` - Confidence score calculation mismatch
**Root Cause:** Test expects simple multiplication (0.95 * 1.0), but actual calculation uses compound confidence scoring
**Current Logic:** Field confidence × source reliability = 0.9025 (not 0.95)
**Fix Priority:** HIGH - Logic assertion incorrect; test needs alignment with actual algorithm

**Code Location:**
```python
# tests/unit/test_ai_enrichment.py:573
score = confidence_scorer.score_inference(inference)
assert score == 0.95  # WRONG - actual value is 0.9025
```

### 3. test_ai_enrichment.py::TestConfidenceScorer::test_get_source_reliability

**Status:** FAILED
**Error:** Source reliability calculation mismatch
**Root Cause:** Similar to test #2 - test assertion doesn't match implementation
**Fix Priority:** HIGH

---
