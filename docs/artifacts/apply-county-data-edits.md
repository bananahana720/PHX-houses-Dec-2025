# County Data Integration - Edit Instructions

This file contains the exact `old_string` → `new_string` replacements for integrating county data extraction into the documentation.

---

## File: `.claude/commands/analyze-property.md`

### Edit 1: Add County Data Extraction Step

**Find this text (lines 43-59):**

```markdown
### 2. Check Existing State

```bash
# Check what's already been processed
cat data/property_images/metadata/extraction_state.json

# Check enrichment completeness
python -c "import json; d=json.load(open('data/enrichment_data.json')); addr='TARGET_ADDRESS'; p=next((x for x in d if x['full_address']==addr), None); print(json.dumps(p, indent=2) if p else 'Not found')"
```

### 3. Check Existing Images

```bash
# List available property image directories
ls data/property_images/processed/
```

### 4. Check Research Queue
```

**Replace with:**

```markdown
### 2. Check Existing State

```bash
# Check what's already been processed
cat data/property_images/metadata/extraction_state.json

# Check enrichment completeness
python -c "import json; d=json.load(open('data/enrichment_data.json')); addr='TARGET_ADDRESS'; p=next((x for x in d if x['full_address']==addr), None); print(json.dumps(p, indent=2) if p else 'Not found')"
```

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

### 4. Check Existing Images

```bash
# List available property image directories
ls data/property_images/processed/
```

### 5. Check Research Queue
```

---

### Edit 2: Add Phase 0 to Orchestration Workflow

**Find this text (line 244):**

```markdown
## Orchestration Workflow

### Phase 1: Data Collection (Parallel)
```

**Replace with:**

```markdown
## Orchestration Workflow

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

### Phase 1: Data Collection (Parallel)
```

---

## File: `.claude/AGENT_BRIEFING.md`

### Edit 3: Expand Scripts Reference Table

**Find this text (lines 231-247):**

```markdown
## 3. SCRIPTS REFERENCE

| Script | Command | Purpose |
|--------|---------|---------|
| `scripts/analyze.py` | `python scripts/analyze.py` | Full analysis pipeline |
| `scripts/extract_images.py` | `python scripts/extract_images.py --address "..."` | Image extraction |

### Extract Images Options

```bash
--all                 # Process all unprocessed from CSV
--address "..."       # Single property
--sources x,y,z       # Filter sources
--resume              # Continue from state (default)
--fresh               # Ignore state, start over
--dry-run             # Discover only, no download
```
```

**Replace with:**

```markdown
## 3. SCRIPTS REFERENCE

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

### Extract Images Options

```bash
--all                 # Process all unprocessed from CSV
--address "..."       # Single property
--sources x,y,z       # Filter sources
--resume              # Continue from state (default)
--fresh               # Ignore state, start over
--dry-run             # Discover only, no download
```
```

---

### Edit 4: Add County Data Source Note to Enrichment Schema

**Find this text (line 281, end of enrichment fields):**

```markdown
  "roof_age": "int|null",
  "hvac_age": "int|null"
}
```

**Replace with:**

```markdown
  "roof_age": "int|null",
  "hvac_age": "int|null"
}

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

## File: `.claude/agents/listing-browser.md`

### Edit 5: Add County Data Cross-Reference

**Find this text (lines 54-57):**

```markdown
### 4. Check Existing Enrichment

Read `data/enrichment_data.json` to see what data already exists for this property.

---
```

**Replace with:**

```markdown
### 4. Check Existing Enrichment

Read `data/enrichment_data.json` to see what data already exists for this property.

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

---
```

---

### Edit 6: Update Return Format with Data Conflicts

**Find this text (lines 183-184 in listing-browser.md):**

```markdown
    "listing_date": "2025-01-15"
  },
```

**Replace with:**

```markdown
    "listing_date": "2025-01-15",
    "data_source_conflicts": [
      {"field": "lot_sqft", "listing_value": 7500, "county_value": 8000, "recommendation": "Use county value (authoritative)"}
    ]
  },
```

---

## File: `.claude/agents/map-analyzer.md`

### Edit 7: Add County Data Cross-Check

**Find this text (lines 60-62):**

```markdown
Use existing data when available to avoid redundant work.

---
```

**Replace with:**

```markdown
Use existing data when available to avoid redundant work.

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

---
```

---

## File: `.claude/agents/image-assessor.md`

### Edit 8: Add County Data Context

**Find this text (lines 68-70):**

```markdown
Only score categories that are null or missing.

---
```

**Replace with:**

```markdown
Only score categories that are null or missing.

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

---
```

---

## Application Order

Apply edits in this sequence to avoid conflicts:

1. `.claude/AGENT_BRIEFING.md` (Edit 3, 4) - Shared context first
2. `.claude/agents/listing-browser.md` (Edit 5, 6) - Agent definitions
3. `.claude/agents/map-analyzer.md` (Edit 7) - Agent definitions
4. `.claude/agents/image-assessor.md` (Edit 8) - Agent definitions
5. `.claude/commands/analyze-property.md` (Edit 1, 2) - Orchestrator last

---

## Verification After Edits

```bash
# Check all files were updated
grep -l "extract_county_data" .claude/commands/analyze-property.md .claude/AGENT_BRIEFING.md .claude/agents/*.md

# Should return 5 files:
# - .claude/commands/analyze-property.md
# - .claude/AGENT_BRIEFING.md
# - .claude/agents/listing-browser.md
# - .claude/agents/map-analyzer.md
# - .claude/agents/image-assessor.md

# Verify Phase 0 exists
grep "Phase 0: County Data Extraction" .claude/commands/analyze-property.md

# Verify scripts table updated
grep "extract_county_data.py" .claude/AGENT_BRIEFING.md
```

---

*Edit instructions generated: 2025-11-30*
*Target: Integrate Maricopa County Assessor API capability*
