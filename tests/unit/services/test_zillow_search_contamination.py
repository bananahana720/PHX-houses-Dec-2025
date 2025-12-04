"""Unit tests for Zillow search result contamination fix.

These tests validate the fixes implemented to prevent extracting images from
search results pages, "similar homes" carousels, and other properties when
the target is a specific property detail page.

Bug Description:
- For property "7233 W Corrine Dr, Peoria, AZ 85381"
- Expected: 27 gallery photos from the property listing
- Extracted: 42 images
- 98% were from DIFFERENT PROPERTIES - search result thumbnails

Root Causes Addressed:
1. JSON traversal captured ALL responsivePhotos arrays (including carousels)
2. No zpid validation in extracted URLs
3. gdpClientCache zpid filtering was incomplete
4. Regex fallback captured any photos.zillowstatic.com URL

Fixes Implemented:
1. _is_search_result_url() - Detects carousel/search URL patterns
2. _validate_zpid_in_url() - Validates zpid in image URLs
3. _filter_urls_for_property() - Comprehensive post-extraction filter
4. Zpid-aware JSON traversal in _extract_photos_from_next_data()
5. MAX_EXPECTED_IMAGES_PER_PROPERTY threshold with capping
"""

import logging

import pytest

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestSearchResultUrlDetection:
    """Test 1: _is_search_result_url() method correctly identifies contaminated URLs."""

    def test_detects_search_path_in_url(self):
        """URLs containing /search/ path should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        search_urls = [
            "https://photos.zillowstatic.com/search/123456.jpg",
            "https://www.zillow.com/search/results/image.jpg",
            "https://photos.zillowstatic.com/fp/search/thumbnail.webp",
        ]

        for url in search_urls:
            assert extractor._is_search_result_url(url) is True, f"Should reject: {url}"

        logger.info("Correctly rejects URLs with /search/ path")

    def test_detects_carousel_pattern(self):
        """URLs containing carousel indicators should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        carousel_urls = [
            "https://photos.zillowstatic.com/carousel/property-123.jpg",
            "https://photos.zillowstatic.com/similar-homes/abc.webp",
            "https://photos.zillowstatic.com/nearby/def.jpg",
            "https://photos.zillowstatic.com/recommendation/ghi.webp",
        ]

        for url in carousel_urls:
            assert extractor._is_search_result_url(url) is True, f"Should reject: {url}"

        logger.info("Correctly rejects carousel pattern URLs")

    def test_accepts_clean_property_urls(self):
        """Clean property gallery URLs should be accepted."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        clean_urls = [
            "https://photos.zillowstatic.com/fp/123456789_uncrate.jpg",
            "https://photos.zillowstatic.com/p_e/123456789/abcdef.webp",
            "https://photos.zillowstatic.com/uncrate/property-photo.jpg",
        ]

        for url in clean_urls:
            assert extractor._is_search_result_url(url) is False, f"Should accept: {url}"

        logger.info("Correctly accepts clean property gallery URLs")


class TestZpidValidation:
    """Test 2: _validate_zpid_in_url() correctly identifies mismatched zpids."""

    def test_accepts_url_with_matching_zpid(self):
        """URLs containing the expected zpid should be accepted."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        expected_zpid = "123456789"

        matching_urls = [
            f"https://photos.zillowstatic.com/p_e/{expected_zpid}/photo.jpg",
            f"https://photos.zillowstatic.com/fp/zpid_{expected_zpid}_uncrate.jpg",
            f"https://photos.zillowstatic.com/{expected_zpid}_zpid/photo.webp",
        ]

        for url in matching_urls:
            assert extractor._validate_zpid_in_url(url, expected_zpid) is True, (
                f"Should accept matching zpid URL: {url}"
            )

        logger.info("Correctly accepts URLs with matching zpid")

    def test_rejects_url_with_different_zpid(self):
        """URLs containing a DIFFERENT zpid should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        expected_zpid = "123456789"
        different_zpid = "987654321"

        mismatched_urls = [
            f"https://photos.zillowstatic.com/p_e/{different_zpid}/photo.jpg",
            f"https://photos.zillowstatic.com/{different_zpid}_zpid/photo.webp",
        ]

        for url in mismatched_urls:
            assert extractor._validate_zpid_in_url(url, expected_zpid) is False, (
                f"Should reject mismatched zpid URL: {url}"
            )

        logger.info("Correctly rejects URLs with different zpid")

    def test_accepts_url_without_zpid_when_unknown(self):
        """URLs should be accepted when expected_zpid is None."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        url = "https://photos.zillowstatic.com/fp/987654321/photo.jpg"

        # When no zpid is expected, allow all URLs through
        assert extractor._validate_zpid_in_url(url, None) is True
        logger.info("Correctly accepts URLs when zpid is unknown")

    def test_accepts_url_without_any_zpid(self):
        """URLs without any zpid pattern should be accepted (can't validate)."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        expected_zpid = "123456789"

        # URL without any zpid - should be allowed through
        url = "https://photos.zillowstatic.com/fp/abc123_uncrate.jpg"
        assert extractor._validate_zpid_in_url(url, expected_zpid) is True

        logger.info("Correctly accepts URLs without zpid pattern")


class TestUrlFilteringPipeline:
    """Test 3: _filter_urls_for_property() applies all filters correctly."""

    def test_filters_search_result_urls(self):
        """Search result URLs should be filtered out."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        expected_zpid = "123456789"

        urls = [
            "https://photos.zillowstatic.com/fp/123456789/good.jpg",  # Valid
            "https://photos.zillowstatic.com/search/bad.jpg",  # Search result
            "https://photos.zillowstatic.com/carousel/bad2.jpg",  # Carousel
            "https://photos.zillowstatic.com/fp/123456789/good2.webp",  # Valid
        ]

        filtered = extractor._filter_urls_for_property(urls, expected_zpid)

        assert len(filtered) == 2
        assert "good.jpg" in filtered[0]
        assert "good2.webp" in filtered[1]

        logger.info("Correctly filters out search result URLs")

    def test_filters_mismatched_zpid_urls(self):
        """URLs with wrong zpid should be filtered out."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        expected_zpid = "123456789"
        wrong_zpid = "999888777"

        urls = [
            f"https://photos.zillowstatic.com/p_e/{expected_zpid}/good.jpg",
            f"https://photos.zillowstatic.com/p_e/{wrong_zpid}/bad.jpg",  # Wrong zpid
            f"https://photos.zillowstatic.com/{expected_zpid}_zpid/good2.webp",
        ]

        filtered = extractor._filter_urls_for_property(urls, expected_zpid)

        # Wrong zpid URL should be filtered
        assert len(filtered) == 2
        assert all(wrong_zpid not in url for url in filtered)

        logger.info("Correctly filters out mismatched zpid URLs")

    def test_filters_low_quality_urls(self):
        """Low quality URLs (thumbnails, icons) should be filtered out."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        urls = [
            "https://photos.zillowstatic.com/uncrate/good.jpg",  # Valid
            "https://photos.zillowstatic.com/thumb_small.jpg",  # Thumbnail
            "https://photos.zillowstatic.com/icon_agent.png",  # Icon
            "https://photos.zillowstatic.com/uncrate/good2.webp",  # Valid
        ]

        filtered = extractor._filter_urls_for_property(urls, None)

        assert len(filtered) == 2
        assert all("thumb" not in url.lower() for url in filtered)
        assert all("icon" not in url.lower() for url in filtered)

        logger.info("Correctly filters out low quality URLs")


