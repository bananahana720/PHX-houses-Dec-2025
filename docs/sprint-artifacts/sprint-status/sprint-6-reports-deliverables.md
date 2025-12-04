# Sprint 6: Reports & Deliverables

> **Epic**: E7
> **Objective**: Generate actionable deal sheets enabling 2-minute property decisions
> **Stories**: 6
> **PRD Coverage**: FR40-45, FR52-57

### Stories

#### E7.S1 - Deal Sheet HTML Generation [CRITICAL PATH]

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E4.S4, E6.S2 |
| **FRs** | FR40, FR52, FR54, FR55 |

**Acceptance Criteria**:
- [ ] HTML files at `docs/artifacts/deal_sheets/{address}.html`
- [ ] Mobile-responsive (readable on 5-inch screen)
- [ ] Offline capable (no external dependencies)
- [ ] Tier badge and verdict visible above fold

**Definition of Done**:
- [ ] Jinja2 templates in `docs/templates/`
- [ ] Tailwind CSS integration
- [ ] Components: Property Card, Tier Badge, Verdict Card, Score Gauge, Warning Card

---

#### E7.S2 - Deal Sheet Content Structure

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P0 |
| **Dependencies** | E7.S1 |
| **FRs** | FR41 |

**Acceptance Criteria**:
- [ ] Header: address, price, tier badge, kill-switch verdict
- [ ] Summary: 3-section score breakdown with gauges
- [ ] Warnings: up to 5 warnings with severity and consequences
- [ ] Details: complete data table with source attribution
- [ ] Progressive disclosure via `<details>` elements

**Definition of Done**:
- [ ] 2-minute scan UX goal achieved
- [ ] Print stylesheet expands all sections
- [ ] WCAG 2.1 Level AA accessibility

---

#### E7.S3 - Score Explanation Narratives

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P1 |
| **Dependencies** | E7.S2 |
| **FRs** | FR42 |

**Acceptance Criteria**:
- [ ] Plain language explanations (no jargon)
- [ ] Comparative context ("This scored 487 vs average of 450")
- [ ] Top 3 contributors highlighted per section
- [ ] Summary: 2-3 sentences, expandable detail

**Definition of Done**:
- [ ] NarrativeGenerator in `src/phx_home_analysis/reporters/`
- [ ] Templates for each scoring dimension
- [ ] GPT-style natural language output

---

#### E7.S4 - Visual Comparisons (Radar & Scatter)

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P1 |
| **Dependencies** | E4.S4 |
| **FRs** | FR43 |

**Acceptance Criteria**:
- [ ] Radar chart: 3-dimension polygon (Location, Systems, Interior)
- [ ] Up to 5 properties overlaid
- [ ] Scatter plot: X=price, Y=score, color=tier
- [ ] Value properties highlighted (high score, low price)
- [ ] SVG output for HTML embedding

**Definition of Done**:
- [ ] Plotly chart generation
- [ ] Print-friendly (no interactive elements required)

---

#### E7.S5 - Risk Checklists for Property Tours

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P1 |
| **Dependencies** | E6.S2 |
| **FRs** | FR44 |

**Acceptance Criteria**:
- [ ] Each warning becomes a verification item
- [ ] Standard inspection items included (HVAC, water heater, electrical panel)
- [ ] Arizona-specific items (pool equipment, solar panels, desert landscaping)
- [ ] Print-optimized (8.5x11 paper) with checkboxes

**Definition of Done**:
- [ ] ChecklistGenerator service
- [ ] Output: `docs/risk_checklists/{address}_checklist.txt`
- [ ] QR code linking to full deal sheet

---

#### E7.S6 - Deal Sheet Regeneration After Re-Scoring

| Field | Value |
|-------|-------|
| **Status** | `[ ]` pending |
| **Priority** | P1 |
| **Dependencies** | E4.S6, E7.S1 |
| **FRs** | FR45 |

**Acceptance Criteria**:
- [ ] Batch regeneration updates all deal sheets
- [ ] Selective regeneration with --address flag
- [ ] Old/new scores shown in regenerated sheets
- [ ] Tier changes highlighted with arrow notation

**Definition of Done**:
- [ ] Regeneration in deal sheet generator
- [ ] CLI: `python -m scripts.deal_sheets --all` / `--address "123 Main St"`

---
