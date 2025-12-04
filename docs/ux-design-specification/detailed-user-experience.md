# Detailed User Experience

### Defining Experience Statement

**"Glance at the deal sheet → Know instantly if this property is worth touring"**

This is the core interaction that defines the product. Every design decision flows from enabling this 2-minute scan that transforms 50+ weekly listings into 3-5 actionable tour candidates.

### User Mental Model

**Current problem-solving approach:**
- Hours scrolling Zillow with no systematic filter
- Mental tracking of criteria leading to emotional decisions
- Scattered Google searches for Arizona-specific factors
- Biased advice from friends/realtors without evidence

**Mental model users bring:**
- Pass/fail checklist mentality (kill-switch)
- Credit score familiarity (tier system)
- "What am I missing?" anxiety (warning system)
- Evidence verification need (source attribution)

**Confusion points to address:**
- Complex scoring → Progressive disclosure (badge → summary → detail)
- Arizona factors → Inline contextual explanations
- Multiple sources → Explicit confidence levels

### Success Criteria

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Instant comprehension | Tier understood | <5 seconds |
| Decision confidence | Tour/pass decided | <2 minutes |
| Evidence satisfaction | Any score traceable | 1 click to source |
| Warning clarity | Consequence understood | Plain language |
| Mobile usability | Critical info visible | No scroll for badges |

**User success moments:**
- System catches a risk they would have missed
- Score matches gut feeling with evidence
- Re-scoring reveals hidden value properties
- Tour checklist covers exactly what's needed

### Novel UX Patterns

**Established patterns adopted:**
- Tier badges (Airbnb Superhost model)
- Score breakdown (Credit Karma factor display)
- Progressive disclosure (Stripe three-tier model)
- CLI progress (GitHub CLI conventions)

**Novel adaptations:**
- Soft kill-switch severity threshold (≥3.0 = FAIL) — requires first-run education
- Arizona-specific factor explanations — inline tooltips
- Confidence level attribution — legend in header

**Familiar metaphors:**
- "Property score" like credit score
- "Risk report" like Carfax
- "Tour or pass" like Tinder swipe

### Experience Mechanics: The 2-Minute Scan

**Phase 1: Initiation (0-5 seconds)**
- Property image as visual anchor
- Address + price for identification
- Tier badge (🦄/🥊/⏭️) top-right for instant quality signal
- Kill-switch verdict (🟢/🔴/🟡) below tier

**Phase 2: First Glance (5-30 seconds)**
- Score summary: 3-dimension breakdown visible without scroll
- Top 3 warnings: consequence-first text
- Key facts: beds, baths, sqft, lot, year as scannable list

**Phase 3: Deep Dive (30-90 seconds)** — if interested
- Score detail via expandable `<details>` sections
- Warning detail: source + evidence + action
- Property facts: all data fields in scrollable table
- Data provenance: source + confidence + freshness

**Phase 4: Decision (90-120 seconds)**
- Tour checklist: property-specific verification items
- Quick actions: add to tour list, flag, dismiss
- Share: copy summary to clipboard

**Phase 5: Completion Feedback**
- "✅ Added to tour list (3 of 5)"
- "⏭️ Dismissed — 42 more to review"
- "🚩 Flagged — review with realtor"
