# County Data Integration - Documentation Updates

## Overview

This document contains all proposed updates to integrate the new Maricopa County Assessor API data extraction capability into the property analysis workflow.

**New Capability:** `scripts/extract_county_data.py`
- Automatically extracts kill-switch fields from Maricopa County Assessor API
- Reduces manual data entry for lot_sqft, year_built, garage_spaces, has_pool, etc.
- Provides authoritative source for property characteristics

---

## File 1: `.claude/commands/analyze-property.md`

### Edit 1: Add County Data Extraction Step

**Location:** After "### 2. Check Existing State" section, before "### 3. Check Existing Images"

**Insert new section:**

```markdown
### 3. Extract County Data (Kill-Switch Fields)

**IMPORTANT**: Run county data extraction BEFORE Phase 1 to populate kill-switch fields.

```bash
# For single property mode
python scripts/extract_county_data.py --address "STREET ADDRESS" --update-only

# For batch/test mode
python scripts/extract_county_data.py --all --update-only
```

This extracts from Maricopa County Assessor API:
- `lot_sqft` - Lot size (kill-switch: 7,000-15,000 required)
- `year_built` - Year constructed (kill-switch: < 2024 required)
- `garage_spaces` - Number of garage stalls (kill-switch: >= 2 required)
- `has_pool` - Pool presence (scoring: Section B)
- `livable_sqft` - Living area square footage
- `baths` - Estimated bathrooms (from BathFixtures / 3)
- `full_cash_value` - County assessed value
- `roof_type` - Roof material type

**NOT available from API** (require manual research or other sources):
- `sewer_type` - Requires manual county lookup
- `beds` - Not tracked by assessor
- `tax_annual` - Requires Treasurer API (separate)

**Skip if:**
- Property already has complete enrichment data (all kill-switch fields populated)
- Using `--update-only` flag will only fill missing fields
```

**Then renumber:** Current "### 3. Check Existing Images" becomes "### 4. Check Existing Images"
**And renumber:** Current "### 4. Check Research Queue" becomes "### 5. Check Research Queue"

---

### Edit 2: Update Orchestration Workflow Phase 0

**Location:** Before "### Phase 1: Data Collection (Parallel)" section

**Insert new Phase 0 section:**

```markdown
### Phase 0: County Data Extraction (Pre-Phase 1)

**Display**: "Phase 0: Extracting official county records..."

**Execute BEFORE launching Phase 1 agents:**

```bash
# For single property
python scripts/extract_county_data.py --address "STREET ADDRESS ONLY" --update-only -v

# For batch mode
python scripts/extract_county_data.py --all --update-only -v
```

**Why Phase 0?**
- Populates kill-switch fields from authoritative source (Maricopa County Assessor)
- Enables early elimination of properties failing kill-switches before expensive Phase 1 work
- Provides baseline data for Section B scoring (lot_sqft, garage_spaces, has_pool)

**After Phase 0 completes:**

1. Check enrichment_data.json for updated fields
2. Validate kill-switch fields are populated:
   - `lot_sqft` (7,000-15,000 required)
   - `year_built` (< 2024 required)
   - `garage_spaces` (>= 2 required)
3. If kill-switch failures detected:
   - Mark property as "FAILED" tier immediately
   - Skip Phase 1-4 (save API quota)
   - Log reason: "Kill-switch failure: {field}"
   - Move to next property
4. Show Phase 0 results:
   - Lot size: {lot_sqft} sqft
   - Year built: {year_built}
   - Garage: {garage_spaces} spaces
   - Pool: {has_pool}
   - Full cash value: ${full_cash_value}

**Missing Fields Protocol:**
If county API returns incomplete data:
- Continue to Phase 1 (don't block on county data)
- Create research task for missing kill-switch fields
- Agents may find missing data from listing sites

**API Failure Protocol:**
If county API is unavailable:
- Log warning: "County API unavailable - proceeding with existing enrichment data"
- Continue to Phase 1 (don't block pipeline)
- Property will need manual kill-switch verification later

---
```

---

## File 2: `.claude/AGENT_BRIEFING.md`

### Edit 3: Update SCRIPTS REFERENCE Section

**Location:** Section 3 "SCRIPTS REFERENCE"

**Current table:**
```markdown
| Script | Command | Purpose |
|--------|---------|---------|
| `scripts/analyze.py` | `python scripts/analyze.py` | Full analysis pipeline |
| `scripts/extract_images.py` | `python scripts/extract_images.py --address "..."` | Image extraction |
```

**Replace with expanded table:**

