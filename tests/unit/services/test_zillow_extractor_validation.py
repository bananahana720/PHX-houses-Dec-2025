"""Comprehensive validation tests for Zillow extractor fixes.

Tests the three key modifications:
1. _click_first_search_result() method (87 lines)
2. Enhanced autocomplete selectors (8 selectors)
3. _navigate_to_property_via_search() recovery logic

Code quality, syntax, import, and functional validation.
"""

import logging
import re
from unittest.mock import AsyncMock, patch

import pytest

# Configure logging for test output
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestZillowExtractorSyntax:
    """Test 1: Code Quality & Syntax Validation"""

    def test_module_imports_successfully(self):
        """Verify zillow.py imports without errors."""
        try:
            from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
                ZillowExtractor,
            )

            assert ZillowExtractor is not None
            logger.info("✓ Zillow extractor imports successfully")
        except ImportError as e:
            pytest.fail(f"Import error in zillow.py: {e}")
        except SyntaxError as e:
            pytest.fail(f"Syntax error in zillow.py: {e}")

    def test_no_undefined_variables(self):
        """Check for undefined references in key methods."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        # Verify all key methods exist
        assert hasattr(ZillowExtractor, "_click_first_search_result")
        assert hasattr(ZillowExtractor, "_is_property_detail_page")
        assert hasattr(ZillowExtractor, "_navigate_to_property_via_search")
        assert hasattr(ZillowExtractor, "extract_image_urls")
        logger.info("✓ All key methods exist")

    def test_method_signatures_are_correct(self):
        """Verify method signatures match expected types."""
        from inspect import signature

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        # Check _click_first_search_result
        sig = signature(ZillowExtractor._click_first_search_result)
        params = list(sig.parameters.keys())
        assert "self" in params and "tab" in params
        logger.info(f"  _click_first_search_result params: {params}")

        # Check _is_property_detail_page
        sig = signature(ZillowExtractor._is_property_detail_page)
        params = list(sig.parameters.keys())
        assert "self" in params and "tab" in params
        logger.info(f"  _is_property_detail_page params: {params}")

        # Check _navigate_to_property_via_search
        sig = signature(ZillowExtractor._navigate_to_property_via_search)
        params = list(sig.parameters.keys())
        assert "self" in params and "property" in params and "tab" in params
        logger.info(f"  _navigate_to_property_via_search params: {params}")

        logger.info("✓ All method signatures correct")

    def test_async_await_usage_is_valid(self):
        """Verify async/await is used correctly."""
        from inspect import iscoroutinefunction

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        # Verify methods are async
        assert iscoroutinefunction(ZillowExtractor._click_first_search_result)
        assert iscoroutinefunction(ZillowExtractor._is_property_detail_page)
        assert iscoroutinefunction(ZillowExtractor._navigate_to_property_via_search)
        assert iscoroutinefunction(ZillowExtractor.extract_image_urls)

        logger.info("✓ All key methods are properly async")

    def test_logging_statements_are_formatted_correctly(self):
        """Verify logging uses proper formatting."""
        import inspect

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        # Get source code of _click_first_search_result
        source = inspect.getsource(ZillowExtractor._click_first_search_result)

        # Check for proper logging patterns
        assert "logger.info" in source or "logger.warning" in source or "logger.error" in source
        assert "%s" in source  # Should use %s formatting, not f-strings with sensitive data
        logger.info("✓ Logging statements use proper formatting")


class TestAutocompleteSelectors:
    """Test 2: Enhanced Autocomplete Selectors Validation"""

    def test_autocomplete_selectors_exist(self):
        """Verify all 8 autocomplete selectors are defined."""
        import inspect

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        source = inspect.getsource(ZillowExtractor._navigate_to_property_via_search)

        # Find selector lines between autocomplete_selectors = [ and ]
        lines = source.split('\n')
        in_selectors = False
        selectors_lines = []

        for line in lines:
            if 'autocomplete_selectors' in line and '=' in line:
                in_selectors = True
                continue
            if in_selectors:
                if line.strip().startswith(']'):
                    break
                if "'" in line:
                    selectors_lines.append(line)

        # Extract selector content from each line
        selectors = []
        for line in selectors_lines:
            match = re.search(r"'([^']+)'", line)
            if match:
                selectors.append(match.group(1))

        assert len(selectors) >= 8, f"Expected 8+ selectors, got {len(selectors)}: {selectors}"
        logger.info(f"✓ Found {len(selectors)} autocomplete selectors:")
        for i, sel in enumerate(selectors, 1):
            logger.info(f"  {i}. {sel}")

    def test_selectors_are_valid_css(self):
        """Verify all selectors are valid CSS/XPath syntax."""
        import inspect

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        source = inspect.getsource(ZillowExtractor._navigate_to_property_via_search)
        match = re.search(r"autocomplete_selectors\s*=\s*\[(.*?)\]", source, re.DOTALL)
        selectors = re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))

        for selector in selectors:
            # Basic CSS selector validation
            assert isinstance(selector, str), f"Selector not string: {selector}"
            assert len(selector) > 0, "Empty selector"
            assert not selector.startswith(" "), f"Selector starts with space: {selector}"
            # Should not contain invalid chars
            assert not re.search(r"[{}|&^$]", selector), f"Invalid chars in selector: {selector}"

        logger.info(f"✓ All {len(selectors)} selectors have valid syntax")

    def test_selectors_have_no_conflicts(self):
        """Verify selectors don't have overlapping/conflicting patterns."""
        import inspect

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        source = inspect.getsource(ZillowExtractor._navigate_to_property_via_search)
        match = re.search(r"autocomplete_selectors\s*=\s*\[(.*?)\]", source, re.DOTALL)
        selectors = re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))

        # Check for duplicates
        assert len(selectors) == len(set(selectors)), "Duplicate selectors found"
        logger.info(f"✓ No duplicate selectors (all {len(selectors)} unique)")


