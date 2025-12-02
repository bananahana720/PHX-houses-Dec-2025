# Unit Tests for Repository Classes

## Overview

Comprehensive unit test suite for `CsvPropertyRepository` and `JsonEnrichmentRepository` classes with 50 tests covering all major functionality, edge cases, and error handling.

**Location:** `tests/unit/test_repositories.py`
**Status:** All 50 tests passing
**Coverage:** 88% of repository code

## Test Structure

### Test Organization

The test suite is organized into logical test classes:

1. **TestCsvPropertyRepositoryLoad** (9 tests) - CSV loading functionality
2. **TestCsvPropertyRepositorySave** (6 tests) - CSV saving functionality
3. **TestCsvPropertyRepositoryParsing** (16 tests) - Parsing helper methods
4. **TestJsonEnrichmentRepositoryLoad** (7 tests) - JSON loading functionality
5. **TestJsonEnrichmentRepositorySave** (3 tests) - JSON saving functionality
6. **TestJsonEnrichmentRepositoryApplyEnrichment** (4 tests) - Enrichment application
7. **TestJsonEnrichmentRepositorySerialization** (3 tests) - Serialization/deserialization
8. **TestRepositoryIntegration** (2 tests) - Integration between repositories

## CsvPropertyRepository Tests

### Loading Tests (TestCsvPropertyRepositoryLoad)

| Test Name | Purpose | Edge Cases Covered |
|-----------|---------|-------------------|
| `test_load_valid_csv` | Load well-formed CSV with multiple properties | Basic happy path |
| `test_load_empty_csv` | Handle CSV with headers only | Empty data |
| `test_load_missing_file` | Error handling for non-existent file | File not found |
| `test_load_missing_required_columns` | Error on missing required columns | Schema validation |
| `test_load_malformed_row` | Graceful handling of malformed numeric data | Data type coercion |
| `test_load_by_address_found` | Lookup single property by address | Cache utilization |
| `test_load_by_address_not_found` | Handle missing addresses | Null safety |
| `test_load_by_address_uses_cache` | Verify cache is used after initial load | Performance/caching |
| `test_cache_behavior` | Cache is populated after loading | State management |

**Key Features Tested:**
- File I/O and CSV parsing
- Error handling with `DataLoadError` exceptions
- Caching mechanism for performance
- Address lookup functionality
- Handles missing/malformed data gracefully

### Saving Tests (TestCsvPropertyRepositorySave)

| Test Name | Purpose | Edge Cases Covered |
|-----------|---------|-------------------|
| `test_save_properties` | Write properties to CSV file | Basic write operation |
| `test_save_empty_list` | Save empty property list | Edge case: no data |
| `test_save_creates_parent_directory` | Auto-create nested directories | Path creation |
| `test_save_without_ranked_path` | Error when output path not configured | Configuration validation |
| `test_save_one_not_implemented` | Verify NotImplementedError for single save | API contract |
| `test_save_and_reload` | Round-trip: save and reload | Data consistency |

**Key Features Tested:**
- CSV file writing
- Parent directory creation
- Configuration validation
- Error handling with `DataSaveError` exceptions
- Data round-trip integrity (save/load consistency)

### Parsing Tests (TestCsvPropertyRepositoryParsing)

#### Integer Parsing
- Valid integers: `"12345"` → `12345`
- None/empty strings: `None`, `""`, `"  "` → `None`
- Invalid values: `"not_a_number"` → `None`

#### Float Parsing
- Valid floats: `"123.45"` → `123.45`
- None/empty strings handled
- Invalid values return `None`

#### Boolean Parsing
- True values: `"true"`, `"True"`, `"1"`, `"yes"`
- False values: `"false"`, `"False"`, `"0"`, `"no"`
- Case-insensitive parsing
- None/empty strings return `None`