```markdown
| Script | Command | Purpose |
|--------|---------|---------|
| `scripts/analyze.py` | `python scripts/analyze.py` | Full analysis pipeline |
| `scripts/extract_county_data.py` | `python scripts/extract_county_data.py --all --update-only` | Extract kill-switch fields from Maricopa County Assessor API |
| `scripts/extract_images.py` | `python scripts/extract_images.py --address "..."` | Image extraction |

### Extract County Data Options

```bash
--all                     # Process all properties from phx_homes.csv
--address "STREET"        # Single property (street address only, e.g., "4732 W Davis Rd")
--update-only             # Only fill missing fields, preserve existing values
--dry-run                 # Preview what would be extracted without saving
-v, --verbose             # Detailed logging
```

**Fields Extracted:**
- `lot_sqft` - From LotSize (kill-switch: 7,000-15,000)
- `year_built` - From ConstructionYear (kill-switch: < 2024)
- `garage_spaces` - From NumberOfGarages (kill-switch: >= 2)
- `has_pool` - From Pool sqft value (scoring: Section B)
- `livable_sqft` - From LivableSpace
- `baths` - Estimated from BathFixtures / 3
- `full_cash_value` - From Valuations array (most recent year)
- `roof_type` - From RoofCover (e.g., "As - Asphalt")

**NOT Available from API:**
- `sewer_type` (city/septic) - Requires manual county lookup or GIS layers
- `beds` - Not tracked by assessor
- `tax_annual` - Requires Treasurer API (separate system)
```

---

### Edit 4: Update Enrichment JSON Fields Section

**Location:** Section 4 "DATA SCHEMAS" -> "Enrichment JSON Fields"

**Add note at end of enrichment fields:**

```markdown
**County Data Sources:**

The following fields are automatically populated by `extract_county_data.py` from Maricopa County Assessor API:
- `lot_sqft` - Official parcel lot size
- `year_built` - Construction year from building records
- `garage_spaces` - Number of garage stalls
- `has_pool` - Pool presence (boolean)
- `livable_sqft` - Living area square footage
- `roof_type` - Roof material/cover type

If these fields are null/missing after county extraction, they require manual research or are unavailable in county records.
```

---

## File 3: `.claude/agents/listing-browser.md`

### Edit 5: Add County Data Cross-Reference

**Location:** After "### 4. Check Existing Enrichment" section in "Pre-Task Protocol"

**Insert new section:**

```markdown
### 5. Note County Data Availability

If enrichment data exists, check which fields came from county vs listing sources:

```python
# County-sourced fields (if present, likely accurate):
county_fields = ["lot_sqft", "year_built", "garage_spaces", "has_pool", "livable_sqft"]

# Listing-sourced fields (if differ from county, county is authoritative):
listing_fields = ["price_num", "beds", "baths", "hoa_fee", "description"]
```

**Cross-Reference Priority:**
- For `lot_sqft`, `year_built`, `garage_spaces`: County Assessor > Listing Site
- For `price_num`, `beds`, `baths`: Listing Site > County Assessor
- If values conflict: Note discrepancy in return data for investigation
```

---

### Edit 6: Update Standard Return Format

**Location:** "Standard Return Format" section

**Add new field to `data` object:**

```markdown
  "data": {
    "price": 450000,
    "images": ["url1", "url2"],
    "beds": 4,
    "baths": 2,
    "sqft": 1800,
    "lot_sqft": 8000,
    "year_built": 1995,
    "hoa_monthly": 0,
    "description": "...",
    "listing_date": "2025-01-15",
    "data_source_conflicts": [
      {
        "field": "lot_sqft",
        "listing_value": 7500,
        "county_value": 8000,
        "recommendation": "Use county value (authoritative)"
      }
    ]
  },
```

---

## File 4: `.claude/agents/map-analyzer.md`

### Edit 7: Add County Data Reference

**Location:** After "### 4. Reference Existing Analysis" section in "Pre-Task Protocol"

**Insert new note:**

```markdown
### 5. County Data Cross-Check

Before collecting data, check if county extraction already populated fields:

```python
enrichment = json.load(open("data/enrichment_data.json"))
prop = next((p for p in enrichment if p["full_address"] == target_address), None)

# These should be populated by county extraction (Phase 0):
county_fields = {
    "lot_sqft": prop.get("lot_sqft"),
    "year_built": prop.get("year_built"),
    "garage_spaces": prop.get("garage_spaces"),
    "has_pool": prop.get("has_pool")
}

