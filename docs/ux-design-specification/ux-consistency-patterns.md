# UX Consistency Patterns

### Button Hierarchy

**Primary Actions:**
- **Visual:** Green background (#10B981), white text, bold weight, 44px minimum height
- **Usage:** Tour decision, Add to shortlist, Generate checklist
- **Behavior:** Immediate action with success feedback
- **Mobile:** Full-width on mobile, fixed at 88px width on desktop
- **Accessibility:** ARIA label, Enter key support, focus ring (2px solid)

**Secondary Actions:**
- **Visual:** White background, gray border, dark text
- **Usage:** View details, Copy summary, Share
- **Behavior:** Non-destructive, can be reversed
- **Mobile:** Inline with primary action
- **Accessibility:** Same as primary, visually distinct

**Destructive Actions:**
- **Visual:** Amber background (#F59E0B, not red), dark text
- **Usage:** Dismiss property, Reset scoring weights
- **Behavior:** Confirmation dialog with consequence preview
- **Mobile:** Separated from primary actions
- **Accessibility:** Warning announced before action

### Feedback Patterns

**Success States:**
- **Visual:** Green badge with checkmark emoji (✅)
- **Message:** Action-oriented (e.g., "Added to tour list (3 of 5)")
- **Duration:** 3 seconds auto-dismiss or manual close
- **Sound:** Optional success chime (accessibility setting)
- **Persistence:** Available in notification history

**Error States:**
- **Visual:** Amber badge (not red) with warning emoji (⚠️)
- **Message:** Calm language + actionable next step (e.g., "Pipeline paused — resume with `--resume`")
- **Duration:** Persistent until acknowledged
- **Actions:** Always include recovery action button
- **Log:** Automatically captured with timestamp

**Warning States:**
- **Visual:** Yellow badge with alert emoji (🟡)
- **Message:** Consequence-first (e.g., "🛡️ Saved you from $15K solar lease liability")
- **Duration:** Persistent on deal sheet, dismissible in CLI
- **Severity:** Visual weight matches severity (border thickness)
- **Actions:** "Learn more" expands full context

**Info States:**
- **Visual:** Blue badge with info emoji (ℹ️)
- **Message:** Contextual help (e.g., "HVAC lifespan in AZ: 10-15 years")
- **Duration:** Auto-dismiss after 5 seconds
- **Trigger:** Inline tooltips on hover/tap
- **Accessibility:** Screen reader announces on focus

### Form Patterns

**Configuration Editing (YAML):**
- **Validation:** Real-time with inline error markers
- **Preview:** "What if?" preview showing score deltas before save
- **Feedback:** Green checkmark for valid, amber warning for syntax errors
- **Auto-save:** Every 500ms with debouncing
- **Recovery:** Auto-backup before any edit session

**Filter Controls:**
- **Visual:** Horizontal pills on mobile, sidebar on desktop
- **Behavior:** Instant filter application with result count update
- **Reset:** "Clear all filters" always visible
- **Persistence:** Saved to localStorage for session
- **Accessibility:** Keyboard shortcuts (Ctrl+F to focus)

**Search Patterns:**
- **Visual:** Magnifying glass icon, 44px minimum height
- **Behavior:** Debounced search (300ms) with loading spinner
- **Results:** Highlighted matches, result count displayed
- **Mobile:** Full-width search bar at top
- **Accessibility:** ARIA live region for result updates

### Navigation Patterns

**Mobile Navigation (Deal Sheets):**
- **Pattern:** Bottom tab bar (fixed) with 3-5 primary sections
- **Visual:** Icons + labels, active state with accent color
- **Gesture:** Swipe left/right between properties
- **Scroll:** Infinite scroll with "Load more" trigger
- **Accessibility:** Skip navigation link at top

**Desktop Navigation (Visualizations):**
- **Pattern:** Left sidebar with collapsible sections
- **Visual:** Tree structure with expand/collapse icons
- **Behavior:** Persistent navigation, current item highlighted
- **Scroll:** Independent scroll for nav and content
- **Accessibility:** Keyboard arrow navigation

**Breadcrumbs (CLI Output):**
- **Pattern:** Phase → Property → Step
- **Visual:** Separated by "→" or "/" characters
- **Behavior:** Non-interactive (terminal output)
- **Truncation:** Shorten middle segments on narrow terminals
- **Accessibility:** Full path in screen reader

### Modal and Overlay Patterns

**Confirmation Dialogs:**
- **Visual:** Centered modal with backdrop blur
- **Trigger:** Destructive actions only
- **Content:** Consequence preview + action confirmation
- **Actions:** Primary (proceed) + secondary (cancel)
- **Escape:** Esc key or tap backdrop to dismiss
- **Accessibility:** Focus trap, ARIA role="dialog"

**Detail Panels (Score Breakdown):**
- **Visual:** Native `<details>` + `<summary>` elements
- **Trigger:** Tap/click on score section
- **Animation:** Smooth expand/collapse (200ms ease)
- **State:** Remembers expanded state in session
- **Accessibility:** Native keyboard support (Space/Enter)

**Toast Notifications:**
- **Visual:** Bottom-right corner (desktop), top (mobile)
- **Stack:** Maximum 3 visible, oldest auto-dismissed
- **Actions:** Undo, View details, Dismiss
- **Duration:** 3s (success), 5s (warning), persistent (error)
- **Accessibility:** ARIA live="polite" region

### Empty States and Loading States

**Empty Property List:**
- **Visual:** Centered illustration + message
- **Message:** "No properties match your criteria — try adjusting kill-switches"
- **Actions:** "Reset filters" button, "Learn more" link
- **Context:** Show active filters that caused empty state
- **Accessibility:** Focusable heading for screen readers

**Loading States (Pipeline Runs):**
- **Visual:** Spinner + progress bar + time estimate
- **Message:** Current phase + property being processed
- **Updates:** Every ≤30 seconds with actionable status
- **Cancel:** "Pause pipeline" button always visible
- **Accessibility:** ARIA live="polite" for updates

**Partial Data States:**
- **Visual:** Grayed-out section + "Pending Phase X" label
- **Message:** "Image scoring available after Phase 2 completes"
- **Actions:** "Resume pipeline" if paused
- **Context:** Show which phases completed vs pending
- **Accessibility:** Clear labeling of incomplete sections

**Error Recovery States:**
- **Visual:** Amber alert box with recovery instructions
- **Message:** Error summary + recommended action
- **Actions:** "Resume", "Skip property", "Reset state"
- **Logs:** Expandable error log section
- **Accessibility:** Error announced, actions keyboard-navigable

### Search and Filtering Patterns

**Quick Filter Pills:**
- **Visual:** Horizontal scrollable row of filter chips
- **States:** Default (gray), Active (green), Disabled (light gray)
- **Behavior:** Toggle on/off, multi-select supported
- **Reset:** "X" icon on active filters + "Clear all" button
- **Accessibility:** ARIA role="checkbox" for each pill

**Advanced Filter Panel:**
- **Visual:** Collapsible panel with grouped controls
- **Controls:** Range sliders, checkboxes, radio groups
- **Preview:** Live result count as filters change
- **Save:** "Save filter set" for reusable queries
- **Accessibility:** Form semantics, label associations

**Search Results:**
- **Visual:** Highlighted matches in bold + background color
- **Sorting:** Relevance (default), Score, Price, Date added
- **Pagination:** Infinite scroll with "Load more" marker
- **Empty:** "No matches — try different keywords" with suggestions
- **Accessibility:** Result count announced, keyboard navigation
