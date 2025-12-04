# E1.S2: Property Data Storage Layer

**Status:** Ready for Development
**Epic:** Epic 1 - Foundation & Data Infrastructure
**Priority:** P0
**Estimated Points:** 5
**Dependencies:** E1.S1 (Configuration System Setup)
**Functional Requirements:** FR7

## User Story

As a system administrator, I want JSON-based property data storage with atomic writes, so that raw data is preserved separately from derived scores and survives crashes.

## Acceptance Criteria

### AC1: Normalized Address Field
**Given** a property record with `full_address` like "123 Main St, Phoenix, AZ 85001"
**When** the record is saved to `enrichment_data.json`
**Then** the record includes both `full_address` (original) and `normalized_address` (lowercase, no punctuation)

### AC2: Normalized Address Lookup
**Given** a lookup request for "123 Main St, Phoenix, AZ 85001"
**When** `load_for_property()` is called
**Then** the lookup uses normalized address matching (case-insensitive, punctuation-removed)
**And** matches records regardless of original address formatting variations

### AC3: Backup Before Write (Already Implemented)
**Given** an existing `enrichment_data.json` file
**When** `save_all()` is called
**Then** a timestamped backup is created at `{stem}.{timestamp}.bak.json`
**And** the backup is created before any modifications

### AC4: Atomic Writes (Already Implemented)
**Given** a write operation to `enrichment_data.json`
**When** the write is in progress
**Then** the operation uses temp file + atomic rename pattern
**And** on crash, either the old file is intact or the new file is complete (never partial)

### AC5: Restore from Backup
**Given** a corrupted or missing `enrichment_data.json`
**And** a valid backup file exists (e.g., `enrichment_data.20251203_143000.bak.json`)
**When** `restore_from_backup()` is called
**Then** the most recent valid backup is restored to `enrichment_data.json`
**And** the operation logs the restore action

### AC6: Raw vs Derived Data Separation
**Given** a property record in `enrichment_data.json`
**When** viewing the record structure
**Then** raw data fields (from sources) are distinguishable from derived fields (computed)
**And** each field optionally includes a `_source` or `_derived` suffix field for lineage

### AC7: List Format Preservation (Already Implemented)
**Given** property data operations
**When** reading or writing `enrichment_data.json`
**Then** the file format remains a LIST of property dictionaries (not keyed by address)

## Technical Tasks

### Task 1: Add `normalized_address` Field to EnrichmentData Entity
**File:** `src/phx_home_analysis/domain/entities.py:388-420`
**Action:** Add new field to the `EnrichmentData` dataclass

**Implementation:**
```python
@dataclass
class EnrichmentData:
    """Enrichment data for a property from external research."""

    full_address: str
    normalized_address: str | None = None  # NEW: Lowercase, no punctuation

    # ... existing fields unchanged ...
```

**Acceptance Criteria:**
- [ ] `normalized_address: str | None = None` field added after `full_address`
- [ ] Field is optional (defaults to None for backward compatibility)
- [ ] Type annotations are correct

### Task 2: Implement Address Normalization Utility Function
**File:** `src/phx_home_analysis/utils/address_utils.py` (NEW)
**Lines:** ~40

**Implementation:**
```python
"""Address normalization utilities for consistent property lookups."""

import re


def normalize_address(address: str) -> str:
    """Normalize address for consistent lookups.

    Applies normalization rules from epic spec:
    - Convert to lowercase
    - Remove commas
    - Remove periods
    - Strip leading/trailing whitespace
    - Collapse multiple spaces to single space

    Args:
        address: Raw address string (e.g., "123 Main St., Phoenix, AZ 85001")

    Returns:
        Normalized address (e.g., "123 main st phoenix az 85001")

    Example:
        >>> normalize_address("123 Main St., Phoenix, AZ 85001")
        '123 main st phoenix az 85001'
        >>> normalize_address("  456 ELM AVE,  Mesa,  AZ  ")
        '456 elm ave mesa az'
    """
    if not address:
        return ""

    # Core normalization per epic spec
    normalized = address.lower()
    normalized = normalized.replace(",", "")
    normalized = normalized.replace(".", "")
    normalized = normalized.strip()

    # Additional cleanup: collapse multiple spaces
    normalized = re.sub(r'\s+', ' ', normalized)

    return normalized


def addresses_match(address1: str, address2: str) -> bool:
    """Check if two addresses match after normalization.

    Args:
        address1: First address to compare
        address2: Second address to compare

    Returns:
        True if normalized addresses are equal

    Example:
        >>> addresses_match("123 Main St.", "123 main st")
        True
        >>> addresses_match("456 Elm Ave", "789 Oak Blvd")
        False
    """
    return normalize_address(address1) == normalize_address(address2)
```

