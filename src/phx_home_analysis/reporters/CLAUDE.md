---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
flags: []
---
# reporters

## Purpose
Output formatters for property analysis results. Generates terminal, CSV, and HTML reports with tier classification, scoring breakdown (605-point scale), and kill-switch verdicts for multi-format distribution.

## Contents
| Path | Purpose |
|------|---------|
| `base.py` | Abstract Reporter interface with `generate(properties, output_path)` contract |
| `console_reporter.py` | Terminal output with ANSI colors, 605-point scale, section % breakdown |
| `csv_reporter.py` | CSV export for spreadsheet analysis and ranking |
| `html_reporter.py` | Web-ready HTML reports with tier color coding and styling |
| `__init__.py` | Package exports (Reporter, ConsoleReporter, CsvReporter, HtmlReporter) |

## Tasks
- [x] Implement 605-point scale display in console reporter `P:H`
- [x] Add section percentage calculation and formatting `P:H`
- [x] Document reporter interface and extensibility `P:H`
- [ ] Add HTML styling for tier color coding `P:M`
- [ ] Add JSON export format for APIs `P:L`

## Learnings
- Console reporter supports compact and verbose modes via `compact` flag
- All reporters inherit from `base.Reporter` abstract class; new formats require implementing `generate()` method
- 605-point scale: Location 250 + Systems 175 + Interior 180
- Section percentages: (section_score / section_max) × 100

## Refs
- Reporter interface: `base.py:1-50`
- Console implementation: `console_reporter.py:1-120` (605-point scale with sections)
- CSV export: `csv_reporter.py:1-80`
- HTML formatter: `html_reporter.py:1-150`
- Package exports: `__init__.py:1-20`

## Deps
← Imports from:
  - `..domain.entities` (Property)
  - `..domain.enums` (Tier, RiskLevel)
  - `..config.scoring_weights` (605-point configuration)

→ Imported by:
  - `pipeline/orchestrator.py` (AnalysisPipeline orchestration)
  - `scripts/phx_home_analyzer.py` (CLI runner)
  - `/analyze-property` command