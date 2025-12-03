# Repository Layer Implementation Summary

## Overview

The repository layer provides a clean abstraction for data persistence and retrieval in the PHX Home Analysis pipeline. It follows the Repository pattern with abstract base classes and concrete implementations for CSV and JSON data sources.

## Architecture

```
repositories/
├── __init__.py              # Module exports
├── base.py                  # Abstract base classes and exceptions
├── csv_repository.py        # CSV-based property repository
└── json_repository.py       # JSON-based enrichment repository
```

## Components

### 1. Base Classes (`base.py`)

**Exceptions:**
- `DataLoadError` - Raised when data cannot be loaded from a source
- `DataSaveError` - Raised when data cannot be saved to a destination

**Abstract Repositories:**

#### `PropertyRepository (ABC)`
- `load_all() -> list[Property]` - Load all properties
- `load_by_address(full_address: str) -> Optional[Property]` - Load single property
- `save_all(properties: list[Property]) -> None` - Save all properties
- `save_one(property: Property) -> None` - Save single property

#### `EnrichmentRepository (ABC)`
- `load_all() -> dict[str, EnrichmentData]` - Load all enrichment data indexed by address
- `load_for_property(full_address: str) -> Optional[EnrichmentData]` - Load enrichment for specific property
- `save_all(enrichment_data: dict[str, EnrichmentData]) -> None` - Save all enrichment data

### 2. CSV Property Repository (`csv_repository.py`)

**Class:** `CsvPropertyRepository(PropertyRepository)`

**Purpose:** Handles loading and saving property data from CSV files.

**Key Features:**
- Reads from input CSV (`phx_homes.csv`)
- Writes to ranked output CSV (`phx_homes_ranked.csv`)
- Handles both raw listing data and enriched/scored data
- Type-safe parsing with null handling
- In-memory caching for O(1) lookups by address

**CSV Columns Supported:**
- **Address:** street, city, state, zip, full_address
- **Listing:** price, price_num, beds, baths, sqft, price_per_sqft
- **County data:** lot_sqft, year_built, garage_spaces, sewer_type, tax_annual
- **Location:** hoa_fee, commute_minutes, school_district, school_rating, orientation, distance_to_grocery_miles, distance_to_highway_miles
- **Features:** solar_status, solar_lease_monthly, has_pool, pool_equipment_age, roof_age, hvac_age
- **Manual scores:** kitchen_layout_score, master_suite_score, natural_light_score, high_ceilings_score, fireplace_present, laundry_area_score, aesthetics_score, backyard_utility_score, safety_neighborhood_score, parks_walkability_score
- **Analysis:** score_location, score_lot_systems, score_interior, total_score, tier, kill_switch_passed, kill_switch_failures
- **Geocoding:** latitude, longitude

**Helper Methods:**
- `_row_to_property(row)` - Convert CSV row dict to Property entity
- `_property_to_row(property)` - Convert Property entity to CSV row dict
- `_parse_int(value)` - Safe integer parsing
- `_parse_float(value)` - Safe float parsing
- `_parse_bool(value)` - Boolean parsing (true/false/1/0/yes/no)
- `_parse_list(value)` - Delimited list parsing (semicolon-separated)
- `_parse_enum(value, enum_class)` - Case-insensitive enum parsing

**Usage:**
```python
from pathlib import Path
from src.phx_home_analysis.repositories import CsvPropertyRepository

# Initialize
repo = CsvPropertyRepository(
    csv_file_path='data/phx_homes.csv',
    ranked_csv_path='data/phx_homes_ranked.csv'
)

# Load all properties
properties = repo.load_all()

# Load specific property
property = repo.load_by_address('4732 W Davis Rd, Glendale, AZ 85306')

# Save ranked results
repo.save_all(properties)
```

### 3. JSON Enrichment Repository (`json_repository.py`)

**Class:** `JsonEnrichmentRepository(EnrichmentRepository)`

**Purpose:** Handles loading and saving enrichment data from JSON files.

**Key Features:**
- Reads from `enrichment_data.json`
- Supports both list and dict JSON formats
- Creates template file if not exists
- O(1) lookup by address via dictionary indexing
- Helper method to apply enrichment to Property entities

**JSON Structure:**
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

**Helper Methods:**
- `_dict_to_enrichment(data)` - Convert JSON dict to EnrichmentData entity
- `_enrichment_to_dict(enrichment)` - Convert EnrichmentData to JSON dict
- `_create_default_template()` - Create example template file
- `apply_enrichment_to_property(property, enrichment_dict)` - Merge enrichment into Property

**Usage:**
```python
from src.phx_home_analysis.repositories import JsonEnrichmentRepository

# Initialize
repo = JsonEnrichmentRepository('data/enrichment_data.json')

# Load all enrichment data
enrichment_dict = repo.load_all()

# Load for specific property
enrichment = repo.load_for_property('4732 W Davis Rd, Glendale, AZ 85306')

# Apply enrichment to property
property = repo.apply_enrichment_to_property(property, enrichment_dict)
```

## Data Flow

