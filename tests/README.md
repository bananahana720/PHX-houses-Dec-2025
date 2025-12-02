# PHX Home Analysis - Unit Tests

Comprehensive unit test suite for the PHX Home Analysis pipeline with 188+ tests covering domain models, kill switches, and scoring logic.

## Test Structure

```
tests/
├── conftest.py              # Shared pytest fixtures
├── unit/
│   ├── __init__.py
│   ├── test_domain.py       # Domain models, enums, value objects
│   ├── test_kill_switch.py  # Kill switch filters and criteria
│   └── test_scorer.py       # Property scoring and tier classification
├── fixtures/                # Sample data files (to be populated)
│   ├── sample_properties.csv
│   └── sample_enrichment.json
└── integration/             # Integration tests (placeholder)
```

## Test Coverage

### Total Tests: 188

#### Test Files:
- **test_domain.py**: 67 tests
  - Tier enum (11 tests)
  - RiskLevel enum (5 tests)
  - SewerType enum (3 tests)
  - SolarStatus enum (3 tests)
  - Orientation enum (8 tests)
  - Address value object (5 tests)
  - RiskAssessment value object (6 tests)
  - Property entity (20 tests)
  - Enum string normalization (3 tests)

- **test_kill_switch.py**: 75 tests
  - NoHoaKillSwitch (7 tests)
  - CitySewerKillSwitch (7 tests)
  - MinGarageKillSwitch (7 tests)
  - MinBedroomsKillSwitch (7 tests)
  - MinBathroomsKillSwitch (8 tests)
  - LotSizeKillSwitch (11 tests)
  - NoNewBuildKillSwitch (8 tests)
  - KillSwitchFilter integration (13 tests)
  - Edge cases (8 tests)

- **test_scorer.py**: 46 tests
  - PropertyScorer (13 tests)
  - Tier classification (8 tests)
  - Score value object (10 tests)
  - ScoreBreakdown value object (11 tests)
  - Manual assessments (2 tests)
  - Real-world scenarios (3 tests)

## Running Tests

### Run All Unit Tests
```bash
pytest tests/unit/ -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_domain.py -v
pytest tests/unit/test_kill_switch.py -v
pytest tests/unit/test_scorer.py -v
```

### Run Specific Test Class
```bash
pytest tests/unit/test_domain.py::TestTierEnum -v
pytest tests/unit/test_kill_switch.py::TestKillSwitchFilter -v
```

### Run Specific Test
```bash
pytest tests/unit/test_domain.py::TestTierEnum::test_tier_values -v
```

### Run with Short Traceback
```bash
pytest tests/unit/ --tb=short
```

### Run Failing Tests Only
```bash
pytest tests/unit/ --lf
```

## Test Fixtures (conftest.py)

### Property Fixtures
- `sample_property()` - Basic property with all fields, passes all kill switches
- `sample_unicorn_property()` - High-scoring property (>400 points)
- `sample_failed_property()` - Property with HOA fee (fails kill switch)
- `sample_septic_property()` - Property with septic system (fails kill switch)
- `sample_property_minimal()` - Property with only required fields
- `sample_properties()` - List of 6 properties with various characteristics

### Enrichment Data Fixtures
- `sample_enrichment()` - Dict of enrichment data
- `sample_enrichment_data()` - EnrichmentData value object

### Configuration Fixtures
- `mock_config()` - AppConfig for testing
- `mock_scoring_weights()` - ScoringWeights configuration
- `mock_tier_thresholds()` - TierThresholds configuration

### Value Object Fixtures
- `sample_scores()` - List of Score objects
- `sample_score_breakdown()` - ScoreBreakdown value object

## Key Test Scenarios

### Kill Switch Tests

**Happy Path:**
- Property with hoa_fee=0 passes NO_HOA kill switch
- Property with city sewer passes CITY_SEWER kill switch
- Property with 2+ garage spaces passes MIN_GARAGE kill switch
- Property with 4+ bedrooms passes MIN_BEDROOMS kill switch
- Property with 2+ bathrooms passes MIN_BATHROOMS kill switch
- Property with lot size 7,000-15,000 sqft passes LOT_SIZE kill switch
- Property built before 2024 passes NO_NEW_BUILD kill switch

