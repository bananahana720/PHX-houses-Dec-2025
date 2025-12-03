# County Data Integration - Executive Summary

## What Changed

A new capability was implemented to automatically extract property data from the Maricopa County Assessor API. This update integrates that capability into the multi-agent property analysis workflow.

## New Script

**Location:** `scripts/extract_county_data.py`

**What it does:**
- Searches Maricopa County Assessor API by street address
- Extracts official property records (lot size, year built, garage count, pool, etc.)
- Merges data into `enrichment_data.json`
- Automatically populates kill-switch fields that previously required manual entry

**Usage:**
```bash
# Single property
python scripts/extract_county_data.py --address "4732 W Davis Rd" --update-only

# All properties
python scripts/extract_county_data.py --all --update-only
```

## Documentation Updates Required

### 5 Files Need Updates

1. **`.claude/commands/analyze-property.md`** (2 edits)
   - Add new "Phase 0: County Data Extraction" before Phase 1
   - Add pre-execution step to extract county data
   - Enables early kill-switch filtering

2. **`.claude/AGENT_BRIEFING.md`** (2 edits)
   - Add `extract_county_data.py` to scripts reference table
   - Document which fields come from county API
   - Note fields NOT available from API

3. **`.claude/agents/listing-browser.md`** (2 edits)
   - Add county data cross-reference protocol
   - Handle conflicts between listing and county data
   - County data is authoritative for lot_sqft, year_built, garage_spaces

4. **`.claude/agents/map-analyzer.md`** (1 edit)
   - Skip extracting county-sourced fields
   - Focus on map-specific data (orientation, schools, distances)
   - Avoid redundant work

5. **`.claude/agents/image-assessor.md`** (1 edit)
   - Use county data (year_built, has_pool) to inform visual assessment
   - Adjust expectations based on year built
   - Flag missing photos if pool exists in county records

## Workflow Changes

### Before (4 phases)
```
Phase 1: Extract listing + map data (manual kill-switch entry)
Phase 2: Assess images
Phase 3: Score property
Phase 4: Generate report
```

### After (5 phases)
```
Phase 0: Extract county data (auto-populate kill-switches) ← NEW
Phase 1: Extract listing + map data (skip county fields)
Phase 2: Assess images (use county context)
Phase 3: Score property
Phase 4: Generate report
```

## Benefits

1. **Automation**: No more manual entry for lot_sqft, year_built, garage_spaces, has_pool
2. **Early Filtering**: Kill-switch failures detected in Phase 0, before expensive API calls
3. **Data Quality**: County records are authoritative source, more accurate than listings
4. **Conflict Detection**: Cross-reference listing data against official records
5. **Time Savings**: Reduces manual research time per property

## Fields Auto-Populated

| Field | Source | Kill-Switch? | Notes |
|-------|--------|--------------|-------|
| `lot_sqft` | County API | Yes (7,000-15,000) | Official parcel size |
| `year_built` | County API | Yes (< 2024) | Construction year |
| `garage_spaces` | County API | Yes (>= 2) | Number of stalls |
| `has_pool` | County API | No (scoring) | Pool presence |
| `livable_sqft` | County API | No | Living area |
| `baths` | County API | No | Estimated from fixtures |
| `full_cash_value` | County API | No | County assessed value |
| `roof_type` | County API | No | Roof material |

## Fields Still Manual

These require other sources or manual research:

| Field | Why Not in County API | Alternative Source |
|-------|----------------------|-------------------|
| `sewer_type` | Not in basic API | Manual county lookup or GIS |
| `beds` | Not tracked by assessor | Listing sites |
| `tax_annual` | Separate Treasurer system | County Treasurer API |
| `hoa_fee` | Not public record | Listing sites or HOA lookup |

## Integration Strategy

