# Integration Tests - PHX Home Analysis

## Quick Start

Run all integration tests:
```bash
pytest tests/integration/ -v
```

## Test Structure

### 1. `test_pipeline.py` (31 tests)
End-to-end pipeline validation:
- Full property processing (filter → score)
- Enrichment data application
- CSV input/output
- Scoring variations
- Error handling

**Key Scenarios:**
- Complete data through full pipeline
- Incomplete/missing data handling
- Mixed batch processing
- CSV formatting
- Score breakdown validation

### 2. `test_kill_switch_chain.py` (27 tests)
Kill-switch severity system validation:
- HARD criteria (HOA, beds, baths) - immediate fail
- SOFT criteria (sewer, year, garage, lot) - severity accumulation
- WARNING threshold (>=1.5 severity)
- FAIL threshold (>=3.0 severity)
- Boundary conditions at critical thresholds

**Key Scenarios:**
- Single soft failures at each severity level
- Multiple failures accumulating
- Exact boundary testing
- Verdict consistency

### 3. `test_deal_sheets_simple.py` (5 tests)
Data loading and merge validation:
- CSV loading and parsing
- JSON enrichment loading
- Data merge preservation
- Directory structure

## Kill-Switch Severity Reference

| Criterion | Severity | Type | Requirement |
|-----------|----------|------|-------------|
| NO HOA | - | HARD | hoa_fee = 0 or None |
| Min 4 beds | - | HARD | beds >= 4 |
| Min 2 baths | - | HARD | baths >= 2.0 |
| City sewer | 2.5 | SOFT | sewer_type == 'city' |
| No new builds | 2.0 | SOFT | year_built < 2024 |
| 2+ car garage | 1.5 | SOFT | garage_spaces >= 2 |
| Lot size | 1.0 | SOFT | 7000-15000 sqft |

**Verdict Rules:**
- HARD fail → FAIL (no accumulation)
- SOFT severity >= 3.0 → FAIL
- SOFT severity >= 1.5 → WARNING
- SOFT severity < 1.5 → PASS

## Running Specific Tests

Run single test module:
```bash
pytest tests/integration/test_pipeline.py -v
pytest tests/integration/test_kill_switch_chain.py -v
pytest tests/integration/test_deal_sheets_simple.py -v
```

Run single test class:
```bash
pytest tests/integration/test_kill_switch_chain.py::TestSeverityAccumulation -v
pytest tests/integration/test_pipeline.py::TestFullPipeline -v
```

Run single test:
```bash
pytest tests/integration/test_pipeline.py::TestFullPipeline::test_pipeline_accepts_properties_with_all_data -v
```

Run with coverage:
```bash
pytest tests/integration/ --cov=src --cov-report=term-missing
```

## Fixtures Used

All tests share fixtures from `tests/conftest.py`:

- `sample_property` - Valid property with all required fields
- `sample_unicorn_property` - High-scoring property (5 bed/3.5 bath)
- `sample_failed_property` - Property with $200 HOA fee
- `sample_septic_property` - Property with septic system
- `sample_property_minimal` - Property with minimal data (many None fields)
- `sample_properties` - List of 6 properties with varied characteristics

## Test Execution Time

- Total: ~0.5 seconds
- Average per test: ~10ms

## Current Status

**48 tests - All Passing ✓**

- test_pipeline.py: 31 passing
- test_kill_switch_chain.py: 27 passing
- test_deal_sheets_simple.py: 5 passing

## Key Implementation Notes

1. **PropertyScorer.score()** returns ScoreBreakdown with:
   - `location_total` (0-230)
   - `systems_total` (0-180)
   - `interior_total` (0-190)
   - `total_score` (0-600)

2. **KillSwitchFilter.evaluate_with_severity()** returns:
   - verdict: KillSwitchVerdict enum (PASS, WARNING, FAIL)
   - severity: float accumulation score
   - failures: list of failure messages

3. **Kill-switch properties** are mutated by filter (adds verdict fields)

4. **CSV I/O** tests validate format and column presence only

## Troubleshooting

If tests fail:
1. Check fixture imports in conftest.py
2. Verify KillSwitchFilter and PropertyScorer APIs haven't changed
3. Ensure sample properties have required fields for the test

For details, see `INTEGRATION_TEST_SUMMARY.md`.
