# Repository Unit Tests

This directory contains comprehensive unit tests for the data access layer repositories.

## File Structure

- **test_repositories.py** (729 lines) - Main test suite for CSV and JSON repositories

## Quick Start

### Run all repository tests
```bash
pytest tests/unit/test_repositories.py -v
```

### Run with coverage
```bash
pytest tests/unit/test_repositories.py --cov=src.phx_home_analysis.repositories
```

### Run specific test class
```bash
pytest tests/unit/test_repositories.py::TestCsvPropertyRepositoryLoad -v
```

## Test Statistics

- **Total Tests**: 50
- **Test Classes**: 8
- **Code Coverage**: 88%
- **Status**: All passing

### Test Breakdown by Class

1. **TestCsvPropertyRepositoryLoad** - 9 tests
   - CSV file loading
   - Address lookup
   - Caching behavior
   - Error handling

2. **TestCsvPropertyRepositorySave** - 6 tests
   - CSV file writing
   - Directory creation
   - Data round-trip
   - Configuration validation

3. **TestCsvPropertyRepositoryParsing** - 16 tests
   - Integer, float, boolean parsing
   - List and enum parsing
   - Edge case handling

4. **TestJsonEnrichmentRepositoryLoad** - 7 tests
   - JSON file loading
   - Template creation
   - Property lookup
   - Caching behavior

5. **TestJsonEnrichmentRepositorySave** - 3 tests
   - JSON file writing
   - Directory creation
   - Empty data handling

6. **TestJsonEnrichmentRepositoryApplyEnrichment** - 4 tests
   - Enrichment application
   - Field updates
   - Null safety

7. **TestJsonEnrichmentRepositorySerialization** - 3 tests
   - Serialization/deserialization
   - Format flexibility

8. **TestRepositoryIntegration** - 2 tests
   - Cross-repository workflows
   - Data consistency

## Coverage Details

### CsvPropertyRepository
- **Coverage**: 91%
- **Untested paths**: Error handling edge cases (IOError line 51, OSError lines 101-102)
- **Strengths**: All main code paths tested, parsing functions fully covered

### JsonEnrichmentRepository
- **Coverage**: 88%
- **Untested paths**: Template creation failures (lines 249-252), partial error paths
- **Strengths**: All critical paths tested, enrichment application fully covered

## Key Testing Features

### 1. Fixture-Based Testing
- Temporary files created with `tmp_path` fixture
- Automatic cleanup after tests
- Properly quoted CSV data for comma-separated addresses

### 2. Error Scenario Coverage
- Missing files → `DataLoadError`
- Malformed JSON → `DataLoadError`
- Invalid CSV schema → `DataLoadError`
- Missing output path → `DataSaveError`
- Invalid numeric data → graceful `None` return

### 3. Data Type Parsing
- **Integers**: Valid, invalid, None/empty handling
- **Floats**: Valid, invalid, None/empty handling
- **Booleans**: Multiple formats (true/false, 1/0, yes/no)
- **Lists**: Delimited strings with whitespace handling
- **Enums**: Case-insensitive matching

### 4. Caching Validation
- Cache populated after load
- Subsequent calls use cache
- Cache integrity with file changes

### 5. Round-Trip Testing
- CSV: Load → Save → Reload
- JSON: Load → Apply → Save → Reload

## Test Execution Flow

```
test_repositories.py
├── Fixtures (temp files, sample data)
├── CsvPropertyRepository Tests
│   ├── Load operations (9 tests)
│   ├── Save operations (6 tests)
│   └── Parsing helpers (16 tests)
├── JsonEnrichmentRepository Tests
│   ├── Load operations (7 tests)
│   ├── Save operations (3 tests)
│   ├── Enrichment application (4 tests)
│   └── Serialization (3 tests)
└── Integration Tests (2 tests)
```

## Fixtures Overview

### CSV Fixtures
- `temp_csv_file` - Valid data (2 properties)
- `temp_csv_empty` - Headers only
- `temp_csv_missing_columns` - Missing required columns
- `temp_csv_malformed` - Invalid numeric data

### JSON Fixtures
- `temp_json_file` - Valid data (2 properties)
- `temp_json_empty` - Empty object
- `temp_json_invalid` - Malformed JSON

### Reused Fixtures (from conftest.py)
- `sample_property` - Valid property
- `sample_property_minimal` - Minimal property
- `sample_enrichment_data` - Enrichment data

## Assertion Patterns

### File Operations
```python
assert csv_file.exists()
assert csv_output.exists()
```

### Data Loading
```python
properties = repo.load_all()
assert len(properties) == 2
assert properties[0].street == "123 Main St"
```

### Error Handling
```python
with pytest.raises(DataLoadError, match="CSV file not found"):
    repo.load_all()
```

### Caching
```python
assert repo._properties_cache is None
properties = repo.load_all()
assert repo._properties_cache is not None
```

### Round-Trip
```python
repo1.save_all([property_obj])
repo2.load_all()  # from same file
# Verify data integrity
```

## Performance Notes

- **Execution Time**: ~0.2 seconds for full suite
- **Memory Usage**: Minimal (temp files auto-cleanup)
- **Scalability**: Tests handle 0 to 2+ properties efficiently

## Edge Cases Covered

1. **Empty Data**
   - CSV with headers only
   - JSON with empty object
   - Empty property lists

2. **Missing Data**
   - Non-existent files (create template for JSON)
   - Missing optional fields (return None)
   - Missing properties in enrichment

3. **Invalid Data**
   - Malformed JSON
   - Invalid numeric values
   - Mismatched field types
   - Missing required columns

4. **Special Cases**
   - Addresses with commas (require CSV quoting)
   - Whitespace handling in parsing
   - Case-insensitive enum matching
   - Multiple boolean representations

## Integration Points

These tests validate the repositories work with:
- **Domain Entities**: Property, EnrichmentData
- **Domain Enums**: SewerType, SolarStatus, Orientation, Tier
- **Value Objects**: Used in property deserialization
- **Error Types**: DataLoadError, DataSaveError

## Maintenance Guidelines

1. **Adding New Tests**
   - Follow existing class organization
   - Use temp fixtures for file I/O
   - Test both happy path and error cases
   - Include docstrings

2. **Updating Fixtures**
   - Keep fixture names descriptive
   - Ensure auto-cleanup with tmp_path
   - Document fixture purpose

3. **CSV Format Changes**
   - Remember to quote addresses with commas
   - Update temp_csv_file fixture
   - Add regression tests for new fields

4. **JSON Format Changes**
   - Test both list and dict formats
   - Update temp_json_file fixture
   - Validate serialization round-trip

## Known Limitations

1. **Thread Safety**: Tests don't cover concurrent access
2. **Disk Space**: No exhaustion scenario testing
3. **Character Encoding**: Limited to UTF-8
4. **Large Files**: Performance not tested above 2 properties

## Deprecation Notes

None currently. All tested code paths are maintained.

## Related Documentation

- `docs/TEST_REPOSITORIES_SUMMARY.md` - Detailed test documentation
- `src/phx_home_analysis/repositories/` - Implementation source
- `tests/conftest.py` - Shared test fixtures
