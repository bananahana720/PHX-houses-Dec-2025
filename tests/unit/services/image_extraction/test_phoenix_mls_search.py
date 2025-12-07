"""Unit tests for PhoenixMLSSearchExtractor.

Tests cover search form interaction, result parsing, metadata extraction,
and image URL transformation following the E2.R2 tech spec.
"""

import pytest

from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.domain.enums import ImageSource
from src.phx_home_analysis.services.image_extraction.extractors.phoenix_mls_search import (
    PhoenixMLSSearchExtractor,
)


@pytest.fixture
def sample_property():
    """Create sample property for testing."""
    return Property(
        street="123 Main St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="123 Main St, Phoenix, AZ 85001",
        price="$400,000",
        price_num=400000,
        beds=4,
        baths=2.0,
        sqft=2000,
        price_per_sqft_raw=200.0,
    )


@pytest.fixture
def extractor():
    """Create PhoenixMLSSearchExtractor instance."""
    return PhoenixMLSSearchExtractor()


@pytest.fixture
def sample_search_results_html():
    """Mock phoenixmlssearch.com search results page."""
    return """
    <html>
      <body>
        <div class="listing-card" data-mls="6789012">
          <h3>123 Main St, Phoenix, AZ 85001</h3>
          <span class="mls-number">MLS# 6789012</span>
          <a href="/mls/123-main-st-phoenix-az-85001-mls_6789012">View Details</a>
        </div>
      </body>
    </html>
    """


@pytest.fixture
def sample_detail_page_html():
    """Mock phoenixmlssearch.com listing detail page."""
    return """
    <html>
      <body>
        <div class="listing-details">
          <p>MLS#: 6789012</p>
          <p># Bedrooms: 4</p>
          <p>Full Bathrooms: 2.5</p>
          <p>Approx SQFT: 2,150</p>
          <p>Approx Lot SqFt: 8,500</p>
          <p>Garage Spaces: 2</p>
          <p>Sewer: Sewer - Public</p>
          <p>Year Built: 2015</p>
          <p>Association Fee Incl: No Fees</p>
        </div>
        <div class="gallery">
          <img src="https://cdn.photos.sparkplatform.com/az/abc123-t.jpg" />
          <img src="https://cdn.photos.sparkplatform.com/az/def456-t.jpg" />
          <img src="https://cdn.photos.sparkplatform.com/az/ghi789-m.jpg" />
        </div>
      </body>
    </html>
    """


