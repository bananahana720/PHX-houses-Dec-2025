# Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/phx_home_analysis --cov-report=html

# Run specific test file
pytest tests/unit/test_scorer.py

# Run specific test
pytest tests/unit/test_scorer.py::test_school_district_scorer

# Run integration tests only
pytest tests/integration/

# Run with verbose output
pytest -v
```

### Test Structure

```
tests/
├── unit/                    # Unit tests (fast, no I/O)
│   ├── test_domain.py       # Test entities, value objects
│   ├── test_scorer.py       # Test scoring strategies
│   ├── test_kill_switch.py  # Test kill-switch logic
│   └── ...
├── integration/             # Integration tests (slower, with I/O)
│   ├── test_pipeline.py     # Test complete pipeline
│   ├── test_repositories.py # Test file I/O
│   └── ...
├── benchmarks/              # Performance tests
│   └── test_lsh_performance.py
├── fixtures/                # Test data fixtures
│   ├── sample_properties.json
│   └── ...
└── conftest.py              # Pytest configuration and fixtures
```

### Writing Tests

**Unit Test Example:**
```python
# tests/unit/test_scorer.py
import pytest
from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.services.scoring.strategies.location import SchoolDistrictScorer

def test_school_district_scorer_high_rating():
    """Test scorer with high school rating."""
    prop = Property(
        school_rating=9.0,
        # ... other required fields
    )
    scorer = SchoolDistrictScorer()
    assert scorer.score(prop) == 9.0  # 0-10 scale

def test_school_district_scorer_missing_data():
    """Test scorer with missing school rating."""
    prop = Property(school_rating=None)
    scorer = SchoolDistrictScorer()
    assert scorer.score(prop) == 5.0  # Neutral default
```

**Integration Test Example:**
```python
# tests/integration/test_pipeline.py
import pytest
from src.phx_home_analysis.pipeline.orchestrator import AnalysisPipeline

def test_complete_pipeline(sample_properties):
    """Test complete pipeline from CSV to reports."""
    pipeline = AnalysisPipeline()
    result = pipeline.run()

    assert len(result.passed_properties) > 0
    assert all(p.tier is not None for p in result.passed_properties)
    assert all(p.score_breakdown is not None for p in result.passed_properties)
```

---
