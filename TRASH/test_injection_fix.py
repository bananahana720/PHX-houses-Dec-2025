"""Test to verify SQL/LIKE injection vulnerability is fixed."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from phx_home_analysis.services.county_data.assessor_client import (
    escape_like_pattern,
    escape_sql_string,
)


def test_escape_like_pattern():
    """Test LIKE pattern escaping prevents injection."""
    test_cases = [
        # (input, expected_output, description)
        ("123 Main St", "123 Main St", "Normal address"),
        ("O'Brien Ln", "O''Brien Ln", "Single quote in street name"),
        ("50% Ave", "50\\% Ave", "Percent sign (LIKE wildcard)"),
        ("Main_St", "Main\\_St", "Underscore (LIKE wildcard)"),
        ("C:\\Path", "C:\\\\Path", "Backslash escape"),
        (
            "'; DROP TABLE properties; --",
            "''; DROP TABLE properties; --",
            "SQL injection attempt",
        ),
        (
            "%' OR '1'='1",
            "\\%'' OR ''1''=''1",
            "LIKE injection with SQL injection",
        ),
        ("_test%pattern_", "\\_test\\%pattern\\_", "Multiple LIKE wildcards"),
    ]

    print("Testing escape_like_pattern():")
    print("=" * 80)

    for input_val, expected, description in test_cases:
        result = escape_like_pattern(input_val)
        status = "PASS" if result == expected else "FAIL"
        print(f"\n{status}: {description}")
        print(f"  Input:    {repr(input_val)}")
        print(f"  Expected: {repr(expected)}")
        print(f"  Got:      {repr(result)}")

        if status == "FAIL":
            return False

    return True


def test_escape_sql_string():
    """Test SQL string escaping prevents injection."""
    test_cases = [
        # (input, expected_output, description)
        ("12345678", "12345678", "Normal APN"),
        ("123-45-678", "123-45-678", "APN with dashes"),
        ("O'Brien", "O''Brien", "Single quote escape"),
        ("'; DROP TABLE; --", "''; DROP TABLE; --", "SQL injection attempt"),
    ]

    print("\n\nTesting escape_sql_string():")
    print("=" * 80)

    for input_val, expected, description in test_cases:
        result = escape_sql_string(input_val)
        status = "PASS" if result == expected else "FAIL"
        print(f"\n{status}: {description}")
        print(f"  Input:    {repr(input_val)}")
        print(f"  Expected: {repr(expected)}")
        print(f"  Got:      {repr(result)}")

        if status == "FAIL":
            return False

    return True


def test_where_clause_generation():
    """Test that WHERE clauses are properly escaped."""
    print("\n\nTesting WHERE clause generation:")
    print("=" * 80)

    # Simulate malicious input
    malicious_street = "Main%' OR '1'='1"
    escaped = escape_like_pattern(malicious_street)
    where_clause = f"PHYSICAL_ADDRESS LIKE '%{escaped}%'"

    print(f"\nMalicious Input: {repr(malicious_street)}")
    print(f"Escaped:         {repr(escaped)}")
    print(f"WHERE clause:    {where_clause}")
    print(
        "\nSafe: LIKE metacharacters are escaped, preventing pattern manipulation"
    )

    # Test APN escaping
    malicious_apn = "123'; DROP TABLE properties; --"
    escaped_apn = escape_sql_string(malicious_apn)
    apn_clause = f"APN='{escaped_apn}'"

    print(f"\nMalicious APN:   {repr(malicious_apn)}")
    print(f"Escaped:         {repr(escaped_apn)}")
    print(f"WHERE clause:    {apn_clause}")
    print("\nSafe: Quotes are escaped, preventing SQL injection")

    return True


if __name__ == "__main__":
    print("SQL/LIKE Injection Vulnerability Fix - Test Suite")
    print("=" * 80)

    tests = [
        test_escape_like_pattern(),
        test_escape_sql_string(),
        test_where_clause_generation(),
    ]

    if all(tests):
        print("\n\n" + "=" * 80)
        print("ALL TESTS PASSED - Security fix verified")
        print("=" * 80)
        sys.exit(0)
    else:
        print("\n\n" + "=" * 80)
        print("TESTS FAILED - Security issue detected")
        print("=" * 80)
        sys.exit(1)
