# PHX Houses Analysis Pipeline - Development Guide

## Quick Start

### Prerequisites
- Python 3.11 or higher
- Git
- Chrome/Chromium browser (for stealth automation)
- Maricopa County Assessor API token
- (Optional) Virtual display for browser isolation

### Installation

```bash
# Clone repository
cd PHX-houses-Dec-2025

# Install dependencies using uv
uv sync

# Install development dependencies
uv sync --group dev

# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Set environment variables
cp .env.example .env
# Edit .env with your API keys
export MARICOPA_ASSESSOR_TOKEN=<your-token>
```

### Running the System

```bash
# Main analysis pipeline
python scripts/phx_home_analyzer.py

# County data extraction (Phase 0)
python scripts/extract_county_data.py --all

# Image extraction (Phase 1)
python scripts/extract_images.py --all

# Generate deal sheets
python -m scripts.deal_sheets

# Multi-agent orchestrated analysis
/analyze-property --all
```

---

## Project Organization

### Key Directories

| Directory | Purpose |
|-----------|---------|
| `src/phx_home_analysis/` | Core Python package |
| `scripts/` | Executable analysis scripts |
| `tests/` | Test suite (pytest) |
| `.claude/` | Multi-agent AI system |
| `data/` | Data files and state |
| `reports/` | Generated output |
| `docs/` | Technical documentation |

### Key Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project configuration, dependencies |
| `uv.lock` | Dependency lock file |
| `CLAUDE.md` | Project documentation (instructions, tool rules) |
| `.claude/AGENT_BRIEFING.md` | Agent orientation guide |
| `.claude/protocols.md` | Operational protocols (TIER 0-3) |

---

## Development Workflow

### Adding a New Property

1. **Add to CSV**
   ```bash
   # Edit data/phx_homes.csv
   # Add row: address,price,beds,baths,sqft,price_per_sqft
   ```

2. **Extract County Data**
   ```bash
   python scripts/extract_county_data.py --address "123 Main St, City, AZ 85000"
   ```

3. **Extract Images**
   ```bash
   python scripts/extract_images.py --address "123 Main St, City, AZ 85000"
   ```

4. **Run Multi-Agent Analysis**
   ```bash
   /analyze-property "123 Main St, City, AZ 85000"
   ```

### Adding a New Scoring Criterion

**Example: Add "Noise Level" scorer (25 pts)**

1. **Update Constants**
   ```python
   # src/phx_home_analysis/config/constants.py
   SCORE_SECTION_A_NOISE_LEVEL: Final[int] = 25
   ```

2. **Update Scoring Weights**
   ```python
   # src/phx_home_analysis/config/scoring_weights.py
   @dataclass(frozen=True)
   class ScoringWeights:
       # Section A
       noise_level: int = 25  # NEW
   ```

3. **Create Scorer Strategy**
   ```python
   # src/phx_home_analysis/services/scoring/strategies/location.py
   class NoiseLevelScorer(ScoringStrategy):
       """Score based on noise pollution (airports, highways, railroads)."""

       def score(self, property: Property) -> float:
           """Return score 0-10 based on noise level."""
           if property.noise_level_db is None:
               return 5.0  # Neutral default

           # Scoring logic: < 50dB = 10pts, > 70dB = 0pts
           if property.noise_level_db < 50:
               return 10.0
           elif property.noise_level_db > 70:
               return 0.0
           else:
               # Linear interpolation
               return 10.0 - ((property.noise_level_db - 50) / 2.0)
   ```

4. **Register Strategy**
   ```python
   # src/phx_home_analysis/services/scoring/__init__.py
   LOCATION_STRATEGIES: list[tuple[ScoringStrategy, int]] = [
       (SchoolDistrictScorer(), 42),
       (NoiseLevel Scorer(), 25),  # NEW
       # ... other strategies
   ]
   ```

5. **Update Domain Model**
   ```python
   # src/phx_home_analysis/domain/entities.py
   @dataclass
   class Property:
       noise_level_db: float | None = None  # NEW
   ```

6. **Write Tests**
   ```python
   # tests/unit/test_noise_level_scorer.py
   def test_noise_level_scorer_quiet():
       prop = Property(noise_level_db=45.0, ...)
       scorer = NoiseLevelScorer()
       assert scorer.score(prop) == 10.0

   def test_noise_level_scorer_loud():
       prop = Property(noise_level_db=75.0, ...)
       scorer = NoiseLevelScorer()
       assert scorer.score(prop) == 0.0
   ```