**Acceptance Criteria:**
- [ ] `normalize_address()` function implements spec: `address.lower().replace(",", "").replace(".", "").strip()`
- [ ] `addresses_match()` helper for comparison
- [ ] Docstrings with examples
- [ ] Handles empty strings gracefully

### Task 3: Update `_dict_to_enrichment()` to Compute Normalized Address
**File:** `src/phx_home_analysis/repositories/json_repository.py:238-267`
**Action:** Modify conversion to compute normalized_address if not present

**Implementation:**
```python
def _dict_to_enrichment(self, data: dict) -> EnrichmentData:
    """Convert dictionary to EnrichmentData object."""
    from ..utils.address_utils import normalize_address

    full_address = data['full_address']
    # Compute normalized_address if not in data
    normalized = data.get('normalized_address') or normalize_address(full_address)

    return EnrichmentData(
        full_address=full_address,
        normalized_address=normalized,  # NEW
        lot_sqft=data.get('lot_sqft'),
        # ... rest unchanged ...
    )
```

**Acceptance Criteria:**
- [ ] Computes `normalized_address` from `full_address` if not present in data
- [ ] Uses existing `normalized_address` from data if present
- [ ] Imports `normalize_address` from utils

### Task 4: Update `_enrichment_to_dict()` to Include Normalized Address
**File:** `src/phx_home_analysis/repositories/json_repository.py:269-298`
**Action:** Add normalized_address to serialized output

**Implementation:**
```python
def _enrichment_to_dict(self, enrichment: EnrichmentData) -> dict:
    """Convert EnrichmentData object to dictionary for JSON serialization."""
    from ..utils.address_utils import normalize_address

    # Ensure normalized_address is present
    normalized = enrichment.normalized_address or normalize_address(enrichment.full_address)

    return {
        'full_address': enrichment.full_address,
        'normalized_address': normalized,  # NEW
        'lot_sqft': enrichment.lot_sqft,
        # ... rest unchanged ...
    }
```

**Acceptance Criteria:**
- [ ] `normalized_address` included in dict output
- [ ] Computes from `full_address` if not set on entity

### Task 5: Enhance `load_for_property()` with Normalized Lookup
**File:** `src/phx_home_analysis/repositories/json_repository.py:108-123`
**Action:** Change lookup to use normalized address matching

**Implementation:**
```python
def load_for_property(self, full_address: str) -> EnrichmentData | None:
    """Load enrichment data for a specific property using normalized address matching.

    Args:
        full_address: The address to look up (will be normalized).

    Returns:
        EnrichmentData object if found, None otherwise.

    Raises:
        DataLoadError: If data cannot be loaded.
    """
    from ..utils.address_utils import normalize_address

    if self._enrichment_cache is None:
        self.load_all()

    if not self._enrichment_cache:
        return None

    # Normalize the lookup address
    normalized_lookup = normalize_address(full_address)

    # Search by normalized address
    for enrichment in self._enrichment_cache.values():
        if enrichment.normalized_address == normalized_lookup:
            return enrichment

    # Fallback: exact full_address match (backward compatibility)
    return self._enrichment_cache.get(full_address)
```

**Acceptance Criteria:**
- [ ] Normalizes input address before lookup
- [ ] Searches cache by `normalized_address` field
- [ ] Falls back to exact `full_address` match for backward compatibility
- [ ] Returns None if not found

### Task 6: Add `restore_from_backup()` Method
**File:** `src/phx_home_analysis/repositories/json_repository.py` (add after `save_all`)
**Lines:** ~60