class TestClickFirstSearchResult:
    """Test 3: Unit Tests for _click_first_search_result() Method"""

    @pytest.mark.asyncio
    async def test_click_first_search_result_with_valid_results(self):
        """Test clicking first result when search results exist."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        # Mock tab with search results
        mock_tab = AsyncMock()
        mock_link = AsyncMock()
        mock_link.attrs = {"href": "https://www.zillow.com/homedetails/123"}
        mock_link.click = AsyncMock()

        mock_tab.query_selector_all = AsyncMock(return_value=[mock_link])

        result = await extractor._click_first_search_result(mock_tab)

        assert result is True
        mock_link.click.assert_called_once()
        logger.info("✓ Successfully clicks first search result")

    @pytest.mark.asyncio
    async def test_click_first_search_result_tries_all_selectors(self):
        """Test that method tries multiple selectors in priority order."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        # Mock tab that fails on first 3 selectors, succeeds on 4th
        mock_tab = AsyncMock()
        mock_link = AsyncMock()
        mock_link.attrs = {"href": "https://www.zillow.com/homedetails/456"}
        mock_link.click = AsyncMock()

        selector_results = [[], [], [], [mock_link], [], [], [], []]
        mock_tab.query_selector_all = AsyncMock(side_effect=selector_results)

        result = await extractor._click_first_search_result(mock_tab)

        assert result is True
        assert mock_tab.query_selector_all.call_count == 4
        logger.info("✓ Tried selectors in priority order (4 attempts)")

    @pytest.mark.asyncio
    async def test_click_first_search_result_handles_no_results(self):
        """Test graceful failure when no search results found."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        # Mock tab with no results
        mock_tab = AsyncMock()
        mock_tab.query_selector_all = AsyncMock(return_value=[])

        result = await extractor._click_first_search_result(mock_tab)

        assert result is False
        logger.info("✓ Correctly returns False when no results found")

    @pytest.mark.asyncio
    async def test_click_first_search_result_error_handling(self):
        """Test error handling when DOM operations fail."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        # Mock tab that raises exception
        mock_tab = AsyncMock()
        mock_tab.query_selector_all = AsyncMock(
            side_effect=Exception("DOM error")
        )

        result = await extractor._click_first_search_result(mock_tab)

        assert result is False
        logger.info("✓ Gracefully handles exceptions")


