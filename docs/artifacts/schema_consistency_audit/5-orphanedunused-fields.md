# 5. ORPHANED/UNUSED FIELDS

### 5.1 EnrichmentDataSchema Fields Never Populated

**From comparison with enrichment_data.json:**

1. **`backyard_utility_score`** - Defined in schema, missing from JSON sample
   - Status: EXPECTED if not yet assessed
   - Used by: BackyardUtilityScorer

2. **`fireplace_present`** - Schema has bool, JSON has `fireplace_score` float
   - Status: MISMATCH - different field semantics
   - Used by: FireplaceScorer (expects boolean)

3. **`noise_level`** - Defined in schema (0-10, lower is quieter)
   - Status: NOT IN JSON - unused field
   - Not used by any scorer (QuietnessScorer uses `distance_to_highway_miles`)
   - **Recommendation:** Remove from schema if truly unused

---

### 5.2 Enrichment JSON Fields Without Schema Validation

**Data lineage/metadata fields (18 fields):**
```
aesthetics_score_source
ceiling_height_score_source
fireplace_score_source
kitchen_quality_score_source
laundry_score_source
master_quality_score_source
natural_light_score_source
parks_data_source
safety_data_source
hvac_age_confidence
pool_equipment_age_confidence
roof_age_confidence
```

**Status:** Not validated - useful for provenance tracking

**Recommendation:** Create `FieldMetadata` schema or keep as unvalidated dict keys

---

**Computed/derived fields (6 fields):**
```
cost_breakdown (dict)
monthly_cost (float)
kill_switch_passed (bool)
kill_switch_failures (list)
price (numeric - duplicate of list_price)
sqft (duplicate from Property)
```

**Status:** Redundant - computed from other fields

**Recommendation:** Remove from JSON, compute on-demand

---

**Synonym fields (7 fields - DUPLICATES):**
```
ceiling_height_score (synonym of high_ceilings_score)
kitchen_quality_score (synonym of kitchen_layout_score)
master_quality_score (synonym of master_suite_score)
fireplace_score (different from fireplace_present)
laundry_score (synonym of laundry_area_score)
list_price (synonym of price_num)
distance_to_park_miles (not in schema)
```

**Status:** Redundant synonyms cause confusion

**Recommendation:** Remove all synonyms, use canonical names only

---

### 5.3 Schema Enum Values Never Used

**SewerTypeSchema:**
- `CITY` ✓ Used in kill-switch
- `SEPTIC` ✓ Used in kill-switch
- `UNKNOWN` ✓ Used as default

**SolarStatusSchema:**
- `OWNED` ✓ Used in scoring
- `LEASED` ✓ Used in scoring (penalized)
- `NONE` ✓ Used for no solar
- `UNKNOWN` ✓ Used as default

**OrientationSchema:**
- `N, S, E, W, NE, NW, SE, SW` ✓ All used in OrientationScorer
- `UNKNOWN` ✓ Used as default

**Status:** All enum values are actively used ✓

---