**Implementation:**
```python
def restore_from_backup(self, backup_path: Path | str | None = None) -> bool:
    """Restore enrichment data from backup file.

    If backup_path is not specified, finds the most recent valid backup
    in the same directory as the main JSON file.

    Args:
        backup_path: Specific backup file to restore from.
            If None, uses most recent backup matching pattern.

    Returns:
        True if restore was successful, False if no valid backup found.

    Raises:
        DataLoadError: If backup file cannot be read or is invalid.

    Example:
        >>> repo = JsonEnrichmentRepository("data/enrichment_data.json")
        >>> if repo.restore_from_backup():
        ...     print("Restored from backup successfully")
    """
    import shutil

    if backup_path is None:
        # Find most recent backup
        backup_pattern = f"{self.json_file_path.stem}.*.bak{self.json_file_path.suffix}"
        backups = sorted(
            self.json_file_path.parent.glob(backup_pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        if not backups:
            logger.warning(f"No backup files found matching {backup_pattern}")
            return False

        backup_path = backups[0]
    else:
        backup_path = Path(backup_path)

    if not backup_path.exists():
        logger.error(f"Backup file not found: {backup_path}")
        return False

    # Validate backup is valid JSON with expected structure
    try:
        with open(backup_path, encoding='utf-8') as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise DataLoadError(f"Invalid backup format: expected list, got {type(data)}")

        # Verify at least one entry has required fields
        if data and not all('full_address' in item for item in data[:5]):
            raise DataLoadError("Backup file missing required 'full_address' field")

    except json.JSONDecodeError as e:
        raise DataLoadError(f"Invalid JSON in backup file: {e}") from e

    # Create backup of current (possibly corrupted) file before restore
    if self.json_file_path.exists():
        corrupted_backup = self.json_file_path.with_suffix('.corrupted.json')
        try:
            shutil.copy2(self.json_file_path, corrupted_backup)
            logger.info(f"Saved corrupted file to: {corrupted_backup}")
        except OSError:
            pass  # Best effort

    # Restore from backup
    shutil.copy2(backup_path, self.json_file_path)
    logger.info(f"Restored from backup: {backup_path}")

    # Invalidate cache to force reload
    self._enrichment_cache = None

    return True
```

**Acceptance Criteria:**
- [ ] Finds most recent backup if path not specified
- [ ] Validates backup is valid JSON with list structure
- [ ] Saves current (corrupted) file before overwriting
- [ ] Restores backup to main file path
- [ ] Invalidates cache after restore
- [ ] Returns True on success, False if no backup found

### Task 7: Add Raw/Derived Data Markers (Optional Enhancement)
**File:** `src/phx_home_analysis/domain/entities.py:388-503`
**Action:** Add documentation distinguishing raw vs derived fields

This is an optional enhancement for this story. The primary approach is documentation-based:

**Implementation:**
```python
@dataclass
class EnrichmentData:
    """Enrichment data for a property from external research.

    Field Categories:
    -----------------
    RAW FIELDS (from external sources):
        - full_address: CSV/user input
        - normalized_address: Computed from full_address
        - lot_sqft, year_built, garage_spaces, sewer_type, tax_annual: County Assessor
        - hoa_fee, school_rating, orientation: Phase 1 extraction
        - kitchen_layout_score, master_suite_score, etc.: Phase 2 image assessment

    DERIVED FIELDS (computed during scoring):
        - Scores are NOT stored in enrichment_data.json
        - Scores are computed at runtime by PropertyScorer
        - This keeps raw data separate from derived values

    Note: The design intentionally does NOT store scores in enrichment_data.json.
    Raw enrichment data is preserved; scores are computed fresh each run.
    """
```

**Acceptance Criteria:**
- [ ] Clear docstring documenting which fields are raw vs derived
- [ ] Confirms scores are NOT stored in enrichment_data.json (by design)

### Task 8: Unit Tests for Address Normalization
**File:** `tests/unit/utils/test_address_utils.py` (NEW)
**Lines:** ~80

**Test Cases:**
```python
import pytest
from phx_home_analysis.utils.address_utils import normalize_address, addresses_match


class TestNormalizeAddress:
    """Tests for address normalization function."""

    def test_lowercase_conversion(self):
        """Address should be converted to lowercase."""
        assert normalize_address("123 MAIN ST") == "123 main st"

    def test_comma_removal(self):
        """Commas should be removed."""
        assert normalize_address("Phoenix, AZ") == "phoenix az"

    def test_period_removal(self):
        """Periods should be removed."""
        assert normalize_address("123 Main St.") == "123 main st"

    def test_strip_whitespace(self):
        """Leading and trailing whitespace should be stripped."""
        assert normalize_address("  123 Main St  ") == "123 main st"

    def test_collapse_multiple_spaces(self):
        """Multiple spaces should collapse to single space."""
        assert normalize_address("123   Main    St") == "123 main st"

    def test_full_normalization(self):
        """Full address normalization with all rules applied."""
        result = normalize_address("  123 Main St., Phoenix, AZ 85001  ")
        assert result == "123 main st phoenix az 85001"

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert normalize_address("") == ""

    def test_none_handling(self):
        """None should be handled gracefully."""
        # Depending on design, could return "" or raise
        with pytest.raises(AttributeError):
            normalize_address(None)


class TestAddressesMatch:
    """Tests for address comparison function."""

    def test_same_address_matches(self):
        """Identical addresses should match."""
        assert addresses_match("123 Main St", "123 Main St") is True

    def test_case_insensitive_match(self):
        """Addresses should match regardless of case."""
        assert addresses_match("123 MAIN ST", "123 main st") is True

    def test_punctuation_insensitive_match(self):
        """Addresses should match regardless of punctuation."""
        assert addresses_match("123 Main St.", "123 Main St") is True

    def test_different_addresses_no_match(self):
        """Different addresses should not match."""
        assert addresses_match("123 Main St", "456 Oak Ave") is False
```

