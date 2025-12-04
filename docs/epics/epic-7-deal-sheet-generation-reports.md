# Epic 7: Deal Sheet Generation & Reports

**User Value:** Produce actionable deal sheets with tier badges, kill-switch verdicts, score breakdowns, warnings, and tour checklists that enable confident property decisions in under 2 minutes - viewable on mobile during tours.

**PRD Coverage:** FR40-45, FR52-57
**Architecture References:** Presentation Layer, UX Design Specification

---

### E7.S1: Deal Sheet HTML Generation

**Priority:** P0 | **Dependencies:** E4.S4, E6.S2 | **FRs:** FR40, FR52, FR54, FR55

**User Story:** As a first-time homebuyer, I want comprehensive HTML deal sheets generated for each property, so that I can review properties on my mobile phone during tours.

**Acceptance Criteria:** HTML at `docs/artifacts/deal_sheets/{normalized_address}.html`. Mobile-responsive (320px viewport). Works offline (no external JS, CSS embedded). Size < 500KB. On mobile: Tier Badge and Kill-Switch Verdict visible above fold; details in collapsible `<details>` elements. `--regenerate` overwrites with fresh data. Single address generation supported.

**Technical Notes:** Jinja2 templates in `docs/templates/`. Tailwind CSS (CDN dev, compiled prod). Components: Property Card, Tier Badge, Verdict Card, Score Gauge, Warning Card, Collapsible Details. Mobile-first single column.

**Definition of Done:** Jinja2 template | Tailwind integration | Mobile-responsive | Offline capability | Regeneration CLI | Unit tests

---

### E7.S2: Deal Sheet Content Structure (Progressive Disclosure)

**Priority:** P0 | **Dependencies:** E7.S1 | **FRs:** FR41

**User Story:** As a first-time homebuyer, I want deal sheets structured for the 2-minute scan workflow, so that I can make tour/pass decisions quickly.

**Acceptance Criteria:** **Tier 1 (0-5s):** Hero image, address, price, Tier Badge, Kill-Switch Verdict. **Tier 2 (5-30s):** 3 Score Gauges, top 3 Warning Cards, key facts. **Tier 3 (30s+):** Collapsible: full score breakdown, all warnings, data table, provenance. Print stylesheet expands all `<details>`. WCAG 2.1 AA: semantic HTML, ARIA labels, 4.5:1 contrast, 44px touch targets.

**Technical Notes:** Property Card Container wrapper. Native `<details>` + `<summary>`. Print CSS: `details { display: block; }`. Lighthouse accessibility >= 95.

**Definition of Done:** Three-tier structure | All 6 UX components | Progressive disclosure | Print stylesheet | WCAG compliance | iPhone SE/14 Pro manual review

---

### E7.S3: Score Explanation Narratives

**Priority:** P1 | **Dependencies:** E7.S2 | **FRs:** FR42

**User Story:** As a first-time homebuyer, I want natural language explanations of WHY properties scored as they did, so that I understand the reasoning.

**Acceptance Criteria:** Narrative describes key factors in plain language, no jargon. Comparisons: "8% above batch average." Top 3 contributors per section highlighted with AZ context where relevant. Summary 2-3 sentences; detail expandable. Key insights highlighted (e.g., "⭐ Best-in-class: #1 Location score").

**Technical Notes:** Implement `NarrativeGenerator` in `src/phx_home_analysis/reporters/`. Template-based with variables. Comparative language from batch statistics. Output: summary, detail, highlights, data_citations.

**Definition of Done:** NarrativeGenerator | Templates per dimension | Plain language | Comparative context | AZ context | Length management | Unit tests

---

### E7.S4: Visual Comparisons (Radar Charts & Value Spotter)

**Priority:** P1 | **Dependencies:** E4.S4 | **FRs:** FR43

**User Story:** As a first-time homebuyer, I want visual comparison charts, so that I can quickly compare properties and identify value opportunities.

**Acceptance Criteria:** **Radar chart:** 3 dimensions (Location %, Systems %, Interior %), up to 5 properties overlaid. **Value Spotter scatter:** X=price, Y=score, color by tier (green/amber/gray), "Value" quadrant highlighted, outliers labeled. Output: SVG for embedding, PNG for sharing. Print-friendly.

**Technical Notes:** Plotly for charts. Radar: percentage scale 0-100%. Scatter: 4 quadrants, size by lot_sqft optional. SVG inline or base64. Output: `data/visualizations/`.

**Definition of Done:** Radar chart | Scatter plot | Multi-property overlay | Tier coloring | SVG/PNG export | Print compatibility

---

### E7.S5: Risk Checklists for Property Tours

**Priority:** P1 | **Dependencies:** E6.S2 | **FRs:** FR44

**User Story:** As a first-time homebuyer, I want property-specific tour checklists generated from warnings, so that I know exactly what to verify during visits.

**Acceptance Criteria:** Warnings become verification items with specific actions, prioritized by severity. **Standard items:** HVAC, water heater, electrical panel, roof, windows. **AZ-specific:** pool equipment, solar panels, desert landscaping, orientation. Print-optimized 8.5x11 with 0.5" checkboxes and note space. QR code (1" min) links to deal sheet.

**Technical Notes:** Implement `ChecklistGenerator`. Output: HTML, TXT, PDF. Storage: `docs/risk_checklists/`. QR via `qrcode` library.

**Definition of Done:** ChecklistGenerator | Warning-to-item transform | Standard items | AZ items | Print layout | QR generation | Multiple formats

---

### E7.S6: Deal Sheet Regeneration After Re-Scoring

**Priority:** P1 | **Dependencies:** E4.S6, E7.S1 | **FRs:** FR45

**User Story:** As a first-time homebuyer, I want deal sheets automatically regenerated after re-scoring, so that reports reflect my updated priorities and show changes.

**Acceptance Criteria:** `--regenerate` updates all deal sheets with new scores. Deltas show old→new with tier changes (🥊 → 🦄). Dimension-level deltas with change explanation. `--address` regenerates single property. Batch shows progress bar and tier distribution summary.

**Technical Notes:** Delta display via `{% if has_score_delta %}`. Side-by-side flex layout. Green/red text for +/-. CLI: `python -m scripts.deal_sheets --regenerate [--all|--address "..."]`.

**Definition of Done:** Batch regeneration | Selective by address | Delta display | Tier highlighting | Dimension breakdown | Progress reporting | Integration test

---
