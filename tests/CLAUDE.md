# tests/CLAUDE.md

---
last_updated: 2025-12-02
updated_by: Claude Code (Sonnet 4.5)
staleness_hours: 72
---

## Purpose

Comprehensive pytest test suite for the PHX Home Analysis pipeline with 1063+ tests covering unit tests, integration tests, service layer tests, and benchmarks.

## Directory Structure

```
tests/
├── conftest.py                      # Shared pytest fixtures (property, enrichment, config)
├── README.md                        # Comprehensive test documentation
├── QUICK_START.md                   # Quick reference for running tests
├── unit/                            # Unit tests (domain, kill-switches, scoring)
│   ├── test_domain.py              # Domain models, enums, value objects (67 tests)
│   ├── test_kill_switch.py         # Kill switch filters and criteria (75 tests)
│   ├── test_scorer.py              # Property scoring & tier classification (46 tests)
│   ├── test_lib_kill_switch.py     # Kill-switch library tests
│   ├── test_validation.py          # Schema validation tests
│   ├── test_repositories.py        # Data repository tests
│   ├── test_cost_estimation.py     # Cost calculation tests
│   ├── test_county_pipeline.py     # County API pipeline tests
│   ├── test_ai_enrichment.py       # AI enrichment tests
│   ├── test_quality_metrics.py     # Data quality tracking tests
│   ├── test_state_manager.py       # State management tests
│   ├── test_extraction_stats.py    # Extraction statistics tests
│   ├── test_deduplicator.py        # Address deduplication tests
│   ├── test_standardizer.py        # Address standardization tests
│   ├── test_url_validator.py       # URL validation tests
│   ├── test_logging_utils.py       # Logging utilities tests
│   ├── test_processing_pool.py     # Parallel processing tests
│   ├── test_proxy_extension_builder.py # Proxy extension tests
│   ├── README_REPOSITORIES.md      # Repository test documentation
│   └── README_DEDUPLICATOR_TESTS.md # Deduplication test guide
├── integration/                     # Integration tests (full pipeline)
│   ├── README.md                   # Integration test guide
│   ├── test_pipeline.py            # End-to-end pipeline (31 tests)
│   ├── test_kill_switch_chain.py   # Severity system validation (27 tests)
│   ├── test_deal_sheets_simple.py  # Data loading & merge (5 tests)
│   └── test_proxy_extension.py     # Proxy extension integration
├── services/                        # Service layer tests
│   ├── data_integration/
│   │   ├── test_field_mapper.py    # Field mapping tests
│   │   └── test_merge_strategy.py  # Data merge strategy tests
│   └── image_extraction/
│       └── test_orchestrator.py    # Image extraction orchestration
├── benchmarks/                      # Performance benchmarks
│   └── test_lsh_performance.py     # LSH optimization benchmarks
├── test_reporters.py                # Test result reporters
├── test_data_cache.py               # Data caching tests
└── test_conflict_detection.py       # Data conflict detection tests
```

## Key Files

### conftest.py (638 lines)
Central pytest configuration providing reusable fixtures:

**Property Fixtures:**
- `sample_property()` - Basic 4bd/2ba property, passes all kill-switches ($475k)
- `sample_unicorn_property()` - High-scoring 5bd/3.5ba property ($650k, >480pts)
- `sample_failed_property()` - Property with $200/mo HOA (fails kill-switch)
- `sample_septic_property()` - Property with septic system (fails kill-switch)
- `sample_property_minimal()` - Property with minimal data (many None fields)
- `sample_properties()` - Collection of 6 varied properties

**Enrichment Data Fixtures:**
- `sample_enrichment()` - Dict of enrichment data
- `sample_enrichment_data()` - EnrichmentData value object

**Configuration Fixtures:**
- `mock_config()` - AppConfig for testing
- `mock_scoring_weights()` - ScoringWeights configuration
- `mock_tier_thresholds()` - TierThresholds configuration