**Boundary Testing:**
- Lot size exactly 6,999 sqft (below minimum) - fails
- Lot size exactly 7,000 sqft (at minimum) - passes
- Lot size exactly 15,000 sqft (at maximum) - passes
- Lot size exactly 15,001 sqft (above maximum) - fails
- Year built 2023 - passes
- Year built 2024 - fails
- Garage spaces exactly 2 - passes
- Garage spaces exactly 1 - fails
- Bathrooms exactly 2.0 - passes
- Bathrooms exactly 1.9 - fails
- HOA fee exactly 0 - passes
- HOA fee exactly 1 - fails

**Edge Cases:**
- Missing/None values handled gracefully
- Unknown enum values default appropriately
- Multiple kill switch failures collected and reported

### Scoring Tests

**Score Calculations:**
- Weighted score formula: (base_score / 10) * weight
- Score breakdown aggregates location, systems, interior sections
- Tier classification:
  - >400 points: UNICORN
  - 300-400 points: CONTENDER
  - <300 points: PASS
  - Failed kill switches: FAILED

**Real-World Scenarios:**
- Good school district (9.5) scores better than poor (2.0)
- North-facing orientation scores better than west-facing
- Newer roof/HVAC (1 year old) scores better than old (20 years)

**Missing Data:**
- Scores calculated with neutral defaults (5.0)
- Enums default to UNKNOWN
- None values handled without errors

## Coverage Goals

- **Domain Models:** >95% coverage
  - All enums tested (values, properties, methods)
  - All value objects tested (creation, immutability, calculations)
  - All entity properties tested (computed properties, mutations)

- **Kill Switches:** >95% coverage
  - Each criterion tested individually
  - Integration tests with KillSwitchFilter
  - Boundary and edge cases verified

- **Scoring:** >85% coverage
  - Score calculations validated
  - Tier classification verified
  - ScoreBreakdown aggregation tested
  - Real-world scoring scenarios validated

## Writing New Tests

### Test Naming Convention
```python
def test_<feature>_<scenario>_<expected_result>(self):
    """Docstring explaining what is tested."""
```

### Test Structure Pattern
```python
# 1. Arrange - Set up test data
property = sample_property()
property.hoa_fee = 100

# 2. Act - Execute the code being tested
kill_switch = NoHoaKillSwitch()
result = kill_switch.check(property)

# 3. Assert - Verify the result
assert result is False
```

### Using Fixtures
```python
def test_with_fixture(self, sample_property):
    """Tests automatically receive fixtures as parameters."""
    assert sample_property.beds == 4
```

### Testing Exceptions
```python
def test_invalid_score_raises_error(self):
    """Test that invalid data raises appropriate exceptions."""
    with pytest.raises(ValueError):
        Score(criterion="Test", base_score=10.1, weight=50)
```

## Common Test Patterns

### Testing Boundary Values
```python
def test_boundary_condition(self):
    """Test values at exact boundaries."""
    # Just below minimum
    assert check(6999) is False

    # At minimum
    assert check(7000) is True

    # At maximum
    assert check(15000) is True

    # Just above maximum
    assert check(15001) is False
```

### Testing Computed Properties
```python
def test_computed_property(self, sample_property):
    """Verify property calculations."""
    # price_per_sqft = price / sqft
    expected = 475000 / 2200
    assert abs(sample_property.price_per_sqft - expected) < 1.0
```

### Testing Collections
```python
def test_collection_operations(self, sample_properties):
    """Test filtering and aggregating collections."""
    filter_service = KillSwitchFilter()
    passed, failed = filter_service.filter_properties(sample_properties)

    assert len(passed) > 0
    assert len(failed) > 0
    assert len(passed) + len(failed) == len(sample_properties)
```

## Debugging Tests

### Verbose Output
```bash
pytest tests/unit/test_domain.py -vv
```

### Show Print Statements
```bash
pytest tests/unit/ -s
```

### Drop to Debugger on Failure
```bash
pytest tests/unit/ --pdb
```

### Run with Timing Information
```bash
pytest tests/unit/ --durations=10
```

## CI/CD Integration

Tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run unit tests
  run: |
    pytest tests/unit/ -v --tb=short

- name: Verify all tests pass
  run: |
    pytest tests/unit/ -q
```

## Future Test Additions

- [ ] Repository tests (CSV/JSON loading)
- [ ] Configuration tests
- [ ] Pipeline orchestrator tests
- [ ] Integration tests (full pipeline end-to-end)
- [ ] Performance/benchmark tests
- [ ] Fixture data files (sample_properties.csv, sample_enrichment.json)
