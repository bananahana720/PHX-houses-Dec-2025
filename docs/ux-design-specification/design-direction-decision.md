# Design Direction Decision

### Design Directions Explored

The design direction for PHX Houses Analysis Pipeline balances **professional data density** with **mobile-first glanceability**. Three primary visual approaches were considered:

**Direction A: "Dashboard Dense"**
- Multi-column layout with data tables
- Information-rich density for power users
- Desktop-first with mobile adaptation
- Emphasis on comparison views
- Risk: Overwhelming on mobile screens

**Direction B: "Card Minimalist"**
- Card-based progressive disclosure
- Mobile-first with large touch targets
- White space emphasis for clarity
- Single-column focus
- Risk: Slower access to details

**Direction C: "Hybrid Progressive" (Chosen)**
- Card-based mobile foundation
- Progressive density: badge → summary → detail
- Touch-first with keyboard shortcuts
- Collapsible sections for depth
- Balances scan speed with detail access

**Direction D: "CLI-First"**
- Terminal-centric with HTML as export
- ASCII art visualizations
- Text-based navigation
- Risk: Limited mobile usability

### Chosen Direction

**Direction C: Hybrid Progressive Disclosure**

This approach prioritizes the core 2-minute mobile scan while providing drill-down depth for desktop analysis. The design uses a three-tier disclosure model:

**Tier 1: Glance (0-5 seconds)**
```
┌─────────────────────────────────────┐
│ 🏠 123 Main St, Phoenix             │
│ $485K              🦄 Unicorn 487pts │
│                    🟢 PASS           │
├─────────────────────────────────────┤
│ Location: 195/230  Systems: 165/180 │
│ Interior: 127/190                   │
└─────────────────────────────────────┘
```

**Tier 2: Summary (5-30 seconds)**
- Expandable warnings section (top 3 visible)
- Key facts checklist
- Source confidence indicators

**Tier 3: Detail (30+ seconds)**
- Full score breakdown by strategy
- Complete data table
- Evidence links

### Design Rationale

**Why Hybrid Progressive:**

1. **Mobile-First Reality**: 70% of deal sheet views happen during property tours on mobile devices
2. **Cognitive Load Management**: 600-point scoring system requires layered disclosure to prevent overwhelm
3. **Speed + Depth**: Glance layer enables 2-minute scans; detail layer builds confidence
4. **Offline Capability**: Card-based HTML works without JavaScript
5. **Print-Friendly**: Collapsible sections expand in print CSS for physical checklists

**Key Visual Decisions:**

| Element | Choice | Rationale |
|---------|--------|-----------|
| Tier badge | Top-right, large (48px) | First eye scan on mobile |
| Score display | Monospace, bold, dimension breakdown | Familiar credit score pattern |
| Warnings | Amber border cards, not red alerts | Calm framing, not panic |
| Touch targets | 44px minimum | Outdoor usability |
| Typography | System fonts | Instant loading, native feel |

**Alignment with Emotional Goals:**

- **Confidence**: Tier badge provides instant quality signal
- **Calm**: Progressive disclosure prevents information overload
- **Control**: Expandable sections give user-paced exploration
- **Trust**: Evidence always one tap away

### Implementation Approach

**HTML Structure:**
```html
<article class="property-card">
  <header class="card-header">
    <!-- Tier 1: Glance -->
  </header>
  <section class="card-summary">
    <!-- Tier 2: Summary -->
  </section>
  <details class="card-details">
    <summary>Full Details</summary>
    <!-- Tier 3: Detail -->
  </details>
</article>
```

**CSS Strategy:**
- Tailwind utility classes for layout
- CSS custom properties for tier/verdict colors
- `<details>` native element for progressive disclosure
- Print stylesheet expands all `<details>` automatically

**Mobile-First Breakpoints:**
- Mobile: Single column, 16px padding
- Tablet (768px+): Two-column comparisons
- Desktop (1024px+): Three-column batch view

**Accessibility:**
- ARIA labels on all badges
- Keyboard navigation via tab order
- High contrast mode support
- Screen reader friendly semantic HTML
