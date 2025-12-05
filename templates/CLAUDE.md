---
last_updated: 2025-12-05
updated_by: agent
staleness_hours: 24
---
# templates

## Purpose
Jinja2 HTML templates for generating property analysis reports (risk assessments, renovation gap analysis). Provides styled HTML output for buyer decision-making and property due diligence documentation.

## Contents
| File | Purpose |
|------|---------|
| `risk_report.html` | Due Diligence Risk Report template (kill-switch verdict, severity scoring, risk categories) |
| `renovation_report.html` | Renovation Gap Analysis template (component conditions, repair estimates, timeline) |

## Key Patterns
- **Responsive design**: CSS Grid/Flexbox for mobile-first layouts (max-width: 1200px container)
- **Gradient headers**: Purple gradient (667eea → 764ba2) for visual consistency
- **System fonts**: -apple-system, BlinkMacSystemFont, Segoe UI stack for native look
- **Structured sections**: Header, main content, footer with semantic HTML
- **Embedded styling**: All CSS inline (no external stylesheets) for email compatibility

## Tasks
- [x] Map template files and purpose `P:H`
- [x] Document HTML structure and styling approach `P:H`
- [ ] Add Jinja2 variable documentation ({% for %}, {% if %}) `P:M`
- [ ] Create template usage guide (how to render, pass context) `P:L`

## Learnings
- **Email-safe design**: Inline styles required for email HTML rendering (Outlook, Gmail compatibility)
- **System font stack**: Native fonts faster than web fonts, consistent with OS UI
- **Container max-width**: 1200px prevents text from spanning too wide on desktop
- **Semantic HTML**: header, main, footer elements aid accessibility and screen readers

## Refs
- Risk report: `risk_report.html:1-30` (structure, gradient header)
- Renovation report: `renovation_report.html:1-30` (structure, styling)
- Template usage: `src/phx_home_analysis/services/reports/` (renderer service)

## Deps
← imports: Jinja2 (template engine), Python rendering context (property data, scores, verdicts)
→ used by: Report generation service, email delivery, web UI