**Acceptance Criteria:**
- [ ] Test lowercase conversion
- [ ] Test comma removal
- [ ] Test period removal
- [ ] Test whitespace stripping
- [ ] Test multiple space collapse
- [ ] Test full address normalization
- [ ] Test addresses_match helper

### Task 9: Unit Tests for Repository Enhancements
**File:** `tests/unit/repositories/test_json_repository.py` (enhance existing or create)
**Lines:** ~120 additional

**Test Cases:**
```python
import pytest
from pathlib import Path
from phx_home_analysis.repositories.json_repository import JsonEnrichmentRepository


class TestNormalizedAddressLookup:
    """Tests for normalized address lookup functionality."""

    def test_load_for_property_exact_match(self, repo_with_data):
        """Exact address match should return enrichment data."""
        result = repo_with_data.load_for_property("123 Main St, Phoenix, AZ 85001")
        assert result is not None
        assert result.full_address == "123 Main St, Phoenix, AZ 85001"

    def test_load_for_property_normalized_match(self, repo_with_data):
        """Normalized address match should return enrichment data."""
        # Data stored as "123 Main St., Phoenix, AZ 85001"
        result = repo_with_data.load_for_property("123 MAIN ST PHOENIX AZ 85001")
        assert result is not None

    def test_load_for_property_case_insensitive(self, repo_with_data):
        """Lookup should be case-insensitive."""
        result = repo_with_data.load_for_property("123 main st, phoenix, az 85001")
        assert result is not None

    def test_load_for_property_not_found(self, repo_with_data):
        """Non-existent address should return None."""
        result = repo_with_data.load_for_property("999 Nonexistent St, Mesa, AZ 85201")
        assert result is None


class TestNormalizedAddressPersistence:
    """Tests for normalized address being persisted."""

    def test_save_includes_normalized_address(self, tmp_path):
        """Saved data should include normalized_address field."""
        repo = JsonEnrichmentRepository(tmp_path / "test.json")
        # ... setup and save ...
        # Verify normalized_address in saved JSON

    def test_load_computes_normalized_if_missing(self, tmp_path):
        """Loading data without normalized_address should compute it."""
        # Write JSON without normalized_address field
        # Load and verify normalized_address is populated


class TestRestoreFromBackup:
    """Tests for backup restore functionality."""

    def test_restore_finds_most_recent_backup(self, repo_with_backups):
        """Should restore from most recent backup when path not specified."""
        result = repo_with_backups.restore_from_backup()
        assert result is True

    def test_restore_specific_backup(self, repo_with_backups, backup_path):
        """Should restore from specified backup path."""
        result = repo_with_backups.restore_from_backup(backup_path)
        assert result is True

    def test_restore_no_backup_returns_false(self, empty_repo):
        """Should return False when no backups exist."""
        result = empty_repo.restore_from_backup()
        assert result is False

    def test_restore_invalidates_cache(self, repo_with_backups):
        """Should invalidate cache after restore."""
        repo_with_backups.load_all()  # Populate cache
        repo_with_backups.restore_from_backup()
        assert repo_with_backups._enrichment_cache is None

    def test_restore_saves_corrupted_file(self, repo_with_corrupted_main, tmp_path):
        """Should save corrupted file before overwriting."""
        repo_with_corrupted_main.restore_from_backup()
        corrupted = tmp_path / "enrichment_data.corrupted.json"
        assert corrupted.exists()
```