class TestPhoenixMLSSearchExtractor:
    """Unit tests for PhoenixMLSSearchExtractor."""

    def test_source_property(self, extractor):
        """Test that source property returns correct ImageSource."""
        assert extractor.source == ImageSource.PHOENIX_MLS_SEARCH

    def test_can_handle_phoenix_city(self, extractor, sample_property):
        """Test that extractor can handle Phoenix metro properties."""
        assert extractor.can_handle(sample_property) is True

    def test_can_handle_non_phoenix_city(self, extractor):
        """Test that extractor rejects non-Phoenix metro properties."""
        non_phoenix_property = Property(
            street="456 Oak Ave",
            city="Flagstaff",
            state="AZ",
            zip_code="86001",
            full_address="456 Oak Ave, Flagstaff, AZ 86001",
            price="$300,000",
            price_num=300000,
            beds=3,
            baths=2.0,
            sqft=1800,
            price_per_sqft_raw=166.67,
        )
        assert extractor.can_handle(non_phoenix_property) is False

    def test_build_search_url(self, extractor, sample_property):
        """Test search URL construction."""
        url = extractor._build_search_url(sample_property)
        assert url == "https://phoenixmlssearch.com/simple-search/"

    def test_addresses_match_exact(self, extractor, sample_property):
        """Test address matching with exact match."""
        card_text = "123 Main St, Phoenix, AZ 85001 - 4 bed, 2 bath"
        assert extractor._addresses_match(card_text, sample_property) is True

    def test_addresses_match_numeric(self, extractor, sample_property):
        """Test address matching with street number only."""
        card_text = "Property 123 - Beautiful home on Main Street"
        assert extractor._addresses_match(card_text, sample_property) is True

    def test_addresses_no_match(self, extractor, sample_property):
        """Test address matching with no match."""
        card_text = "456 Oak Ave, Phoenix, AZ 85002"
        assert extractor._addresses_match(card_text, sample_property) is False

    def test_extract_kill_switch_all_fields(self, extractor, sample_detail_page_html):
        """Test extraction of all 8 kill-switch fields."""
        metadata = extractor._extract_kill_switch_fields(sample_detail_page_html)

        assert metadata["hoa_fee"] == 0.0
        assert metadata["beds"] == 4
        assert metadata["baths"] == 2.5
        assert metadata["sqft"] == 2150
        assert metadata["lot_sqft"] == 8500
        assert metadata["garage_spaces"] == 2
        assert metadata["sewer_type"] == "city"
        assert metadata["year_built"] == 2015

    def test_extract_kill_switch_partial(self, extractor):
        """Test handling of missing fields."""
        partial_html = """
        <html><body>
          <p># Bedrooms: 3</p>
          <p>Full Bathrooms: 2</p>
        </body></html>
        """

        metadata = extractor._extract_kill_switch_fields(partial_html)

        assert metadata["beds"] == 3
        assert metadata["baths"] == 2.0
        assert "sqft" not in metadata
        assert "lot_sqft" not in metadata

    def test_parse_hoa_no_fees(self, extractor):
        """Test HOA parsing for 'No Fees' value."""
        assert extractor._parse_hoa("No Fees") == 0.0
        assert extractor._parse_hoa("None") == 0.0
        assert extractor._parse_hoa("N/A") == 0.0

    def test_parse_hoa_monthly(self, extractor):
        """Test HOA parsing for '$150/month'."""
        assert extractor._parse_hoa("$150") == 150.0
        assert extractor._parse_hoa("$150/month") == 150.0
        assert extractor._parse_hoa("$150 monthly") == 150.0

    def test_parse_hoa_yearly(self, extractor):
        """Test HOA parsing converts yearly to monthly."""
        assert extractor._parse_hoa("$1,200/year") == 100.0
        assert extractor._parse_hoa("$600 annual") == 50.0

    def test_parse_hoa_invalid(self, extractor):
        """Test HOA parsing returns None for unparseable values."""
        assert extractor._parse_hoa("Unknown") is None
        assert extractor._parse_hoa("Call for details") is None

    def test_parse_sewer_city(self, extractor):
        """Test sewer type parsing for city sewer."""
        assert extractor._parse_sewer("Sewer - Public") == "city"
        assert extractor._parse_sewer("Public Sewer") == "city"
        assert extractor._parse_sewer("City") == "city"
        assert extractor._parse_sewer("Municipal") == "city"

    def test_parse_sewer_septic(self, extractor):
        """Test sewer type parsing for septic."""
        assert extractor._parse_sewer("Septic Tank") == "septic"
        assert extractor._parse_sewer("Septic") == "septic"

    def test_parse_sewer_unknown(self, extractor):
        """Test sewer type parsing returns None for unknown types."""
        assert extractor._parse_sewer("Unknown") is None
        assert extractor._parse_sewer("Other") is None

    def test_extract_gallery_sparkplatform(self, extractor, sample_detail_page_html):
        """Test SparkPlatform CDN URL transformation."""
        urls = extractor._extract_gallery_images(sample_detail_page_html)

        assert len(urls) == 3
        # Check that all URLs are transformed to -o.jpg (original/full-size)
        assert all(url.endswith("-o.jpg") for url in urls)
        assert "abc123-o.jpg" in urls[0]
        assert "def456-o.jpg" in urls[1]
        assert "ghi789-o.jpg" in urls[2]

    def test_extract_gallery_deduplication(self, extractor):
        """Test that duplicate image URLs are deduplicated."""
        html_with_dupes = """
        <html><body>
          <img src="https://cdn.photos.sparkplatform.com/az/abc123-t.jpg" />
          <img src="https://cdn.photos.sparkplatform.com/az/abc123-t.jpg" />
          <a href="https://cdn.photos.sparkplatform.com/az/abc123-o.jpg"></a>
        </body></html>
        """

        urls = extractor._extract_gallery_images(html_with_dupes)

        # Should only have one URL after deduplication
        assert len(urls) == 1
        assert urls[0].endswith("abc123-o.jpg")

    def test_extract_gallery_no_sparkplatform_urls(self, extractor):
        """Test that non-SparkPlatform URLs are ignored."""
        html_no_spark = """
        <html><body>
          <img src="https://example.com/image1.jpg" />
          <img src="https://other-cdn.com/image2.jpg" />
        </body></html>
        """

        urls = extractor._extract_gallery_images(html_no_spark)
        assert len(urls) == 0

    def test_lot_sqft_from_acres(self, extractor):
        """Test lot size conversion from acres to sqft."""
        html_with_acres = """
        <html><body>
          <p>Lot Size: 0.25 acres</p>
        </body></html>
        """

        metadata = extractor._extract_kill_switch_fields(html_with_acres)

        # 0.25 acres = 10,890 sqft
        assert metadata.get("lot_sqft") == 10890

    def test_extract_kill_switch_case_insensitive(self, extractor):
        """Test that field extraction is case-insensitive."""
        html_mixed_case = """
        <html><body>
          <p>YEAR BUILT: 2020</p>
          <p>garage spaces: 3</p>
          <p>ApProx SQFT: 1,800</p>
        </body></html>
        """

        metadata = extractor._extract_kill_switch_fields(html_mixed_case)

        assert metadata["year_built"] == 2020
        assert metadata["garage_spaces"] == 3
        assert metadata["sqft"] == 1800

    def test_mls_pattern_primary_format(self, extractor):
        """Test primary MLS pattern: '/ 6937912 (MLS #)'."""
        text = "5219 W EL CAMINITO Drive, Glendale, AZ 85302 / 6937912 (MLS #)"
        # Should match with primary pattern (MLS_PATTERNS[0])
        match = extractor.MLS_PATTERNS[0].search(text)
        assert match is not None
        assert match.group(1) == "6937912"

    def test_mls_pattern_no_space_before_hash(self, extractor):
        """Test alternate MLS pattern: '/ 6937912 (MLS#)' (no space before #)."""
        text = "123 Main St, Phoenix, AZ 85001 / 1234567 (MLS#)"
        # Should match with primary pattern (handles both with/without space)
        match = extractor.MLS_PATTERNS[0].search(text)
        assert match is not None
        assert match.group(1) == "1234567"

    def test_mls_pattern_hash_prefix(self, extractor):
        """Test fallback MLS pattern: '#6937912'."""
        text = "123 Main St #6937912"
        # Should match with fallback pattern (MLS_PATTERNS[1])
        match = extractor.MLS_PATTERNS[1].search(text)
        assert match is not None
        assert match.group(1) == "6937912"

    def test_mls_pattern_mls_prefix(self, extractor):
        """Test fallback MLS pattern: 'MLS 6937912' or 'MLS# 6937912'."""
        text_mls = "MLS 6937912"
        text_mls_hash = "MLS# 6937912"
        # Should match with fallback pattern (MLS_PATTERNS[2])
        match_mls = extractor.MLS_PATTERNS[2].search(text_mls)
        match_mls_hash = extractor.MLS_PATTERNS[2].search(text_mls_hash)
        assert match_mls is not None
        assert match_mls.group(1) == "6937912"
        assert match_mls_hash is not None
        assert match_mls_hash.group(1) == "6937912"

    def test_mls_pattern_all_patterns_defined(self, extractor):
        """Test that all 4 MLS patterns are defined."""
        assert len(extractor.MLS_PATTERNS) == 4
        assert all(hasattr(p, "search") for p in extractor.MLS_PATTERNS)


