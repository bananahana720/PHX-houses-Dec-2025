# KILL SWITCH CRITERIA (HARD FILTERS)

Properties must pass ALL criteria or be excluded:

| Criterion | Rule | Failure Message |
|-----------|------|-----------------|
| HOA | `hoa_fee == 0 or hoa_fee is None` | "Must be NO HOA" |
| Sewer | `sewer_type == "city" or sewer_type is None` | "Must be City Sewer" |
| Garage | `garage_spaces >= 2 or garage_spaces is None` | "Minimum 2-Car Garage" |
| Beds | `beds >= 4` | "Minimum 4 Bedrooms" |
| Baths | `baths >= 2` | "Minimum 2 Bathrooms" |
| Lot Size | `7000 <= lot_sqft <= 15000 or lot_sqft is None` | "Lot 7,000-15,000 sqft" |
| Year Built | `year_built < 2024 or year_built is None` | "No New Builds (< 2024)" |

---
