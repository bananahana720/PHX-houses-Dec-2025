# Security Fix: SQL/LIKE Injection Vulnerability

**Date:** 2025-12-02
**File:** `src/phx_home_analysis/services/county_data/assessor_client.py`
**Severity:** High
**Status:** FIXED

## Vulnerability Summary

The Maricopa County Assessor API client had SQL/LIKE injection vulnerabilities in two methods that construct ArcGIS WHERE clauses from user-controlled input.

### Affected Code

**Location 1: `_search_arcgis()` method (line 173)**
```python
# BEFORE (VULNERABLE):
street_clean = street.replace("'", "''")  # Only escaped single quotes
where_clause = f"PHYSICAL_ADDRESS LIKE '%{street_clean}%'"
```

**Location 2: `_get_arcgis_parcel()` method (line 252)**
```python
# BEFORE (VULNERABLE):
params = {"where": f"APN='{apn}'"}  # No escaping at all
```

## Attack Vectors

### 1. LIKE Pattern Injection
User input containing LIKE metacharacters could manipulate query patterns:
- `%` - Matches any sequence of characters
- `_` - Matches any single character
- `\` - Escape character

**Example Attack:**
```python
street = "Main%' OR '1'='1"
# Generated unsafe query:
# PHYSICAL_ADDRESS LIKE '%Main%' OR '1'='1%'
```

### 2. SQL Injection
User input containing SQL syntax could break out of string literals:
```python
apn = "123'; DROP TABLE properties; --"
# Generated unsafe query:
# APN='123'; DROP TABLE properties; --'
```

## Fix Implementation

### New Helper Functions

**`escape_like_pattern(value: str) -> str`**
- Escapes all LIKE metacharacters: `\`, `%`, `_`
- Escapes SQL string delimiter: `'`
- Proper escape order prevents double-escaping
- Used for LIKE clause patterns

**`escape_sql_string(value: str) -> str`**
- Escapes SQL string delimiter: `'`
- Used for equality comparisons
- Simpler than LIKE escaping (no wildcards)

### Fixed Code

**Location 1: `_search_arcgis()` method**
```python
# AFTER (SECURE):
street_escaped = escape_like_pattern(street)
where_clause = f"PHYSICAL_ADDRESS LIKE '%{street_escaped}%'"
```

**Location 2: `_get_arcgis_parcel()` method**
```python
# AFTER (SECURE):
apn_escaped = escape_sql_string(apn)
params = {"where": f"APN='{apn_escaped}'"}
```

## Escaping Examples

### escape_like_pattern()

| Input | Escaped Output | Reason |
|-------|----------------|--------|
| `O'Brien Ln` | `O''Brien Ln` | SQL quote escape |
| `50% Ave` | `50\% Ave` | LIKE wildcard escape |
| `Main_St` | `Main\_St` | LIKE wildcard escape |
| `C:\Path` | `C:\\Path` | Backslash escape |
| `%' OR '1'='1` | `\%'' OR ''1''=''1` | Combined attack prevention |

### escape_sql_string()

| Input | Escaped Output | Reason |
|-------|----------------|--------|
| `12345678` | `12345678` | No special chars |
| `O'Brien` | `O''Brien` | SQL quote escape |
| `'; DROP TABLE; --` | `''; DROP TABLE; --` | SQL injection prevention |

## Verification

Created `test_injection_fix.py` with comprehensive test cases:
- Normal input handling
- Single quote escaping
- LIKE wildcard escaping
- SQL injection attempt prevention
- Combined attack scenarios

**Result:** All tests pass, security fix verified.

## Defense-in-Depth Principles Applied

1. **Input Validation:** Escape all user-controlled input
2. **Proper Escaping:** Use context-aware escaping (LIKE vs. equality)
3. **Consistent Application:** Apply to all query construction points
4. **Documentation:** Clear security notes in docstrings
5. **Testing:** Verify fix prevents known attack vectors

## Risk Assessment

**Before Fix:**
- Attackers could manipulate query patterns
- Potential data exfiltration via LIKE wildcards
- SQL injection could compromise database integrity
- User input from CSV files directly used in queries

**After Fix:**
- All LIKE metacharacters properly escaped
- SQL injection prevented via quote escaping
- Defense-in-depth even for system-generated values (APNs)
- Maintains existing functionality while adding security

## Notes

- APNs are typically system-generated, but defense-in-depth principle applies
- The fix maintains backward compatibility
- No breaking changes to method signatures
- All existing functionality preserved
- Proper error handling retained
