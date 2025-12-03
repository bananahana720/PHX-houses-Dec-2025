# Deprecation Guide: Legacy deal_sheets.py

## Status: COMPLETED (December 2, 2025)

The legacy `scripts/deal_sheets.py` file has been deprecated in favor of the modern modular package at `scripts/deal_sheets/`.

## What Happened

The monolithic 1,057-line file was refactored into a modular package structure:

```
Before: scripts/deal_sheets.py (1,057 lines)
   ↓
After:  scripts/deal_sheets/
        ├── __init__.py          (Clean exports)
        ├── __main__.py          (CLI entry)
        ├── generator.py         (Orchestration)
        ├── renderer.py          (HTML generation)
        ├── templates.py         (Jinja2 templates)
        ├── data_loader.py       (CSV/JSON loading)
        ├── utils.py             (Helpers)
        └── README.md            (Documentation)
```

## Deprecation Warnings

### 1. On Module Import

```python
import scripts.deal_sheets
```

Issues:
```
DeprecationWarning: deal_sheets.py is deprecated.
Use 'python -m scripts.deal_sheets' instead.
See scripts/deal_sheets/README.md for migration details.
```

### 2. On Script Execution

Running the legacy script displays:

```
======================================================================
WARNING: This script is deprecated!
======================================================================
Please use instead:
    python -m scripts.deal_sheets

The legacy deal_sheets.py file will be removed in a future version.
See scripts/deal_sheets/README.md for migration details.
======================================================================
Continuing with legacy implementation...
```

## Migration Instructions

### Quick Start

**Old (Deprecated):**
```bash
python scripts/deal_sheets.py
```

**New (Recommended):**
```bash
python -m scripts.deal_sheets
```

### For Python Code

**Old (Deprecated):**
```python
import sys
sys.path.insert(0, 'scripts')
from deal_sheets import main, generate_deal_sheets
main()
```

**New (Recommended):**
```python
from scripts.deal_sheets import main, generate_deal_sheets
main()
```

### For Documentation

Replace all references:
- `scripts/deal_sheets.py` → `python -m scripts.deal_sheets`
- `python scripts/deal_sheets.py` → `python -m scripts.deal_sheets`
- File paths → Command invocations

## Backward Compatibility

**Important:** The legacy file is NOT being removed yet.

- All existing functionality remains identical
- Output is byte-for-byte compatible
- No breaking changes introduced
- Graceful transition period provided

## Functional Equivalence

The modular package is **100% functionally equivalent** to the legacy file:

| Aspect | Status |
|--------|--------|
| HTML Output | Identical (byte-for-byte) |
| Kill-Switch Logic | Shared via `scripts/lib/kill_switch.py` |
| Data Flow | Identical (Load → Merge → Map → Render) |
| Output Location | Same: `reports/deal_sheets/` |
| Configuration | Same fields, same defaults |
| Dependencies | pandas, jinja2 (unchanged) |

## Timeline

| When | What |
|------|------|
| Now (Dec 2025) | Deprecation warnings issued |
| Next Release | Continue warning, review migration progress |
| Future (TBD) | Remove legacy file after transition period |

## Next Steps

1. **Update Your Workflows**
   - Replace `python scripts/deal_sheets.py` with `python -m scripts.deal_sheets`
   - Update documentation and scripts

2. **Verify Compatibility**
   - Test `python -m scripts.deal_sheets` output
   - Compare with legacy output (should be identical)

3. **Remove Legacy References**
   - Check CI/CD pipelines
   - Update documentation
   - Update team processes

## Questions?

- **Technical Details:** See `scripts/deal_sheets/README.md`
- **Deprecation Details:** See `scripts/deal_sheets.py` docstring
- **Project Context:** See `CLAUDE.md`

## Files Modified

1. **scripts/deal_sheets.py**
   - Added module docstring deprecation notice
   - Added import-time DeprecationWarning
   - Added runtime warning in main()

2. **scripts/deal_sheets/README.md**
   - Added MIGRATION NOTICE section
   - Added comprehensive Migration Guide
   - Added timeline information

3. **New Files**
   - `DEPRECATION_SUMMARY.md` - Technical summary
   - `docs/DEPRECATION_GUIDE.md` - This file (user-facing)
