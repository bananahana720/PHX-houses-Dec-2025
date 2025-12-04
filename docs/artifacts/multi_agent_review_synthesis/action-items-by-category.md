# Action Items by Category

### 1. Scoring System Fixes (500→600)

**Problem:** Display layer shows incorrect maximum scores, undermining trust in analysis.

**Root Cause:** Templates hardcoded to 500-point system from earlier version. Section maxes also outdated.

**Action Items:**
1. **Update deal sheet template** (`scripts/deal_sheets/templates.py`):
   ```python
   # BEFORE: "{score}/500 pts"
   # AFTER:  "{score}/600 pts"
   ```
2. **Fix section maxes** in HTML generation:
   ```python
   # BEFORE: Section A: 150 pts, Section B: 160 pts, Section C: 190 pts
   # AFTER:  Section A: 230 pts, Section B: 180 pts, Section C: 190 pts
   ```
3. **Verify radar charts** use correct scale (0-600)
4. **Update any prose descriptions** mentioning point totals

**Files to Update:**
- `scripts/deal_sheets/templates.py` (primary)
- `scripts/deal_sheets/renderer.py` (if section maxes there)
- Search codebase for "500" and verify context

**Validation:**
- Regenerate all 75 deal sheets
- Spot-check 5 random properties for correct totals
- Verify tier thresholds still align (Unicorn >480, Contender 360-480)

---

### 2. Data Quality Infrastructure

**Problem:** LineageTracker infrastructure built but never invoked. County API overwrites manual research without audit trail. Field name mismatches cause 100% missing rates.

**Root Cause:**
- LineageTracker requires explicit calls that were never added
- No integration layer between county data and enrichment JSON
- Field naming conventions differ between sources

**Action Items:**

#### 2A. Wire Up LineageTracker (3 days)
1. **Add tracking calls** to all data update paths:
   ```python
   # In extract_county_data.py
   tracker.track_field_update(
       property_hash=prop_hash,
       field_name="lot_sqft",
       old_value=existing_value,
       new_value=county_value,
       source="maricopa_county_api",
       timestamp=datetime.now()
   )
   ```
2. **Invoke after each extraction phase:**
   - Phase 0: County API (`extract_county_data.py`)
   - Phase 1: Listings (`extract_images.py` - Zillow/Redfin)
   - Phase 2: Manual research (enrichment_data.json updates)
3. **Generate `field_lineage.json`** after pipeline runs
4. **Add validation report** showing field coverage by source

**Files to Update:**
- `scripts/extract_county_data.py`
- `scripts/extract_images.py` (listing extraction portions)
- `src/phx_home_analysis/services/quality/lineage_tracker.py` (ensure write path works)

#### 2B. Create Field Mapping Layer (2 days)
1. **Build canonical field mapping**:
   ```python
   FIELD_MAPPING = {
       "county_api": {
           "lot_sqft": "lot_size_sqft",      # County uses lot_sqft
           "year_built": "year_built",        # Match
           "garage_spaces": "garage_spaces",  # Match
           # ... etc
       },
       "enrichment_json": {
           "lot_size_sqft": "lot_size_sqft",  # Canonical
           # ... etc
       }
   }
   ```
2. **Add merge strategy** (manual > county > listing > default):
   ```python
   def merge_property_data(enrichment, county, listing):
       """Merge with explicit precedence and audit trail."""
       result = {}
       for field in ALL_FIELDS:
           if enrichment.get(field) and is_manually_verified(field):
               result[field] = enrichment[field]
               result[f"{field}_source"] = "manual_research"
           elif county.get(FIELD_MAPPING["county_api"].get(field)):
               result[field] = county[...]
               result[f"{field}_source"] = "county_api"
           # ... etc
       return result
   ```
3. **Log conflicts** when county data would overwrite manual research
4. **Create merge report** showing source precedence outcomes

**Files to Update:**
- New: `src/phx_home_analysis/services/data_integration/field_mapper.py`
- New: `src/phx_home_analysis/services/data_integration/merge_strategy.py`
- Update: `scripts/extract_county_data.py` (use mapper)

#### 2C. Cross-Stage Validation (2 days)
1. **Add validation checkpoints** after each phase:
   ```python
   # After Phase 0 (County)
   validate_required_fields(["lot_sqft", "year_built", "garage_spaces"])

   # After Phase 1 (Listings)
   validate_required_fields(["price", "beds", "baths", "listing_url"])

   # After Phase 2 (Manual)
   validate_kill_switch_criteria(["hoa_fee", "sewer_type"])
   ```
