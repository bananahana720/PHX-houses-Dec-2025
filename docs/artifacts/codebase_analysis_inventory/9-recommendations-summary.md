# 9. RECOMMENDATIONS SUMMARY

### Priority 1: Configuration Module (HIGH IMPACT)

**Create:** `config.py` module

**Consolidate:**
1. All input/output file paths
2. Kill switch criteria (single source of truth)
3. Scoring weights and tier thresholds
4. Renovation cost estimates
5. Risk category thresholds
6. Orientation cooling costs
7. Map configuration constants

**Benefits:**
- Single source of truth for all constants
- Easy to adjust thresholds without code changes
- Enables YAML/JSON config files later
- Eliminates hardcoded paths

### Priority 2: Shared Data Loaders (MEDIUM IMPACT)

**Create:** `data_loaders.py` module

**Consolidate:**
1. `load_csv()` - unified CSV loading with pandas
2. `load_json()` - unified JSON loading
3. `load_enrichment_data()` - standard enrichment loader
4. `load_ranked_properties()` - standard ranked CSV loader
5. `create_address_lookup()` - reusable dict builder

**Benefits:**
- Eliminate 20+ instances of duplicated loading code
- Consistent error handling
- Standard path resolution
- Easier to add caching layer

### Priority 3: Template Externalization (MEDIUM IMPACT)

**Create:** `templates/` directory

**Extract:**
1. risk_report.py HTML template (170 lines) → `templates/risk_report.html`
2. renovation_gap.py HTML template (336 lines) → `templates/renovation_gap.html`
3. deal_sheets.py templates (738 lines) → `templates/deal_sheet.html` + `templates/index.html`

**Benefits:**
- Remove 1,244 lines of HTML from Python files
- Proper separation of concerns
- Easier to edit HTML/CSS
- Already using Jinja2 in deal_sheets.py

### Priority 4: Function Decomposition (LOW-MEDIUM IMPACT)

**Refactor large functions:**

1. **data_quality_report.py:**
   - Split `generate_report()` into section generators
   - Extract `find_data_quality_issues()` validation rules to config

2. **risk_report.py:**
   - Extract `generate_due_diligence_checklist()` to template

3. **renovation_gap.py:**
   - Split `print_summary_report()` into formatters

**Benefits:**
- Improved testability
- Better code organization
- Easier to maintain

### Priority 5: Path Handling (HIGH IMPACT - CRITICAL BUG)

**Fix:** radar_charts.py line 18 hardcoded Windows path

**Standardize:**
1. All scripts use `Path(__file__).parent` for base directory
2. All paths go through config module
3. Support environment variable overrides

**Benefits:**
- Cross-platform compatibility
- No hardcoded user paths
- Easy to run from different directories

---
