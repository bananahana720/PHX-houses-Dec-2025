# County Data Overwrite Protection

**Date:** 2025-12-01
**Status:** Implemented and Tested

## Summary

Added conflict detection and protection logic to `scripts/extract_county_data.py` to prevent the county API from overwriting manually-researched property data without warning.

## Problem

The county data extraction script was silently overwriting all existing enrichment data, including values that were manually researched by the user. This could result in loss of valuable manual research work.

## Solution

Implemented a 3-tier protection system:

### 1. Source-Based Protection

Fields with these source markers are **never overwritten**:
- `manual`
- `manual_research`
- `user`
- `web_research`

Example:
```json
{
  "lot_sqft": 8000,
  "lot_sqft_source": "manual_research"
}
```
**Result:** County value of 8712 will NOT overwrite the manual value of 8000.

### 2. Conflict Detection

When county data differs from existing non-manual data:
- **Logs the change** at INFO level
- **Updates with county data** (county is authoritative for non-manual sources)
- **Tracks the conflict** in the conflict report

Example:
```
INFO: lot_sqft: Updating 8000 → 8712 (existing source: listing)
```

### 3. Comprehensive Reporting

At the end of extraction, displays:
- Count of preserved manual fields
- Count of updated fields (county override)
- Count of new fields added
- Detailed list of all preserved manual fields
- Sample of updated conflicts (up to 10)

## Implementation Details

### New Function: `should_update_field()`

```python
def should_update_field(
    entry: dict,
    field_name: str,
    county_value: any,
    logger: logging.Logger,
) -> tuple[bool, str]:
    """Determine if a field should be updated with county data.

    Returns: (should_update: bool, reason: str)
    """
```

**Logic:**
1. Check if field has a `*_source` marker for manual research → Preserve
2. Check if no existing value → Update
3. Check if values match → Skip (no change needed)
4. Otherwise → Update and log the change

### Modified Function: `merge_parcel_into_enrichment()`

**Changes:**
- Now returns `tuple[dict, dict]` instead of just `dict`
- Second return value is a conflict report with:
  - `preserved_manual`: List of fields preserved due to manual research
  - `updated`: List of fields updated with county data
  - `skipped_no_change`: List of fields where values matched
  - `new_fields`: List of fields that were newly added

### Modified Function: `print_summary()`

**Changes:**
- Now accepts `all_conflicts: dict` parameter
- Displays comprehensive conflict report
- Shows preserved manual fields in detail
- Shows sample of updated conflicts

## Testing

Created `test_conflict_detection.py` with comprehensive test cases:

### Test Coverage

1. **Manual research preservation** - Verifies manual data is never overwritten
2. **Web research preservation** - Verifies web research data is protected
3. **No existing value** - Verifies new fields are added
4. **Values match** - Verifies no unnecessary updates
5. **County override (non-manual)** - Verifies county data wins for non-manual sources
6. **County override (no source)** - Verifies county data wins when no source specified
7. **New property** - Verifies all fields added for new properties
8. **Update-only mode** - Verifies `--update-only` flag behavior
9. **Multiple conflicts** - Verifies complex scenarios with multiple field types

### Test Results

```
✓ All tests passed successfully!
```

All 9 test scenarios pass, demonstrating:
- Manual research is always preserved
- County data properly overrides non-manual sources
- Conflicts are properly tracked and reported
- Update-only mode works correctly

## Usage

### Run with protection (default)

```bash
python scripts/extract_county_data.py --all
```

**Behavior:**
- Preserves manual research
- Logs all conflicts
- Shows conflict report at end

### Run in update-only mode

```bash
python scripts/extract_county_data.py --all --update-only
```

**Behavior:**
- Only fills missing fields (value is `None`)
- Never overwrites existing values (manual or otherwise)

### Run in dry-run mode

```bash
python scripts/extract_county_data.py --all --dry-run
```

**Behavior:**
- Shows what would be extracted
- Shows what would be updated
- Does NOT save changes

## Example Output

### Conflict Report Sample

```
============================================================
Conflict Report
============================================================
Fields preserved (manual research): 2
Fields updated (county override): 5
New fields added: 3

Manually researched fields preserved:

  4732 W Davis Rd, Glendale, AZ 85306:
    - lot_sqft: kept 8000 (county had 8712)
    - sewer_type: kept city (county had septic)

Fields updated (county data authoritative):

  2353 W Tierra Buena Ln, Phoenix, AZ 85023:
    - year_built: 1980 → 1979
    - garage_spaces: 1 → 2

  2344 W Marconi Ave, Phoenix, AZ 85023:
    - tax_annual: 1500 → 1645
```

## Benefits

1. **Data Integrity** - Manual research is never lost
2. **Transparency** - All conflicts are logged and reported
3. **Audit Trail** - Clear visibility into what changed and why
4. **Flexibility** - `--update-only` mode for conservative updates
5. **Safety** - `--dry-run` mode for previewing changes

## Related Files

- `scripts/extract_county_data.py` - Main implementation
- `test_conflict_detection.py` - Test suite
- `src/phx_home_analysis/config/settings.py` - Added missing `datetime` import (bug fix)

## Notes

- The protection logic checks for `*_source` fields (e.g., `lot_sqft_source`)
- Manual research sources: `manual`, `manual_research`, `user`, `web_research`
- County data is authoritative for **non-manual** sources
- Coordinate fields (`latitude`, `longitude`) follow the same protection logic

## Future Enhancements

Potential improvements:
1. Add `--force` flag to override manual research if needed
2. Add conflict resolution prompts (interactive mode)
3. Save conflict report to a JSON file for auditing
4. Add email/notification when manual data conflicts detected
