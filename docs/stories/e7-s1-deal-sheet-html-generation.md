# Story 7.1: Deal Sheet HTML Generation

Status: done

## Story

As a system user,
I want comprehensive HTML deal sheets,
so that I can review properties on mobile during tours.

## Acceptance Criteria

1. **Mobile-first responsive design**
   - [ ] Viewport meta tag configured for mobile devices
   - [ ] Flexbox/CSS Grid layout adapts to screen widths (320px to 1920px)
   - [ ] Touch-friendly tap targets (min 44px)
   - [ ] Readable text without horizontal scrolling on mobile

2. **Property data rendering**
   - [ ] Full address displayed in header
   - [ ] List price formatted with commas ($XXX,XXX)
   - [ ] Beds/baths/sqft displayed prominently
   - [ ] Lot size, year built, garage spaces shown
   - [ ] HOA fee displayed if applicable

3. **Score visualizations**
   - [ ] Total score displayed as X/605 pts
   - [ ] Tier badge (UNICORN/CONTENDER/PASS) with appropriate colors
   - [ ] Three-section breakdown with progress bars:
     - Location: X/250 pts
     - Systems: X/175 pts
     - Interior: X/180 pts
   - [ ] Percentage indicators on progress bars

4. **Kill-switch status display**
   - [ ] Verdict badge (PASS/WARNING/FAIL)
   - [ ] HARD criteria ([H]) vs SOFT criteria ([S]) markers
   - [ ] Individual criterion status table
   - [ ] Severity score display for soft failures
   - [ ] Failure explanation messages

5. **Image gallery section**
   - [ ] Displays available property images
   - [ ] Images load from `data/property_images/processed/{hash}/` path
   - [ ] Graceful handling when no images available
   - [ ] Responsive image grid

6. **Tour checklist section**
   - [ ] Dynamically generated based on warnings
   - [ ] Items for each WARNING or FAIL criterion
   - [ ] Printable checkbox format
   - [ ] Includes specific inspection points

7. **Performance and validation**
   - [ ] HTML passes W3C validation (no critical errors)
   - [ ] Page loads in <2 seconds on mobile (lighthouse check)
   - [ ] No JavaScript required for core functionality
   - [ ] Print-friendly styles via @media print

## Tasks / Subtasks

