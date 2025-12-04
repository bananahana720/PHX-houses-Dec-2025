# Responsive Design & Accessibility

### Responsive Strategy

**Mobile-First Design Philosophy:**
The PHX Houses Analysis Pipeline prioritizes mobile deal sheet review during property tours. All layouts start mobile and progressively enhance for larger screens.

**Device-Specific Strategies:**

**Mobile (320px - 767px):**
- Single-column layout with full-width cards
- Bottom navigation bar (fixed) for primary sections
- Swipe gestures between properties
- Critical info (tier badge, verdict, top 3 warnings) above fold
- Collapsible sections via native `<details>` elements
- Large touch targets (44px minimum)
- Reduced data density — show essentials only

**Tablet (768px - 1023px):**
- Two-column layout for property comparisons
- Side navigation panel (collapsible)
- Touch-optimized controls retained from mobile
- Increased data density — show more fields
- Split view: list + detail panel
- Gesture support: swipe, pinch-to-zoom on images

**Desktop (1024px+):**
- Three-column layout for batch property views
- Persistent left sidebar navigation
- Keyboard shortcuts for power users
- Maximum data density — all fields visible
- Hover interactions for tooltips and previews
- Multi-panel dashboard for visualizations

**Platform-Specific Adaptations:**

| Feature | Mobile | Tablet | Desktop |
|---------|--------|--------|---------|
| Navigation | Bottom tabs | Side panel | Sidebar |
| Property cards | Full-width stack | 2-column grid | 3-column grid |
| Score detail | Expandable sections | Split view | Always visible |
| Warnings | Top 3 only | Top 5 with summaries | All warnings |
| Actions | Full-width buttons | Inline button group | Icon buttons |
| Images | Hero only | Hero + thumbnails | Gallery grid |

### Breakpoint Strategy

**Tailwind CSS Breakpoints (Mobile-First):**

```css
/* Mobile (default): 320px - 767px */
.property-card { @apply w-full; }

/* Tablet: 768px+ */
@media (min-width: 768px) {
  .property-card { @apply w-1/2; }
}

/* Desktop: 1024px+ */
@media (min-width: 1024px) {
  .property-card { @apply w-1/3; }
}

/* Large Desktop: 1280px+ */
@media (min-width: 1280px) {
  .property-card { @apply w-1/4; }
}
```

**Critical Breakpoints:**

- **640px (sm:)**: Transition from stacked to inline button groups
- **768px (md:)**: Enable two-column layouts, show side navigation
- **1024px (lg:)**: Enable three-column grids, persistent sidebar
- **1280px (xl:)**: Maximum content width, add extra whitespace

**Container Strategy:**
- Mobile: 100% width with 16px horizontal padding
- Tablet: Max 768px centered with 24px padding
- Desktop: Max 1280px centered with 32px padding
- Large Desktop: Max 1536px centered with 48px padding

**Content Adaptation Rules:**

| Content Type | Mobile | Tablet | Desktop |
|--------------|--------|--------|---------|
| Score breakdown | 3 dimensions | 3 dimensions + tooltips | Full 18 strategies |
| Property images | 1 hero image | 1 hero + 3 thumbnails | Gallery grid (6+) |
| Warning cards | Top 3 expanded | Top 5 with summaries | All with detail |
| Data fields | 6 key facts | 12 facts in table | All fields visible |
| Navigation | Bottom 4 tabs | Side panel 6 items | Sidebar full tree |

### Accessibility Strategy

**WCAG 2.1 Level AA Compliance:**

PHX Houses Analysis Pipeline targets WCAG 2.1 Level AA compliance to ensure accessibility for users with disabilities while maintaining practical implementation feasibility.

**Rationale for Level AA:**
- **Level A** is insufficient for users with moderate vision/mobility impairments
- **Level AA** is industry standard, legally defensible, improves UX for all users
- **Level AAA** is aspirational but not required for this use case

**Key Accessibility Requirements:**

