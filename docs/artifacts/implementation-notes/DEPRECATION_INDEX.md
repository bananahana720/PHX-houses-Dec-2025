# Deprecation Index: deal_sheets.py

**Status:** Completed December 2, 2025
**Legacy File:** `scripts/deal_sheets.py` (1,057 lines)
**Modern Package:** `scripts/deal_sheets/` (modular structure)

## Quick Navigation

### For Users
- **Want to migrate?** → Read [`docs/DEPRECATION_GUIDE.md`](docs/DEPRECATION_GUIDE.md)
- **Need quick command?** → See [Migration Commands](#migration-commands) below
- **Need before/after examples?** → Check [`scripts/deal_sheets/README.md`](scripts/deal_sheets/README.md#migration-guide-from-legacy-scriptsdeal_sheetspy)

### For Developers
- **Technical details?** → See [`DEPRECATION_SUMMARY.md`](DEPRECATION_SUMMARY.md)
- **Verification checklist?** → See [`DEPRECATION_CHECKLIST.md`](DEPRECATION_CHECKLIST.md)
- **Code changes?** → See [Files Modified](#files-modified) below

### For Maintainers
- **Package README** → [`scripts/deal_sheets/README.md`](scripts/deal_sheets/README.md)
- **Package source** → [`scripts/deal_sheets/`](scripts/deal_sheets/)

## Migration Commands

### Quick Start

**Before (Deprecated):**
```bash
python scripts/deal_sheets.py
```

**After (Recommended):**
```bash
python -m scripts.deal_sheets
```

### For Python Code

**Before (Deprecated):**
```python
import sys
sys.path.insert(0, 'scripts')
from deal_sheets import main
```

**After (Recommended):**
```python
from scripts.deal_sheets import main
```

## Files Modified

### 1. Legacy File: `scripts/deal_sheets.py`

**Changes:**
- Enhanced module docstring (lines 1-27) with deprecation notice
- Added import warning (lines 37-43) using `warnings.warn()`
- Added runtime warning in `main()` (lines 959-969) with migration instructions

**Status:** Fully functional, no breaking changes

### 2. Modern Package: `scripts/deal_sheets/README.md`

**Additions:**
- MIGRATION NOTICE section (lines 5-18)
- Migration Guide section (lines 94-147) with examples:
  - Direct script execution (before/after)
  - Python imports (before/after)
  - Documentation updates (search patterns)
  - Behavior equivalence assurance

**Status:** Complete migration documentation

## Documentation Files Created

### 1. `DEPRECATION_SUMMARY.md` (Technical)
- Changes made breakdown
- File modifications with line numbers
- Migration paths for users
- Backward compatibility statement
- Verification performed

### 2. `docs/DEPRECATION_GUIDE.md` (User-Facing)
- What happened and why
- Deprecation warnings explanation
- Migration instructions (quick + detailed)
- Backward compatibility guarantees
- Functional equivalence table
- Timeline information
- Next steps and FAQ

### 3. `DEPRECATION_CHECKLIST.md` (Sign-Off)
- Complete deliverables list
- Quality checks performed
- Verification status
- Reference links
- Next steps for users

### 4. `DEPRECATION_INDEX.md` (This File)
- Navigation guide for all audiences
- Quick start commands
- File reference list

## Deprecation Warnings

### On Module Import
```python
>>> import scripts.deal_sheets
DeprecationWarning: deal_sheets.py is deprecated.
Use 'python -m scripts.deal_sheets' instead.
See scripts/deal_sheets/README.md for migration details.
```

### On Script Execution
```bash
$ python scripts/deal_sheets.py
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

## Key Points

✓ **Backward Compatible:** Legacy file remains fully functional
✓ **No Breaking Changes:** Output identical to modern package
✓ **Clear Migration Path:** Well-documented before/after examples
✓ **Graceful Transition:** Deprecation warnings, not errors
✓ **Well Documented:** 500+ lines of migration documentation
✓ **Future Ready:** Timeline for removal in place

## Timeline

| When | What |
|------|------|
| Now (Dec 2025) | Deprecation warnings issued, migration guide provided |
| Next Release | Continue warnings, monitor adoption |
| Future (TBD) | Remove legacy file after transition period |

## Reference Links

| Document | Purpose |
|----------|---------|
| [`DEPRECATION_SUMMARY.md`](DEPRECATION_SUMMARY.md) | Technical implementation details |
| [`docs/DEPRECATION_GUIDE.md`](docs/DEPRECATION_GUIDE.md) | User migration guide |
| [`DEPRECATION_CHECKLIST.md`](DEPRECATION_CHECKLIST.md) | Verification and sign-off |
| [`scripts/deal_sheets/README.md`](scripts/deal_sheets/README.md) | Modern package documentation |
| [`scripts/deal_sheets.py`](scripts/deal_sheets.py) | Legacy file (deprecated, lines 1-43) |

## FAQ

**Q: Do I have to migrate right away?**
A: No. The legacy file remains fully functional. Migrate at your convenience within the transition period.

**Q: Will the output change?**
A: No. The modern package produces byte-for-byte identical output.

**Q: What's the timeline for removal?**
A: TBD. A graceful transition period will be provided before removal.

**Q: Can I still use the legacy file?**
A: Yes, but you'll see deprecation warnings encouraging migration.

**Q: What if I have questions?**
A: See `docs/DEPRECATION_GUIDE.md` for detailed migration instructions and examples.

## Status

**COMPLETE AND VERIFIED**

All deprecation warnings in place
All documentation created
Backward compatibility maintained
Ready for team migration

---

*For detailed information, see the reference links above.*
