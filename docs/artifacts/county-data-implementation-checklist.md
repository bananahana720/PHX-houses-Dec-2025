# County Data Integration - Implementation Checklist

Step-by-step checklist for applying all documentation updates.

---

## Pre-Implementation

- [ ] **Backup current documentation**
  ```bash
  cp .claude/commands/analyze-property.md .claude/commands/analyze-property.md.backup
  cp .claude/AGENT_BRIEFING.md .claude/AGENT_BRIEFING.md.backup
  cp .claude/agents/listing-browser.md .claude/agents/listing-browser.md.backup
  cp .claude/agents/map-analyzer.md .claude/agents/map-analyzer.md.backup
  cp .claude/agents/image-assessor.md .claude/agents/image-assessor.md.backup
  ```

- [ ] **Read implementation docs**
  - [ ] `county-data-integration-summary.md` (executive overview)
  - [ ] `county-data-integration-updates.md` (full documentation)
  - [ ] `apply-county-data-edits.md` (edit instructions)
  - [ ] `county-data-file-map.md` (visual reference)

- [ ] **Verify county script exists and works**
  ```bash
  # Check script exists
  ls scripts/extract_county_data.py

  # Test help
  python scripts/extract_county_data.py --help

  # Test dry run on single property
  python scripts/extract_county_data.py --address "4732 W Davis Rd" --dry-run -v
  ```

---

## Phase 1: Edit Shared Context (Foundation)

### Edit `.claude/AGENT_BRIEFING.md`

- [ ] **Edit 3: Expand scripts reference table**
  - Location: Line ~231, Section 3 "SCRIPTS REFERENCE"
  - Action: Replace scripts table with expanded version
  - Adds: `extract_county_data.py` row and options section
  - Verification: `grep "extract_county_data.py" .claude/AGENT_BRIEFING.md`
  - Expected: 2+ matches

- [ ] **Edit 4: Add county data source note**
  - Location: Line ~281, after enrichment JSON schema
  - Action: Add "County Data Sources" section
  - Adds: Documentation of which fields come from county API
  - Verification: `grep "County Data Sources" .claude/AGENT_BRIEFING.md`
  - Expected: 1 match

**Phase 1 Verification:**
```bash
# Check both edits applied
grep -c "extract_county_data" .claude/AGENT_BRIEFING.md
# Expected: 2+

# Check county sources documented
grep "County Data Sources" .claude/AGENT_BRIEFING.md
# Expected: section header found
```

---

## Phase 2: Edit Agent Files (Parallel)

### Edit `.claude/agents/listing-browser.md`

- [ ] **Edit 5: Add county data cross-reference**
  - Location: Line ~54, after "### 4. Check Existing Enrichment"
  - Action: Insert "### 5. Note County Data Availability" section
  - Adds: Cross-reference protocol for county vs listing data
  - Verification: `grep "County Data Availability" .claude/agents/listing-browser.md`
  - Expected: 1 match

- [ ] **Edit 6: Update return format with conflicts**
  - Location: Line ~183, in standard return format
  - Action: Add `data_source_conflicts` field to JSON return
  - Adds: Conflict tracking between county and listing data
  - Verification: `grep "data_source_conflicts" .claude/agents/listing-browser.md`
  - Expected: 1 match

### Edit `.claude/agents/map-analyzer.md`

- [ ] **Edit 7: Add county data cross-check**
  - Location: Line ~60, after existing analysis reference
  - Action: Insert "### 5. County Data Cross-Check" section
  - Adds: Skip county-sourced fields, focus on map data
  - Verification: `grep "County Data Cross-Check" .claude/agents/map-analyzer.md`
  - Expected: 1 match

### Edit `.claude/agents/image-assessor.md`

- [ ] **Edit 8: Add county data context**
  - Location: Line ~68, after "### 4. Check Existing Scores"
  - Action: Insert "### 5. County Data for Context" section
  - Adds: Use county data to inform visual assessment
  - Verification: `grep "County Data for Context" .claude/agents/image-assessor.md`
  - Expected: 1 match

