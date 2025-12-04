# Appendix A: SQL Injection Test Cases

```python
# Comprehensive SQL injection test suite
SQL_INJECTION_TEST_CASES = [
    # Basic injection
    ("'; DROP TABLE properties; --", "''; DROP TABLE properties; --"),
    ("' OR '1'='1", "'' OR ''1''=''1"),

    # LIKE wildcards
    ("100% done", "100\\% done"),
    ("file_name", "file\\_name"),

    # Escape sequences
    ("\\backslash", "\\\\backslash"),
    ("multiple \\ slashes \\\\", "multiple \\\\ slashes \\\\\\\\"),

    # Combined attacks
    ("'%; DROP--", "''\\%; DROP--"),
    ("_wildcard' OR 1=1--", "\\_wildcard'' OR 1=1--"),
]

@pytest.mark.parametrize("input_val,expected", SQL_INJECTION_TEST_CASES)
def test_escape_like_pattern(input_val, expected):
    """Verify SQL LIKE pattern escaping."""
    assert escape_like_pattern(input_val) == expected
```

---