class TestContaminationScenario:
    """Test 4: Simulate the actual contamination bug scenario."""

    def test_mixed_property_urls_filtered(self):
        """URLs from multiple properties should be filtered to single property."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        # Simulate the bug: 42 URLs but 98% from different properties
        target_zpid = "123456789"
        other_zpids = ["111111111", "222222222", "333333333"]

        urls = []
        # 2 valid URLs from target property
        urls.append(f"https://photos.zillowstatic.com/p_e/{target_zpid}/photo1.jpg")
        urls.append(f"https://photos.zillowstatic.com/p_e/{target_zpid}/photo2.jpg")

        # 40 contaminated URLs from other properties (simulating search results)
        for other_zpid in other_zpids:
            for i in range(13):  # ~13 each = 39 total
                urls.append(
                    f"https://photos.zillowstatic.com/p_e/{other_zpid}/photo{i}.jpg"
                )

        # 1 carousel URL
        urls.append("https://photos.zillowstatic.com/similar-homes/promo.jpg")

        # Total: 42 URLs (matching the bug report)
        assert len(urls) == 42

        # Filter should reduce to only target property
        filtered = extractor._filter_urls_for_property(urls, target_zpid)

        # Should only have 2 URLs from target property
        assert len(filtered) == 2
        assert all(target_zpid in url for url in filtered)

        logger.info(
            f"Correctly filtered contaminated URLs: {len(urls)} -> {len(filtered)}"
        )

    def test_promotional_overlay_urls_rejected(self):
        """URLs with promotional patterns should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        # The bug report mentioned "$1,000 FREE RENT!!" promotional overlays
        # These would come from search results, not property galleries
        urls = [
            "https://photos.zillowstatic.com/uncrate/valid_property.jpg",
            "https://photos.zillowstatic.com/showcase/promo_rent.jpg",  # Promotional
            "https://photos.zillowstatic.com/partner/special_offer.jpg",  # Partner
        ]

        filtered = extractor._filter_urls_for_property(urls, None)

        # Promotional/partner URLs should be filtered
        assert len(filtered) == 1
        assert "valid_property" in filtered[0]

        logger.info("Correctly filters promotional overlay URLs")