**Phase 2 Verification:**
```bash
# Check all agents reference county data
for agent in listing-browser map-analyzer image-assessor; do
  echo "=== $agent ==="
  grep -c -i "county" .claude/agents/$agent.md
done
# Expected: Each agent has 2+ matches

# Verify new sections exist
grep "### 5" .claude/agents/*.md
# Expected: 3 matches (one per agent file)
```

---

## Phase 3: Edit Orchestrator (Depends on Agents)

### Edit `.claude/commands/analyze-property.md`

- [ ] **Edit 1: Add county data extraction step (pre-execution)**
  - Location: Line ~43, after "### 2. Check Existing State"
  - Action: Insert "### 3. Extract County Data (Kill-Switch Fields)" section
  - Then: Renumber existing "### 3" → "### 4" and "### 4" → "### 5"
  - Adds: Pre-execution county data extraction step
  - Verification: `grep "### 3. Extract County Data" .claude/commands/analyze-property.md`
  - Expected: 1 match

- [ ] **Edit 2: Add Phase 0 to workflow**
  - Location: Line ~244, before "### Phase 1: Data Collection"
  - Action: Insert "### Phase 0: County Data Extraction (Pre-Phase 1)" section
  - Adds: Complete Phase 0 workflow with kill-switch filtering
  - Verification: `grep "Phase 0: County Data Extraction" .claude/commands/analyze-property.md`
  - Expected: 1 match

**Phase 3 Verification:**
```bash
# Check Phase 0 exists
grep "Phase 0" .claude/commands/analyze-property.md
# Expected: Multiple matches (section header, workflow, progress display)

# Check section renumbering
grep "### 3. Extract County Data" .claude/commands/analyze-property.md
grep "### 4. Check Existing Images" .claude/commands/analyze-property.md
grep "### 5. Check Research Queue" .claude/commands/analyze-property.md
# Expected: All three sections found in order

# Verify orchestrator references county script
grep "extract_county_data.py" .claude/commands/analyze-property.md
# Expected: 2+ matches
```

---

## Post-Implementation Verification

### 1. All Files Updated

- [ ] **Verify edit count**
  ```bash
  # Check all files reference county data extraction
  grep -l "extract_county_data\|County Data\|county data" \
    .claude/commands/analyze-property.md \
    .claude/AGENT_BRIEFING.md \
    .claude/agents/listing-browser.md \
    .claude/agents/map-analyzer.md \
    .claude/agents/image-assessor.md
  ```
  - Expected: All 5 files listed

- [ ] **Count total mentions**
  ```bash
  grep -c "extract_county_data\|County Data\|county" .claude/**/*.md
  ```
  - Expected: 50+ total matches across all files

### 2. Structural Integrity

- [ ] **Check markdown syntax**
  ```bash
  # Verify all section headers are properly formatted
  grep "^###" .claude/commands/analyze-property.md | head -n 20
  ```
  - Expected: All headers use `###` format, no broken headers

