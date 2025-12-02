# Deal Sheets Package

Refactored from monolithic `scripts/deal_sheets.py` (1,057 lines) into modular package structure.

## Package Structure

```
scripts/deal_sheets/
├── __init__.py          # Package exports (main, generate_deal_sheets)
├── __main__.py          # CLI entry point
├── templates.py         # HTML/CSS templates (Jinja2)
├── data_loader.py       # CSV/JSON loading functions
├── renderer.py          # HTML generation (deal sheets + index)
├── utils.py             # Helper functions (slugify, extract_features)
└── generator.py         # Main orchestration logic
```

## Usage

### As Python Module
```python
from scripts.deal_sheets import main, generate_deal_sheets

# Simple invocation
main()

# With custom base directory
output_dir = generate_deal_sheets(base_dir="/path/to/project")
```

### As CLI Command
```bash
# Run as module
python -m scripts.deal_sheets

# Or from within scripts directory
cd scripts
python -m deal_sheets
```

## Key Features

- **Modular Design**: Each file has single responsibility
- **Shared Kill Switch Logic**: Uses `scripts/lib/kill_switch.py` (single source of truth)
- **Data Mapping**: Automatically maps CSV fields to template expectations
- **Error Handling**: Filters malformed CSV rows, handles NaN values
- **Template Preservation**: Exact HTML/CSS preserved from original

## Generated Output

- **Location**: `reports/deal_sheets/`
- **Files**:
  - Individual deal sheets: `{rank:02d}_{address_slug}.html`
  - Master index: `index.html`

## Data Flow

1. **Load**: `phx_homes_ranked.csv` + `enrichment_data.json`
2. **Merge**: Enrichment data with CSV (preserves CSV priority)
3. **Map**: CSV fields → Template expectations
4. **Evaluate**: Kill switches (from `scripts/lib/kill_switch.py`)
5. **Render**: Individual deal sheets + index page
6. **Output**: HTML files to `reports/deal_sheets/`

## Refactoring Changes

- **Removed**: Duplicate kill switch criteria (lines 14-51)
- **Removed**: Duplicate `evaluate_kill_switches()` function (lines 806-832)
- **Uses**: `scripts.lib.kill_switch.evaluate_kill_switches_for_display()`
- **Improved**: Data validation (filters NaN rows)
- **Improved**: Field mapping (CSV ↔ Template)

## Dependencies

- pandas
- jinja2
- scripts.lib.kill_switch (internal)

## Notes

- Filters out malformed CSV rows (missing rank/address)
- Replaces NaN values appropriately for template rendering
- Uses enrichment data to supplement CSV but preserves CSV values
- Maintains exact template formatting and CSS styling
