---
name: deal-sheets
description: Generate property deal sheets with kill-switch status, score breakdowns, tier classification, and recommendation summaries. Use for Phase 4 report generation, property summaries, or buyer presentations.
allowed-tools: Read, Bash(python:*), Write
---

# Deal Sheet Generation Skill

Expert at creating comprehensive property analysis summaries for home buying decisions.

## CLI Usage

```bash
# Generate deal sheet for single property
python -m scripts.deal_sheets --property "123 Main St, Phoenix, AZ 85001"

# Generate all deal sheets
python -m scripts.deal_sheets

# Alternative entry points
python scripts/deal_sheets/generator.py --property "123 Main St"
python scripts/generate_single_deal_sheet.py "123 Main St"
```

## Deal Sheet Components

### 1. Header Section

```markdown
# PROPERTY DEAL SHEET
**Address:** 123 Main St, Phoenix, AZ 85001
**Price:** $425,000 | **$/sqft:** $236
**Beds:** 4 | **Baths:** 2 | **Sqft:** 1,800
**Lot:** 8,500 sqft | **Year Built:** 1998
**Tier:** CONTENDER | **Score:** 385/600 (64%)
```

### 2. Kill Switch Panel

```markdown
## KILL SWITCH STATUS: PASS

| Criterion | Status | Value |
|-----------|--------|-------|
| HOA | PASS | $0/mo |
| Sewer | PASS | City |
| Garage | PASS | 2-car |
| Beds | PASS | 4 beds |
| Baths | PASS | 2 baths |
| Lot Size | PASS | 8,500 sqft |
| Year Built | PASS | 1998 |
```

Color coding:
- Green: PASS
- Yellow: UNKNOWN (data missing but passes)
- Red: FAIL

### 3. Score Breakdown

```markdown
## SCORE BREAKDOWN (385/600)

### Section A: Location (178/250)
| Category | Score | Max | Data |
|----------|-------|-----|------|
| Schools | 38 | 50 | 7.6/10 |
| Quietness | 40 | 50 | 0.8 mi from highway |
| Safety | 30 | 50 | 6/10 |
| Grocery | 32 | 40 | 0.6 mi |
| Parks | 24 | 30 | 0.4 mi |
| Orientation | 25 | 30 | NE facing |

### Section B: Lot/Systems (92/160)
| Category | Score | Max | Data |
|----------|-------|-----|------|
| Roof | 30 | 50 | ~12 years |
| Backyard | 28 | 40 | 8,500 sqft |
| Plumbing | 24 | 40 | 1998 build |
| Pool | 10 | 30 | No pool |

### Section C: Interior (115/190)
| Category | Score | Max | Data |
|----------|-------|-----|------|
| Kitchen | 28 | 40 | 7/10 |
| Master | 32 | 40 | 8/10 |
| Light | 18 | 30 | 6/10 |
| Ceilings | 15 | 30 | Standard 8ft |
| Fireplace | 10 | 20 | Gas, good |
| Laundry | 8 | 20 | Garage |
| Aesthetics | 4 | 10 | Dated 90s |
```

### 4. Strengths & Concerns

```markdown
## TOP 3 STRENGTHS
1. Excellent school district (Washington Elementary 7.6/10)
2. Updated kitchen with granite counters
3. Large lot with mature landscaping

## TOP 3 CONCERNS
1. Roof approaching replacement age (~12 years in AZ)
2. HVAC system age unknown - budget $8-12k
3. West-facing backyard (high cooling costs)
```

### 5. Cost Analysis

```markdown
## HIDDEN COST ANALYSIS

### Monthly Costs
| Item | Estimate |
|------|----------|
| Mortgage (20% down) | $2,200 |
| Property Tax | $180 |
| Insurance | $150 |
| HOA | $0 |
| Utilities | $250 |
| Pool (if any) | $0 |
| **Total** | **$2,780/mo** |

### Near-Term Repairs
| Item | Timeline | Cost |
|------|----------|------|
| Roof | 3-5 years | $12,000-18,000 |
| HVAC | Unknown | $8,000-12,000 |
| Pool Equipment | N/A | $0 |
```