**Value Object Fixtures:**
- `sample_scores()` - List of Score objects
- `sample_score_breakdown()` - ScoreBreakdown value object

### Test Documentation Files
- `README.md` - Comprehensive testing guide (307 lines)
- `QUICK_START.md` - Quick command reference (192 lines)
- `integration/README.md` - Integration test guide (140 lines)
- `unit/README_REPOSITORIES.md` - Repository pattern tests
- `unit/README_DEDUPLICATOR_TESTS.md` - Deduplication test guide

## Running Tests

### Run All Tests
```bash
# All tests (1063+)
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Service layer tests
pytest tests/services/ -v

# Quick summary
pytest tests/ -q
```

### Run Specific Test Files
```bash
# Domain models
pytest tests/unit/test_domain.py -v

# Kill-switch logic
pytest tests/unit/test_kill_switch.py -v

# Scoring system
pytest tests/unit/test_scorer.py -v

# Full pipeline
pytest tests/integration/test_pipeline.py -v

# Severity chain
pytest tests/integration/test_kill_switch_chain.py -v
```

### Run Specific Test Classes/Methods
```bash
# Single test class
pytest tests/unit/test_domain.py::TestTierEnum -v

# Single test method
pytest tests/unit/test_kill_switch.py::TestNoHoaKillSwitch::test_passes_when_hoa_fee_is_zero -v

# Pattern matching
pytest tests/ -k "kill_switch" -v
pytest tests/ -k "boundary" -v
```

### Debugging Options
```bash
# Show print statements
pytest tests/unit/ -s

# Short traceback
pytest tests/unit/ --tb=short

# Stop on first failure
pytest tests/unit/ -x

# Run only failing tests
pytest tests/unit/ --lf

# Drop to debugger on failure
pytest tests/unit/ --pdb

# Show slowest tests
pytest tests/unit/ --durations=10
```

### Coverage
```bash
# Run with coverage report
pytest tests/ --cov=src --cov-report=term-missing

# Coverage for specific module
pytest tests/unit/ --cov=src.phx_home_analysis.domain --cov-report=html
```

## Test Categories

### Unit Tests (unit/)
**Focus:** Individual components in isolation

**Key Test Files:**
- `test_domain.py` (67 tests) - Enums, value objects, entities
- `test_kill_switch.py` (75 tests) - Kill-switch criteria (NO_HOA, CITY_SEWER, etc.)
- `test_scorer.py` (46 tests) - Scoring calculations, tier classification
- `test_validation.py` - Pydantic schema validation
- `test_repositories.py` - Data access patterns (CSV/JSON)
- `test_cost_estimation.py` - Monthly cost calculations
- `test_quality_metrics.py` - Data quality tracking

**Coverage Goals:** >95% for domain models and kill-switches, >85% for scoring

### Integration Tests (integration/)
**Focus:** Multi-component workflows and end-to-end scenarios

**Key Test Files:**
- `test_pipeline.py` (31 tests) - Full property processing (filter → score)
- `test_kill_switch_chain.py` (27 tests) - Severity accumulation system
- `test_deal_sheets_simple.py` (5 tests) - Data loading and merge validation

**Key Scenarios:**
- Complete data through full pipeline
- Incomplete/missing data handling
- Severity threshold testing (HARD vs SOFT criteria)
- CSV input/output formatting

### Service Tests (services/)
**Focus:** Service layer components

**Areas Covered:**
- Data integration (field mapping, merge strategies)
- Image extraction orchestration
- Multi-source data reconciliation

### Benchmarks (benchmarks/)
**Focus:** Performance and optimization

**Key Tests:**
- LSH (Locality Sensitive Hashing) performance tests
- Address deduplication efficiency

## Fixtures Deep Dive

### Property Test Data

**sample_property** (Standard Case):
- 123 Desert Rose Ln, Phoenix, AZ 85001
- 4bd/2ba, 2200 sqft, $475,000
- Lot: 9,500 sqft, Built: 2010
- Garage: 2 spaces, Sewer: City, HOA: $0
- North orientation, School rating: 7.5
- **Passes all kill-switches**