7. **Update Documentation**
   ```markdown
   # docs/scoring-system.md
   ## Section A: Location (255 pts) <- Update total

   ### Noise Level (25 pts)
   - < 50dB: 10 pts (very quiet)
   - 60dB: 5 pts (moderate)
   - > 70dB: 0 pts (very loud)
   ```

---

## Testing

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

## Code Style

### Linting and Formatting

```bash
# Run ruff linter
ruff check src/ scripts/ tests/

# Run ruff formatter
ruff format src/ scripts/ tests/

# Run mypy type checker
mypy src/ scripts/
```

### Style Guidelines

1. **Type Hints**
   - Always use type hints for function signatures
   - Use `| None` instead of `Optional[T]`
   - Use `list[T]` instead of `List[T]` (Python 3.11+)

   ```python
   # Good
   def score(self, property: Property) -> float:
       pass

   def load_all(self) -> list[Property]:
       pass

   # Bad
   def score(self, property):  # No type hints
       pass
   ```

2. **Docstrings**
   - Use Google style docstrings
   - Include Args, Returns, Raises sections

   ```python
   def score(self, property: Property) -> float:
       """Calculate property score.

       Args:
           property: Property entity with all data

       Returns:
           Score value 0-10

       Raises:
           ValueError: If property is invalid
       """
       pass
   ```

3. **Naming Conventions**
   - Classes: `PascalCase`
   - Functions/methods: `snake_case`
   - Constants: `UPPER_SNAKE_CASE`
   - Private methods: `_leading_underscore`

4. **Line Length**
   - Maximum 100 characters
   - Break long lines at logical points

5. **Imports**
   - Organized by: stdlib, third-party, local
   - Sorted alphabetically within each group
   - Use absolute imports

   ```python
   # Good
   import json
   from pathlib import Path

   import pandas as pd
   from pydantic import BaseModel

   from src.phx_home_analysis.domain.entities import Property

   # Bad
   from pathlib import Path
   import json  # Wrong order
   from ..domain.entities import Property  # Relative import
   ```

---

## Git Workflow

### Commit Guidelines

1. **Never bypass pre-commit hooks**
   ```bash
   # NEVER do this
   git commit --no-verify  # PROHIBITED
   git commit -n           # PROHIBITED
   ```

2. **Commit message format**
   ```
   type: brief description

   Longer explanation if needed.

   🤖 Generated with [Claude Code](https://claude.com/claude-code)

   Co-Authored-By: Claude <noreply@anthropic.com>
   ```

   Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

3. **Pre-commit hook failures**
   - Read error messages carefully
   - Fix all reported issues
   - Stage fixes: `git add <files>`
   - Commit again (hooks run automatically)

### Branching Strategy

```bash
# Create feature branch
git checkout -b feature/add-noise-scorer

# Make changes, commit
git add src/ tests/
git commit -m "feat: add noise level scorer"

# Push to remote
git push origin feature/add-noise-scorer

# Create pull request (if applicable)
```

---

## Multi-Agent Development

### Creating a New Agent

1. **Create agent definition**
   ```markdown
   # .claude/agents/my-new-agent.md
   ---
   name: my-new-agent
   model: claude-haiku-3.5
   skills: property-data, state-management
   ---

   # My New Agent

   ## Purpose
   Extract XYZ data from ABC source.

   ## Task
   You are responsible for...

   ## Skills
   - property-data: Load and update property data
   - state-management: Track progress

   ## Output Format
   Return structured JSON:
   ```json
   {
     "status": "success",
     "data": {...}
   }
   ```
   ```

2. **Create skill module (if needed)**
   ```markdown
   # .claude/skills/my-skill/SKILL.md
   # My Skill

   Provides capability to...

   ## Usage
   python scripts/my_script.py --address "..."
   ```

3. **Test agent**
   ```bash
   # Spawn agent with Task tool
   Task: Load my-new-agent and run on sample property
   ```

### Debugging Agents

1. **Check agent output**
   ```bash
   # Agent logs go to terminal
   # Look for errors, warnings
   ```

2. **Verify state files**
   ```bash
   # Check work_items.json for progress
   cat data/work_items.json | jq '.work_items[] | select(.address | contains("123"))'

   # Check enrichment_data.json for data
   cat data/enrichment_data.json | jq '.[] | select(.full_address | contains("123"))'
   ```

3. **Validate prerequisites**
   ```bash
   python scripts/validate_phase_prerequisites.py --address "123 Main St" --phase phase2_images --json
   ```

---

## Common Tasks

### Adding a New Data Source

