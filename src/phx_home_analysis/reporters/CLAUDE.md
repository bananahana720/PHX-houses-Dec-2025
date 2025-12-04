---
last_updated: 2025-12-04
updated_by: main
staleness_hours: 24
flags: []
---
# reporters

## Purpose

Output formatters for property analysis results. Generates terminal, CSV, and HTML reports with tier classification, scoring breakdown, and kill-switch verdicts for multi-format distribution.

## Contents

| Path | Purpose |
|------|---------|
| `base.py` | Abstract Reporter interface defining contract for all formatters |
| `console_reporter.py` | Terminal output with ANSI color codes; shows /605 scale and section percentages |
| `csv_reporter.py` | CSV export for spreadsheet analysis |
| `html_reporter.py` | Web-ready HTML reports with styling |

## Key Updates

- **Console reporter (2025-12-04):** Updated to display 605-point scale (`/605`) with section-level percentage breakdown (Location %, Systems %, Interior %)
- **All reporters:** Implement `Reporter.generate(properties, output_path)` interface for consistent orchestration

## Tasks

- [x] Implement 605-point scale display in console reporter
- [x] Add section percentage calculation and formatting
- [ ] Add HTML styling for tier color coding P:M

## Learnings

- Console reporter supports compact and verbose modes via `compact` flag
- All reporters inherit from `base.Reporter` abstract class; adding new format requires implementing `generate()` method

## Refs

- Reporter interface: `base.py:1-50`
- Console implementation: `console_reporter.py:1-100` (605-point scale update)
- CSV export: `csv_reporter.py:1-80`
- HTML formatter: `html_reporter.py:1-150`

## Deps

← Imports from:
  - `..domain.entities` (Property dataclass)
  - `..domain.enums` (Tier, RiskLevel)

→ Imported by:
  - `pipeline/orchestrator.py` (AnalysisPipeline)
  - `scripts/phx_home_analyzer.py` (CLI runner)