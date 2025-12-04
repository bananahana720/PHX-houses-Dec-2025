---
name: property-data
description: Load, query, update, and validate property data from CSV listings and JSON enrichment files. Provides Pydantic schemas for validation, atomic write patterns, and data normalization. Use for any property data access, CRUD operations on enrichment_data.json, or address lookups.
allowed-tools: Read, Write, Bash(python:*), Grep
---

# Property Data Management Skill

Manage property data for the PHX houses analysis project with Pydantic-based validation.

## Data Sources

| File | Type | Access |
|------|------|--------|
| `data/phx_homes.csv` | CSV | Read-only (master listing) |
| `data/enrichment_data.json` | JSON | Read/write (enriched data) |
| `data/phx_homes_ranked.csv` | CSV | Generated (scored output) |

## Quick Reference: Schemas

**CSV Fields:** `street, city, state, zip, price, price_num, beds, baths, sqft, full_address`

**Enrichment Fields:**
```
full_address, lot_sqft, year_built, garage_spaces, sewer_type,
hoa_fee, school_rating, orientation, solar_status, has_pool,
pool_equipment_age, roof_age, hvac_age, safety_neighborhood_score
```

## Service Layer

```python
from src.phx_home_analysis.validation import PropertyValidator, validate_property
from src.phx_home_analysis.services.data_cache import PropertyDataCache

# Validate single property
result = validate_property({"address": "123 Main", "beds": 4, "baths": 2})
if result.is_valid:
    clean_data = result.normalized_data
else:
    errors = result.error_messages()

# Use cache for repeated loads (auto-invalidates on file change)
cache = PropertyDataCache()
enrichment = cache.get_enrichment_data(Path("data/enrichment_data.json"))
```

## Data Operations

### Load All Properties
```python
import json, csv

with open("data/phx_homes.csv") as f:
    listings = list(csv.DictReader(f))

with open("data/enrichment_data.json") as f:
    enrichment = {p["full_address"]: p for p in json.load(f)}

# Merge
for listing in listings:
    listing.update(enrichment.get(listing["full_address"], {}))
```

### Query Single Property
```python
def get_property(address: str) -> dict | None:
    enrichment = json.load(open("data/enrichment_data.json"))
    for prop in enrichment:
        if prop["full_address"].lower() == address.lower():
            return prop
    return None
```

### Update Property (Atomic)
```python
def update_property(address: str, updates: dict) -> bool:
    enrichment = json.load(open("data/enrichment_data.json"))
    for prop in enrichment:
        if prop["full_address"] == address:
            prop.update(updates)
            # Atomic write: temp + rename
            with open("data/enrichment_data.json.tmp", "w") as f:
                json.dump(enrichment, f, indent=2)
            os.replace("data/enrichment_data.json.tmp", "data/enrichment_data.json")
            return True
    return False
```

## Validation Rules

| Field | Type | Constraint |
|-------|------|------------|
| `address` | str | min 5 chars, contains digit |
| `beds` | int | 1-20 |
| `baths` | float | 0.5-20, 0.5 increments |
| `sqft` | int | 100-100,000 |
| `lot_sqft` | int | 0-500,000 |
| `year_built` | int | 1800-current year |
| `hoa_fee` | float | ≥0 (None=unknown, 0=no HOA) |
| `sewer_type` | enum | city/septic/unknown |
| `orientation` | enum | n/s/e/w/ne/nw/se/sw |

## Address Normalization

```python
from src.phx_home_analysis.validation.normalizer import normalize_address

normalize_address("123 W Main St")  # "123 west main street"
```

**Transformations:** lowercase, expand abbreviations (N→north, St→street)

## Validation API

```python
from src.phx_home_analysis.validation import (
    PropertyValidator,
    ValidationResult,
    BatchValidator,
)

validator = PropertyValidator(normalize=True)
result = validator.validate(data)          # Core property
result = validator.validate_enrichment(data)  # Enrichment data
result = validator.validate_kill_switch(data)  # Buyer criteria

# Batch validation
batch = BatchValidator()
results, summary = batch.validate_batch(records)
print(f"Valid: {summary['valid']}/{summary['total']}")
```

## Best Practices

1. **Atomic writes** - Always use temp + rename pattern
2. **Preserve data** - Merge updates, don't overwrite entire objects
3. **Normalize addresses** - Use `full_address` as canonical key
4. **Handle nulls** - Distinguish None (unknown) from 0 (confirmed zero)
5. **Validate on input** - Use PropertyValidator for external data
6. **Use cache** - PropertyDataCache for repeated loads

## Module Locations

| Component | Path |
|-----------|------|
| Schemas | `src/phx_home_analysis/validation/schemas.py` |
| Validators | `src/phx_home_analysis/validation/validators.py` |
| Normalizer | `src/phx_home_analysis/validation/normalizer.py` |
| Data Cache | `src/phx_home_analysis/services/data_cache.py` |