- [ ] Task 1: Enhance mobile responsiveness (AC: #1)
  - [ ] 1.1: Add viewport meta and mobile CSS reset
  - [ ] 1.2: Implement CSS Grid for metrics layout
  - [ ] 1.3: Add touch-friendly button/link sizes
  - [ ] 1.4: Test on 320px, 375px, 768px, 1024px viewports

- [ ] Task 2: Update score display for 605-point system (AC: #3)
  - [ ] 2.1: Update DEAL_SHEET_TEMPLATE max scores in templates.py
  - [ ] 2.2: Fix denominator references (250, 175, 180)
  - [ ] 2.3: Verify percentage calculations
  - [ ] 2.4: Test tier badge color mappings

- [ ] Task 3: Add image gallery component (AC: #5)
  - [ ] 3.1: Create image gallery HTML structure
  - [ ] 3.2: Implement responsive CSS grid for images
  - [ ] 3.3: Add address-to-folder lookup integration
  - [ ] 3.4: Handle missing images gracefully

- [ ] Task 4: Add tour checklist section (AC: #6)
  - [ ] 4.1: Design checklist HTML/CSS structure
  - [ ] 4.2: Generate checklist items from kill-switch warnings
  - [ ] 4.3: Add inspection points based on property age/condition
  - [ ] 4.4: Style for print (checkbox icons)

- [ ] Task 5: W3C validation and performance (AC: #7)
  - [ ] 5.1: Run W3C validator on generated HTML
  - [ ] 5.2: Fix any validation errors
  - [ ] 5.3: Optimize CSS (remove unused rules)
  - [ ] 5.4: Add lighthouse performance check

## Dev Notes

### Technical Context

**Existing Implementation:**
The deal sheets module already exists at `scripts/deal_sheets/` with:
- `templates.py`: COMMON_CSS, DEAL_SHEET_CSS, INDEX_CSS, DEAL_SHEET_TEMPLATE, INDEX_TEMPLATE
- `renderer.py`: `generate_deal_sheet()` and `generate_index()` functions
- `generator.py`: Main orchestration with data loading and iteration

**Current Template Issues to Fix:**
1. Score display shows incorrect denominators in some places (hardcoded values)
2. Mobile responsiveness is basic - needs enhancement
3. No image gallery section
4. No tour checklist section

### Architecture Compliance

**File Organization:**
- Templates: `scripts/deal_sheets/templates.py` (inline Jinja2)
- Existing components: `docs/templates/components/` (separate files)
- Output: `reports/deal_sheets/*.html`

**Data Sources:**
- Property data: `data/enrichment_data.json` (LIST of dicts)
- Scored data: `data/phx_homes_ranked.csv`
- Image lookup: `data/property_images/metadata/address_folder_lookup.json`
- Scoring config: `src/phx_home_analysis/config/scoring_weights.py`

**Key Constants (from scoring_weights.py):**
```python
# Section A: Location & Environment = 250 pts
# Section B: Lot & Systems = 175 pts
# Section C: Interior & Features = 180 pts
# Total = 605 pts

# Tier thresholds:
unicorn_min: 484  # 80%+ of 605
contender_min: 363  # 60-80% of 605
pass_max: 362  # <60% of 605
```

### Library/Framework Requirements

**Already in use (no new deps needed):**
- Jinja2 (templating)
- pandas (data loading)
- Python 3.12

**CSS Requirements:**
- Use system fonts (-apple-system, BlinkMacSystemFont, etc.)
- Prefer CSS Grid and Flexbox over floats
- Use CSS custom properties for colors if refactoring

### File Structure Requirements

**Modified Files:**
- `scripts/deal_sheets/templates.py` - Update CSS and HTML templates
- `scripts/deal_sheets/renderer.py` - Add image gallery and checklist rendering

**No new files needed** - extend existing module.

### Testing Requirements

**Unit Tests:**
- Test score percentage calculations
- Test tier badge assignment
- Test checklist generation from warnings

**Integration Tests:**
- Generate deal sheet from sample property data
- Verify HTML structure matches expected output
- Test with missing data fields (graceful degradation)

**Manual Verification:**
- Open generated HTML in mobile browser
- Test print functionality
- Run W3C validator

### Previous Story Intelligence

**Relevant patterns from E4.S1 (scoring):**
- ScoringWeights dataclass provides `section_a_max`, `section_b_max`, `section_c_max` properties
- TierThresholds provides `classify()` method for tier assignment
- Scores are floats, tiers are strings ("Unicorn", "Contender", "Pass")

**Kill-switch integration (from renderer.py):**
```python
from scripts.lib.kill_switch import (
    SEVERITY_FAIL_THRESHOLD,  # 3.0
    SEVERITY_WARNING_THRESHOLD,  # 1.5
    evaluate_kill_switches_for_display,
)
```

### Project Structure Notes

- **Alignment**: Story follows existing deal_sheets package structure
- **No conflicts**: No architectural changes needed, only template enhancements
- **Naming**: Follow existing snake_case convention for variables

### References

- [Source: scripts/deal_sheets/templates.py] - Current HTML/CSS templates
- [Source: scripts/deal_sheets/renderer.py] - Current rendering logic
- [Source: src/phx_home_analysis/config/scoring_weights.py:1-394] - 605-point scoring system
- [Source: docs/templates/components/score_breakdown.html] - Reusable scorecard component
- [Source: docs/templates/base.html] - Base template with common styles

## Dev Agent Record

### Context Reference

<!-- Path(s) to story context XML will be added here by context workflow -->

### Agent Model Used

Claude (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

### File List

**Files to modify:**
- `scripts/deal_sheets/templates.py`
- `scripts/deal_sheets/renderer.py`

**Files to read for context:**
- `data/enrichment_data.json`
- `data/property_images/metadata/address_folder_lookup.json`
- `src/phx_home_analysis/config/scoring_weights.py`
- `scripts/lib/kill_switch.py`