2. **Generate validation report** showing missing/invalid fields
3. **Block scoring** if critical fields missing (beds, baths, price)
4. **Warn but continue** if nice-to-have fields missing

**Files to Update:**
- New: `src/phx_home_analysis/services/validation/stage_validator.py`
- Update: `scripts/phx_home_analyzer.py` (add validation calls)

---

### 3. Schema Consolidation

**Problem:** 3 duplicate model definitions, 8 naming inconsistency categories, 28 unvalidated JSON fields.

**Root Cause:** Organic growth without refactoring. Different modules defining their own versions of shared concepts.

**Action Items:**

#### 3A. Merge Duplicate Models (1 day)
1. **Identify canonical location** for each duplicate:
   - `SourceStats`: Move to `src/phx_home_analysis/validation/schemas.py`
   - `ExtractionResult`: Move to `src/phx_home_analysis/validation/schemas.py`
   - `ExtractionState`: Move to `src/phx_home_analysis/validation/schemas.py`

2. **Delete duplicates** and update imports:
   ```python
   # BEFORE: from scripts.extract_images import SourceStats
   # AFTER:  from phx_home_analysis.validation.schemas import SourceStats
   ```

3. **Verify tests still pass**

**Files to Update:**
- Delete duplicates in `scripts/lib/state_models.py` (or wherever they are)
- Update all imports across codebase
- Run: `python -m pytest tests/` to verify

#### 3B. Standardize Naming Conventions (1 week - P2)
1. **Choose canonical patterns**:
   - Lot size: `lot_sqft` (matches county API)
   - Quality scores: `{domain}_score` (e.g., `kitchen_score`, not `kitchen_quality_score`)
   - Binary flags: `has_{feature}` (e.g., `has_pool`, not `pool`)
   - Counts: `{feature}_count` (e.g., `bedroom_count`, not `beds`)

2. **Create migration script**:
   ```python
   # Rename fields in enrichment_data.json
   def migrate_field_names():
       for prop in enrichment_data:
           if "kitchen_quality_score" in prop:
               prop["kitchen_score"] = prop.pop("kitchen_quality_score")
           # ... etc
   ```

3. **Update schemas to match**

**Files to Update:**
- `data/enrichment_data.json` (via migration script)
- All Pydantic schemas
- All dataclasses
- Templates that reference these fields

#### 3C. Validate Orphaned Metadata Fields (3 days - P2)
1. **Audit all `*_source` and `*_confidence` fields** in enrichment_data.json
2. **Add to Pydantic schemas** if should be retained:
   ```python
   class PropertyEnrichment(BaseModel):
       lot_sqft: Optional[int]
       lot_sqft_source: Optional[str]  # NEW
       lot_sqft_confidence: Optional[float]  # NEW
   ```
3. **Or delete if unused** (LineageTracker should replace these)

**Files to Update:**
- `src/phx_home_analysis/validation/schemas.py`
- `data/enrichment_data.json` (if deleting unused fields)

---

### 4. Dead Code Removal

**Problem:** 26 orphaned files/classes/functions (~15-25% of codebase). Creates confusion and maintenance burden.

**Action Items:**

#### 4A. Remove High-Confidence Dead Code (2 days)
**Safe to delete immediately (10 items):**
1. `scripts/proxy_listing_extractor.py` - Superseded by extract_images.py
2. `scripts/gen_9832_deal_sheet.py` - One-off script
3. `src/phx_home_analysis/services/ai_enrichment/field_inferencer.py` - FieldInferencer class never used
4. `tests/test_analyze.py` - Tests non-existent module
5. `tests/test_quality.py` - Tests non-existent module
6. `.venv.bak/` - Backup directory
7. Potentially others from Wave 3 report (need full list)

**Process:**
1. Git commit before deleting (safety net)
2. Delete file
3. Search codebase for imports: `rg "from scripts.proxy_listing_extractor"`
4. If no matches, delete is safe
5. Run tests: `python -m pytest tests/`
6. If tests pass, commit deletion