### 6. Recommendation

```markdown
## RECOMMENDATION

**TIER: CONTENDER (385/600)**

This property merits serious consideration. Strong school district and
updated kitchen are significant positives. Primary concerns are
aging roof and unknown HVAC status.

**Action Items:**
- [ ] Request roof inspection report
- [ ] Get HVAC age from seller
- [ ] Verify city sewer connection
- [ ] Calculate actual commute time

**Negotiation Points:**
- Roof age may support $5-10k price reduction
- Request HVAC service records
```

## Enrichment Merger Service

**Location:** `src/phx_home_analysis/services/enrichment/merger.py`

```python
from phx_home_analysis.services.enrichment import EnrichmentMerger

merger = EnrichmentMerger()
property = merger.merge(property, enrichment_data)
```

**Handles:**
- County assessor data (lot size, year built, garage)
- HOA and tax information
- Location data (schools, distances, commute)
- Arizona-specific features (solar, pool, HVAC, roof)
- Type-safe enum conversions

## Data Sources for Deal Sheet

```python
# Required data sources
data_sources = {
    "phx_homes.csv": ["price", "beds", "baths", "sqft", "full_address"],
    "enrichment_data.json": [
        "lot_sqft", "year_built", "garage_spaces", "hoa_fee",
        "sewer_type", "school_rating", "orientation",
        "roof_age", "hvac_age", "has_pool", "pool_equipment_age",
        "kitchen_layout_score", "master_suite_score", # etc
    ],
    "phx_homes_ranked.csv": ["total_score", "tier", "score_location", "score_lot_systems", "score_interior"],
}
```

## Using Kill Switch Display

```python
from scripts.lib.kill_switch import evaluate_kill_switches_for_display

# Get display-friendly kill switch results
results = evaluate_kill_switches_for_display(property_data)

# Example output:
# {
#   "HOA": {"passed": True, "color": "green", "label": "PASS", "description": "$0/mo"},
#   "Sewer": {"passed": True, "color": "yellow", "label": "UNKNOWN", "description": "Unknown"},
#   ...
# }
```

## Template System

### Package Structure

```
scripts/deal_sheets/
├── __init__.py
├── __main__.py      # CLI entry point
├── generator.py     # Main orchestration
├── data_loader.py   # Load/merge data
├── templates.py     # Markdown templates
├── renderer.py      # Render templates
└── utils.py         # Helpers
```

### Using Templates

```python
from scripts.deal_sheets.templates import DEAL_SHEET_TEMPLATE
from scripts.deal_sheets.renderer import render_deal_sheet

# Generate markdown
markdown = render_deal_sheet(
    property_data=prop,
    scores=score_breakdown,
    kill_switch_results=ks_results
)

# Save to file
output_path = f"docs/artifacts/deal_sheets/{prop['full_address']}.md"
with open(output_path, "w") as f:
    f.write(markdown)
```

## Tier-Specific Deal Sheet Customization

### UNICORN Properties (>480 pts)

**Visual Treatment:**
- Header background: Green highlight
- Status badge: "UNICORN - Top Tier"
- Priority marker: "SCHEDULE IMMEDIATELY"

**Content Emphasis:**
- Lead with strengths (full detail)
- Minimize concerns (brief mentions only)
- Include competition analysis:
  ```markdown
  ## MARKET CONTEXT

  **Days on Market:** 5
  **Showing Activity:** High (expect multiple offers)
  **Comparable Sales:** 3 similar properties sold in 30 days
  **Recommendation:** Submit offer within 48 hours
  ```

**Cost Section:**
- De-emphasize minor repairs
- Focus on investment value
- Include appreciation potential estimate