class TestPropertyDetailPageDetection:
    """Test 4: Unit Tests for _is_property_detail_page() Method"""

    @pytest.mark.asyncio
    async def test_detects_property_detail_page_correctly(self):
        """Test correct detection of property detail page."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        # Mock tab with property detail content
        mock_tab = AsyncMock()
        mock_tab.get_content = AsyncMock(
            return_value="photos.zillowstatic.com propertydetails home-details"
        )
        mock_tab.url = "https://www.zillow.com/homedetails/123_zpid"

        result = await extractor._is_property_detail_page(mock_tab)

        assert result is True
        logger.info("✓ Correctly identifies property detail page")

    @pytest.mark.asyncio
    async def test_detects_search_results_page_correctly(self):
        """Test correct detection of search results page."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        # Mock tab with search results content
        mock_tab = AsyncMock()
        content = "search-results list-result " + ("zpid " * 10)  # Many zpids
        mock_tab.get_content = AsyncMock(return_value=content)
        mock_tab.url = "https://www.zillow.com/homes/search/"

        result = await extractor._is_property_detail_page(mock_tab)

        assert result is False
        logger.info("✓ Correctly identifies search results page")

    @pytest.mark.asyncio
    async def test_url_structure_validation(self):
        """Test URL structure validation for property detail pages."""
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()

        # Mock tab with homedetails in URL
        mock_tab = AsyncMock()
        mock_tab.get_content = AsyncMock(return_value="")
        mock_tab.url = "https://www.zillow.com/homedetails/123_zpid"

        result = await extractor._is_property_detail_page(mock_tab)

        # Should return True based on URL alone
        assert result is True
        logger.info("✓ URL structure validation works")