# If county fields are None, county extraction may have failed or property not in county records
# Continue with map analysis - may find some data from GIS/Maps
```

**Note:** Do NOT re-extract county-sourced fields. Focus on map-specific data:
- `orientation` (from satellite imagery)
- `school_rating` (from GreatSchools)
- `distance_to_grocery_miles` (from Google Maps)
- `distance_to_highway_miles` (from Google Maps)
- `commute_minutes` (from Google Maps)
```

---

## File 5: `.claude/agents/image-assessor.md`

### Edit 8: Add County Data Usage Note

**Location:** After "### 4. Check Existing Scores" section in "Pre-Task Protocol"

**Insert new note:**

```markdown
### 5. County Data for Context

Use county data to inform visual assessment:

```python
enrichment = json.load(open("data/enrichment_data.json"))
prop = next((p for p in enrichment if p["full_address"] == target_address), None)

# County data informs expectations:
year_built = prop.get("year_built")  # Expect finishes/styles from this era
has_pool = prop.get("has_pool")      # Should see pool in backyard photos
garage_spaces = prop.get("garage_spaces")  # Verify garage size in photos
```

**Assessment Adjustments:**
- If `year_built` < 1990: Expect dated finishes (lower aesthetics baseline)
- If `year_built` >= 2000: Expect modern features (higher ceilings, open concept)
- If `has_pool` but no pool photos: Flag as "missing critical photos"
- If `garage_spaces` = 3 but photos show 2: Note discrepancy
```

---

## Summary of Changes

### Files Updated
1. `.claude/commands/analyze-property.md` - Added Phase 0 county extraction step
2. `.claude/AGENT_BRIEFING.md` - Added county data script reference and field documentation
3. `.claude/agents/listing-browser.md` - Added county data cross-reference protocol
4. `.claude/agents/map-analyzer.md` - Added county data cross-check to avoid duplication
5. `.claude/agents/image-assessor.md` - Added county data context for visual assessment

### Integration Points

**Phase 0 (New):** County data extraction before Phase 1
- Populates kill-switch fields from authoritative source
- Enables early elimination of failed properties
- Reduces manual data entry burden

**Phase 1:** Agents check county data and skip redundant extraction
- listing-browser notes conflicts between listing and county data
- map-analyzer focuses on map-specific fields, skips county fields

**Phase 2:** image-assessor uses county data for context
- Year built informs finish expectations
- Pool presence validates photo completeness
- Garage spaces cross-referenced with photos

**Phase 3-4:** Unchanged (use enrichment data regardless of source)

### Workflow Changes

**Before:**
1. Phase 1: Extract listing + map data (manual entry for kill-switches)
2. Phase 2: Assess images
3. Phase 3: Score
4. Phase 4: Report

**After:**
1. **Phase 0: Extract county data (auto-populate kill-switches)**
2. Phase 1: Extract listing + map data (skip county-sourced fields)
3. Phase 2: Assess images (use county data for context)
4. Phase 3: Score
5. Phase 4: Report

### Benefits

1. **Reduced Manual Work:** Automatically populate lot_sqft, year_built, garage_spaces, has_pool
2. **Earlier Filtering:** Kill-switch failures detected in Phase 0, save API quota
3. **Data Quality:** Authoritative county source more accurate than listing sites
4. **Conflict Detection:** Cross-reference listing data against county records

### Usage Examples

```bash
# Single property analysis (with county data)
/analyze-property "4732 W Davis Rd, Glendale, AZ"

# Batch mode (test first 5)
/analyze-property --test

# Full batch processing
/analyze-property --all
```

All modes will automatically run Phase 0 county extraction before Phase 1.

---

## Implementation Checklist

- [ ] Update `.claude/commands/analyze-property.md` with Phase 0 section
- [ ] Update section numbering in analyze-property.md (3→4, 4→5)
- [ ] Update `.claude/AGENT_BRIEFING.md` scripts reference table
- [ ] Add county data fields documentation to AGENT_BRIEFING.md
- [ ] Update `.claude/agents/listing-browser.md` with cross-reference protocol
- [ ] Update `.claude/agents/map-analyzer.md` with county data check
- [ ] Update `.claude/agents/image-assessor.md` with county context
- [ ] Test Phase 0 integration with single property
- [ ] Test batch mode with Phase 0
- [ ] Verify kill-switch filtering in Phase 0
- [ ] Document data source conflicts in agent returns

---

*Document generated: 2025-11-30*
*New capability: Maricopa County Assessor API integration*
*Script location: `scripts/extract_county_data.py`*