**1. Color Contrast (Success Criterion 1.4.3):**
- Normal text: 4.5:1 minimum contrast ratio
- Large text (18pt+): 3:1 minimum contrast ratio
- UI components: 3:1 minimum contrast ratio
- Tier badges: Dark text on light backgrounds (never rely on color alone)
- High contrast mode support via `prefers-contrast: high`

**2. Keyboard Navigation (Success Criterion 2.1.1):**
- All interactive elements keyboard-accessible (Tab, Enter, Space)
- Focus indicators visible (2px solid ring, high contrast)
- Skip navigation link to main content
- Keyboard shortcuts for power users (with escape hatch)
- Modal dialogs trap focus, Esc to close

**3. Screen Reader Support (Success Criterion 4.1.2):**
- Semantic HTML structure (`<header>`, `<main>`, `<nav>`, `<section>`)
- ARIA labels for icon-only buttons
- ARIA live regions for dynamic updates (pipeline progress, filter results)
- ARIA roles for custom components (tabs, dialogs)
- Alternative text for all images (property photos, charts)

**4. Touch Targets (Success Criterion 2.5.5):**
- Minimum 44px × 44px for all interactive elements
- 8px spacing between adjacent targets
- Touch-optimized controls on mobile (no hover-only actions)
- Gesture alternatives (swipe = arrow buttons)

**5. Focus Management:**
- Visible focus indicators at all times (never `outline: none`)
- Logical tab order following visual layout
- Focus returns to trigger after modal close
- Skip links for repetitive navigation

**6. Forms and Validation:**
- Labels associated with all form controls
- Error messages linked via `aria-describedby`
- Real-time validation with polite announcements
- Clear instructions before form fields

**7. Content Accessibility:**
- Headings in logical hierarchy (h1 → h2 → h3)
- Lists use semantic markup (`<ul>`, `<ol>`)
- Data tables use `<th>` with scope attributes
- Abbreviations expanded on first use

### Testing Strategy

**Responsive Testing:**

**Device Testing:**
- **Real devices:** iPhone SE (320px), iPhone 14 Pro (393px), iPad Air (820px), MacBook Pro (1440px)
- **Browser DevTools:** Responsive mode testing across breakpoints
- **Network conditions:** Slow 3G simulation for mobile performance
- **Orientation:** Portrait and landscape testing for tablets

**Browser Testing:**
- **Desktop:** Chrome (latest), Firefox (latest), Safari (latest), Edge (latest)
- **Mobile:** Safari iOS (latest 2 versions), Chrome Android (latest)
- **Tablet:** Safari iPadOS, Chrome Android

**Responsive Testing Checklist:**
- [ ] All touch targets ≥44px on mobile
- [ ] Critical info (tier, verdict, warnings) above fold on 5-inch screens
- [ ] No horizontal scrolling at any breakpoint
- [ ] Images scale appropriately (no distortion)
- [ ] Navigation accessible at all breakpoints
- [ ] Text readable without zoom (16px minimum)

**Accessibility Testing:**

**Automated Testing Tools:**
- **axe DevTools:** Integrated into CI/CD pipeline
- **Lighthouse:** Accessibility score ≥95 required
- **WAVE:** Manual testing for complex components
- **Pa11y:** Command-line accessibility testing

**Manual Testing:**
- **Screen readers:** VoiceOver (macOS/iOS), NVDA (Windows), JAWS (Windows)
- **Keyboard-only navigation:** Complete all flows without mouse
- **Color blindness simulation:** Chrome DevTools vision deficiencies
- **Zoom testing:** 200% zoom with no content loss
- **High contrast mode:** Windows High Contrast, `prefers-contrast`

**Assistive Technology Testing:**
- **Screen readers:** Test with VoiceOver, NVDA (at minimum)
- **Voice control:** Dragon NaturallySpeaking, Voice Control (iOS)
- **Switch control:** iOS/Android switch access
- **Screen magnifiers:** ZoomText, Windows Magnifier

**User Testing:**
- Include users with disabilities in testing (minimum 2-3 participants)
- Test with diverse assistive technologies
- Validate with actual target devices (not just simulators)
- Gather feedback on perceived accessibility barriers