- [ ] **Check code blocks**
  ```bash
  # Count opening and closing backticks (should be equal)
  grep -c '```' .claude/commands/analyze-property.md
  ```
  - Expected: Even number (pairs of opening/closing)

### 3. Cross-References Valid

- [ ] **Verify file paths in docs**
  ```bash
  # Check all script references exist
  ls scripts/extract_county_data.py
  ls data/enrichment_data.json
  ```
  - Expected: All files exist

- [ ] **Check agent references**
  ```bash
  # Verify orchestrator references correct agent files
  grep "listing-browser.md\|map-analyzer.md\|image-assessor.md" \
    .claude/commands/analyze-property.md
  ```
  - Expected: All three agent files referenced

---

## Functional Testing

### Test 1: Single Property Analysis

- [ ] **Run with county extraction**
  ```bash
  # This should trigger Phase 0
  /analyze-property "4732 W Davis Rd, Glendale, AZ"
  ```

- [ ] **Verify Phase 0 executed**
  - Check output mentions "Phase 0: Extracting official county records..."
  - Check enrichment_data.json updated with county fields
  - Check kill-switches evaluated (lot_sqft, year_built, garage_spaces)

- [ ] **Verify enrichment data populated**
  ```bash
  python -c "
  import json
  d = json.load(open('data/enrichment_data.json'))
  p = next(x for x in d if '4732 W Davis' in x['full_address'])

  # County-sourced fields
  print('lot_sqft:', p.get('lot_sqft'))
  print('year_built:', p.get('year_built'))
  print('garage_spaces:', p.get('garage_spaces'))
  print('has_pool:', p.get('has_pool'))
  print('livable_sqft:', p.get('livable_sqft'))
  "
  ```
  - Expected: All fields populated with values (not None)

### Test 2: Batch Mode (Test)

- [ ] **Run test mode**
  ```bash
  /analyze-property --test
  ```

- [ ] **Verify batch Phase 0**
  - Check output shows "Extracting county data for 5 properties..."
  - Check all 5 properties get county data before Phase 1
  - Check any kill-switch failures detected early

### Test 3: Kill-Switch Filtering

- [ ] **Test property that fails kill-switch**
  - Find or create property with lot_sqft < 7000 or > 15000
  - Run analysis
  - Verify marked as "FAILED" tier
  - Verify Phase 1-4 skipped

### Test 4: Data Conflict Detection

- [ ] **Check for conflicts in output**
  - Run analysis on property where listing lot_sqft ≠ county lot_sqft
  - Verify agent notes conflict in return data
  - Verify county value used (authoritative)

---

## Rollback (If Needed)

If issues arise, restore backups:

- [ ] **Restore from backups**
  ```bash
  cp .claude/commands/analyze-property.md.backup .claude/commands/analyze-property.md
  cp .claude/AGENT_BRIEFING.md.backup .claude/AGENT_BRIEFING.md
  cp .claude/agents/listing-browser.md.backup .claude/agents/listing-browser.md
  cp .claude/agents/map-analyzer.md.backup .claude/agents/map-analyzer.md
  cp .claude/agents/image-assessor.md.backup .claude/agents/image-assessor.md
  ```

- [ ] **Verify rollback**
  ```bash
  grep "Phase 0" .claude/commands/analyze-property.md
  ```
  - Expected: No matches (Phase 0 removed)

---

## Completion Checklist

- [ ] All 8 edits applied successfully
- [ ] All 5 files updated
- [ ] Verification commands passed
- [ ] Single property test passed
- [ ] Batch mode test passed
- [ ] Kill-switch filtering works
- [ ] Data conflicts detected
- [ ] Documentation backups created
- [ ] No markdown syntax errors
- [ ] All cross-references valid

---

## Metrics

**Implementation time estimate:**
- Reading docs: 10 minutes
- Applying edits: 20 minutes
- Verification: 10 minutes
- Testing: 15 minutes
- **Total: ~55 minutes**

**Lines added:**
- analyze-property.md: ~60 lines
- AGENT_BRIEFING.md: ~35 lines
- listing-browser.md: ~22 lines
- map-analyzer.md: ~18 lines
- image-assessor.md: ~15 lines
- **Total: ~150 lines**

**Files modified:**
- 5 documentation files
- 0 code files (county script already exists)

**Breaking changes:**
- None (purely additive)

**Rollback complexity:**
- Easy (restore 5 files from backups)

---

## Success Criteria

Implementation is complete when:

1. ✅ All 8 edits applied across 5 files
2. ✅ All verification commands pass
3. ✅ Single property analysis includes Phase 0
4. ✅ County data auto-populates enrichment fields
5. ✅ Kill-switches evaluated in Phase 0
6. ✅ Agents reference county data appropriately
7. ✅ No markdown syntax errors
8. ✅ Documentation remains consistent

---

## Notes

- **Edit order matters:** Shared context first, then agents, then orchestrator
- **Test incrementally:** Verify each file after editing before moving to next
- **Use exact text:** Copy old_string and new_string from `apply-county-data-edits.md` exactly
- **Check line numbers:** They're approximate - use text search instead
- **Backup first:** Always create backups before editing

---

*Checklist created: 2025-11-30*
*For: Maricopa County Assessor API integration*
*Version: 1.0*
