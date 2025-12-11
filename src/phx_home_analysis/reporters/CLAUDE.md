---
last_updated: 2025-12-10
updated_by: agent
---

# reporters

## Purpose
Output formatters for property analysis results. Generates terminal, CSV, HTML, and deal sheet reports with 605-point scoring, tier classification, and kill-switch verdicts.

## Contents
| File | Purpose |
|------|---------|
| `base.py` | Abstract Reporter interface with `generate(properties, output_path)` contract |
| `console_reporter.py` | Terminal output with ANSI colors, 605-point scale, section % breakdown |
| `csv_reporter.py` | CSV export for spreadsheet analysis, ranking, and bulk comparison |
| `html_reporter.py` | Web-ready HTML with tier color coding and responsive styling |
| `deal_sheet_reporter.py` | Deal sheet HTML with property overview, scoring breakdown, recommendations |
| `scoring_formatter.py` | Formatting utilities (percentages, tier labels, section display) |
| `__init__.py` | Package exports (Reporter, all reporters) |

## Key Patterns
- **Reporter interface**: Abstract base class for extensibility
- **605-point scale**: Location 250 + Systems 175 + Interior 180 = 605
- **Section percentages**: (section_score / section_max) × 100
- **Tier color coding**: Unicorn (green) → Contender (yellow) → Pass (gray)
- **Compact/verbose modes**: Toggle detail level in console reporter

## Tasks
- [x] Implement 605-point scale display `P:H`
- [x] Add section percentage formatting `P:H`
- [x] Implement deal sheet reporter `P:H`
- [ ] Add JSON export format for APIs `P:M`

## Refs
- Reporter interface: `base.py:1-50` (contract)
- Console reporter: `console_reporter.py:1-150` (ANSI formatting)
- Scoring formatter: `scoring_formatter.py:1-100` (percentage, tier display)
- Deal sheet: `deal_sheet_reporter.py:20-80` (HTML generation)

## Deps
← imports: Property, Tier, RiskLevel, ScoringWeights
→ used by: AnalysisPipeline, scripts, `/analyze-property` command
