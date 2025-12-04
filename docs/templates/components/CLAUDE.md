---
last_updated: 2025-12-04
updated_by: Claude Code
staleness_hours: 24
flags: []
---
# components

## Purpose

Reusable HTML/Jinja2 components for property report generation. Provides modular, responsive UI building blocks with dynamic scoring support.

## Contents

| Path | Purpose |
|------|---------|
| `score_breakdown.html` | Three-section scorecard with progress bars (Location/250, Systems/175, Interior/180) |
| `property_card.html` | Property summary card with image, address, score, tier badge, and kill-switch status |
| `risk_badge.html` | Risk level badge component (Critical/High/Medium/Low severity indicators) |

## Key Updates

**605-Point System:** Templates updated to use dynamic scoring with section maximums:
- Location: 250 pts (Section A)
- Systems: 175 pts (Section B)
- Interior: 180 pts (Section C)
- Total: 605 pts

Uses `section_a_max`, `section_b_max`, `section_c_max` properties for flexible point allocation.

## Tasks

- [x] Update score_breakdown.html for 605-point system
- [x] Update property_card.html with new scoring
- [ ] Add unit tests for component rendering
- [ ] Document Jinja2 context requirements

## Learnings

- Components use Jinja2 filters (`format`, conditional rendering) for dynamic data
- Progress bars scale automatically with `percentage` calculations
- Modular design allows reuse across risk_report.html and renovation_report.html

## Refs

- Usage examples: `docs/artifacts/deal_sheets/`
- Base template: `docs/templates/base.html`
- Report templates: `docs/templates/risk_report.html`, `docs/templates/renovation_report.html`
- Scoring config: `src/phx_home_analysis/config/scoring_weights.py:1-50`

## Deps

← `docs/templates/base.html`
→ `docs/templates/risk_report.html`, `docs/templates/renovation_report.html`
