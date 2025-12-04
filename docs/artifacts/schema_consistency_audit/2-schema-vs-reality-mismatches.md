# 2. SCHEMA VS REALITY MISMATCHES

### 2.1 PropertySchema vs CSV Columns

**CSV Columns (phx_homes.csv):**
```
street, city, state, zip, price, price_num, beds, baths, sqft, price_per_sqft, full_address
```

**PropertySchema Fields:**
```python
address, beds, baths, sqft, lot_sqft, year_built, price, hoa_fee,
garage_spaces, has_pool, pool_equipment_age, sewer_type, roof_age,
hvac_age, solar_status, orientation
```

**Mismatch Analysis:**
- CSV has `street, city, state, zip` → Schema has `address` (consolidated)
- CSV has `price_per_sqft` → Schema does NOT have this (computed in Property entity)
- Schema has 11 fields NOT in CSV (populated from enrichment):
  - `lot_sqft`, `year_built`, `hoa_fee`, `garage_spaces`, `has_pool`,
  - `pool_equipment_age`, `sewer_type`, `roof_age`, `hvac_age`,
  - `solar_status`, `orientation`

**Status:** EXPECTED - Schema is superset of CSV, enrichment fills gaps

---

### 2.2 EnrichmentDataSchema vs enrichment_data.json

**enrichment_data.json Sample Keys (60 fields):**
```
aesthetics_score, aesthetics_score_source, baths, beds, ceiling_height_score,
ceiling_height_score_source, commute_minutes, cost_breakdown,
distance_to_grocery_miles, distance_to_highway_miles, distance_to_park_miles,
fireplace_score, fireplace_score_source, full_address, garage_spaces,
has_pool, high_ceilings_score, hoa_fee, hvac_age, hvac_age_confidence,
kill_switch_failures, kill_switch_passed, kitchen_layout_score,
kitchen_quality_score, kitchen_quality_score_source, laundry_area_score,
laundry_score, laundry_score_source, list_price, lot_sqft,
master_quality_score, master_quality_score_source, master_suite_score,
monthly_cost, natural_light_score, natural_light_score_source, orientation,
parks_data_source, parks_walkability_score, pool_equipment_age,
pool_equipment_age_confidence, price, roof_age, roof_age_confidence,
safety_data_source, safety_neighborhood_score, school_district,
school_rating, sewer_type, solar_lease_monthly, solar_status, sqft,
tax_annual, year_built
```

**EnrichmentDataSchema Fields (32 fields):**
```python
full_address, beds, baths, lot_sqft, year_built, garage_spaces, sewer_type,
hoa_fee, tax_annual, has_pool, list_price, school_rating, safety_score,
noise_level, commute_minutes, distance_to_grocery_miles,
distance_to_highway_miles, kitchen_layout_score, master_suite_score,
natural_light_score, high_ceilings_score, laundry_area_score,
aesthetics_score, backyard_utility_score, parks_walkability_score,
fireplace_present, roof_age, hvac_age, pool_equipment_age, orientation,
solar_status, solar_lease_monthly
```

**Critical Gaps:**

**Fields in JSON but NOT in Schema (28 fields):**
- `*_source` fields (12): `aesthetics_score_source`, `ceiling_height_score_source`, etc.
- `*_confidence` fields (3): `hvac_age_confidence`, `pool_equipment_age_confidence`, `roof_age_confidence`
- `kill_switch_*` fields (2): `kill_switch_passed`, `kill_switch_failures`
- Computed fields (4): `cost_breakdown`, `monthly_cost`, `price`, `sqft`
- Synonym fields (7): `ceiling_height_score`, `kitchen_quality_score`, `master_quality_score`, `fireplace_score`, `laundry_score`, `list_price`, `distance_to_park_miles`

**Fields in Schema but NOT in JSON (2):**
- `backyard_utility_score` - Expected but missing from sample
- `fireplace_present` - Expected but missing (JSON has `fireplace_score` instead)

**Status:** PROBLEMATIC - Schema does not match reality. Many JSON fields lack schema validation.

---

### 2.3 Property Entity vs EnrichmentData DTO

**Field Count:**
- Property: 47 fields
- EnrichmentData: 19 fields

**Property fields NOT in EnrichmentData:**
```python
# Address decomposition (5)
street, city, state, zip_code, full_address

# Listing data (6)
price (formatted string), price_num, sqft, price_per_sqft_raw

# Geocoding (2)
latitude, longitude

# Analysis results (9)
kill_switch_passed, kill_switch_failures, score_breakdown, tier,
risk_assessments, renovation_estimate

# Additional manual scores (6)
safety_neighborhood_score, parks_walkability_score,
# (rest overlap with EnrichmentData)
```

**EnrichmentData fields match core county/enrichment sources**

**Status:** EXPECTED - Property is aggregate entity, EnrichmentData is DTO

---
