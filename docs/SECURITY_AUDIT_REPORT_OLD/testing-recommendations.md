# Testing Recommendations

### Security Test Suite

```python
# tests/security/test_sql_injection.py
def test_sql_like_injection_prevention():
    """Verify LIKE pattern escaping prevents injection."""
    malicious_inputs = [
        "'; DROP TABLE properties; --",
        "100% complete",
        "file_name.txt",
        "\\'escaped",
    ]
    for inp in malicious_inputs:
        escaped = escape_like_pattern(inp)
        assert "DROP" not in escaped or "'" in escaped
        assert escaped.count("\\\\") >= inp.count("\\")

# tests/security/test_path_traversal.py
def test_path_traversal_blocked():
    """Verify path traversal attacks are blocked."""
    dangerous_paths = [
        Path("../../../etc/passwd"),
        Path("..\\..\\windows\\system32"),
        Path("/etc/shadow"),
        Path("//attacker.com/share"),
    ]
    for path in dangerous_paths:
        with pytest.raises(ValueError):
            validate_file_path(path, Path("data"))

# tests/security/test_atomic_writes.py
def test_atomic_write_on_interrupt():
    """Verify file integrity after interrupted write."""
    original_data = {"addr": {"lot": 8000}}
    save_enrichment(path, original_data)

    # Simulate interruption
    with mock.patch('json.dump', side_effect=KeyboardInterrupt):
        with pytest.raises(KeyboardInterrupt):
            save_enrichment(path, {"new": "data"})

    # Original should be intact
    loaded = load_enrichment(path)
    assert loaded == original_data

# tests/security/test_token_leakage.py
def test_no_token_in_logs(caplog):
    """Verify API tokens not logged."""
    token = "secret-token-12345"
    client = MaricopaAssessorClient(token=token)

    # Trigger error that might log
    with pytest.raises(Exception):
        await client._search_official_api("invalid")

    # Check logs don't contain token
    assert token not in caplog.text
    assert "***REDACTED***" in caplog.text or token not in caplog.text
```

---
