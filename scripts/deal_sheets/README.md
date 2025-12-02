# Deal Sheets Package

Refactored from monolithic `scripts/deal_sheets.py` (1,057 lines) into modular package structure.

## MIGRATION NOTICE (DEPRECATED)

**Status:** The legacy `scripts/deal_sheets.py` is now **DEPRECATED**.

**Action Required:** Please update any scripts or documentation that reference the legacy file.

**New Command:**
```bash
python -m scripts.deal_sheets
```

**Timeline:**
- Current: Deprecation warning issued on import and execution
- Future: Legacy file will be removed in a subsequent release

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

## Migration Guide (From Legacy `scripts/deal_sheets.py`)

### For Direct Script Execution

**Before (Deprecated):**
```bash
cd scripts
python deal_sheets.py
```

**After (New):**
```bash
# From project root
python -m scripts.deal_sheets

# Or from scripts directory
cd scripts
python -m deal_sheets
```

### For Python Imports

**Before (Deprecated):**
```python
import sys
sys.path.insert(0, 'scripts')
from deal_sheets import main, generate_deal_sheets

main()
```

**After (New):**
```python
from scripts.deal_sheets import main, generate_deal_sheets

main()
```

### For Documentation Updates

Replace any references to:
- `scripts/deal_sheets.py` → `python -m scripts.deal_sheets`
- `python scripts/deal_sheets.py` → `python -m scripts.deal_sheets`
- Command examples in docs → Update to use `python -m scripts.deal_sheets`

### Behavior Equivalence

The modular package is **100% functionally equivalent** to the legacy file:
- Same HTML output (byte-identical templates)
- Same kill-switch evaluation logic (shared `scripts/lib/kill_switch.py`)
- Same data loading and enrichment flow
- Same output location: `reports/deal_sheets/`

No changes to output format, structure, or results.

## Notes

- Filters out malformed CSV rows (missing rank/address)
- Replaces NaN values appropriately for template rendering
- Uses enrichment data to supplement CSV but preserves CSV values
- Maintains exact template formatting and CSS styling
- Legacy file kept temporarily for backward compatibility (issues deprecation warnings)