1. **Create client**
   ```python
   # src/phx_home_analysis/services/my_source/client.py
   class MySourceClient:
       def fetch_data(self, address: str) -> dict:
           # API call or web scraping
           pass
   ```

2. **Create models**
   ```python
   # src/phx_home_analysis/services/my_source/models.py
   from pydantic import BaseModel

   class MySourceData(BaseModel):
       field1: str
       field2: int
   ```

3. **Add to extraction script**
   ```python
   # scripts/extract_my_source_data.py
   from src.phx_home_analysis.services.my_source.client import MySourceClient

   client = MySourceClient()
   data = client.fetch_data(address)
   # Update enrichment_data.json
   ```

### Updating Scoring Weights

1. **Edit constants**
   ```python
   # src/phx_home_analysis/config/constants.py
   SCORE_SECTION_A_SCHOOL_DISTRICT: Final[int] = 50  # Was 42
   ```

2. **Update scoring_weights.py**
   ```python
   # src/phx_home_analysis/config/scoring_weights.py
   @dataclass(frozen=True)
   class ScoringWeights:
       school_district: int = 50  # Was 42
   ```

3. **Verify total**
   ```python
   # Ensure total still equals 600
   weights = ScoringWeights()
   assert weights.total_possible_score == 600
   ```

4. **Update docs**
   ```markdown
   # docs/scoring-system.md
   ## Section A: Location (258 pts) <- Update total

   ### School District (50 pts) <- Update weight
   ```

### Debugging Data Issues

**Problem: enrichment_data.json missing fields**

```bash
# Check structure
cat data/enrichment_data.json | jq '.[] | select(.full_address | contains("123")) | keys'

# Check specific field
cat data/enrichment_data.json | jq '.[] | select(.full_address | contains("123")) | .location.school_rating'

# If missing, re-run extraction
python scripts/extract_county_data.py --address "123 Main St"
```

**Problem: Images not found for Phase 2**

```bash
# Check image manifest
cat data/property_images/metadata/image_manifest.json | jq 'keys'

# Check address lookup
cat data/property_images/metadata/address_folder_lookup.json | jq '.mappings["123 Main St, City, AZ 85000"]'

# Re-run image extraction
python scripts/extract_images.py --address "123 Main St, City, AZ 85000" --sources zillow,redfin
```

---

## Performance Optimization

### Profiling

```bash
# Profile script execution
python -m cProfile -o profile.stats scripts/phx_home_analyzer.py

# Visualize with snakeviz
snakeviz profile.stats
```

### Benchmarking

```bash
# Run benchmark tests
pytest tests/benchmarks/ -v

# Specific benchmark
pytest tests/benchmarks/test_lsh_performance.py -v
```

### Optimization Tips

1. **Batch operations**
   - Extract all properties in one session (saves API calls)
   - Use parallel processing for independent tasks

2. **Cache expensive operations**
   - Cache geocoding results
   - Cache API responses

3. **Use efficient data structures**
   - Consider migrating to database for >1000 properties
   - Use pandas for bulk operations

---

## Troubleshooting

### Common Errors

#### `TypeError: list indices must be integers`

**Cause:** Treating `enrichment_data.json` as dict instead of list.

**Fix:**
```python
# WRONG
data = json.load(open('data/enrichment_data.json'))
prop = data[address]  # Error

# CORRECT
data = json.load(open('data/enrichment_data.json'))
prop = next((p for p in data if p['full_address'] == address), None)
```

#### `403 Forbidden` when scraping Zillow/Redfin

**Cause:** PerimeterX bot detection.

**Fix:**
- Ensure using nodriver (not Playwright)
- Check proxy configuration
- Add delays between requests

#### Phase 2 agent fails with "images not found"

**Cause:** Phase 1 not complete or images not extracted.

**Fix:**
```bash
# Validate prerequisites
python scripts/validate_phase_prerequisites.py --address "..." --phase phase2_images --json

# If blocked, run Phase 1
python scripts/extract_images.py --address "..."
```

---

## Resources

### Internal Documentation
- `CLAUDE.md` - Project overview, tool usage rules
- `.claude/AGENT_BRIEFING.md` - Agent orientation
- `.claude/protocols.md` - Operational protocols
- `docs/architecture.md` - System architecture
- `docs/project-overview.md` - Executive summary

### External Resources
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Claude Code Documentation](https://claude.com/claude-code)
- [Maricopa County Assessor](https://mcassessor.maricopa.gov/)

---

**Document Version:** 1.0
**Generated:** 2025-12-03
**Last Updated:** 2025-12-03
