---
last_updated: 2025-12-04
updated_by: agent
staleness_hours: 24
flags: []
---

# tests/unit/utils

## Purpose

Unit tests for utility functions covering address normalization and matching logic. Validates address comparison used in property deduplication and enrichment merge, ensuring robust address matching across CSV/JSON sources with various formatting variations (case, punctuation, spacing).

## Contents

| Path | Purpose |
|------|---------|
| `__init__.py` | Package marker (empty) |
| `test_address_utils.py` | Tests for normalize_address() and addresses_match() functions (2 test classes, ~15 tests) |

## Test Classes

### TestNormalizeAddress (test_address_utils.py:11-62)
**Focus:** Address normalization function behavior

**Test Methods (9+):**
- `test_lowercase_conversion()` - "123 MAIN ST" → "123 main st", "Phoenix, AZ" → "phoenix az"
- `test_comma_removal()` - "Phoenix, AZ" → "phoenix az"
- `test_period_removal()` - "123 Main St." → "123 main st", "Dr. Martin Luther King Jr. Blvd" → "dr martin luther king jr blvd"
- `test_strip_whitespace()` - Remove leading/trailing spaces and tabs
- `test_collapse_multiple_spaces()` - "123   Main    St" → "123 main st"
- `test_full_normalization()` - "  123 Main St., Phoenix, AZ 85001  " → "123 main st phoenix az 85001"
- `test_empty_string()` - "" → ""
- `test_whitespace_only()` - "   " → "", "\t\n" → ""
- `test_complex_address()` - "123 N. Main St., Apt. 4B, Phoenix, AZ 85001" → "123 n main st apt 4b phoenix az 85001"
- `test_mixed_case_preservation_after_lowering()` - "McDonalds Rd" → "mcdonalds rd"

**Normalization Rules:**
1. Convert to lowercase
2. Remove commas (,)
3. Remove periods (.)
4. Strip leading/trailing whitespace
5. Collapse multiple spaces to single space

### TestAddressesMatch (test_address_utils.py:64-110)
**Focus:** Two-address comparison for robust matching

**Test Methods (6+):**
- `test_case_insensitive_matching()` - "123 MAIN ST" matches "123 main st"
- `test_punctuation_insensitive_matching()` - "123 Main St." matches "123 Main St"
- `test_whitespace_tolerance()` - Handles extra spaces, tabs, newlines
- `test_full_address_variations()` - Multiple formatting styles match correctly
- `test_non_matching_addresses()` - "123 Main St" does NOT match "456 Oak Ave"
- `test_empty_strings()` - Edge case: both empty strings should match

**Matching Logic:**
- Normalize both addresses using normalize_address()
- Compare normalized forms for equality
- Case-insensitive by design (normalization lowercases)
- Punctuation-insensitive by design (normalization removes punctuation)

## Design Patterns

### Canonical Form Normalization
- **Purpose:** Create consistent representation for address matching
- **Applied to:** Property lookups, deduplication, enrichment merge
- **Benefits:** Handles formatting variations (case, punctuation, spacing)
- **Trade-offs:** Loses original punctuation/spacing (acceptable for matching)

### Two-Function Architecture
- **normalize_address()** - Individual address cleanup (reusable)
- **addresses_match()** - Direct two-address comparison (convenience wrapper)
- **Pattern:** normalize_address(a) == normalize_address(b) under the hood

### Edge Case Coverage
- Empty strings (return empty)
- Whitespace-only strings (become empty)
- Multiple spaces (collapse to single)
- Complex addresses with abbreviations (handled uniformly)
- Mixed case (all converted to lowercase)

## Testing Strategy

### Unit Test Isolation
- Tests are pure functions (no I/O, no external dependencies)
- Fast execution (~1ms per test)
- Deterministic results (no randomness, no timing)
- Can run in any order, parallel execution safe

### Realistic Test Data
- Real Phoenix address formats
- Common abbreviations (St., Ave., Dr., etc.)
- Apartment/suite numbers (Apt. 4B)
- Mixed case names (McDonalds)
- Full addresses with city, state, ZIP

### Boundary & Edge Cases
- Empty strings
- Whitespace-only strings
- Single space (should remain)
- Multiple consecutive spaces
- Tabs and newlines in input
- Periods and commas scattered throughout
- Addresses without punctuation

### Assertion Patterns
- Exact string equality (not regex or contains)
- Unidirectional matches (a=b and b=a both tested)
- Non-matching pairs validated to differ

## Key Learnings

### Address Normalization Design
- **Canonical form:** lowercase + no punctuation + single spaces
- **Case-insensitive matching:** Essential for handling title case, ALL CAPS, mixed case
- **Punctuation-agnostic:** Critical for handling abbreviations (St., St, ST) and commas (Phoenix, AZ vs Phoenix AZ)
- **Whitespace normalization:** Handles copy-paste variations and manual data entry errors

### Integration Points
- **Deduplication** uses addresses_match() to detect duplicate records across sources
- **Enrichment merge** uses normalized_address for robust property lookup
- **Repository queries** use normalize_address for case-insensitive address lookups
- **Services** (quality, lifecycle) apply normalization to ensure consistent matching

### Test Coverage Observations
- **Simple and effective:** Two functions, ~15 tests cover all important cases
- **No external dependencies:** Tests are purely functional
- **Reusable logic:** normalize_address() called by multiple services and repositories
- **Well-documented:** Docstrings provide clear specifications

## Tasks

- [x] Assess address utility test coverage `P:H`
- [x] Document normalization patterns and edge cases `P:H`
- [ ] Add file_ops.py tests for atomic_json_save and backup cleanup `P:M`
- [ ] Add property-based testing with Hypothesis for normalization robustness `P:L`
- [ ] Expand tests for international address formats (future enhancement) `P:L`

## Refs

- `normalize_address()` implementation: `src/phx_home_analysis/utils/address_utils.py:10-46`
- `addresses_match()` implementation: `src/phx_home_analysis/utils/address_utils.py:49-66`
- Normalization usage in deduplication: `src/phx_home_analysis/validation/deduplication.py:31-60`
- Repository usage: `src/phx_home_analysis/repositories/json_repository.py:124-144`
- TestNormalizeAddress class: `test_address_utils.py:11-62`
- TestAddressesMatch class: `test_address_utils.py:64-110`

## Deps

← Imports from:
- `src.phx_home_analysis.utils.address_utils` (normalize_address, addresses_match)
- Standard library: none (pytest provides testing framework)

→ Imported by:
- pytest (test framework and execution)
- CI/CD pipeline (must pass before merge)
- Pre-commit hooks (optional validation)

---

**Focus Areas**: Address normalization, case-insensitive matching, punctuation handling, edge case coverage

**Test Count**: 2 test classes, ~15 test methods

**Execution Time**: ~5-10ms total

**Coverage**: 100% of utility functions (only 2 functions, both trivial)