class TestMaxImagesThreshold:
    """Test 5: MAX_EXPECTED_IMAGES_PER_PROPERTY threshold works correctly."""

    def test_threshold_constant_exists(self):
        """Verify MAX_EXPECTED_IMAGES_PER_PROPERTY constant is defined."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        assert hasattr(ZillowExtractor, "MAX_EXPECTED_IMAGES_PER_PROPERTY")
        assert ZillowExtractor.MAX_EXPECTED_IMAGES_PER_PROPERTY == 50

        logger.info("MAX_EXPECTED_IMAGES_PER_PROPERTY constant verified")

    def test_search_result_patterns_list_exists(self):
        """Verify SEARCH_RESULT_URL_PATTERNS list is defined."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        assert hasattr(ZillowExtractor, "SEARCH_RESULT_URL_PATTERNS")
        patterns = ZillowExtractor.SEARCH_RESULT_URL_PATTERNS

        expected_patterns = [
            "/search/",
            "carousel",
            "similar-homes",
            "nearby",
            "recommendation",
        ]

        for pattern in expected_patterns:
            assert pattern in patterns, f"Missing pattern: {pattern}"

        logger.info("SEARCH_RESULT_URL_PATTERNS list verified")


class TestJsonTraversalZpidFiltering:
    """Test 6: JSON traversal correctly skips non-matching zpid sections."""

    def test_carousel_section_names_are_skipped(self):
        """Known carousel/search section names should be skipped during traversal."""
        # This test verifies the fix was implemented by checking the code behavior
        import inspect

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        # Get the source of _extract_photos_from_next_data
        source = inspect.getsource(ZillowExtractor._extract_photos_from_next_data)

        # Verify the fix includes skipping known sections
        skip_sections = [
            "searchResults",
            "similarHomes",
            "nearbyHomes",
            "recommendedHomes",
            "otherListings",
            "carousel",
        ]

        for section in skip_sections:
            assert section in source, f"Missing section skip for: {section}"

        logger.info("JSON traversal includes section skipping logic")

    def test_zpid_context_tracking_implemented(self):
        """Verify zpid context tracking is implemented in walk() function."""
        import inspect

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        source = inspect.getsource(ZillowExtractor._extract_photos_from_next_data)

        # Verify the fix includes zpid context tracking
        assert "parent_zpid" in source, "Missing parent_zpid parameter in walk()"
        assert "current_zpid" in source, "Missing current_zpid tracking"
        assert "expected_zpid" in source, "Missing expected_zpid comparison"

        logger.info("Zpid context tracking is implemented")


class TestRegressionPrevention:
    """Test 7: Ensure fixes don't break normal extraction flow."""

    def test_empty_zpid_allows_extraction(self):
        """When zpid is unknown, extraction should still work."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        urls = [
            "https://photos.zillowstatic.com/uncrate/photo1.jpg",
            "https://photos.zillowstatic.com/uncrate/photo2.jpg",
            "https://photos.zillowstatic.com/uncrate/photo3.webp",
        ]

        # No zpid provided - all valid URLs should pass through
        filtered = extractor._filter_urls_for_property(urls, None)

        assert len(filtered) == 3
        logger.info("Extraction works correctly with unknown zpid")

    def test_valid_property_urls_not_rejected(self):
        """Valid property gallery URLs should never be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        zpid = "123456789"

        valid_urls = [
            f"https://photos.zillowstatic.com/p_e/{zpid}/kitchen.jpg",
            f"https://photos.zillowstatic.com/p_e/{zpid}/bedroom.jpg",
            f"https://photos.zillowstatic.com/p_e/{zpid}/bathroom.webp",
            f"https://photos.zillowstatic.com/p_e/{zpid}/exterior.jpg",
            f"https://photos.zillowstatic.com/{zpid}_zpid/pool.jpg",
            "https://photos.zillowstatic.com/uncrate/living_room.jpg",
        ]

        filtered = extractor._filter_urls_for_property(valid_urls, zpid)

        assert len(filtered) == len(valid_urls)
        logger.info("Valid property URLs correctly accepted")

    def test_method_signatures_unchanged(self):
        """Verify public method signatures are unchanged for backwards compatibility."""
        from inspect import signature

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        # extract_image_urls should still accept Property
        sig = signature(ZillowExtractor.extract_image_urls)
        params = list(sig.parameters.keys())
        assert "property" in params

        # _is_property_detail_page should accept tab
        sig = signature(ZillowExtractor._is_property_detail_page)
        params = list(sig.parameters.keys())
        assert "tab" in params

        logger.info("Method signatures are backwards compatible")