**Acceptance Criteria:**
- [ ] Test normalized lookup with various address formats
- [ ] Test normalized_address persistence in JSON
- [ ] Test restore_from_backup() with various scenarios
- [ ] Test cache invalidation after restore

### Task 10: Integration Test for Crash Recovery
**File:** `tests/integration/test_crash_recovery.py` (NEW)
**Lines:** ~80

**Test Cases:**
```python
import pytest
import json
from pathlib import Path
from phx_home_analysis.repositories.json_repository import JsonEnrichmentRepository


class TestCrashRecoveryIntegration:
    """Integration tests for crash recovery scenarios."""

    def test_recovery_after_corrupt_json(self, tmp_path):
        """System should recover from corrupted JSON file."""
        # Setup: Create valid data and backup
        json_path = tmp_path / "enrichment_data.json"
        valid_data = [{"full_address": "123 Main St, Phoenix, AZ 85001", "lot_sqft": 8500}]

        repo = JsonEnrichmentRepository(json_path)
        repo.save_all({"123 Main St, Phoenix, AZ 85001": EnrichmentData(**valid_data[0])})

        # Simulate corruption
        json_path.write_text("{invalid json content")

        # Recovery
        repo2 = JsonEnrichmentRepository(json_path)
        assert repo2.restore_from_backup() is True

        # Verify recovered data
        recovered = repo2.load_all()
        assert "123 Main St, Phoenix, AZ 85001" in recovered

    def test_recovery_after_missing_file(self, tmp_path):
        """System should recover when main file is missing but backup exists."""
        json_path = tmp_path / "enrichment_data.json"
        backup_path = tmp_path / "enrichment_data.20251203_120000.bak.json"

        # Create only backup
        backup_data = [{"full_address": "456 Oak Ave, Mesa, AZ 85201", "lot_sqft": 9000}]
        backup_path.write_text(json.dumps(backup_data))

        # Recovery
        repo = JsonEnrichmentRepository(json_path)
        assert repo.restore_from_backup() is True
        assert json_path.exists()

    def test_atomic_write_survives_simulated_crash(self, tmp_path):
        """Atomic write pattern should leave valid file after simulated crash."""
        # This test verifies the atomic write implementation by:
        # 1. Creating initial valid file
        # 2. Checking that temp file pattern is used
        # 3. Verifying no partial writes occur
        pass  # Implementation depends on how to simulate crash
```

**Acceptance Criteria:**
- [ ] Test recovery from corrupted JSON
- [ ] Test recovery when main file missing
- [ ] Test atomic write integrity

## Test Plan Summary

### Unit Tests
| Suite | File | Test Count |
|-------|------|------------|
| Address Normalization | `tests/unit/utils/test_address_utils.py` | 10 |
| Repository Enhancements | `tests/unit/repositories/test_json_repository.py` | 12 |

### Integration Tests
| Suite | File | Test Count |
|-------|------|------------|
| Crash Recovery | `tests/integration/test_crash_recovery.py` | 4 |

**Total New Tests:** ~26

## Dependencies

### New Dependencies Required
None - all required packages already installed.

### Existing Dependencies Used
- `shutil` (stdlib) - File copying for backups
- `re` (stdlib) - Regex for address normalization
- `json` (stdlib) - JSON serialization
- `pathlib` (stdlib) - Path operations

### Internal Dependencies
- `src/phx_home_analysis/domain/entities.py` - EnrichmentData entity
- `src/phx_home_analysis/repositories/json_repository.py` - JsonEnrichmentRepository
- `src/phx_home_analysis/utils/file_ops.py` - atomic_json_save (already implemented)

## Definition of Done Checklist

### Implementation
- [ ] `normalized_address` field added to `EnrichmentData` entity
- [ ] `normalize_address()` utility function implemented in `utils/address_utils.py`
- [ ] `addresses_match()` helper function implemented
- [ ] `_dict_to_enrichment()` computes normalized_address
- [ ] `_enrichment_to_dict()` includes normalized_address
- [ ] `load_for_property()` uses normalized address lookup
- [ ] `restore_from_backup()` method implemented
- [ ] Docstrings updated to document raw vs derived field separation

### Testing
- [ ] Unit tests for address normalization pass
- [ ] Unit tests for repository enhancements pass
- [ ] Integration test for crash recovery passes
- [ ] All tests pass: `pytest tests/unit/utils/test_address_utils.py tests/unit/repositories/test_json_repository.py tests/integration/test_crash_recovery.py`

