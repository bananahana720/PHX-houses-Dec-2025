# Appendix B: Path Traversal Test Cases

```python
# Path traversal attack test cases
PATH_TRAVERSAL_ATTACKS = [
    # Unix-style
    "../../../etc/passwd",
    "../../.env",
    "/etc/shadow",

    # Windows-style
    "..\\..\\windows\\system32",
    "C:\\Windows\\System32",

    # Mixed
    "../../../windows/system32",
    "..\\../etc/passwd",

    # Encoded
    "%2e%2e%2f%2e%2e%2f",  # ../../../
    "..%252f..%252f",       # Double-encoded

    # UNC paths
    "//attacker.com/share/data.json",
    "\\\\attacker.com\\share\\data.json",
]

@pytest.mark.parametrize("path", PATH_TRAVERSAL_ATTACKS)
def test_path_traversal_blocked(path):
    """Verify path traversal attacks are blocked."""
    with pytest.raises(ValueError, match="outside allowed directory"):
        validate_file_path(Path(path), Path("data"))
```

---

**End of Security Audit Report**

*For questions or clarifications, contact the security team.*