class TestPlaceholderImageFiltering:
    """Test placeholder image detection and filtering."""

    def test_detects_no_photo_pattern(self):
        """URLs with 'no-photo' pattern should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        no_photo_urls = [
            "https://photos.zillowstatic.com/no-photo.jpg",
            "https://photos.zillowstatic.com/no-photo-available.jpg",
            "https://cdn.example.com/images/no-photo.webp",
            "https://example.com/property/no-photo_placeholder.jpg",
        ]

        for url in no_photo_urls:
            assert extractor._is_placeholder_url(url) is True, f"Should reject: {url}"

        logger.info("Correctly rejects URLs with 'no-photo' pattern")

    def test_detects_no_image_pattern(self):
        """URLs with 'no-image' pattern should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        no_image_urls = [
            "https://photos.zillowstatic.com/no-image.jpg",
            "https://cdn.example.com/no-image-available.jpg",
            "https://example.com/no-image_fallback.png",
        ]

        for url in no_image_urls:
            assert extractor._is_placeholder_url(url) is True, f"Should reject: {url}"

        logger.info("Correctly rejects URLs with 'no-image' pattern")

    def test_detects_placeholder_pattern(self):
        """URLs with 'placeholder' pattern should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        placeholder_urls = [
            "https://photos.zillowstatic.com/placeholder.jpg",
            "https://cdn.example.com/placeholder-image.jpg",
            "https://example.com/images/placeholder_photo.png",
        ]

        for url in placeholder_urls:
            assert extractor._is_placeholder_url(url) is True, f"Should reject: {url}"

        logger.info("Correctly rejects URLs with 'placeholder' pattern")

    def test_detects_unavailable_pattern(self):
        """URLs with 'unavailable' pattern should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        unavailable_urls = [
            "https://photos.zillowstatic.com/unavailable.jpg",
            "https://cdn.example.com/image-unavailable.jpg",
            "https://example.com/photo_unavailable.png",
        ]

        for url in unavailable_urls:
            assert extractor._is_placeholder_url(url) is True, f"Should reject: {url}"

        logger.info("Correctly rejects URLs with 'unavailable' pattern")

    def test_detects_default_image_pattern(self):
        """URLs with 'default-image' pattern should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        default_urls = [
            "https://photos.zillowstatic.com/default-image.jpg",
            "https://cdn.example.com/default-image-fallback.jpg",
        ]

        for url in default_urls:
            assert extractor._is_placeholder_url(url) is True, f"Should reject: {url}"

        logger.info("Correctly rejects URLs with 'default-image' pattern")

    def test_detects_missing_photo_pattern(self):
        """URLs with 'missing-photo' pattern should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        missing_urls = [
            "https://photos.zillowstatic.com/missing-photo.jpg",
            "https://cdn.example.com/missing-photo.png",
        ]

        for url in missing_urls:
            assert extractor._is_placeholder_url(url) is True, f"Should reject: {url}"

        logger.info("Correctly rejects URLs with 'missing-photo' pattern")

    def test_detects_no_underscore_photo_pattern(self):
        """URLs with 'no_photo' (underscore variant) pattern should be rejected."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        no_underscore_urls = [
            "https://photos.zillowstatic.com/no_photo.jpg",
            "https://cdn.example.com/no_photo_available.jpg",
        ]

        for url in no_underscore_urls:
            assert extractor._is_placeholder_url(url) is True, f"Should reject: {url}"

        logger.info("Correctly rejects URLs with 'no_photo' pattern")

    def test_accepts_real_property_urls(self):
        """Real property photo URLs should not be flagged as placeholders."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        real_property_urls = [
            "https://photos.zillowstatic.com/p_e/123456789/kitchen_photo.jpg",
            "https://photos.zillowstatic.com/uncrate/bedroom_uncrate.jpg",
            "https://cdn.example.com/property_photos/living_room.png",
            "https://photos.zillowstatic.com/fp/property123/exterior.jpg",
        ]

        for url in real_property_urls:
            assert extractor._is_placeholder_url(url) is False, f"Should accept: {url}"

        logger.info("Correctly accepts real property URLs")

    def test_case_insensitive_detection(self):
        """Placeholder detection should be case-insensitive."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        case_variants = [
            "https://photos.zillowstatic.com/NO-PHOTO.jpg",  # All caps
            "https://photos.zillowstatic.com/No-Photo.jpg",  # Mixed case
            "https://photos.zillowstatic.com/nO-pHoTo.jpg",  # Random case
            "https://photos.zillowstatic.com/PLACEHOLDER.jpg",  # All caps
            "https://photos.zillowstatic.com/Placeholder_Image.jpg",  # Mixed case
        ]

        for url in case_variants:
            assert extractor._is_placeholder_url(url) is True, f"Should reject: {url}"

        logger.info("Placeholder detection is case-insensitive")

    def test_placeholder_urls_filtered_in_pipeline(self):
        """Placeholder URLs should be filtered out by _filter_urls_for_property."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        mixed_urls = [
            "https://photos.zillowstatic.com/uncrate/kitchen.jpg",  # Valid
            "https://photos.zillowstatic.com/no-photo.jpg",  # Placeholder
            "https://photos.zillowstatic.com/uncrate/bedroom.jpg",  # Valid
            "https://photos.zillowstatic.com/placeholder-image.jpg",  # Placeholder
            "https://photos.zillowstatic.com/uncrate/living_room.jpg",  # Valid
        ]

        filtered = extractor._filter_urls_for_property(mixed_urls, None)

        # Should only keep the 3 valid URLs
        assert len(filtered) == 3
        assert all("no-photo" not in url for url in filtered)
        assert all("placeholder" not in url for url in filtered)

        logger.info("Placeholder filtering works correctly in filter pipeline")

    def test_placeholder_detection_reports_metrics(self, caplog):
        """Verify placeholder detection is counted in filtering metrics."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        urls = [
            "https://photos.zillowstatic.com/uncrate/valid1.jpg",
            "https://photos.zillowstatic.com/no-photo.jpg",
            "https://photos.zillowstatic.com/uncrate/valid2.jpg",
            "https://photos.zillowstatic.com/placeholder.jpg",
            "https://photos.zillowstatic.com/uncrate/valid3.jpg",
        ]

        # Filtering should log the rejection with caplog fixture
        with caplog.at_level(logging.DEBUG, logger="src.phx_home_analysis.services.image_extraction.extractors.zillow"):
            filtered = extractor._filter_urls_for_property(urls, None)

            # Verify we rejected 2 placeholder images
            assert len(filtered) == 3
            # Check that rejection messages were logged
            rejection_logs = [
                rec for rec in caplog.records
                if "rejecting placeholder URL" in rec.message
            ]
            assert len(rejection_logs) >= 2

        logger.info("Placeholder detection metrics are reported")

    def test_real_world_scenario_glendale_property(self):
        """Test the actual bug scenario: filtering mixed property and placeholder images."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        # Simulate extraction from 5219 W El Caminito Dr, Glendale, AZ 85302
        # Bug: 1 of 41 extracted images was placeholder (no-photo.jpg)
        urls = [
            "https://photos.zillowstatic.com/uncrate/bedroom1.jpg",  # Real
            "https://photos.zillowstatic.com/uncrate/kitchen.jpg",  # Real
            "https://photos.zillowstatic.com/uncrate/bathroom.jpg",  # Real
            "https://photos.zillowstatic.com/uncrate/exterior.jpg",  # Real
            "https://photos.zillowstatic.com/uncrate/poolarea.jpg",  # Real
            "https://photos.zillowstatic.com/no-photo.jpg",  # Placeholder (32eda25c-ab45-4c88-82fc-d8ea27d042b4.png equivalent)
            "https://photos.zillowstatic.com/uncrate/livingroom.jpg",  # Real
        ]

        filtered = extractor._filter_urls_for_property(urls, None)

        # Should filter out the placeholder
        assert len(filtered) == 6
        assert all("no-photo" not in url for url in filtered)

        logger.info("Real-world Glendale scenario correctly filters placeholder image")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
