# Phase 2: Split deal_sheets.py (HIGH)

### Problem Statement

`deal_sheets.py` (1,057 lines) violates Single Responsibility Principle with:
- HTML template generation
- Data loading and transformation
- Kill-switch evaluation
- File I/O operations
- Slug/URL generation

### Solution

Extract into focused modules:

```
scripts/deal_sheets/
├── __init__.py
├── generator.py      # Main orchestrator (< 100 lines)
├── data_loader.py    # CSV/enrichment loading (< 150 lines)
├── evaluator.py      # Property evaluation (uses service layer)
├── templates.py      # HTML templates (< 200 lines)
└── renderer.py       # HTML rendering (< 150 lines)
```

### Implementation Steps

#### Step 2.1: Extract data_loader.py

```python
"""Data loading utilities for deal sheet generation."""

from pathlib import Path
import pandas as pd
from typing import Optional

from src.phx_home_analysis.repositories import CSVRepository
from src.phx_home_analysis.domain.entities import Property


def load_properties(csv_path: Path, enrichment_path: Optional[Path] = None) -> list[Property]:
    """Load properties from CSV with optional enrichment."""
    repo = CSVRepository(csv_path, enrichment_path)
    return repo.load_all()


def filter_by_tier(properties: list[Property], tiers: list[str]) -> list[Property]:
    """Filter properties by tier classification."""
    return [p for p in properties if p.tier in tiers]
```

#### Step 2.2: Extract templates.py

```python
"""HTML templates for deal sheets."""

CSS_STYLES = '''
/* Move all CSS from deal_sheets.py */
'''

DEAL_SHEET_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>{address}</title>
    <style>{css}</style>
</head>
<body>
    {content}
</body>
</html>
'''

def render_kill_switch_section(property: Property) -> str:
    """Render kill switch results as HTML."""
    # Template rendering logic
    pass

def render_scoring_section(property: Property) -> str:
    """Render scoring breakdown as HTML."""
    pass
```

#### Step 2.3: Update generator.py (main entry point)

```python
"""Deal sheet generator - main entry point."""

from pathlib import Path
from typing import Optional

from .data_loader import load_properties, filter_by_tier
from .renderer import render_deal_sheet
from src.phx_home_analysis.services.kill_switch import KillSwitchFilter
from src.phx_home_analysis.services.scoring import PropertyScorer


def generate_deal_sheets(
    output_dir: Path,
    csv_path: Path,
    enrichment_path: Optional[Path] = None,
    tiers: list[str] = ["Unicorn", "Contender"],
) -> list[Path]:
    """Generate deal sheets for filtered properties.

    Returns:
        List of generated file paths
    """
    # Load and filter
    properties = load_properties(csv_path, enrichment_path)

    # Evaluate with canonical services
    filter_service = KillSwitchFilter()
    scorer = PropertyScorer()

    for prop in properties:
        filter_service.evaluate(prop)
        scorer.score(prop)

    # Filter by tier
    filtered = filter_by_tier(properties, tiers)

    # Generate sheets
    output_files = []
    for prop in filtered:
        file_path = render_deal_sheet(prop, output_dir)
        output_files.append(file_path)

    return output_files


if __name__ == "__main__":
    # CLI interface
    pass
```

### Testing Strategy

1. Create integration test comparing output before/after refactor
2. Unit test each extracted module
3. Verify HTML output is byte-identical (or semantically equivalent)

---
