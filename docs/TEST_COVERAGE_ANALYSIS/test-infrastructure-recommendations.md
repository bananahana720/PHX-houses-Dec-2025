# Test Infrastructure Recommendations

### 1. Fixture Organization (Current: Good)

Centralize in `tests/conftest.py`:
```python
# Already exists - add these missing factories:

@pytest.fixture
def property_factory():
    """Factory for creating test properties with variations."""
    def make_property(**overrides):
        defaults = {
            "street": "123 Test St",
            "city": "Phoenix",
            "state": "AZ",
            "price_num": 500000,
            "beds": 4,
            "baths": 2.0,
            "lot_sqft": 10000,
            "year_built": 2015,
            "garage_spaces": 2,
        }
        defaults.update(overrides)
        return Property(**defaults)
    return make_property

@pytest.fixture
def enrichment_factory():
    """Factory for creating test enrichment data."""
    def make_enrichment(**overrides):
        defaults = {
            "lot_sqft": 10000,
            "year_built": 2015,
            "garage_spaces": 2,
            "sewer_type": "city",
            "hoa_fee": 0,
        }
        defaults.update(overrides)
        return EnrichmentData(**defaults)
    return make_enrichment
```

### 2. Parametrized Tests Pattern

Improve test comprehensiveness:
```python
@pytest.mark.parametrize("score,expected_tier", [
    (0, Tier.PASS),
    (100, Tier.PASS),
    (359, Tier.PASS),
    (360, Tier.CONTENDER),
    (420, Tier.CONTENDER),
    (480, Tier.CONTENDER),
    (481, Tier.UNICORN),
    (600, Tier.UNICORN),
])
def test_tier_classification_ranges(score, expected_tier):
    """Test all tier boundaries with parametrized inputs."""
    classifier = TierClassifier(thresholds=...)
    prop = Property(score_breakdown=ScoreBreakdown(total_score=score))

    assert classifier.classify(prop) == expected_tier
```

### 3. Async Test Coverage

Improve pytest-asyncio usage:
```python
# Add to conftest.py
@pytest.fixture
async def async_property_repo():
    """Async repository fixture."""
    repo = AsyncPropertyRepository()
    yield repo
    await repo.cleanup()

# Use in tests
class TestAsyncPipeline:
    @pytest.mark.asyncio
    async def test_async_property_loading(self, async_property_repo):
        """Test async property loading."""
        properties = await async_property_repo.load_all_async()
        assert len(properties) > 0
```

### 4. Mock/Spy Pattern Documentation

Add to test files:
```python
from unittest.mock import MagicMock, patch, call
import respx

# Pattern 1: Service Mock
@pytest.fixture
def mock_scorer():
    """Mock scoring service."""
    scorer = MagicMock(spec=PropertyScorer)
    scorer.score.return_value = ScoreBreakdown(total_score=400)
    return scorer

# Pattern 2: HTTP Mock (respx)
@respx.mock
def test_with_http_mock(respx_mock):
    """Test with HTTP mocking."""
    respx_mock.get("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={"data": "value"})
    )

# Pattern 3: Spy (call tracking)
def test_with_spy():
    """Track method calls."""
    merger = EnrichmentMerger()
    merger.merge = MagicMock(wraps=merger.merge)

    # Call method
    merger.merge(prop, enrichment)

    # Verify call
    merger.merge.assert_called_once_with(prop, enrichment)
```

---