**Action Items:**
- Schedule showing immediately
- Pre-approve financing
- Prepare competitive offer strategy
- Consider escalation clause

### CONTENDER Properties (360-480 pts)

**Visual Treatment:**
- Header background: Yellow highlight
- Status badge: "CONTENDER - Strong Candidate"
- Priority marker: "SCHEDULE THIS WEEK"

**Content Emphasis:**
- Balanced strengths and concerns
- Full detail on both
- Include value analysis:
  ```markdown
  ## VALUE ANALYSIS

  **Score vs Price:** 420 pts at $425k = 0.99 pts/$1k
  **Comparison:** Average contender: 0.85 pts/$1k
  **Assessment:** Above-average value for tier
  ```

**Cost Section:**
- Full near-term repair budget
- Highlight negotiation opportunities
- Include total cost of ownership

**Action Items:**
- Schedule showing within 1 week
- Research comparable properties
- Prepare list of inspection priorities
- Identify negotiation leverage points

### PASS Properties (<360 pts)

**Visual Treatment:**
- Header background: Gray (muted)
- Status badge: "PASS - Monitor Only"
- Priority marker: "WATCH LIST"

**Content Emphasis:**
- Lead with concerns (why it's a PASS)
- Brief strengths section
- Include threshold analysis:
  ```markdown
  ## THRESHOLD ANALYSIS

  **Current Score:** 320 pts
  **Contender Threshold:** 360 pts
  **Gap:** 40 pts (7%)

  **What Would Change Tier:**
  - Price drop to $380k (+15 value pts) OR
  - School rating improvement (+10 pts) OR
  - Roof replacement by seller (+20 pts)
  ```

**Cost Section:**
- Emphasize hidden costs
- Full repair estimates
- "True cost" calculation

**Action Items:**
- Monitor for price drops
- Set alert for $X price threshold
- Track comparable sales
- Revisit in 30 days

### FAILED Properties (Kill-Switch Failure)

**Visual Treatment:**
- Header background: Red highlight
- Status badge: "FAILED - Disqualified"
- Priority marker: "DO NOT PURSUE"

**Content Emphasis:**
- Lead with failure reason(s) prominently
- Minimal other analysis
- Clear rejection statement:
  ```markdown
  ## DISQUALIFICATION

  **Failed Criteria:**
  - HOA: $185/month (Requirement: $0)

  **Non-Negotiable:** This criterion cannot be overcome.
  This property does not meet buyer requirements.

  **Recommendation:** Remove from consideration.
  ```

**Content to SKIP for FAILED:**
- Detailed score breakdown (unnecessary)
- Full cost analysis (irrelevant)
- Action items (none applicable)

## Arizona-Specific Sections

### Solar Status

```markdown
## SOLAR STATUS: LEASED

**WARNING:** This property has a solar lease.

- Lessor: SunRun
- Monthly Payment: $185
- Escalator: 2.5%/year
- Years Remaining: 18
- Estimated Remaining Liability: $47,000

**Transfer Requirements:**
- Buyer credit check required
- May require assumption agreement
- Can complicate closing
```

### Pool Section

```markdown
## POOL ASSESSMENT

- **Present:** Yes
- **Equipment Age:** ~8 years
- **Condition:** Moderate wear

**Estimated Monthly Costs:**
| Service | $125 |
| Chemicals | $50 |
| Electricity | $75 |
| **Total** | **$250/mo** |

**Near-Term Repairs:**
- Filter replacement (1-2 years): $800
- Pump rebuild (3-5 years): $500-1,500
```

## Output Locations

```
docs/artifacts/deal_sheets/
├── 123_main_st_phoenix_az_85001.md
├── 456_oak_ave_glendale_az_85302.md
└── ...
```

## Deal Sheet Quality Verification

Before finalizing any deal sheet, verify ALL items:

### Completeness Checklist

```
DATA COMPLETENESS
[ ] Address matches exactly across all sections
[ ] Price current (check listing date)
[ ] All 7 kill-switch criteria evaluated
[ ] Score breakdown totals match overall score
[ ] All 3 sections (A, B, C) have scores

CALCULATION ACCURACY
[ ] Section A subtotal correct (max 250)
[ ] Section B subtotal correct (max 160)
[ ] Section C subtotal correct (max 190)
[ ] Total = A + B + C (max 600)
[ ] Tier assignment matches score range
[ ] $/sqft calculation accurate

CONTENT QUALITY
[ ] Top 3 strengths are substantive (not generic)
[ ] Top 3 concerns are property-specific
[ ] Cost estimates have sources/reasoning
[ ] Recommendation matches tier
[ ] Action items are actionable

FORMAT & PRESENTATION
[ ] Markdown renders correctly
[ ] Tables aligned properly
[ ] No placeholder text remaining
[ ] Tier-specific visual treatment applied
[ ] File saved to correct location
```

### Automated Validation

```python
def validate_deal_sheet(sheet: dict) -> dict:
    """Validate deal sheet for quality standards.

    Returns:
        {
            "valid": bool,
            "errors": list[str],   # Must fix before publish
            "warnings": list[str]  # Should fix if possible
        }
    """
    errors, warnings = [], []

    # COMPLETENESS
    required_fields = ["address", "price", "beds", "baths", "total_score", "tier"]
    for field in required_fields:
        if not sheet.get(field):
            errors.append(f"Missing required field: {field}")

    # CALCULATION ACCURACY
    section_totals = (
        sheet.get("score_location", 0) +
        sheet.get("score_systems", 0) +
        sheet.get("score_interior", 0)
    )
    if abs(section_totals - sheet.get("total_score", 0)) > 0.1:
        errors.append(f"Score mismatch: sections={section_totals}, total={sheet['total_score']}")

    # TIER ACCURACY
    total = sheet.get("total_score", 0)
    expected_tier = "UNICORN" if total > 480 else "CONTENDER" if total >= 360 else "PASS"
    if sheet.get("kill_switch_failed"):
        expected_tier = "FAILED"
    if sheet.get("tier") != expected_tier:
        errors.append(f"Tier mismatch: {sheet['tier']} should be {expected_tier}")

    # CONTENT QUALITY
    if len(sheet.get("strengths", [])) < 3:
        warnings.append("Less than 3 strengths listed")
    if len(sheet.get("concerns", [])) < 3:
        warnings.append("Less than 3 concerns listed")

    # Detect placeholder text
    placeholder_patterns = ["TODO", "TBD", "PLACEHOLDER", "XXX", "[INSERT"]
    for pattern in placeholder_patterns:
        if pattern.lower() in str(sheet).lower():
            errors.append(f"Placeholder text found: {pattern}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }
```

### Pre-Publication Review

Before publishing any deal sheet:

1. **Run automated validation:**
   ```python
   result = validate_deal_sheet(sheet_data)
   if not result["valid"]:
       raise ValidationError(result["errors"])
   ```

2. **Visual review:**
   - Open generated markdown in preview
   - Check table formatting
   - Verify links work

3. **Cross-reference source data:**
   - Price matches current listing
   - Scores match enrichment_data.json
   - Tier matches phx_homes_ranked.csv

### Quality Metrics

Track deal sheet quality over time:

| Metric | Target |
|--------|--------|
| Validation pass rate | 100% |
| Warning count per sheet | < 2 |
| Placeholder text found | 0 |
| Score calculation errors | 0 |
| Tier mismatches | 0 |

## Best Practices

1. **Run after scoring** - Requires phx_homes_ranked.csv to exist
2. **Include all sections** - Even if data missing (note as "Unknown")
3. **Color-code status** - Visual hierarchy for quick scanning
4. **Actionable recommendations** - Specific next steps
5. **Cost transparency** - Hidden costs prominently displayed