**Accessibility Testing Checklist:**
- [ ] All images have descriptive alt text
- [ ] Color contrast meets WCAG AA (4.5:1 for text, 3:1 for UI)
- [ ] All interactive elements keyboard-accessible
- [ ] Focus indicators visible on all focusable elements
- [ ] Screen reader announces all dynamic content
- [ ] Forms have associated labels and error messages
- [ ] No content flashing more than 3 times per second
- [ ] Text resizes to 200% without loss of content
- [ ] Headings in logical hierarchy (no skipped levels)
- [ ] ARIA attributes used correctly (validated with axe)

### Implementation Guidelines

**Responsive Development:**

**1. Use Relative Units:**
- Font sizes: `rem` (relative to root) instead of `px`
- Spacing: Tailwind spacing scale (`p-4`, `m-6`) instead of fixed pixels
- Layout: Flexbox and Grid for fluid layouts
- Widths: Percentages (`w-1/2`) or `max-w-*` instead of fixed widths

**2. Mobile-First Media Queries:**
```css
/* Default styles for mobile */
.property-card {
  @apply w-full p-4;
}

/* Tablet styles */
@media (min-width: 768px) {
  .property-card {
    @apply w-1/2 p-6;
  }
}

/* Desktop styles */
@media (min-width: 1024px) {
  .property-card {
    @apply w-1/3 p-8;
  }
}
```

**3. Touch Target Sizing:**
- Buttons: `min-h-[44px] min-w-[44px]`
- Links: Add padding to increase target size
- Icon buttons: Ensure icon + padding ≥44px
- Spacing: `space-x-2` (8px) minimum between targets

**4. Image Optimization:**
- Responsive images: `srcset` with multiple sizes
- Lazy loading: `loading="lazy"` for below-fold images
- Format: WebP with JPEG fallback
- Dimensions: Specify width/height to prevent layout shift

**Accessibility Development:**

**1. Semantic HTML Structure:**
```html
<header>
  <nav aria-label="Main navigation">...</nav>
</header>
<main id="main-content">
  <h1>Page Title</h1>
  <section aria-labelledby="section-heading">
    <h2 id="section-heading">Section Title</h2>
    ...
  </section>
</main>
<footer>...</footer>
```

**2. ARIA Labels and Roles:**
```html
<!-- Icon-only button -->
<button aria-label="Add to tour list">
  <svg>...</svg>
</button>

<!-- Custom tab component -->
<div role="tablist">
  <button role="tab" aria-selected="true">Tab 1</button>
  <button role="tab" aria-selected="false">Tab 2</button>
</div>

<!-- Live region for updates -->
<div aria-live="polite" aria-atomic="true">
  Pipeline progress: 47 of 50 properties analyzed
</div>
```

**3. Keyboard Navigation:**
```javascript
// Ensure keyboard support for custom components
function handleKeyDown(event) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault();
    handleClick();
  }
  if (event.key === 'Escape') {
    closeModal();
  }
}
```

**4. Focus Management:**
```css
/* Visible focus indicator */
.focus-ring:focus {
  @apply outline-none ring-2 ring-blue-500 ring-offset-2;
}

/* Skip link */
.skip-link {
  @apply sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 focus:z-50 focus:p-4 focus:bg-white focus:text-black;
}
```

**5. High Contrast Mode Support:**
```css
/* Ensure borders visible in high contrast */
@media (prefers-contrast: high) {
  .property-card {
    @apply border-2 border-black;
  }
  .badge {
    @apply font-bold;
  }
}
```

**Developer Checklist:**
- [ ] All components use semantic HTML
- [ ] ARIA attributes added where semantic HTML insufficient
- [ ] Focus management implemented for modals/dialogs
- [ ] Keyboard shortcuts have escape hatch (disable option)
- [ ] Color never sole indicator (use emoji/text backup)
- [ ] Touch targets meet 44px minimum
- [ ] Test with screen reader before merge
- [ ] Run axe DevTools and fix all issues
- [ ] Test keyboard-only navigation
- [ ] Verify color contrast with browser tools
