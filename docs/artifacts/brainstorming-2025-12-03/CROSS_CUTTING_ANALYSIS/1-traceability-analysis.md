# 1. TRACEABILITY ANALYSIS

### Current State: Fragmented and Opaque

#### 1.1 What Traces Exist?

**Good:**
- `work_items.json` tracks phase status per property (pending → in_progress → complete)
- `enrichment_data.json` captures raw field values (lot_sqft, year_built, etc.)
- `_last_county_sync`, `_last_updated`, `_phase1_map_completed` timestamps exist
- Phase completion timestamps recorded in work_items

**Missing:**
- **No field-level lineage**: Can't trace where each field came from (County API vs. listing vs. manual?)
- **No scoring audit trail**: Cannot see which scoring strategies contributed to final score
- **No data provenance links**: enrichment_data.json has no `source`, `confidence`, or `lineage_id` fields
- **No user attribution**: Unknown who assessed which images for Section C scoring
- **No version history**: Can't compare old vs. new scores when criteria change
- **No reasoning chains**: Why did a property fail? Which severity threshold was crossed?

#### 1.2 Architecture Problems

**Problem 1: No Provenance Model**

```python
# Current: Just raw values
{
  "full_address": "123 Main St",
  "lot_sqft": 9387,
  "year_built": 1983,
  "_last_updated": "2025-12-03T03:24:41",
  # WHERE did these come from? Assessor API? Zillow? Manual?
  # HOW confident are these? 0.95? 0.70?
  # WHO validated this? Human? Script?
}

# Needed: Provenance per field
{
  "full_address": "123 Main St",
  "lot_sqft": {
    "value": 9387,
    "source": "maricopa_assessor_api",      # Phase 0
    "phase": "phase0_county",
    "confidence": 0.95,
    "extracted_at": "2025-12-03T03:24:56",
    "validated_by": "extract_county_data.py",
  },
  "orientation": {
    "value": "south",
    "source": "satellite_visual_estimate",  # Phase 1
    "phase": "phase1_map",
    "confidence": 0.65,
    "extracted_at": "2025-12-03T05:30:00",
    "validated_by": "map-analyzer",
    "notes": "Medium confidence - satellite view, not on-site"
  }
}
```

**Problem 2: No Scoring Lineage**

Scoring happens in `PropertyScorer` (orchestrator) + 18+ strategy classes. Final score exists, but:

```python
# Current: Only final output
{
  "full_address": "123 Main St",
  "total_score": 425,
  "tier": "contender",
  "score_breakdown": {
    "location": 180,
    "systems": 95,
    "interior": 150
  }
  # HOW did location reach 180? Which sub-scores?
  # If orientation is 0 and schools is 50, what's the middle 130?
  # Can't explain to user WHY this property scored 425
}

# Needed: Detailed reasoning
{
  "scoring_run_id": "abc123-2025-12-03",
  "scored_at": "2025-12-03T06:00:00",
  "strategies_applied": [
    {
      "strategy": "SchoolDistrictScorer",
      "phase": "phase1_map",
      "input": {"school_rating": 8.0},
      "output": {"points": 36, "max_possible": 45},
      "reasoning": "GreatSchools 8/10 = 36/45 (80%)"
    },
    {
      "strategy": "OrientationScorer",
      "phase": "phase1_map",
      "input": {"orientation": "south"},
      "output": {"points": 15, "max_possible": 25},
      "reasoning": "South-facing = moderate (15/25); North would be 25/25"
    },
    # ... all 18 strategies ...
  ],
  "section_summaries": [
    {"name": "Location", "total": 180, "max": 230},
    {"name": "Systems", "total": 95, "max": 180},
    {"name": "Interior", "total": 150, "max": 190}
  ]
}
```

**Problem 3: No Kill-Switch Audit**

Kill-switch failures are recorded, but verdict reasoning is lost:

```python
# Current: Just verdict
{
  "full_address": "123 Main St",
  "kill_switch_passed": False,
  "kill_switch_failures": ["garage_spaces: 1 < 2"]
  # Why is severity a problem? Which soft criteria cumulated?
  # What was severity total? How close to failure threshold?
}

# Needed: Detailed verdict reasoning
{
  "kill_switch_verdict": {
    "verdict": "FAIL",
    "verdict_reason": "severity >= 3.0 (soft criteria accumulated)",
    "evaluated_at": "2025-12-03T03:25:00",
    "evaluator": "KillSwitchFilter",
    "hard_failures": [],  # Empty = passed all hard criteria
    "soft_criteria_results": [
      {
        "criterion": "city_sewer",
        "requirement": "city",
        "actual": "septic",
        "passed": False,
        "severity": 2.5,
        "notes": "Septic systems add maintenance burden"
      },
      {
        "criterion": "garage_spaces",
        "requirement": ">= 2",
        "actual": 1,
        "passed": False,
        "severity": 1.5,
        "notes": "1-car garage inconvenient for family"
      }
    ],
    "total_severity": 4.0,
    "severity_threshold": 3.0,
    "severity_warning_threshold": 1.5,
  }
}
```

#### 1.3 Traceability Impact

**When criteria change** (e.g., "orientation bonus now 30pts instead of 25pts"):
- Can't re-score without re-running all phases
- No audit trail to show impact of change
- Users can't explain "Why did Property X drop from 480 to 475?"

**When data sources conflict** (County API says year_built=1985, Zillow says 1987):
- No provenance to know which source to trust
- No confidence scores to weight the conflict
- Manual review required for every disagreement

**When scoring algorithms improve**:
- Can't baseline old scores for comparison
- No lineage to show which properties were affected by which strategies
- Regression testing requires manual spot-checking

### Recommendations

#### Short-term (1-2 weeks)
1. **Add field-level metadata** to `enrichment_data.json`:
   - Wrap raw values in objects with `value`, `source`, `confidence`, `extracted_at`
   - Preserve backward compatibility with fallback to raw values
   - Update `EnrichmentDataSchema` to allow metadata fields

2. **Create `field_lineage.json`** state file:
   ```json
   {
     "properties": [
       {
         "address": "123 Main St",
         "fields": {
           "lot_sqft": {"source": "maricopa_assessor_api", "phase": "phase0_county"},
           "orientation": {"source": "satellite_visual_estimate", "phase": "phase1_map"}
         }
       }
     ]
   }
   ```

3. **Add scoring lineage capture** in `PropertyScorer`:
   ```python
   # In PropertyScorer.score()
   lineage = {
       "run_id": generate_run_id(),
       "scored_at": datetime.now(),
       "strategies": []
   }
   # Each strategy appends to lineage before final score
   property.scoring_lineage = lineage
   ```

#### Medium-term (3-4 weeks)
1. **Implement versioned scoring system**:
   - Store scoring runs with version numbers
   - Allow rollback to previous scoring algorithm
   - Compare scores across versions

2. **Create scoring explanation generator**:
   ```python
   def explain_score(property: Property, include_breakdown=True):
       """Generate human-readable explanation of score."""
       return f"""
       Property: {property.full_address}

       LOCATION SCORE: {location_score}/230
       - School District: {school_score}/45 (GreatSchools {rating}/10)
       - Safety: {safety_score}/50 (crime index {index})
       - Orientation: {orientation_score}/25 (facing {orientation})

       SYSTEMS SCORE: {systems_score}/180
       - Roof: {roof_score}/50 (built {year}, {age} years old)
       - Plumbing/Electrical: {plumbing_score}/40

       INTERIOR SCORE: {interior_score}/190
       - Kitchen: {kitchen_score}/40
       - Master Suite: {suite_score}/40

       TOTAL: {total}/600 → {tier}
       """
   ```

3. **Implement confidence-aware field aggregation**:
   ```python
   def merge_enrichment(listing_data, enrichment_data):
       """Merge with confidence weighting."""
       # If enrichment_data.year_built has confidence 0.95
       # and listing_data.year_built has confidence 0.70
       # Use enrichment (0.95 wins)
       # Store both with provenance
   ```

#### Long-term (ongoing)
1. **Audit log system** for all property changes:
   - Who changed what field, when, from what to what
   - Supports regulatory compliance (FTC, local real estate laws)

2. **Time-series property snapshots**:
   - Save complete property state before/after each phase
   - Enables "what if" analysis when criteria change

3. **Data lineage visualization**:
   - Graph showing how property data flowed through pipeline
   - Which sources contributed to final verdict

---