**sample_unicorn_property** (High-Scoring):
- 500 Camelback Rd, Paradise Valley, AZ 85253
- 5bd/3.5ba, 3500 sqft, $650,000
- Lot: 12,000 sqft, Built: 2015
- Garage: 3 spaces, Pool, Owned solar
- NE orientation, School rating: 9.5
- **Score: >480 points (Unicorn tier)**

**sample_failed_property** (HOA Failure):
- 789 Sunset Dr, Scottsdale, AZ 85251
- 4bd/2ba, 2100 sqft, $450,000
- **HOA: $200/mo (FAILS kill-switch)**

**sample_septic_property** (Septic Failure):
- 456 Desert Road, Apache Junction, AZ 85220
- 4bd/2ba, 2000 sqft, $380,000
- **Sewer: Septic (FAILS kill-switch)**

**sample_property_minimal** (Edge Case):
- 100 Main St, Phoenix, AZ 85001
- Only required fields populated
- All optional fields set to None
- **Tests missing data handling**

### Using Fixtures in Tests

```python
def test_with_fixture(sample_property):
    """Tests automatically receive fixtures as parameters."""
    assert sample_property.beds == 4
    assert sample_property.hoa_fee == 0

def test_with_collection(sample_properties):
    """sample_properties has 6 varied properties."""
    assert len(sample_properties) == 6
```

## Kill-Switch Testing

### Kill-Switch Criteria Reference

| Criterion | Type | Severity | Requirement |
|-----------|------|----------|-------------|
| NO_HOA | HARD | instant | hoa_fee = 0 or None |
| MIN_BEDROOMS | HARD | instant | beds >= 4 |
| MIN_BATHROOMS | HARD | instant | baths >= 2.0 |
| CITY_SEWER | SOFT | 2.5 | sewer_type == 'city' |
| NO_NEW_BUILD | SOFT | 2.0 | year_built < 2024 |
| MIN_GARAGE | SOFT | 1.5 | garage_spaces >= 2 |
| LOT_SIZE | SOFT | 1.0 | 7,000-15,000 sqft |

### Verdict Rules
- **HARD fail** → FAIL (immediate, no accumulation)
- **SOFT severity >= 3.0** → FAIL
- **SOFT severity >= 1.5** → WARNING
- **SOFT severity < 1.5** → PASS

### Boundary Testing
Tests validate exact boundary conditions:
- Lot size: 6,999 (fail) vs 7,000 (pass)
- Lot size: 15,000 (pass) vs 15,001 (fail)
- Year: 2023 (pass) vs 2024 (fail)
- Baths: 1.9 (fail) vs 2.0 (pass)
- HOA: $0 (pass) vs $1 (fail)

## Scoring System Testing

### Scoring Structure (600 points max)
- **Location:** 230 points (School: 50, Safety: 50, Quietness: 50, Grocery: 40, etc.)
- **Systems:** 180 points (Roof: 50, Plumbing: 40, Backyard: 40, Pool: 30, etc.)
- **Interior:** 190 points (Kitchen: 40, Master: 40, Light: 30, Ceilings: 30, etc.)

### Tier Classification
- **Unicorn:** >480 points (80%+ of max)
- **Contender:** 360-480 points (60-80%)
- **Pass:** <360 points (<60%)
- **Failed:** Any kill-switch failure

### Score Calculation Formula
```
weighted_score = (base_score / 10) * weight
```

Where:
- `base_score`: 0-10 rating
- `weight`: Point weight for criterion
- Example: (7.5 / 10) * 50 = 37.5 points

## Writing New Tests

### Test Naming Convention
```python
def test_<feature>_<scenario>_<expected_result>():
    """Clear docstring explaining what is tested."""
```

### Arrange-Act-Assert Pattern
```python
def test_kill_switch_fails_with_hoa_fee(sample_property):
    # Arrange - Set up test data
    sample_property.hoa_fee = 100

    # Act - Execute the code being tested
    kill_switch = NoHoaKillSwitch()
    result = kill_switch.check(sample_property)

    # Assert - Verify the result
    assert result is False
```