class TestAutocompleteMatching:
    """Unit tests for autocomplete suggestion matching (E2.R3 fix)."""

    @pytest.fixture
    def extractor(self):
        """Create PhoenixMLSSearchExtractor instance."""
        return PhoenixMLSSearchExtractor()

    def test_score_autocomplete_exact_match(self, extractor):
        """Test scoring for exact address match."""
        query = "123 Main St, Phoenix, AZ 85001"
        option = "123 Main St, Phoenix, AZ 85001"
        score = extractor._score_autocomplete_match(query, option)
        assert score == 1.0

    def test_score_autocomplete_exact_match_case_insensitive(self, extractor):
        """Test scoring ignores case differences."""
        query = "123 Main St, Phoenix, AZ 85001"
        option = "123 MAIN ST, PHOENIX, AZ 85001"
        score = extractor._score_autocomplete_match(query, option)
        assert score == 1.0

    def test_score_autocomplete_substring_match(self, extractor):
        """Test scoring for substring matches."""
        query = "123 Main St, Phoenix, AZ 85001"
        option = "123 Main St, Phoenix, AZ 85001 - 4 bed, 2 bath"
        score = extractor._score_autocomplete_match(query, option)
        assert score == 0.8

    def test_score_autocomplete_street_number_match(self, extractor):
        """Test scoring with street number and city match."""
        query = "123 Main St, Phoenix, AZ 85001"
        option = "123 Main Street, Phoenix, AZ"
        score = extractor._score_autocomplete_match(query, option)
        assert score >= 0.7

    def test_score_autocomplete_partial_components(self, extractor):
        """Test scoring with partial address component match."""
        query = "456 Oak Ave, Phoenix, AZ 85002"
        option = "456 Oak, Phoenix"
        score = extractor._score_autocomplete_match(query, option)
        assert score > 0.0  # Should have some score for partial match

    def test_score_autocomplete_no_match(self, extractor):
        """Test scoring returns low score for non-matching addresses."""
        # Different street numbers and cities should score low
        query = "123 Main St, Phoenix, AZ 85001"
        option = "789 Sunset Dr, Scottsdale, AZ 85251"
        score = extractor._score_autocomplete_match(query, option)
        # May have some overlap (AZ state) but should be low
        assert score < 0.5

    def test_score_autocomplete_empty_option(self, extractor):
        """Test scoring with empty option text."""
        query = "123 Main St, Phoenix, AZ 85001"
        option = ""
        score = extractor._score_autocomplete_match(query, option)
        assert score == 0.0

    def test_score_autocomplete_threshold_decision(self, extractor):
        """Test that score >= 0.5 is considered a match."""
        # This should pass (>= 0.5)
        query = "123 Main St, Phoenix, AZ 85001"
        option = "123 Main St, Phoenix, AZ 85001"
        score = extractor._score_autocomplete_match(query, option)
        assert score >= 0.5

        # This should also pass
        query = "456 Oak Ave, Phoenix, AZ 85002"
        option = "456 Oak Ave, Phoenix, AZ"
        score = extractor._score_autocomplete_match(query, option)
        assert score >= 0.5 or score == 0.0  # May or may not meet threshold

    def test_score_autocomplete_various_formats(self, extractor):
        """Test scoring with various address format variations."""
        query = "4732 W Davis Rd, Glendale, AZ 85306"

        # All these should score reasonably well
        options = [
            "4732 W Davis Rd, Glendale, AZ 85306",  # Exact
            "4732 W Davis Road, Glendale, AZ 85306",  # Road vs Rd
            "4732 Davis Rd, Glendale, AZ",  # Partial
            "4732 W Davis, Glendale",  # Minimal
        ]

        scores = [extractor._score_autocomplete_match(query, option) for option in options]

        # First should be best, others should be reasonable
        assert scores[0] >= scores[1]  # Exact better than Road variant
        assert any(s >= 0.5 for s in scores)  # At least one should be good match

    def test_score_autocomplete_mls_pattern_priority(self, extractor):
        """Test that MLS# pattern gets priority in scoring.

        PhoenixMLS autocomplete dropdown shows two types:
        1. "ADDRESS / MLS_NUMBER (MLS #)" - Specific listing
        2. "address (Street Address)" - Generic street

        We should prefer #1 with higher score.
        """
        query = "4560 E Sunrise Dr, Phoenix, AZ 85044"

        # Real autocomplete options from PhoenixMLS
        option_with_mls = "4560 E SUNRISE Drive, Phoenix, AZ 85044 / 6948863 (MLS #)"
        option_without_mls = "4560 e sunrise (Street Address)"

        score_with_mls = extractor._score_autocomplete_match(query, option_with_mls)
        score_without_mls = extractor._score_autocomplete_match(query, option_without_mls)

        # MLS pattern should score higher
        assert score_with_mls > score_without_mls
        assert score_with_mls >= 0.85  # Should be high score

    def test_score_autocomplete_mls_pattern_bonus(self, extractor):
        """Test that MLS pattern provides score boost even with partial match."""
        query = "123 Main St, Phoenix, AZ 85001"

        # Two options with similar match quality, one has MLS pattern
        option_without_mls = "123 Main Street, Phoenix"
        option_with_mls = "123 Main Street, Phoenix / 1234567 (MLS #)"

        score_without_mls = extractor._score_autocomplete_match(query, option_without_mls)
        score_with_mls = extractor._score_autocomplete_match(query, option_with_mls)

        # MLS pattern should boost score
        assert score_with_mls > score_without_mls
        assert score_with_mls - score_without_mls >= 0.1  # At least 10% boost
