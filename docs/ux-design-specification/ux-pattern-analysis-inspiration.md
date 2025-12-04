# UX Pattern Analysis & Inspiration

### Inspiring Products Analysis

**1. Carfax Vehicle History Reports**
- Clear verdict badges (Clean title vs Accident reported)
- Risk iconography with consistent visual language
- Evidence linking — every claim traceable to source
- Consequence framing with dollar/resale impact
- **Key Insight:** "Saves" messaging builds trust without panic

**2. Credit Karma Score Explanations**
- Score gauge visualization with color-coded ranges
- Factor breakdown ("Here's what's helping/hurting")
- Simulation mode for "what if?" scenarios
- Confidence/freshness indicators
- **Key Insight:** ~6 factors with simple up/down arrows — perfect for 3-dimension breakdown

**3. Stripe Dashboard**
- Progressive disclosure (Summary → Trends → Details)
- Status indicators (Green/Yellow/Red dots)
- Developer-friendly technical details on demand
- Mobile-first card design
- **Key Insight:** Three-tier disclosure maps to badge → summary → detail

**4. GitHub CLI**
- Consistent mental model across CLI and web
- Progress spinners with clear status
- Structured output with `--json` flag
- Human-readable errors with suggestions
- **Key Insight:** CLI output scannable with color, spacing, emoji

**5. Airbnb Property Cards**
- Hero image + key stats in one view
- Badge system (Superhost, Rare find)
- Touch-optimized large tap targets
- Quick save/compare actions
- **Key Insight:** Badge hierarchy maps to Unicorn > Contender > Pass

### Transferable UX Patterns

**Navigation:** Card-based browsing (Airbnb), Progressive drill-down (Stripe), Tabbed sections (Credit Karma)

**Interaction:** Simulation preview (Credit Karma), Inline expansion (Stripe), Quick actions (Airbnb), Copy-friendly output (GitHub)

**Visual:** Status badges (All), Score gauges (Credit Karma), Factor arrows (Credit Karma), Semantic colors (Stripe)

**CLI:** Colored output, Progress spinners, Structured flags, Helpful errors (GitHub CLI)

### Anti-Patterns to Avoid

1. **Information dump** → Use progressive disclosure instead
2. **Hidden evidence** → Always show source attribution
3. **Red-heavy errors** → Use amber + calm language
4. **Jargon warnings** → Use consequence-first plain language
5. **Endless scrolling** → Use card-based pagination
6. **No offline mode** → Cache deal sheets locally
7. **Click-heavy navigation** → Use gestures + large tap targets

### Design Inspiration Strategy

**Adopt:**
- Carfax "saves" messaging for kill-switch catches
- Credit Karma factor breakdown for score dimensions
- Stripe progressive disclosure for complexity management
- GitHub CLI conventions for terminal output
- Airbnb card design for mobile property browsing

**Adapt:**
- Credit Karma simulation → YAML config preview (not interactive sliders)
- Stripe status dots → Include severity levels
- Airbnb badges → More prominent tier hierarchy
- GitHub progress → Add time estimation

**Avoid:**
- Zillow infinite scroll (decision fatigue)
- Redfin data density (overwhelming)
- Generic red errors (induces panic)
- Hidden "learn more" (critical info buried)