### Testing Exceptions
```python
def test_invalid_score_raises_error():
    """Test that invalid data raises appropriate exceptions."""
    with pytest.raises(ValueError):
        Score(criterion="Test", base_score=10.1, weight=50)
```

### Testing Computed Properties
```python
def test_price_per_sqft_calculation(sample_property):
    """Verify computed property calculations."""
    expected = sample_property.price_num / sample_property.sqft
    assert abs(sample_property.price_per_sqft - expected) < 1.0
```

## Dependencies

### Testing Framework
- **pytest** (9.0.1+) - Test framework
- **pytest-cov** (7.0.0+) - Coverage reporting
- **pytest-asyncio** (1.3.0+) - Async test support
- **pytest-anyio** (4.12.0+) - AnyIO fixtures
- **pytest-respx** (0.22.0+) - HTTP mocking

### Project Dependencies
All tests depend on:
- `src.phx_home_analysis.domain` - Domain models
- `src.phx_home_analysis.config` - Configuration
- `src.phx_home_analysis.services` - Service layer
- `src.phx_home_analysis.validation` - Schemas

## Test Execution Stats

**Total Tests:** 1063+

**Execution Time:**
- Unit tests: ~0.2 seconds
- Integration tests: ~0.5 seconds
- Full suite: ~1.2 seconds
- Average per test: ~1ms

**Current Status:** All tests passing ✓

## Pending Tasks

- [ ] Add performance regression tests for scoring pipeline
- [ ] Create fixtures for image assessment tests
- [ ] Add end-to-end tests for multi-agent workflow
- [ ] Expand test coverage for edge cases in data merge strategies
- [ ] Add property-based testing with Hypothesis for kill-switch boundaries
- [ ] Create test data files in fixtures/ directory (sample_properties.csv, sample_enrichment.json)
- [ ] Add mutation testing to validate test suite quality

## Key Learnings

### Testing Patterns
- **Boundary testing is critical:** Kill-switch thresholds need exact boundary validation (6999 vs 7000)
- **Fixture reuse:** Shared fixtures in conftest.py ensure test consistency and reduce duplication
- **Severity accumulation:** SOFT criteria accumulate (2.5 + 1.5 = 4.0), requiring careful test design
- **None handling:** All domain logic must gracefully handle None/missing values

### Common Test Failures
- **Floating point comparison:** Use `abs(a - b) < epsilon` instead of `a == b` for scores
- **Enum string matching:** Case-insensitive matching required ("CITY" vs "city")
- **Fixture scope:** Property fixtures are function-scoped, mutations don't affect other tests
- **Path handling:** Windows paths in tests need proper escaping or raw strings

### Test Data Management
- **Fixture factories:** Use fixtures for consistent test data, not hardcoded values
- **Edge cases first:** Test None, empty, boundary conditions before happy path
- **Realistic data:** Use actual Phoenix addresses and market prices for meaningful tests
- **Isolation:** Each test should be independently runnable

### Performance Considerations
- **Parallel execution:** Tests are designed for pytest-xdist parallel execution
- **Fast fixtures:** Fixtures avoid I/O and external calls for speed
- **Mock external services:** County API, web scraping mocked in unit tests
- **Benchmark separately:** Performance tests isolated in benchmarks/ directory

## References

- Pytest documentation: `tests/README.md`
- Quick start guide: `tests/QUICK_START.md`
- Integration test guide: `tests/integration/README.md`
- Repository tests: `tests/unit/README_REPOSITORIES.md`
- Deduplication tests: `tests/unit/README_DEDUPLICATOR_TESTS.md`
- Project scoring logic: `src/phx_home_analysis/config/scoring_weights.py`
- Kill-switch configuration: `src/phx_home_analysis/config/constants.py`
- Domain models: `src/phx_home_analysis/domain/entities.py`