```
Input Sources:
├── phx_homes.csv          → CsvPropertyRepository → Property entities
└── enrichment_data.json   → JsonEnrichmentRepository → EnrichmentData

Processing Pipeline:
1. Load properties from CSV (basic listing data)
2. Load enrichment from JSON (county data, location, features)
3. Merge enrichment into properties
4. Apply kill-switch filters
5. Calculate weighted scores
6. Classify into tiers

Output:
└── phx_homes_ranked.csv   ← CsvPropertyRepository ← Scored Property entities
```

## Error Handling

All repository methods raise specific exceptions:

- **`DataLoadError`**: File not found, invalid format, parsing errors, missing required fields
- **`DataSaveError`**: File write errors, permission issues, invalid data

Example error handling:
```python
from src.phx_home_analysis.repositories import (
    CsvPropertyRepository,
    DataLoadError,
    DataSaveError
)

try:
    repo = CsvPropertyRepository('data/phx_homes.csv')
    properties = repo.load_all()
except DataLoadError as e:
    print(f"Failed to load data: {e}")
```

## Type Safety

All repositories use full type hints for:
- Method signatures
- Return types
- Optional values (using `Optional[T]`)
- Collection types (using `list[T]`, `dict[K, V]`)

This enables:
- IDE autocomplete
- Static type checking with mypy/pyright
- Better documentation
- Fewer runtime errors

## Enum Normalization

The repositories automatically normalize string values to enums:

**Supported Enums:**
- `SewerType`: city, septic, unknown
- `SolarStatus`: owned, leased, none, unknown
- `Orientation`: N, S, E, W, NE, NW, SE, SW, unknown
- `Tier`: unicorn, contender, pass, failed

**Parsing Features:**
- Case-insensitive matching
- Fallback to UNKNOWN for invalid values
- Supports both short (N) and long (north) formats for orientations

## Testing

The repository layer has been tested with:
- Loading 33 properties from `phx_homes.csv`
- Loading 33 enrichment records from `enrichment_data.json`
- Applying enrichment to properties
- Parsing all data types (int, float, bool, list, enum)
- Handling null/missing values gracefully

**Test Results:**
```
✓ Loaded 33 properties from CSV
✓ Loaded enrichment for 33 properties
✓ Successfully applied enrichment to properties
✓ Parsed lot_sqft: 8712
✓ Parsed year_built: 1973
✓ Parsed sewer_type: SewerType.CITY
✓ Parsed garage_spaces: 2
```

## Integration with Domain Layer

The repositories depend on the domain layer:

**From `domain.entities`:**
- `Property` - Main property entity
- `EnrichmentData` - Enrichment data transfer object

**From `domain.enums`:**
- `SewerType`, `SolarStatus`, `Orientation`, `Tier`

**From `domain.value_objects`:**
- `ScoreBreakdown` - Used in CSV output for score sections
- `Address`, `RiskAssessment`, `RenovationEstimate` - Computed properties

## Future Enhancements

Potential improvements for the repository layer:

1. **Async Support**: Add async versions for I/O-bound operations
2. **Batch Loading**: Support pagination/streaming for large datasets
3. **Validation**: Pre-save validation against schema
4. **Caching**: Redis/memcached for distributed systems
5. **Database Support**: PostgreSQL/SQLite repository implementations
6. **Transaction Support**: Rollback capability for save operations
7. **Migration Tools**: Automated schema migration helpers
8. **Bulk Operations**: Optimized bulk insert/update methods

## Dependencies

**Standard Library:**
- `csv` - CSV file handling
- `json` - JSON parsing/serialization
- `pathlib` - Path manipulation
- `typing` - Type hints
- `abc` - Abstract base classes

**Domain Layer:**
- `src.phx_home_analysis.domain.entities`
- `src.phx_home_analysis.domain.enums`
- `src.phx_home_analysis.domain.value_objects`

## File Locations

All repository files are in:
```
C:\Users\Andrew\Downloads\PHX-houses-Dec-2025\src\phx_home_analysis\repositories\
```

**Data Files:**
```
C:\Users\Andrew\Downloads\PHX-houses-Dec-2025\data\
├── phx_homes.csv           # Input listing data
├── enrichment_data.json    # Input enrichment data
└── phx_homes_ranked.csv    # Output ranked results (generated)
```

## Verification Checklist

- [x] Abstract base classes defined with clear contracts
- [x] Custom exceptions for error handling
- [x] CSV repository loads and saves property data
- [x] JSON repository loads and saves enrichment data
- [x] Type hints throughout all code
- [x] UTF-8 encoding for all file operations
- [x] Graceful handling of missing/null values
- [x] Enum parsing from string values
- [x] Helper methods for type conversion
- [x] In-memory caching for performance
- [x] Module exports via __init__.py
- [x] Tested with real project data (33 properties)
- [x] Compatible with updated domain entities
- [x] Support for all CSV columns including manual scores
- [x] Support for score_breakdown value object

---

**Implementation Date:** November 29, 2025
**Python Version:** 3.12+
**Status:** Production Ready