**Deliverable:** Git commit with message:
```
refactor: remove 10 high-confidence dead code items

- proxy_listing_extractor.py (superseded)
- gen_9832_deal_sheet.py (one-off)
- FieldInferencer class (unused)
- test_analyze.py, test_quality.py (orphaned tests)
- .venv.bak/ (backup directory)

All files verified as having zero imports/references.
Tests pass after deletion.
```

#### 4B. Investigate Medium-Confidence Dead Code (2 days - P2)
**Requires verification (11 items):**
1. `scripts/lib/proxy_manager.py` - May be used by browser_pool
2. `scripts/lib/browser_pool.py` - May be used by extract_images
3. `scripts/analyze.py` - Duplicate of phx_home_analyzer.py?
4. Others from Wave 3 report

**Process:**
1. For each file, search for imports: `rg "from scripts.lib.proxy_manager"`
2. If imports exist, trace call chain to entry points
3. If dead, add to deletion list
4. If alive, document purpose in module docstring

---

### 5. Configuration Cleanup

**Problem:** Hardcoded values (63 total), unused config classes, duplicate values across configs.

**Action Items:**

#### 5A. Fix Hardcoded 2024 New-Build Filter (4 hours - P0)
1. **Find all occurrences** of hardcoded 2024:
   ```bash
   rg "year_built.*2024" --type py
   rg "< 2024" --type py
   rg "2024" --type py  # May have false positives
   ```
2. **Replace with dynamic calculation**:
   ```python
   # BEFORE:
   if property.year_built >= 2024:
       return KillSwitchVerdict.FAIL

   # AFTER:
   from datetime import datetime
   CURRENT_YEAR = datetime.now().year
   if property.year_built >= CURRENT_YEAR:
       return KillSwitchVerdict.FAIL
   ```
3. **Update documentation** to reflect "current year" logic
4. **Add comment explaining** why we exclude current-year builds (buyer preference)

**Files to Update:** All 15 files identified in Wave 2 findings

#### 5B. Externalize Buyer Criteria (2 days - P1)
1. **Create BuyerCriteria config file**:
   ```yaml
   # config/buyer_criteria.yaml
   hard_criteria:
     hoa_fee: 0  # Must be zero
     min_beds: 4
     min_baths: 2

   soft_criteria:
     sewer_type:
       required: "city_sewer"
       severity: 2.5
     year_built:
       max: "current_year"  # Special token
       severity: 2.0
     garage_spaces:
       min: 2
       severity: 1.5
     lot_sqft:
       min: 7000
       max: 15000
       severity: 1.0

   severity_threshold: 3.0
   ```

2. **Load config in KillSwitchFilter**:
   ```python
   class KillSwitchFilter:
       def __init__(self, criteria_path: str = "config/buyer_criteria.yaml"):
           self.criteria = load_yaml(criteria_path)
   ```

3. **Delete hardcoded BuyerProfile** dataclass (or make it load from config)

**Files to Update:**
- New: `config/buyer_criteria.yaml`
- Update: `src/phx_home_analysis/services/kill_switch/filter.py`
- Update: `scripts/phx_home_analyzer.py` (pass config path)

#### 5C. Remove Unused Config Classes (1 day - P1)
1. **Delete MapConfig** class (never used):
   ```bash
   rg "MapConfig" --type py  # Verify zero references
   git rm src/phx_home_analysis/config/map_config.py
   ```

2. **Audit ArizonaContext** fields:
   - Keep fields used by scoring/analysis
   - Delete unused fields (8 identified in Wave 3)
   - Document purpose of each field in docstring

3. **Consolidate duplicate values** (ArizonaContext vs RateConfig):
   ```python
   # If same values appear in both configs, keep in ONE place
   # and import where needed
   ```

**Files to Update:**
- Delete: `src/phx_home_analysis/config/map_config.py`
- Update: `src/phx_home_analysis/config/arizona_context.py`
- Update: `src/phx_home_analysis/config/rate_config.py`

#### 5D. Externalize Value Zone Thresholds (4 hours - P2)
1. **Move to scoring_weights.yaml**:
   ```yaml
   # config/scoring_weights.yaml
   value_zones:
     sweet_spot:
       max_price: 550000
       min_score: 365
       label: "Value Sweet Spot"
   ```

2. **Update value_spotter.py** to read from config

**Files to Update:**
- `config/scoring_weights.yaml` (add value_zones section)
- `scripts/value_spotter.py` (load from config)

---
