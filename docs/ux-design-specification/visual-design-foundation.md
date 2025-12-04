# Visual Design Foundation

### Color System

**Semantic Color Palette:**

| Category | Token | Hex | Usage |
|----------|-------|-----|-------|
| Tier: Unicorn | `--color-unicorn` | #10B981 | Best properties (>480 pts) |
| Tier: Contender | `--color-contender` | #F59E0B | Solid options (360-480 pts) |
| Tier: Pass | `--color-pass` | #6B7280 | Below threshold (<360 pts) |
| Verdict: Pass | `--color-verdict-pass` | #10B981 | Kill-switch passed |
| Verdict: Fail | `--color-verdict-fail` | #EF4444 | Kill-switch failed |
| Verdict: Warning | `--color-verdict-warning` | #F59E0B | Kill-switch warning |
| Error | `--color-error` | #F59E0B | Calm errors (amber, not red) |
| Success | `--color-success` | #10B981 | Success states |
| Info | `--color-info` | #3B82F6 | Informational |

**Surface Colors:** Light backgrounds (#FFFFFF, #F9FAFB) with dark mode support via `prefers-color-scheme`.

### Typography System

**Font Stack:** System fonts (`system-ui, -apple-system, ...`) for instant loading and native feel.

**Type Scale:**
- Score display: 2.25rem (36px), bold, monospace
- Page titles: 1.875rem (30px), bold
- Section headers: 1.25rem (20px), semibold
- Body text: 1rem (16px), regular
- Secondary text: 0.875rem (14px), regular
- Metadata: 0.75rem (12px), regular

**Weights:** Regular (400), Medium (500), Semibold (600), Bold (700)

### Spacing & Layout Foundation

**Base Unit:** 4px multiplier system
- Tight: 4px | Small: 8px | Standard: 16px | Medium: 24px | Large: 32px | Section: 48px

**Touch Targets:** Minimum 44px × 44px for all interactive elements

**Layout Grid:**
- Mobile: Single column, 16px horizontal padding
- Tablet: Two-column for comparisons
- Desktop: Three-column for batch views

### Accessibility Considerations

**Contrast:** WCAG AA compliant (4.5:1 for text, 3:1 for large text/icons)

**Color Blindness:** Every colored element has emoji + text backup (never color alone)

**Outdoor Use:**
- High contrast mode support (`prefers-contrast: high`)
- Bold badge text (600-700 weight)
- Large tap targets (44px minimum)
- Dark text on light badge backgrounds