### Quality Gates
- [ ] Type checking passes: `mypy src/phx_home_analysis/utils/address_utils.py src/phx_home_analysis/repositories/json_repository.py src/phx_home_analysis/domain/entities.py`
- [ ] Linting passes: `ruff check src/phx_home_analysis/utils/ src/phx_home_analysis/repositories/ src/phx_home_analysis/domain/`
- [ ] No new warnings introduced
- [ ] Backward compatibility maintained (existing data loads without migration)

### Documentation
- [ ] EnrichmentData docstring documents raw vs derived fields
- [ ] `restore_from_backup()` has comprehensive docstring
- [ ] `normalize_address()` has docstring with examples

## Notes

### Design Decisions

1. **Normalized Address as Field vs Computed Property**: Storing `normalized_address` as a field rather than computing on-the-fly. **Rationale**: Avoids repeated computation during lookups, enables indexing, and makes the normalization explicit in the data.

2. **Backward Compatibility**: `normalized_address` defaults to None, and `_dict_to_enrichment()` computes it if missing. **Rationale**: Existing `enrichment_data.json` files will continue to work without migration.

3. **Fallback to Exact Match**: `load_for_property()` falls back to exact `full_address` match if normalized lookup fails. **Rationale**: Handles edge cases where normalization might differ between versions.

4. **Raw/Derived Separation via Architecture**: Scores are NOT stored in `enrichment_data.json` by design. **Rationale**: Keeping raw data separate from derived values ensures data integrity and allows re-scoring with updated algorithms.

5. **Backup Validation Before Restore**: `restore_from_backup()` validates the backup is valid JSON with expected structure before restoring. **Rationale**: Prevents restoring from a corrupted backup.

### Current Implementation Status

**Already Implemented (in json_repository.py):**
- LIST format handling ✓
- Atomic writes via temp file + rename ✓
- Timestamped backup creation ✓
- CRUD operations (load_all, save_all, load_for_property) ✓

**Gaps to Address (this story):**
- `normalized_address` field missing from entity
- Lookup uses exact match, not normalized
- No restore-from-backup capability
- Raw/derived separation is implicit, needs documentation

### File Locations

| File | Purpose | Lines to Modify |
|------|---------|----------------|
| `src/phx_home_analysis/domain/entities.py` | Add normalized_address field | ~395 |
| `src/phx_home_analysis/utils/address_utils.py` | NEW: Address normalization | ~40 |
| `src/phx_home_analysis/repositories/json_repository.py` | Enhance lookup + add restore | 108-123, 238-298, new method |
| `tests/unit/utils/test_address_utils.py` | NEW: Unit tests | ~80 |
| `tests/unit/repositories/test_json_repository.py` | Enhance tests | ~120 |
| `tests/integration/test_crash_recovery.py` | NEW: Integration test | ~80 |

### Related Stories

**Depends On:**
- E1.S1: Configuration System Setup (for consistent config loading)

**Blocks:**
- E1.S3: Data Provenance and Lineage Tracking (builds on raw/derived separation)
- E2.S*: Any story that reads/writes enrichment data

### Risk Assessment

**Risk 1: Address Normalization Edge Cases**
- **Likelihood:** Medium
- **Impact:** Low (lookup fallback protects against mismatches)
- **Mitigation:** Comprehensive test cases, fallback to exact match

**Risk 2: Backward Compatibility**
- **Likelihood:** Low
- **Impact:** Medium (could break existing workflows)
- **Mitigation:** Optional field with computed default, fallback lookup

## Implementation Order

1. **Phase 1: Entity & Utility** (foundation)
   - Task 1: Add normalized_address to EnrichmentData
   - Task 2: Create address_utils.py with normalize_address()
   - Task 8: Unit tests for address normalization

2. **Phase 2: Repository Enhancement** (core functionality)
   - Task 3: Update _dict_to_enrichment()
   - Task 4: Update _enrichment_to_dict()
   - Task 5: Enhance load_for_property()
   - Task 9: Unit tests for repository

3. **Phase 3: Crash Recovery** (resilience)
   - Task 6: Add restore_from_backup()
   - Task 10: Integration test for crash recovery

4. **Phase 4: Documentation** (completion)
   - Task 7: Document raw vs derived fields

---

**Story Created:** 2025-12-04
**Created By:** PM Agent
**Epic File:** `docs/epics/epic-1-foundation-data-infrastructure.md:24-35`
