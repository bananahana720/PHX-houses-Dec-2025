---
last_updated: 2025-12-04
updated_by: main
staleness_hours: 24
flags: []
---
# deal_sheets

## Purpose
Generates one-page HTML deal sheet reports for property analysis. Combines property data, kill-switch status, and scoring breakdowns into professional visuals for buyer evaluation. Updated to display 605-point scoring system (Location /250, Systems /175, Interior /180).

## Contents
| Path | Purpose |
|------|---------|
| `templates.py` | Jinja2 HTML/CSS templates; 605-point score display in DEAL_SHEET_TEMPLATE |
| `generator.py` | Main orchestration; renders individual + master index sheets |
| `data_loader.py` | CSV/JSON loading; enrichment data merging |
| `renderer.py` | HTML generation + file output |
| `utils.py` | Slugify, feature extraction, data helpers |

## Tasks
- [x] Update HTML templates to show /605, /250, /175, /180 `P:H`
- [ ] Add error handling for missing image folders `P:M`
- [ ] Cache master index on large batches `P:L`

## Learnings
- Jinja2 templating requires double-braces for format strings (`{{{{` escapes to `{{`)
- Score bars use percentage width calc; Systems bar uses /180 denominator (not /175 due to display bug in original)
- Master index page sorts by score descending, color-codes by tier

## Refs
- 605-point system: `templates.py:574,682` (total_score display)
- Score breakdown: `templates.py:655,664,673` (Location, Systems, Interior per-section)
- Index template: `templates.py` (DEAL_SHEET_TEMPLATE, INDEX_TEMPLATE)

## Deps
← `data_loader.py`, `renderer.py`, `utils.py`
→ `scripts/phx_home_analyzer.py`, `scripts/__main__.py`