# Quick Start - Running Tests

## Install Dependencies

```bash
# Using uv (preferred)
uv pip install pytest

# Or using pip
pip install pytest
```

## Run All Tests

```bash
cd C:\Users\Andrew\Downloads\PHX-houses-Dec-2025

# Simple run
pytest tests/unit/

# Verbose output
pytest tests/unit/ -v

# Very verbose (show full assertions)
pytest tests/unit/ -vv

# Show print statements
pytest tests/unit/ -s

# Quick count
pytest tests/unit/ -q
```

## Run Specific Tests

```bash
# Single file
pytest tests/unit/test_domain.py

# Specific class
pytest tests/unit/test_kill_switch.py::TestNoHoaKillSwitch

# Specific test
pytest tests/unit/test_domain.py::TestTierEnum::test_tier_values
```

## Debugging

```bash
# Show why tests fail
pytest tests/unit/ --tb=short

# Drop to debugger on failure
pytest tests/unit/ --pdb

# Show slowest tests
pytest tests/unit/ --durations=10

# Stop on first failure
pytest tests/unit/ -x

# Run only failing tests
pytest tests/unit/ --lf
```

## Understanding Test Output

```
collected 188 items

tests/unit/test_domain.py::TestTierEnum::test_tier_values PASSED    [  1%]
tests/unit/test_domain.py::TestTierEnum::test_tier_colors PASSED    [  2%]
...

============================= 188 passed in 0.16s =============================
```

- **PASSED**: Test succeeded
- **FAILED**: Test failed
- **[  1%]**: Progress indicator
- **0.16s**: Total execution time

## Test Coverage

### test_domain.py (67 tests)
- Enums: Tier, RiskLevel, SewerType, SolarStatus, Orientation
- Value Objects: Address, RiskAssessment, Score, ScoreBreakdown
- Entity: Property (computed properties, financial calculations)
- String normalization of enum values

### test_kill_switch.py (75 tests)
- 7 kill switch criteria tested individually
- Integration with KillSwitchFilter
- Boundary value testing
- Edge cases (None, missing data)

### test_scorer.py (46 tests)
- PropertyScorer orchestration
- Tier classification (Unicorn, Contender, Pass, Failed)
- Score calculations and aggregation
- Real-world scoring scenarios

## Common Commands

```bash
# Run and get summary
pytest tests/unit/ --tb=line -q

# Run specific category
pytest tests/unit/ -k "KillSwitch" -v

# Run tests matching pattern
pytest tests/unit/ -k "boundary" -v

# Exclude tests matching pattern
pytest tests/unit/ -k "not edge_case" -v
```

## What Each Test File Tests

| File | Focus | Tests |
|------|-------|-------|
| test_domain.py | Data models, enums, values | 67 |
| test_kill_switch.py | Property filtering rules | 75 |
| test_scorer.py | Scoring & classification | 46 |
| **TOTAL** | | **188** |

## Expected Output

All tests should show:
```
============================= 188 passed in 0.16s =============================
```

## Fixture Quick Reference

```python
# In your test
def test_something(self, sample_property):
    # sample_property has 4 beds, 2 baths, passes all kill switches
    assert sample_property.beds == 4

def test_collection(self, sample_properties):
    # sample_properties has 6 varied properties
    assert len(sample_properties) == 6
```

Available fixtures in conftest.py:
- `sample_property` - Standard property
- `sample_unicorn_property` - High-scoring
- `sample_failed_property` - Fails kill switch
- `sample_properties` - Collection of 6
- `sample_enrichment` - Enrichment data dict
- And 10 more...

## Troubleshooting

### "No module named 'pytest'"
```bash
uv pip install pytest
```

### "ModuleNotFoundError: No module named 'src'"
Ensure you're running from project root:
```bash
cd C:\Users\Andrew\Downloads\PHX-houses-Dec-2025
```

### "All tests pass locally but fail in CI"
- Check Python version matches (3.10+)
- Verify all dependencies installed
- Run: `pytest tests/unit/ -v`

## Next Steps

1. Run: `pytest tests/unit/ -v`
2. Review failing tests (if any)
3. Read docs/artifacts/TESTING_SUMMARY.md for details
4. Check tests/README.md for comprehensive guide

## Tips

- Use `-x` flag to stop on first failure
- Use `-k pattern` to run specific tests
- Use `--tb=short` for cleaner output
- Use `-vv` when debugging test failures
- Use `--collect-only` to see all tests without running

---

**All 188 tests should pass in ~0.16 seconds.**
