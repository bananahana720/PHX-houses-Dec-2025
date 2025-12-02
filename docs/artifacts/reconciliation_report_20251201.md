# Data Reconciliation Report
**Generated:** 2025-12-01
**Scope:** Complete source-to-output field audit for PHX Home Analysis pipeline

---

## Executive Summary

| Audit Area | Status | Issues Found |
|------------|--------|--------------|
| Scoring Calculations | PASS | 2 minor (comments only) |
| Field Mappings | NEEDS ATTENTION | 45 gaps identified |
| Deal Sheet/Dashboard | NEEDS ATTENTION | 12 issues |
| Type Consistency | NEEDS ATTENTION | 10 inconsistencies |

**Total Fields Audited:** 96
**Complete Mappings:** 35 (36%)
**Gaps Requiring Action:** 45 (47%)

---

## CRITICAL ISSUES (Immediate Fix Required)

### 1. Interior Scoring Fields NOT Exported to CSV
**Severity:** HIGH
**Impact:** Cannot audit/verify scores; deal sheets lack source data

These fields are used in scoring (190 pts) but NOT in output CSV:
- `kitchen_layout_score` (40 pts)
- `master_suite_score` (40 pts)
- `natural_light_score` (30 pts)
- `high_ceilings_score` (30 pts)
- `fireplace_present` (20 pts)
- `laundry_area_score` (20 pts)
- `aesthetics_score` (10 pts)

**Fix:** Add these columns to `generate_ranked_csv()` in phx_home_analyzer.py

### 2. Radar Chart Wrong Denominator
**Severity:** HIGH
**Location:** `scripts/radar_charts.py` line 75
**Current:** `'Location': round((row['section_a_score'] / 250.0) * 10, 2)`
**Should be:** `/ 230.0` (matches actual Section A max)

**Impact:** Location axis displays at wrong scale

### 3. Golden Zone Map Missing Coordinates
**Severity:** CRITICAL
**Location:** `scripts/golden_zone_map.py` line 142
**Problem:** Script expects `lat`/`lng` fields that don't exist
**Impact:** Script will crash if executed

**Fix:** Add geocoding data to enrichment or remove script

### 4. Kill-Switch Fields NOT in Output CSV
**Severity:** HIGH
**Impact:** Can't verify why properties passed/failed

Missing from output:
- `garage_spaces` (kill switch criterion)
- `sewer_type` (kill switch criterion)
- `hoa_fee` (kill switch criterion)

---

## FIELD MAPPING GAPS

### Fields in Enrichment but NOT in Output

| Field | Used In | Impact |
|-------|---------|--------|
| `garage_spaces` | Kill switch, backyard calc | MEDIUM |
| `sewer_type` | Kill switch | MEDIUM |
| `hoa_fee` | Kill switch, cost efficiency | MEDIUM |
| `pool_equipment_age` | Pool scoring | LOW |
| `solar_lease_monthly` | Cost efficiency | LOW |
| `backyard_utility_score` | Systems scoring (40 pts) | MEDIUM |
| `safety_neighborhood_score` | Location scoring (50 pts) | MEDIUM |
| `parks_walkability_score` | Location scoring (30 pts) | MEDIUM |

### Legacy Field Names (Unused)

These fields exist in enrichment but are never mapped:
- `kitchen_quality_score` → Should use `kitchen_layout_score`
- `master_quality_score` → Should use `master_suite_score`
- `ceiling_height_score` → Should use `high_ceilings_score`
- `laundry_score` → Should use `laundry_area_score`
- `fireplace_score` → Should use `fireplace_present`

---

## TYPE INCONSISTENCIES