#### List Parsing
- Delimited lists: `"item1;item2;item3"` → `["item1", "item2", "item3"]`
- Whitespace handling: `"item1 ; item2"` → `["item1", "item2"]`
- Empty/None → `[]`
- Custom delimiter support

#### Enum Parsing
- Case-insensitive matching: `"CITY"` → `SewerType.CITY`
- Invalid values return `None`
- None/empty strings return `None`

## JsonEnrichmentRepository Tests

### Loading Tests (TestJsonEnrichmentRepositoryLoad)

| Test Name | Purpose | Edge Cases Covered |
|-----------|---------|-------------------|
| `test_load_valid_json` | Load valid JSON with enrichment data | Basic happy path |
| `test_load_empty_json` | Handle empty JSON object `{}` | Empty data |
| `test_load_invalid_json` | Error on malformed JSON | JSON parsing errors |
| `test_load_missing_file_creates_template` | Create template when file missing | Auto-initialization |
| `test_load_for_property_found` | Lookup enrichment by address | Key-based access |
| `test_load_for_property_not_found` | Handle missing property | Null safety |
| `test_load_for_property_uses_cache` | Verify caching works | Performance |

**Key Features Tested:**
- JSON parsing and validation
- Both list and dict JSON formats
- Template auto-creation for missing files
- Property-level enrichment lookup
- Caching mechanism

### Saving Tests (TestJsonEnrichmentRepositorySave)

| Test Name | Purpose | Edge Cases Covered |
|-----------|---------|-------------------|
| `test_save_enrichment` | Write enrichment data to JSON | Basic write/read roundtrip |
| `test_save_creates_parent_directory` | Auto-create nested directories | Path creation |
| `test_save_empty_enrichment` | Save empty enrichment dict | Edge case: no data |

### Enrichment Application Tests (TestJsonEnrichmentRepositoryApplyEnrichment)

| Test Name | Purpose | Edge Cases Covered |
|-----------|---------|-------------------|
| `test_apply_enrichment_to_property` | Apply cached enrichment to property | Cache-based enrichment |
| `test_apply_enrichment_with_dict` | Apply dict-based enrichment directly | Direct enrichment |
| `test_apply_enrichment_no_match` | Handle missing enrichment data | Null safety |
| `test_apply_enrichment_updates_property` | Verify field updates | Mutation validation |

**Key Features Tested:**
- Enrichment data application to properties
- Both cache-based and dict-based application
- Field mutation and updates
- Graceful handling of missing enrichment

### Serialization Tests (TestJsonEnrichmentRepositorySerialization)

| Test Name | Purpose | Edge Cases Covered |
|-----------|---------|-------------------|
| `test_dict_to_enrichment` | Convert dict to EnrichmentData object | Deserialization |
| `test_enrichment_to_dict` | Convert EnrichmentData to dict | Serialization |
| `test_load_both_list_and_dict_formats` | Support both JSON formats | Format flexibility |

## Integration Tests

### Cross-Repository Tests (TestRepositoryIntegration)

| Test Name | Purpose |
|-----------|---------|
| `test_csv_and_json_together` | Load CSV properties and apply JSON enrichment |
| `test_property_round_trip` | Full cycle: CSV → Property → CSV with modifications |

## Test Fixtures

### CSV Fixtures

| Fixture | Purpose | Characteristics |
|---------|---------|-----------------|
| `temp_csv_file` | Valid CSV with 2 properties | Properly quoted addresses, all columns |
| `temp_csv_empty` | CSV with headers only | No data rows |
| `temp_csv_missing_columns` | CSV missing required columns | Schema validation trigger |
| `temp_csv_malformed` | CSV with malformed numeric data | Graceful degradation |

### JSON Fixtures

| Fixture | Purpose | Characteristics |
|---------|---------|-----------------|
| `temp_json_file` | Valid JSON with 2 properties | List format with full data |
| `temp_json_empty` | Empty JSON object `{}` | No enrichment data |
| `temp_json_invalid` | Malformed JSON string | JSON parsing error trigger |

