"""Unit tests for address normalization utilities.

Tests the normalize_address() and addresses_match() functions
for various input formats and edge cases.
"""

from src.phx_home_analysis.utils.address_utils import addresses_match, normalize_address


class TestNormalizeAddress:
    """Tests for address normalization function."""

    def test_lowercase_conversion(self):
        """Address should be converted to lowercase."""
        assert normalize_address("123 MAIN ST") == "123 main st"
        assert normalize_address("Phoenix, AZ") == "phoenix az"

    def test_comma_removal(self):
        """Commas should be removed."""
        assert normalize_address("Phoenix, AZ") == "phoenix az"
        assert normalize_address("123 Main St, Phoenix, AZ 85001") == "123 main st phoenix az 85001"

    def test_period_removal(self):
        """Periods should be removed."""
        assert normalize_address("123 Main St.") == "123 main st"
        assert (
            normalize_address("Dr. Martin Luther King Jr. Blvd") == "dr martin luther king jr blvd"
        )

    def test_strip_whitespace(self):
        """Leading and trailing whitespace should be stripped."""
        assert normalize_address("  123 Main St  ") == "123 main st"
        assert normalize_address("\t456 Elm Ave\n") == "456 elm ave"

    def test_collapse_multiple_spaces(self):
        """Multiple spaces should collapse to single space."""
        assert normalize_address("123   Main    St") == "123 main st"
        assert normalize_address("Phoenix,   AZ   85001") == "phoenix az 85001"

    def test_full_normalization(self):
        """Full address normalization with all rules applied."""
        result = normalize_address("  123 Main St., Phoenix, AZ 85001  ")
        assert result == "123 main st phoenix az 85001"

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert normalize_address("") == ""

    def test_whitespace_only(self):
        """Whitespace-only string should return empty string."""
        assert normalize_address("   ") == ""
        assert normalize_address("\t\n") == ""

    def test_complex_address(self):
        """Test complex address with multiple special characters."""
        result = normalize_address("123 N. Main St., Apt. 4B, Phoenix, AZ 85001")
        assert result == "123 n main st apt 4b phoenix az 85001"

    def test_mixed_case_preservation_after_lowering(self):
        """Verify case is properly lowered for mixed case input."""
        assert normalize_address("McDonalds Rd") == "mcdonalds rd"
        assert normalize_address("E. CaMeLbAcK Rd") == "e camelback rd"


class TestAddressesMatch:
    """Tests for address comparison function."""

    def test_same_address_matches(self):
        """Identical addresses should match."""
        assert addresses_match("123 Main St", "123 Main St") is True

    def test_case_insensitive_match(self):
        """Addresses should match regardless of case."""
        assert addresses_match("123 MAIN ST", "123 main st") is True
        assert addresses_match("PHOENIX, AZ", "phoenix, az") is True

    def test_punctuation_insensitive_match(self):
        """Addresses should match regardless of punctuation."""
        assert addresses_match("123 Main St.", "123 Main St") is True
        assert addresses_match("Phoenix, AZ", "Phoenix AZ") is True

    def test_different_addresses_no_match(self):
        """Different addresses should not match."""
        assert addresses_match("123 Main St", "456 Oak Ave") is False
        assert addresses_match("Phoenix, AZ", "Mesa, AZ") is False

    def test_whitespace_differences(self):
        """Addresses should match regardless of whitespace differences."""
        assert addresses_match("123 Main St", "  123  Main  St  ") is True

    def test_full_address_variations(self):
        """Full addresses with various formatting should match."""
        addr1 = "123 Main St., Phoenix, AZ 85001"
        addr2 = "123 MAIN ST PHOENIX AZ 85001"
        addr3 = "  123 Main St, Phoenix,  AZ  85001  "

        assert addresses_match(addr1, addr2) is True
        assert addresses_match(addr1, addr3) is True
        assert addresses_match(addr2, addr3) is True

    def test_empty_strings(self):
        """Empty strings should match each other."""
        assert addresses_match("", "") is True
        assert addresses_match("   ", "") is True

    def test_empty_vs_non_empty(self):
        """Empty string should not match non-empty."""
        assert addresses_match("", "123 Main St") is False
        assert addresses_match("123 Main St", "") is False


class TestEdgeCases:
    """Edge case tests for address utilities."""

    def test_numbers_only(self):
        """Address with only numbers should normalize correctly."""
        assert normalize_address("12345") == "12345"

    def test_special_street_types(self):
        """Various street type abbreviations should normalize."""
        assert normalize_address("123 N. Desert Rd.") == "123 n desert rd"
        assert normalize_address("456 W. Main Blvd.") == "456 w main blvd"

    def test_unit_numbers(self):
        """Unit/apartment numbers should be preserved."""
        assert normalize_address("123 Main St #4") == "123 main st #4"
        assert normalize_address("123 Main St, Unit 4") == "123 main st unit 4"

    def test_zip_plus_four(self):
        """ZIP+4 format should normalize correctly."""
        assert normalize_address("Phoenix, AZ 85001-1234") == "phoenix az 85001-1234"

    def test_ordinal_streets(self):
        """Ordinal street names should normalize."""
        assert normalize_address("123 1st Ave") == "123 1st ave"
        assert normalize_address("456 W. 23rd St.") == "456 w 23rd st"
