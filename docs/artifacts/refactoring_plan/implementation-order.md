# Implementation Order

1. **Phase 1** (COMPLETED) - Kill-switch consolidation
   - Created `scripts/lib/kill_switch.py` as single source of truth
   - Updated `scripts/phx_home_analyzer.py` to use consolidated module
   - Added `evaluate_kill_switches_for_display()` for deal_sheets compatibility
   - 38 unit tests added and passing

2. **Phase 2** (COMPLETED) - Extract state manager from orchestrator
   - Created `src/.../services/image_extraction/state_manager.py`
   - Extracted `ExtractionState` dataclass and `StateManager` class
   - 19 unit tests added and passing

3. **Phase 3** (COMPLETED) - Extract stats tracker from orchestrator
   - Created `src/.../services/image_extraction/extraction_stats.py`
   - Extracted `SourceStats`, `ExtractionResult`, and `StatsTracker` classes
   - Added computed properties for success rates and processing speed
   - 27 unit tests added and passing

4. **Phase 4** (COMPLETED) - Split deal_sheets.py
   - Created `scripts/deal_sheets/` package with 7 focused modules
   - Extracted templates.py (582 lines of HTML/CSS templates)
   - Extracted data_loader.py (CSV/JSON loading utilities)
   - Extracted renderer.py (HTML generation functions)
   - Extracted utils.py (slugify, extract_features helpers)
   - Created generator.py (slim orchestrator using lib/kill_switch.py)
   - Eliminated kill-switch code duplication (now uses shared lib)

5. **Phase 5** (COMPLETED) - Unify scoring
   - Removed 17 duplicate scoring functions from phx_home_analyzer.py (~150 lines)
   - Removed calculate_weighted_score local implementation
   - Now uses canonical PropertyScorer service with adapter pattern
   - Added _convert_to_domain_property() for type conversion
   - 313 tests passing

---
