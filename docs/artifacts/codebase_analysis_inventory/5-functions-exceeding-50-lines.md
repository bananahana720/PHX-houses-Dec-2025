# 5. FUNCTIONS EXCEEDING 50 LINES

### Large HTML Generation Functions

#### risk_report.py: `generate_html_report()` (lines 268-437)
- **Lines:** 170 lines
- **Purpose:** Generate HTML report with embedded CSS and data
- **Issue:** HTML template hardcoded as string literal

#### renovation_gap.py: `generate_html_report()` (lines 159-494)
- **Lines:** 336 lines
- **Purpose:** Generate renovation gap HTML report
- **Issue:** Massive HTML template in Python string

#### deal_sheets.py: `DEAL_SHEET_TEMPLATE` (lines 54-527)
- **Lines:** 474 lines (not a function, but module-level string)
- **Purpose:** Deal sheet HTML template
- **Issue:** Should use Jinja2 templates in separate files

#### deal_sheets.py: `INDEX_TEMPLATE` (lines 530-793)
- **Lines:** 264 lines (module-level string)
- **Purpose:** Index page HTML template

### Complex Analysis Functions

#### data_quality_report.py: `generate_report()` (lines 210-405)
- **Lines:** 196 lines
- **Purpose:** Generate comprehensive quality report
- **Refactor:** Break into smaller functions for each section

#### data_quality_report.py: `find_data_quality_issues()` (lines 80-208)
- **Lines:** 129 lines
- **Purpose:** Validate property data against rules
- **Refactor:** Extract validation rules to config, create validator class

#### risk_report.py: `generate_due_diligence_checklist()` (lines 459-569)
- **Lines:** 111 lines
- **Purpose:** Generate property-specific checklist
- **Refactor:** Use template engine

#### phx_home_analyzer.py: `generate_ranked_csv()` (lines 419-471)
- **Lines:** 53 lines
- **Purpose:** Generate ranked CSV output
- **Borderline:** Could be split into data preparation + CSV writing

#### renovation_gap.py: `print_summary_report()` (lines 496-567)
- **Lines:** 72 lines
- **Purpose:** Print console summary
- **Refactor:** Extract formatting logic

### Main Functions

#### risk_report.py: `main()` (lines 571-673)
- **Lines:** 103 lines
- **Purpose:** Pipeline orchestration
- **Refactor:** Extract print logic to separate reporting function

#### deal_sheets.py: `main()` (lines 987-1057)
- **Lines:** 71 lines
- **Purpose:** Pipeline orchestration
- **Note:** Acceptable length for main orchestrator

---
