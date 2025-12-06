"""Unit tests for PhoenixMLS listing detail page navigation.

Tests the fix for navigating from search results to listing detail page
to extract full property images (not just thumbnails).
"""

import pytest

from src.phx_home_analysis.services.image_extraction.extractors.phoenix_mls import (
    PhoenixMLSExtractor,
)


@pytest.fixture
def extractor():
    """Create PhoenixMLS extractor instance."""
    return PhoenixMLSExtractor()


@pytest.fixture
def search_results_html_with_listing_link():
    """Mock search results page with listing detail link."""
    return """
    <html>
        <body>
            <div class="search-results">
                <div class="property-card" data-listing-id="6789012">
                    <a href="/mls/listing/6789012" class="property-link">
                        <h3>4732 W Davis Rd, Glendale, AZ</h3>
                        <p>$475,000</p>
                    </a>
                </div>
            </div>
        </body>
    </html>
    """


@pytest.fixture
def search_results_html_no_links():
    """Mock search results page with no listing links."""
    return """
    <html>
        <body>
            <div class="search-results">
                <p>No results found</p>
            </div>
        </body>
    </html>
    """


class TestFindListingUrl:
    """Test _find_listing_url() method for extracting detail page URL from search results."""

    def test_find_listing_url_pattern_1_mls_listing(
        self, extractor, search_results_html_with_listing_link
    ):
        """Test finding listing URL via /mls/listing/ pattern."""
        base_url = "https://phoenixmlssearch.com"

        listing_url = extractor._find_listing_url(search_results_html_with_listing_link, base_url)

        assert listing_url is not None
        assert listing_url == "https://phoenixmlssearch.com/mls/listing/6789012"

    def test_find_listing_url_pattern_2_property_card(self, extractor):
        """Test finding listing URL via property card with data-listing-id."""
        html = """
        <html>
            <body>
                <article class="property-card" data-listing-id="123456">
                    <a href="/property/123456">View Details</a>
                </article>
            </body>
        </html>
        """
        base_url = "https://phoenixmlssearch.com"

        listing_url = extractor._find_listing_url(html, base_url)

        assert listing_url is not None
        assert "/property/123456" in listing_url

    def test_find_listing_url_pattern_3_title_link(self, extractor):
        """Test finding listing URL via property title link."""
        html = """
        <html>
            <body>
                <a href="/mls/listing/789" class="property-title">
                    Beautiful Home
                </a>
            </body>
        </html>
        """
        base_url = "https://phoenixmlssearch.com"

        listing_url = extractor._find_listing_url(html, base_url)

        assert listing_url is not None
        assert "/mls/listing/789" in listing_url

    def test_find_listing_url_no_links(self, extractor, search_results_html_no_links):
        """Test returns None when no listing links found."""
        base_url = "https://phoenixmlssearch.com"

        listing_url = extractor._find_listing_url(search_results_html_no_links, base_url)

        assert listing_url is None

    def test_find_listing_url_excludes_search_links(self, extractor):
        """Test excludes search/filter links from generic pattern."""
        html = """
        <html>
            <body>
                <a href="/listing/search?q=test">Search Listings</a>
                <a href="/listing/filter">Filter</a>
                <a href="/listing/123">Real Listing</a>
            </body>
        </html>
        """
        base_url = "https://phoenixmls.com"

        listing_url = extractor._find_listing_url(html, base_url)

        assert listing_url is not None
        assert "/listing/123" in listing_url
        assert "?q=" not in listing_url  # No search query params
        assert "/filter" not in listing_url  # No filter path

    def test_find_listing_url_resolves_relative_urls(self, extractor):
        """Test resolves relative URLs to absolute URLs."""
        html = """
        <html>
            <body>
                <a href="/mls/listing/456">Property</a>
            </body>
        </html>
        """
        base_url = "https://phoenixmlssearch.com"

        listing_url = extractor._find_listing_url(html, base_url)

        assert listing_url is not None
        assert listing_url.startswith("https://")
        assert "phoenixmlssearch.com" in listing_url