| Field | Local Property | Domain Property | Issue |
|-------|----------------|-----------------|-------|
| `price` | `int` | `str` (formatted) | Formatting breaks comparisons |
| `hoa_fee` | `float \| None` | `int \| None` | Precision loss |
| `tax_annual` | `float \| None` | `int \| None` | Precision loss |
| `solar_lease_monthly` | `float \| None` | `int \| None` | Precision loss |
| `sewer_type` | `str \| None` | `SewerType Enum` | Duplicate enum defs |
| `solar_status` | `str \| None` | `SolarStatus Enum` | Duplicate enum defs |
| `orientation` | `str \| None` | `Orientation Enum` | Duplicate enum defs |

---

## SCORING VERIFICATION

### Summary: ALL PASS

| Section | Documented | Implemented | Status |
|---------|------------|-------------|--------|
| A: Location | 230 pts | 230 pts | PASS |
| B: Systems | 180 pts | 180 pts | PASS |
| C: Interior | 190 pts | 190 pts | PASS |
| **Total** | **600 pts** | **600 pts** | **PASS** |

### Minor Documentation Issues

1. Comment in `strategies/__init__.py:34` says "250 pts max" → should be "230 pts max"
2. Comment in `systems.py:9` says "Pool Condition (30 pts)" → should be "20 pts"

---

## NULL/NONE HANDLING

### Permissive (None = Pass with Warning)
- `sewer_type: None` → Passes kill switch
- `garage_spaces: None` → Passes kill switch
- `lot_sqft: None` → Passes kill switch
- `year_built: None` → Passes kill switch

### Strict (None = Fail)
- `beds: 0` → Fails hard
- `baths: 0` → Fails hard

### Default Scoring (None = 5.0 neutral)
- All interior assessment fields default to 5.0
- Produces Interior score of 95 pts (50% of 190)

---

## RECOMMENDED FIXES

### Priority 1: Add Missing Output Fields

Add to `generate_ranked_csv()` fieldnames (phx_home_analyzer.py):
```python
fieldnames = [
    # ... existing ...
    'garage_spaces', 'sewer_type', 'hoa_fee',
    'kitchen_layout_score', 'master_suite_score',
    'natural_light_score', 'high_ceilings_score',
    'fireplace_present', 'laundry_area_score',
    'aesthetics_score', 'backyard_utility_score',
    'safety_neighborhood_score', 'parks_walkability_score',
]
```

### Priority 2: Fix Radar Chart

```python
# scripts/radar_charts.py line 75
# BEFORE:
'Location': round((row['section_a_score'] / 250.0) * 10, 2),
# AFTER:
'Location': round((row['score_location'] / 230.0) * 10, 2),
```

### Priority 3: Standardize Enrichment Field Names

Remove legacy field names from enrichment_data.json:
- Keep: `kitchen_layout_score`, `master_suite_score`, `high_ceilings_score`
- Remove: `kitchen_quality_score`, `master_quality_score`, `ceiling_height_score`

### Priority 4: Normalize Types

Use consistent types across layers:
- `hoa_fee`: `float | None` everywhere
- `tax_annual`: `float | None` everywhere
- Remove duplicate Pydantic enums, use domain enums

### Priority 5: Add Geocoding

Add `latitude`, `longitude` fields to enrichment schema and populate via geocoding script.

---

## VERIFICATION CHECKLIST

After implementing fixes:

- [ ] Interior scores vary by property (not all 95)
- [ ] All kill-switch criteria visible in output CSV
- [ ] Radar charts scale correctly (Location max = 230)
- [ ] Deal sheets show all scoring inputs
- [ ] No type conversion warnings in logs
- [ ] Golden zone map works with coordinates

---

## Files Requiring Changes

| File | Changes Needed |
|------|----------------|
| `scripts/phx_home_analyzer.py` | Add 15+ fields to CSV output |
| `scripts/radar_charts.py` | Fix denominator (250→230), update column names |
| `scripts/deal_sheets/renderer.py` | Add missing fields to templates |
| `data/enrichment_data.json` | Remove legacy field names |
| `src/phx_home_analysis/validation/schemas.py` | Consolidate with domain enums |
| `scripts/golden_zone_map.py` | Add geocoding or disable |

---

*Report generated by multi-agent audit system*
