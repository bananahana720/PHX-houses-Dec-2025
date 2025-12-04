# 3. Orphaned Metadata Fields (12+ fields)

These fields track data provenance via `*_source` and `*_confidence` patterns. Assess whether they're essential for LineageTracker:

### 3.1 Source Fields (17 total)

| Field | Current Value(s) | Used By | Decision |
|-------|-----------------|---------|----------|
| `aesthetics_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `ceiling_height_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `fireplace_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `high_ceilings_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `kitchen_layout_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `kitchen_quality_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `laundry_area_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `laundry_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `master_quality_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `master_suite_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `natural_light_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `safety_neighborhood_score_source` | `default_pending_assessment` | LineageTracker? | INVESTIGATE |
| `data_source` | (varies) | Unknown | ORPHANED? |
| `distance_to_park_miles_source` | (varies) | Unknown | ORPHANED? |
| `orientation_source` | (varies) | Unknown | ORPHANED? |
| `parks_data_source` | `web_research_85306` | Audit trail? | INVESTIGATE |
| `safety_data_source` | `web_research_85306` | Audit trail? | INVESTIGATE |

**Recommendation:** Before cleanup, verify:
1. Which `*_source` fields are actively queried by LineageTracker
2. Whether `field_lineage.json` (LineageTracker's file) is the proper home for this data
3. If enrichment_data.json should store sources at all vs. delegating to LineageTracker

### 3.2 Confidence Fields (6 total)

| Field | Current Value(s) | Purpose | Decision |
|-------|-----------------|---------|----------|
| `assessment_confidence` | (varies) | Overall assessment confidence | UNCLEAR |
| `confidence_breakdown` | (dict?) | Component confidences | UNCLEAR |
| `hvac_age_confidence` | `estimated_replacement_cycle` | HVAC estimation quality | KEEP? |
| `image_assessment_confidence` | (varies) | Image quality score | INVESTIGATE |
| `interior_assessment_confidence` | (varies) | Interior scoring quality | INVESTIGATE |
| `interior_confidence` | (varies) | Interior section confidence | INVESTIGATE |
| `pool_equipment_age_confidence` | `estimated_replacement_cycle` | Pool estimation quality | KEEP? |
| `roof_age_confidence` | `estimated_multiple_replacements` | Roof estimation quality | KEEP? |
| `section_c_confidence` | (varies) | Interior section confidence | INVESTIGATE |

**Recommendation:**
- Age estimation confidence fields (`hvac_age_confidence`, `pool_equipment_age_confidence`, `roof_age_confidence`) appear intentional - KEEP for now
- Assessment confidence fields suggest scoring reliability tracking - CONSOLIDATE into single `scoring_confidence` with detailed breakdown in LineageTracker
- Eliminate duplicates like `interior_confidence` vs `interior_assessment_confidence`

### 3.3 Computed Section Fields (5 total)

These appear to be intermediate scoring results:

| Field | Type | Purpose |
|-------|------|---------|
| `score_interior` | float | Section C total |
| `score_location` | float | Section A total |
| `score_lot_systems` | float | Section B total |
| `total_score` | float | Grand total |
| `scored_at` | datetime? | Scoring timestamp |

**Recommendation:**
- These are scoring artifacts that should be in `phx_homes_ranked.csv` output, not in enrichment_data.json
- If needed during pipeline, compute them dynamically in PropertyScorer
- Remove from persistent storage to avoid stale scores

### 3.4 Interior Section Aliases (8 fields)

These duplicate the main score fields with `interior_` prefix:

| Main Field | Interior Alias |
|-----------|----------------|
| `aesthetics_score` | (no interior version but follows pattern) |
| `high_ceilings_score` | `interior_ceilings_score` |
| `fireplace_score` | `interior_fireplace_score` |
| `natural_light_score` | `interior_light_score` |
| `kitchen_layout_score` | `interior_kitchen_score` |
| `master_suite_score` | `interior_master_score` |
| `laundry_area_score` | `interior_laundry_score` |

**Recommendation:** Choose ONE naming convention:
- Option A: Use main field names only (`high_ceilings_score` not `interior_ceilings_score`)
- Option B: Use `interior_` prefix consistently for Section C
- Document choice in design spec

---