### Phase 0 Execution
- **When:** Before Phase 1 agents launch
- **Command:** `python scripts/extract_county_data.py --address "STREET" --update-only`
- **Duration:** ~2-5 seconds per property
- **Failure handling:** Log warning, continue to Phase 1 (don't block pipeline)

### Kill-Switch Early Exit
```python
# Pseudocode for Phase 0 completion
if lot_sqft < 7000 or lot_sqft > 15000:
    mark_as_failed("Kill-switch: lot_sqft out of range")
    skip_phases_1_4()
    move_to_next_property()
```

### Data Conflict Resolution
```python
# Priority rules
if field in ["lot_sqft", "year_built", "garage_spaces"]:
    authoritative_source = "county"
elif field in ["price_num", "beds", "baths"]:
    authoritative_source = "listing"

if county_value != listing_value:
    log_conflict(field, county_value, listing_value, authoritative_source)
```

## Documentation Files Created

1. **`county-data-integration-updates.md`** (this summary + full documentation)
   - Complete explanation of all changes
   - Integration points and workflow
   - Benefits and usage examples

2. **`apply-county-data-edits.md`** (edit instructions)
   - Exact old_string → new_string replacements
   - Application order
   - Verification commands

3. **`county-data-integration-summary.md`** (executive overview)
   - High-level changes
   - Quick reference
   - Integration strategy

## How to Apply

### Option 1: Manual Edits (Recommended)
Use the Edit tool with exact replacements from `apply-county-data-edits.md`:

```bash
# Read the edit instructions
cat docs/artifacts/apply-county-data-edits.md

# Apply each edit using Edit tool
# Example:
Edit(
  file_path=".claude/AGENT_BRIEFING.md",
  old_string="<exact text from instructions>",
  new_string="<exact replacement from instructions>"
)
```

### Option 2: Automated Script
Create a Python script to apply all edits programmatically.

### Option 3: Git Merge
If you have a feature branch with these changes, merge it.

## Testing After Integration

```bash
# Test single property with county extraction
/analyze-property "4732 W Davis Rd, Glendale, AZ"

# Verify Phase 0 ran
grep "Phase 0" logs/analysis_*.log

# Check enrichment data was populated
python -c "
import json
d = json.load(open('data/enrichment_data.json'))
p = next(x for x in d if '4732 W Davis' in x['full_address'])
print('lot_sqft:', p.get('lot_sqft'))
print('year_built:', p.get('year_built'))
print('garage_spaces:', p.get('garage_spaces'))
"

# Test batch mode
/analyze-property --test
```

## Rollback Plan

If issues arise:

1. Revert documentation files to previous versions
2. County data extraction script can remain (doesn't break existing workflow)
3. Agents will continue working with manual enrichment data
4. No breaking changes - purely additive

## Questions?

**Q: What if county API is down?**
A: Phase 0 logs warning, continues to Phase 1. Property needs manual kill-switch verification.

**Q: What if county data conflicts with listing?**
A: County is authoritative for lot_sqft, year_built, garage_spaces. Listing is authoritative for price, beds, baths.

**Q: Can I skip Phase 0?**
A: Not recommended. Phase 0 enables early filtering and reduces manual work. But if needed, comment out Phase 0 step in orchestrator.

**Q: What about properties outside Maricopa County?**
A: County extraction will fail gracefully. Agents proceed with manual enrichment data. This is Phoenix-specific workflow.

---

## Key Takeaways

1. **Automates** kill-switch field extraction from official county records
2. **Reduces** manual data entry and research time
3. **Improves** data quality with authoritative source
4. **Enables** early property filtering before expensive Phase 1
5. **Integrates** seamlessly with existing 4-phase workflow as new Phase 0

**Implementation time:** ~30 minutes to apply 8 edits across 5 files
**Testing time:** ~15 minutes to verify single property + batch mode
**Total effort:** ~45 minutes

**Payoff:** Saves 3-5 minutes per property × 33 properties = 99-165 minutes saved
**ROI:** 3-4x time investment recovered in first full batch run

---

*Generated: 2025-11-30*
*Documentation update for Maricopa County Assessor API integration*
