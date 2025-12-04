# Design System Foundation

### Design System Choice

**Primary Choice: Tailwind CSS (Utility-First)**

For HTML deal sheets, Tailwind CSS provides the optimal balance of customization, mobile-first design, and integration with Jinja2 templating. The utility-first approach composes naturally in generated HTML templates.

**CLI Design: Native Conventions**

Terminal output uses Python `rich` library for ANSI colors, emoji badges, progress spinners, and formatted tables. No external design system needed — follow GitHub CLI conventions.

### Rationale for Selection

1. **Jinja2 Synergy**: Utility classes compose directly in templates without component abstraction overhead
2. **Mobile-First Built-In**: Responsive breakpoints (`sm:`, `md:`, `lg:`) handle device adaptation
3. **Performance**: PurgeCSS removes unused styles, resulting in tiny CSS bundles
4. **Offline Capability**: Single CSS file with no external dependencies
5. **High Contrast Support**: Easy to add accessibility utilities for outdoor readability
6. **No JavaScript**: `<details>` elements provide progressive disclosure natively

### Implementation Approach

**HTML Deal Sheets:**
- Tailwind CSS via CDN (development) or compiled (production)
- Custom CSS variables for design tokens (tier colors, verdict colors, confidence levels)
- Native HTML5 elements (`<details>`, `<summary>`) for collapsible sections
- Print stylesheet for physical checklist generation

**CLI Output:**
- Python `rich` library for terminal formatting
- ANSI color conventions following GitHub CLI patterns
- Emoji tier badges with color backup (🦄 green, 🥊 yellow, ⏭️ gray)
- Progress bars with time estimation for long-running phases

### Customization Strategy

**Design Tokens (CSS Variables):**

| Token Category | Examples |
|----------------|----------|
| Tier Colors | `--color-unicorn`, `--color-contender`, `--color-pass` |
| Verdict Colors | `--color-pass-verdict`, `--color-fail-verdict`, `--color-warning-verdict` |
| Confidence | `--color-confidence-high`, `--color-confidence-medium`, `--color-confidence-low` |
| Semantic | `--color-error` (amber, not red), `--color-success`, `--color-info` |

**Component Library:**

| Component | Strategy |
|-----------|----------|
| Property Card | Tailwind flex/grid + tier badge composition |
| Tier Badge | Custom class (`.badge-unicorn`) with CSS variable colors |
| Score Gauge | CSS-only progress bar or inline SVG |
| Warning Card | Severity-colored border + icon |
| Collapsible Section | Native `<details>` + `<summary>` |
| Data Table | Tailwind table utilities |
| Checklist | Native checkboxes + Tailwind styling |

**No Build Step Required for MVP:**
- Tailwind CDN for rapid iteration
- Custom `<style>` block for design tokens
- Compile Tailwind only for production optimization
