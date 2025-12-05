# PHX Houses - Development Guide

**Generated:** 2025-12-05
**Python Version:** 3.10+ (recommended: 3.12 or 3.13)

---

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| uv | Latest | Package manager (preferred) |
| Git | 2.x | Version control |
| Node.js | 18+ | Playwright browsers |

---

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/example/phx-houses-dec-2025.git
cd phx-houses-dec-2025
```

### 2. Create Virtual Environment

```bash
# Using uv (recommended)
uv venv
source .venv/bin/activate  # Unix
.venv\Scripts\activate     # Windows

# Or using standard Python
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Using uv (recommended)
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

### 4. Install Playwright Browsers

```bash
playwright install chromium
```

### 5. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
# MARICOPA_ASSESSOR_TOKEN=your_token
# GREATSCHOOLS_API_KEY=your_key
```

### 6. Verify Installation

```bash
# Run smoke tests
pytest tests/unit/ -m smoke -v

# Check linting
ruff check src/

# Type check
mypy src/
```

---

## Project Layout

```
PHX-houses-Dec-2025/
├── src/phx_home_analysis/   # Main package
├── scripts/                  # CLI tools
├── tests/                    # Test suite
├── data/                     # Data files
├── docs/                     # Documentation
├── reports/                  # Generated output
├── pyproject.toml           # Project config
└── CLAUDE.md                # Project docs
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
```

### 2. Make Changes

Follow the patterns established in:
- Domain entities: `src/phx_home_analysis/domain/`
- Services: `src/phx_home_analysis/services/`
- Tests: `tests/unit/`

### 3. Run Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run specific test file
pytest tests/unit/test_kill_switch.py -v

# Run with coverage
pytest tests/unit/ --cov=src/phx_home_analysis --cov-report=html
```

### 4. Lint and Format

```bash
# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/

# Type check
mypy src/
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: description of change"
```

---

## Running the Pipeline

### Full Analysis

```bash
# Run complete pipeline
python scripts/phx_home_analyzer.py

# Or using the Typer CLI
python scripts/pipeline_cli.py run --all
```

### Individual Phases

```bash
# Phase 0: County data
python scripts/extract_county_data.py --all

# Phase 1: Image extraction
python scripts/extract_images.py --all

# Phase 3: Scoring
python scripts/analyze.py

# Phase 4: Reports
python -m scripts.deal_sheets
```

### Single Property

```bash
# Analyze specific address
python scripts/phx_home_analyzer.py "123 Main St, Phoenix, AZ"

# Or with CLI
python scripts/pipeline_cli.py run --address "123 Main St"
```

---

## Testing Guide

### Test Structure

```
tests/
├── unit/               # Fast, isolated tests
├── integration/        # Cross-component tests
└── live/               # Real API tests (skipped by default)
```

### Running Tests

```bash
# All unit tests
pytest tests/unit/ -v

# Skip slow tests
pytest tests/unit/ -m "not slow" -v

# Run live tests (requires network)
pytest tests/live/ -m live -v

# Run with verbose output
pytest tests/unit/ -v --tb=long
```

### Writing Tests

```python
# tests/unit/test_my_feature.py
import pytest
from phx_home_analysis.services.my_service import MyService

class TestMyService:
    def test_basic_functionality(self):
        service = MyService()
        result = service.process("input")
        assert result == "expected"

    @pytest.mark.slow
    def test_slow_operation(self):
        # Long-running test
        pass

    @pytest.mark.live
    def test_live_api(self):
        # Requires network
        pass
```

### Fixtures

Common fixtures are in `tests/conftest.py`:

```python
@pytest.fixture
def sample_property():
    """Return a sample Property for testing."""
    return Property(
        street="123 Main St",
        city="Phoenix",
        # ...
    )

@pytest.fixture
def mock_enrichment_repo():
    """Return a mock enrichment repository."""
    return MockEnrichmentRepository()
```

---

## Code Style

### Python Style Guide

- **Line length:** 100 characters
- **Imports:** Sorted by isort (via ruff)
- **Type hints:** Required for public functions
- **Docstrings:** Google style

### Example

```python
def calculate_score(
    property: Property,
    weights: ScoringWeights,
) -> ScoreBreakdown:
    """Calculate the 605-point score for a property.

    Args:
        property: Property entity with all required data.
        weights: Scoring weights configuration.

    Returns:
        ScoreBreakdown with section scores and total.

    Raises:
        ValueError: If property is missing required fields.
    """
    # Implementation
    pass
```

### Ruff Configuration

From `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py310"
select = ["E", "W", "F", "I", "B", "C4", "UP"]
```

---

## Adding New Features

### New Service

1. Create service module:

```python
# src/phx_home_analysis/services/my_service/__init__.py
from .client import MyServiceClient
from .models import MyModel

__all__ = ["MyServiceClient", "MyModel"]
```

2. Implement client:

```python
# src/phx_home_analysis/services/my_service/client.py
from ..base import BaseAPIClient

class MyServiceClient(BaseAPIClient):
    def __init__(self, api_key: str | None = None):
        super().__init__(base_url="https://api.example.com")
        self.api_key = api_key

    async def fetch_data(self, property_id: str) -> MyModel:
        response = await self._get(f"/properties/{property_id}")
        return MyModel.model_validate(response)
```

3. Add tests:

```python
# tests/unit/services/test_my_service.py
class TestMyServiceClient:
    async def test_fetch_data(self, respx_mock):
        respx_mock.get("https://api.example.com/properties/123").respond(
            json={"id": "123", "value": 42}
        )
        client = MyServiceClient()
        result = await client.fetch_data("123")
        assert result.value == 42
```

### New Scoring Strategy

1. Create strategy:

```python
# src/phx_home_analysis/services/scoring/strategies/my_strategy.py
from ..base import ScoringStrategy

class MyScoreStrategy(ScoringStrategy):
    name = "my_score"
    max_points = 30
    section = "A"  # Location

    def score(self, property: Property) -> int:
        if property.my_field is None:
            return 0
        return min(self.max_points, property.my_field * 3)
```

2. Register in scorer:

```python
# src/phx_home_analysis/services/scoring/scorer.py
from .strategies.my_strategy import MyScoreStrategy

class PropertyScorer:
    def __init__(self):
        self.strategies = {
            # ...existing...
            'my_score': MyScoreStrategy(),
        }
```

---

## Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.debug("Detailed info")
    logger.info("General info")
    logger.warning("Warning")
    logger.error("Error occurred")
```

### Enable Debug Logging

```bash
# Set log level
export LOG_LEVEL=DEBUG

# Or in Python
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Playwright not installed | `playwright install chromium` |
| Missing API key | Check `.env` file |
| Rate limited | Wait or use proxy rotation |
| Import errors | Reinstall with `uv pip install -e .` |

---

## CI/CD

### Pre-commit Checks

Before committing, run:

```bash
# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/

# Tests
pytest tests/unit/ -v
```

### GitHub Actions

The CI pipeline runs:

1. `ruff check` - Linting
2. `mypy src/` - Type checking
3. `pytest tests/unit/` - Unit tests
4. `pip-audit --strict` - Security scan

---

## Useful Commands

```bash
# Quick test run
pytest tests/unit/ -x -v

# Coverage report
pytest --cov=src/phx_home_analysis --cov-report=html

# Find TODOs
rg "TODO|FIXME" src/

# Check dependencies
pip-audit

# Profile script
python -m cProfile -o profile.stats scripts/analyze.py

# Serve reports locally
python scripts/serve_reports.py
```