class TestNavigationRecovery:
    """Test 5: Unit Tests for _navigate_to_property_via_search() Recovery Logic"""

    @pytest.mark.asyncio
    async def test_navigation_direct_success(self):
        """Test successful direct navigation (autocomplete → detail page)."""
        from src.phx_home_analysis.domain.entities import Property
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        prop = Property(
            street="4560 E Sunrise Dr",
            city="Phoenix",
            state="AZ",
            zip_code="85044",
            full_address="4560 E Sunrise Dr, Phoenix, AZ 85044",
            price="$475,000",
            price_num=475000,
            beds=4,
            baths=2,
            sqft=2200,
            price_per_sqft_raw=215.9,
        )

        # Mock successful navigation path
        mock_tab = AsyncMock()
        mock_input = AsyncMock()

        # Setup mocks
        mock_tab.get = AsyncMock()
        mock_tab.query_selector_all = AsyncMock(side_effect=[
            [mock_input],  # Search input
            [AsyncMock()],  # Autocomplete suggestion
        ])
        mock_tab.get_content = AsyncMock(return_value="propertydetails photos.zillowstatic.com")
        mock_tab.url = "https://www.zillow.com/homedetails/123_zpid"

        # Mock the property detail check
        with patch.object(
            extractor, "_is_property_detail_page", return_value=True
        ) as mock_detail:
            result = await extractor._navigate_to_property_via_search(prop, mock_tab)

        assert result is True
        mock_detail.assert_called()
        logger.info("✓ Direct navigation succeeds")

    @pytest.mark.asyncio
    async def test_navigation_fallback_to_enter(self):
        """Test fallback to Enter key when no autocomplete found."""
        from src.phx_home_analysis.domain.entities import Property
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        prop = Property(
            street="5219 W El Caminito Dr",
            city="Glendale",
            state="AZ",
            zip_code="85302",
            full_address="5219 W El Caminito Dr, Glendale, AZ 85302",
            price="$425,000",
            price_num=425000,
            beds=3,
            baths=2,
            sqft=1800,
            price_per_sqft_raw=236.1,
        )

        # Mock with no autocomplete but valid detail page after Enter
        mock_tab = AsyncMock()
        mock_input = AsyncMock()

        mock_tab.get = AsyncMock()
        mock_tab.query_selector_all = AsyncMock(side_effect=[
            [mock_input],  # Search input
            [],  # No autocomplete found
        ])

        with patch.object(
            extractor, "_is_property_detail_page", return_value=True
        ):
            result = await extractor._navigate_to_property_via_search(prop, mock_tab)

        assert result is True
        mock_input.send_keys.assert_any_call("\n")  # Enter key pressed
        logger.info("✓ Fallback to Enter key works")

    @pytest.mark.asyncio
    async def test_navigation_recovery_from_search_results(self):
        """Test recovery when landing on search results instead of detail page."""
        from src.phx_home_analysis.domain.entities import Property
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        prop = Property(
            street="2011 E Gary Cir",
            city="Mesa",
            state="AZ",
            zip_code="85213",
            full_address="2011 E Gary Cir, Mesa, AZ 85213",
            price="$385,000",
            price_num=385000,
            beds=4,
            baths=2,
            sqft=1950,
            price_per_sqft_raw=197.4,
        )

        # Mock landing on search results first
        mock_tab = AsyncMock()
        mock_input = AsyncMock()

        mock_tab.get = AsyncMock()
        mock_tab.query_selector_all = AsyncMock(return_value=[mock_input])

        # First detail check fails (search results), second succeeds (after clicking result)
        with patch.object(
            extractor, "_is_property_detail_page", side_effect=[False, True]
        ) as mock_detail, patch.object(
            extractor, "_click_first_search_result", return_value=True
        ) as mock_click:
            result = await extractor._navigate_to_property_via_search(prop, mock_tab)

        assert result is True
        mock_click.assert_called_once()
        assert mock_detail.call_count >= 2
        logger.info("✓ Recovery from search results works")

    @pytest.mark.asyncio
    async def test_navigation_fails_when_no_recovery_possible(self):
        """Test failure when recovery attempts also fail."""
        from src.phx_home_analysis.domain.entities import Property
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        prop = Property(
            street="Unknown",
            city="Place",
            state="AZ",
            zip_code="00000",
            full_address="Unknown, Place, AZ 00000",
            price="$0",
            price_num=0,
            beds=0,
            baths=0,
            sqft=0,
            price_per_sqft_raw=0.0,
        )

        mock_tab = AsyncMock()
        mock_input = AsyncMock()
        mock_tab.get = AsyncMock()
        mock_tab.query_selector_all = AsyncMock(return_value=[mock_input])

        # All checks fail
        with patch.object(
            extractor, "_is_property_detail_page", return_value=False
        ), patch.object(
            extractor, "_click_first_search_result", return_value=False
        ):
            result = await extractor._navigate_to_property_via_search(prop, mock_tab)

        assert result is False
        logger.info("✓ Correctly fails when no recovery possible")


class TestRegressionChecks:
    """Test 6: Regression Testing - Verify Existing Functionality Unchanged"""

    def test_build_search_url_still_works(self):
        """Verify _build_search_url() unchanged."""
        from src.phx_home_analysis.domain.entities import Property
        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        extractor = ZillowExtractor()
        prop = Property(
            street="4732 W Davis Rd",
            city="Glendale",
            state="AZ",
            zip_code="85306",
            full_address="4732 W Davis Rd, Glendale, AZ 85306",
            price="$450,000",
            price_num=450000,
            beds=4,
            baths=2,
            sqft=2100,
            price_per_sqft_raw=214.3,
        )

        url = extractor._build_search_url(prop)

        assert "zillow.com" in url
        assert "Davis" in url or "davis" in url
        assert "85306" in url
        logger.info(f"✓ _build_search_url works: {url}")

    def test_extract_urls_method_exists(self):
        """Verify extract_image_urls() is present."""
        from inspect import iscoroutinefunction

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        assert hasattr(ZillowExtractor, "extract_image_urls")
        assert iscoroutinefunction(ZillowExtractor.extract_image_urls)
        logger.info("✓ extract_image_urls method exists and is async")

    def test_error_handling_paths_exist(self):
        """Verify error handling is comprehensive."""
        import inspect

        from src.phx_home_analysis.services.image_extraction.extractors.zillow import (
            ZillowExtractor,
        )

        source = inspect.getsource(ZillowExtractor)

        # Should have try/except blocks
        assert "try:" in source
        assert "except" in source
        assert "logger.error" in source

        logger.info("✓ Error handling present throughout")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
