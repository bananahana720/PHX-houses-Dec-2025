# Files Affected Summary

### Modified Files
- `scripts/phx_home_analyzer.py` - Remove duplicates, use services
- `scripts/deal_sheets.py` - Split into module package

### New Files
- `scripts/deal_sheets/__init__.py` - Package exports
- `scripts/deal_sheets/__main__.py` - CLI entry point
- `scripts/deal_sheets/generator.py` - Main orchestrator (~93 lines)
- `scripts/deal_sheets/data_loader.py` - CSV/JSON loading (~70 lines)
- `scripts/deal_sheets/templates.py` - HTML/CSS templates (~582 lines)
- `scripts/deal_sheets/renderer.py` - HTML generation (~168 lines)
- `scripts/deal_sheets/utils.py` - Utility functions (~120 lines)
- `src/.../services/image_extraction/state_manager.py`
- `src/.../services/image_extraction/extraction_stats.py`
- `src/.../services/image_extraction/manifest_manager.py`

### Preserved Files (No Changes)
- `src/.../services/kill_switch/` - Already canonical
- `src/.../services/scoring/` - Already canonical
- All test files - Should pass unchanged