### Reused Fixtures

- `sample_property` - Valid property with all fields
- `sample_property_minimal` - Property with only required fields
- `sample_enrichment_data` - EnrichmentData object

## Coverage Report

```
Name                                                    Stmts   Miss  Cover
-------------------------------------------------------------------------------------
src/phx_home_analysis/repositories/__init__.py              4      0   100%
src/phx_home_analysis/repositories/base.py                30      7    77%
src/phx_home_analysis/repositories/csv_repository.py     105      9    91%
src/phx_home_analysis/repositories/json_repository.py     84     10    88%
-------------------------------------------------------------------------------------
TOTAL                                                    223     26    88%
```

### Coverage by Module

- **csv_repository.py**: 91% - Excellent coverage of main load/save paths
- **json_repository.py**: 88% - Strong coverage of enrichment operations
- **base.py**: 77% - Abstract base class with some untested paths
- **__init__.py**: 100% - All exports tested

## Execution Results

```
========================= 50 passed in 0.27s ==========================
```

All tests pass with no warnings or errors.

## Test Data

### CSV Test Data

Sample CSV content with properly quoted addresses:

```csv
street,city,state,zip,price,price_num,beds,baths,sqft,price_per_sqft,full_address
"123 Main St","Phoenix","AZ","85001","$475000",475000,4,2.0,2200,215.9,"123 Main St, Phoenix, AZ 85001"
```

### JSON Test Data

Sample enrichment data in list format:

```json
[
  {
    "full_address": "123 Main St, Phoenix, AZ 85001",
    "lot_sqft": 9500,
    "year_built": 2010,
    "garage_spaces": 2,
    "sewer_type": "city",
    "tax_annual": 4200,
    "hoa_fee": 0,
    "commute_minutes": 25,
    "school_district": "Phoenix Union",
    "school_rating": 7.5
  }
]
```

## Running the Tests

### Run all tests
```bash
pytest tests/unit/test_repositories.py -v
```

### Run with coverage
```bash
pytest tests/unit/test_repositories.py --cov=src.phx_home_analysis.repositories --cov-report=term-missing
```

### Run specific test class
```bash
pytest tests/unit/test_repositories.py::TestCsvPropertyRepositoryLoad -v
```

### Run specific test
```bash
pytest tests/unit/test_repositories.py::TestCsvPropertyRepositoryLoad::test_load_valid_csv -v
```

## Key Testing Patterns

### 1. Temporary File Fixtures
- Uses pytest's `tmp_path` fixture for isolated file I/O
- Fixtures auto-cleanup after tests
- Files are properly quoted for CSV to handle addresses with commas

### 2. Error Scenario Testing
- Validates `DataLoadError` and `DataSaveError` exceptions
- Tests missing files, invalid formats, malformed data
- Verifies error messages are descriptive

### 3. Caching Validation
- Tests that cache is populated after first load
- Verifies subsequent calls use cached data
- Validates cache behavior with renamed files

### 4. Round-trip Testing
- Saves properties and reloads them
- Verifies data integrity through write/read cycle
- Catches serialization/deserialization issues

### 5. Edge Case Coverage
- Empty datasets (no properties/enrichment)
- Missing optional fields
- Malformed numeric data
- Various boolean representations
- Case-insensitive enum parsing

## Notes

1. **CSV Quoting**: Addresses with commas must be quoted in CSV to prevent parsing errors
2. **Parsing Robustness**: All parsing methods gracefully handle invalid data by returning `None`
3. **Auto-Template**: JSON repository creates template file if missing
4. **Caching Strategy**: Both repositories use caching for performance
5. **NotImplementedError**: CSV repository intentionally doesn't support single-property saves

## Future Improvements

Potential areas for additional testing:
- Concurrent file access scenarios
- Large file performance testing
- Character encoding edge cases (non-ASCII characters)
- Disk space exhaustion scenarios
- File permission errors
- Lock contention under concurrent loads
