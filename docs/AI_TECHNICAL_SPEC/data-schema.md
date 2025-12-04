# DATA SCHEMA

### Input File 1: `phx_homes.csv`
```csv
street,city,state,zip,price,price_num,beds,baths,sqft,price_per_sqft,full_address
4732 W Davis Rd,Glendale,AZ,85306,"$475,000",475000,4,2.0,2241,211.96,"4732 W Davis Rd, Glendale, AZ 85306"
```

**Required Columns**:
- `street`, `city`, `state`, `zip`: Address components
- `price_num`: Integer price in dollars
- `beds`: Integer bedroom count
- `baths`: Float bathroom count (2.5 = 2 full + 1 half)
- `sqft`: Integer living area
- `price_per_sqft`: Float calculated field
- `full_address`: Complete formatted address (used as primary key)

### Input File 2: `enrichment_data.json`
```json
[
  {
    "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
    "lot_sqft": 8712,
    "year_built": 1973,
    "garage_spaces": 2,
    "sewer_type": "city",
    "tax_annual": 1850,
    "hoa_fee": 0,
    "commute_minutes": 35,
    "school_district": "Deer Valley Unified District",
    "school_rating": 8.1,
    "orientation": null,
    "distance_to_grocery_miles": 1.2,
    "distance_to_highway_miles": 2.5,
    "solar_status": null,
    "solar_lease_monthly": null,
    "has_pool": true,
    "pool_equipment_age": null,
    "roof_age": null,
    "hvac_age": null
  }
]
```

**Field Definitions**:
- `lot_sqft`: Total lot size from county assessor
- `year_built`: Construction year
- `garage_spaces`: Number of garage spaces (2 minimum required)
- `sewer_type`: "city" or "septic" (city required)
- `tax_annual`: Annual property tax in dollars
- `hoa_fee`: Monthly HOA fee (0 = no HOA, required for pass)
- `commute_minutes`: Drive time to Desert Ridge
- `school_rating`: GreatSchools 1-10 rating
- `orientation`: Cardinal direction house faces (N, S, E, W, NE, NW, SE, SW)
- `distance_to_grocery_miles`: Miles to nearest grocery store
- `distance_to_highway_miles`: Miles to nearest major highway
- `solar_status`: "owned", "leased", "none", or null
- `has_pool`: Boolean
- `pool_equipment_age`, `roof_age`, `hvac_age`: Integer years or null

---
