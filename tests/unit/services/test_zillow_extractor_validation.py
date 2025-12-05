"""Comprehensive validation tests for Zillow extractor fixes.

Tests the three key modifications:
1. _click_first_search_result() method (87 lines)
2. Enhanced autocomplete selectors (8 selectors)
3. _navigate_to_property_via_search() recovery logic

Also validates the 2-layer CAPTCHA bypass implementation with page refresh detection.

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
    async def test_click_first_search_result_with_valid_results(self) -> None:
        """Test clicking first result when search results exist."""
        from unittest.mock import patch

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

        # Patch internal async methods that are called after click
        with patch.object(
            extractor, "_wait_for_property_detail_page", new=AsyncMock(return_value=True)
        ):
            result = await extractor._click_first_search_result(mock_tab)

        assert result is True
        mock_link.click.assert_called_once()
        logger.info("✓ Successfully clicks first search result")

    @pytest.mark.asyncio
    async def test_click_first_search_result_tries_all_selectors(self) -> None:
        """Test that method tries multiple selectors in priority order."""
        from unittest.mock import patch

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

        # Patch internal async methods that are called after click
        with patch.object(
            extractor, "_wait_for_property_detail_page", new=AsyncMock(return_value=True)
        ):
            result = await extractor._click_first_search_result(mock_tab)

        assert result is True
        assert mock_tab.query_selector_all.call_count == 4
        logger.info("✓ Tried selectors in priority order (4 attempts)")

    @pytest.mark.asyncio
    async def test_click_first_search_result_handles_no_results(self) -> None:
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
    async def test_click_first_search_result_error_handling(self) -> None:
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

        # Mock the property detail check (must use AsyncMock for async method)
        with patch.object(
            extractor, "_is_property_detail_page", new=AsyncMock(return_value=True)
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

        # Track call count to determine what to return
        # Search input selectors use "search" in the selector string
        # Autocomplete selectors use different patterns
        call_count = {"value": 0}
        search_input_found = {"value": False}

        async def mock_query_selector_all(selector: str):
            call_count["value"] += 1
            # Return search input on first call to a search selector
            if not search_input_found["value"] and ("search" in selector.lower() or "input" in selector.lower()):
                search_input_found["value"] = True
                return [mock_input]
            # Return empty for all autocomplete selectors (simulating no autocomplete)
            return []

        mock_tab.query_selector_all = mock_query_selector_all

        # _is_property_detail_page returns False for direct URL attempt (Step 0),
        # then _wait_for_property_detail_page returns True after Enter key
        with patch.object(
            extractor, "_is_property_detail_page", new=AsyncMock(return_value=False)
        ), patch.object(
            extractor, "_wait_for_property_detail_page", new=AsyncMock(return_value=True)
        ), patch.object(
            extractor, "_check_for_captcha", new=AsyncMock(return_value=False)
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
        mock_autocomplete = AsyncMock()

        mock_tab.get = AsyncMock()

        # Track state to return correct values based on selector type
        search_input_found = {"value": False}
        autocomplete_found = {"value": False}

        async def mock_query_selector_all(selector: str):
            # Return search input on first call to a search selector
            if not search_input_found["value"] and ("search" in selector.lower() or "input" in selector.lower()):
                search_input_found["value"] = True
                return [mock_input]
            # Return autocomplete suggestion on first call to an autocomplete selector
            if not autocomplete_found["value"] and ("suggestion" in selector.lower() or "result" in selector.lower() or "autocomplete" in selector.lower() or "option" in selector.lower() or "li" in selector.lower()):
                autocomplete_found["value"] = True
                return [mock_autocomplete]
            return []

        mock_tab.query_selector_all = mock_query_selector_all

        # _is_property_detail_page returns False for direct URL (Step 0)
        # _wait_for_property_detail_page returns False (landed on search results)
        # _click_first_search_result is called as recovery
        with patch.object(
            extractor, "_is_property_detail_page", new=AsyncMock(return_value=False)
        ), patch.object(
            extractor, "_wait_for_property_detail_page", new=AsyncMock(return_value=False)
        ), patch.object(
            extractor, "_click_first_search_result", new=AsyncMock(return_value=True)
        ) as mock_click, patch.object(
            extractor, "_check_for_captcha", new=AsyncMock(return_value=False)
        ):
            result = await extractor._navigate_to_property_via_search(prop, mock_tab)

        assert result is True
        mock_click.assert_called_once()
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


class TestCaptchaV2Integration:
    """Tests for 2-layer CAPTCHA bypass with page refresh detection.

    The 2-layer CAPTCHA system handles PerimeterX's page refresh behavior:
    - Layer 1: Short initial hold (1.5-2.5s) that will be interrupted by refresh
    - Layer 2: After detecting refresh, longer retry hold (4.5-6.5s) for actual solve

    Tests validate:
    - Required imports and method signatures in stealth_base.py
    - Configuration fields with proper defaults and validation
    - Call site migration to v2 solver across all extractors
    """

    def test_imports_time_and_log_captcha_event(self) -> None:
        """Verify stealth_base.py imports time module and log_captcha_event.

        These imports are required for:
        - time: Measuring elapsed time for refresh detection
        - log_captcha_event: Structured logging of CAPTCHA interactions
        """
        import ast
        from pathlib import Path

        stealth_base_path = Path("src/phx_home_analysis/services/image_extraction/extractors/stealth_base.py")
        source = stealth_base_path.read_text(encoding="utf-8")
        tree = ast.parse(source)

        import_names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    import_names.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    import_names.append(alias.name)

        assert "time" in import_names, "import time missing from stealth_base.py"
        assert "log_captcha_event" in import_names, "log_captcha_event import missing"
        logger.info("Required imports present: time, log_captcha_event")

    def test_detect_page_refresh_method_exists(self) -> None:
        """Verify _detect_page_refresh method exists with correct signature.

        Method signature must include:
        - tab: Browser tab to monitor
        - initial_url: URL before CAPTCHA interaction
        - initial_content_length: Page content length for comparison
        """
        import inspect

        from phx_home_analysis.services.image_extraction.extractors.stealth_base import (
            StealthBrowserExtractor,
        )

        assert hasattr(StealthBrowserExtractor, "_detect_page_refresh")
        method = StealthBrowserExtractor._detect_page_refresh
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        assert "tab" in params, "Missing 'tab' parameter"
        assert "initial_url" in params, "Missing 'initial_url' parameter"
        assert "initial_content_length" in params, "Missing 'initial_content_length' parameter"
        logger.info(f"_detect_page_refresh method exists with params: {params}")

    def test_attempt_captcha_solve_has_attempt_number_param(self) -> None:
        """Verify _attempt_captcha_solve accepts attempt_number with default=1.

        The attempt_number parameter controls timing:
        - attempt_number=1: Uses initial hold timing (shorter, expects interrupt)
        - attempt_number>1: Uses retry hold timing (longer, for actual solve)
        """
        import inspect

        from phx_home_analysis.services.image_extraction.extractors.stealth_base import (
            StealthBrowserExtractor,
        )

        method = StealthBrowserExtractor._attempt_captcha_solve
        sig = inspect.signature(method)
        params = sig.parameters

        assert "attempt_number" in params, "Missing 'attempt_number' parameter"
        assert params["attempt_number"].default == 1, (
            f"Expected default=1, got {params['attempt_number'].default}"
        )
        logger.info("_attempt_captcha_solve has attempt_number parameter with default=1")

    def test_config_has_2layer_timing_fields(self) -> None:
        """Verify StealthExtractionConfig has all 2-layer timing fields with correct defaults.

        Expected fields and defaults:
        - captcha_initial_hold_min: 1.5s (first attempt minimum)
        - captcha_initial_hold_max: 2.5s (first attempt maximum)
        - captcha_retry_hold_min: 4.5s (retry attempt minimum)
        - captcha_retry_hold_max: 6.5s (retry attempt maximum)
        - captcha_refresh_wait: 2.0s (delay after detecting refresh)
        """
        from phx_home_analysis.config.settings import StealthExtractionConfig

        config = StealthExtractionConfig()

        # Verify fields exist
        assert hasattr(config, "captcha_initial_hold_min"), "Missing captcha_initial_hold_min"
        assert hasattr(config, "captcha_initial_hold_max"), "Missing captcha_initial_hold_max"
        assert hasattr(config, "captcha_retry_hold_min"), "Missing captcha_retry_hold_min"
        assert hasattr(config, "captcha_retry_hold_max"), "Missing captcha_retry_hold_max"
        assert hasattr(config, "captcha_refresh_wait"), "Missing captcha_refresh_wait"

        # Verify exact default values
        assert config.captcha_initial_hold_min == 1.5, (
            f"Expected 1.5, got {config.captcha_initial_hold_min}"
        )
        assert config.captcha_initial_hold_max == 2.5, (
            f"Expected 2.5, got {config.captcha_initial_hold_max}"
        )
        assert config.captcha_retry_hold_min == 4.5, (
            f"Expected 4.5, got {config.captcha_retry_hold_min}"
        )
        assert config.captcha_retry_hold_max == 6.5, (
            f"Expected 6.5, got {config.captcha_retry_hold_max}"
        )
        assert config.captcha_refresh_wait == 2.0, (
            f"Expected 2.0, got {config.captcha_refresh_wait}"
        )
        logger.info("All 2-layer CAPTCHA config fields present with correct defaults")

    def test_all_call_sites_use_v2_solver(self) -> None:
        """Verify all CAPTCHA call sites migrated to _attempt_captcha_solve_v2.

        Expected call counts:
        - zillow.py: 5 calls to v2 solver (various navigation paths)
        - stealth_base.py: 1 call to v2 solver (base extract_image_urls)
        - v1 solver only called internally by v2 with attempt_number parameter
        """
        from pathlib import Path

        zillow_path = Path("src/phx_home_analysis/services/image_extraction/extractors/zillow.py")
        stealth_base_path = Path("src/phx_home_analysis/services/image_extraction/extractors/stealth_base.py")

        # Check zillow.py - should have v2 calls only
        zillow_source = zillow_path.read_text(encoding="utf-8")
        v2_calls_zillow = re.findall(r"await self\._attempt_captcha_solve_v2\(tab\)", zillow_source)

        assert len(v2_calls_zillow) == 5, (
            f"Expected 5 v2 calls in zillow.py, found {len(v2_calls_zillow)}"
        )
        logger.info(f"Found {len(v2_calls_zillow)} v2 calls in zillow.py")

        # Check stealth_base.py - should have 1 v2 call in extract_image_urls
        stealth_source = stealth_base_path.read_text(encoding="utf-8")
        v2_calls_stealth = re.findall(r"await self\._attempt_captcha_solve_v2\(tab\)", stealth_source)

        assert len(v2_calls_stealth) == 1, (
            f"Expected 1 v2 call in stealth_base.py, found {len(v2_calls_stealth)}"
        )
        logger.info(f"Found {len(v2_calls_stealth)} v2 call in stealth_base.py")

        # Verify v1 calls only appear inside v2 with attempt_number
        v1_with_attempt = re.findall(r"await self\._attempt_captcha_solve\(tab, attempt_number=", stealth_source)
        assert len(v1_with_attempt) == 1, (
            "v2 should call v1 exactly once with attempt_number parameter"
        )
        logger.info("v2 correctly calls v1 with attempt_number parameter")


class TestCaptchaTimingValidation:
    """Tests for CAPTCHA timing configuration validation.

    Validates that StealthExtractionConfig enforces:
    - All timing values must be positive (> 0)
    - Min values must be <= max values for timing ranges
    - Environment variable overrides work correctly
    """

    def test_config_rejects_negative_initial_hold_min(self) -> None:
        """Verify config rejects negative captcha_initial_hold_min."""
        from phx_home_analysis.config.settings import StealthExtractionConfig

        with pytest.raises(ValueError, match="captcha_initial_hold_min must be positive"):
            StealthExtractionConfig(captcha_initial_hold_min=-1.0)

    def test_config_rejects_zero_initial_hold_min(self) -> None:
        """Verify config rejects zero captcha_initial_hold_min."""
        from phx_home_analysis.config.settings import StealthExtractionConfig

        with pytest.raises(ValueError, match="captcha_initial_hold_min must be positive"):
            StealthExtractionConfig(captcha_initial_hold_min=0.0)

    def test_config_rejects_negative_refresh_wait(self) -> None:
        """Verify config rejects negative captcha_refresh_wait."""
        from phx_home_analysis.config.settings import StealthExtractionConfig

        with pytest.raises(ValueError, match="captcha_refresh_wait must be positive"):
            StealthExtractionConfig(captcha_refresh_wait=-0.5)

    def test_config_rejects_initial_min_greater_than_max(self) -> None:
        """Verify config rejects initial_hold_min > initial_hold_max."""
        from phx_home_analysis.config.settings import StealthExtractionConfig

        with pytest.raises(ValueError, match="captcha_initial_hold_min.*must be <="):
            StealthExtractionConfig(
                captcha_initial_hold_min=3.0,
                captcha_initial_hold_max=2.0,
            )

    def test_config_rejects_retry_min_greater_than_max(self) -> None:
        """Verify config rejects retry_hold_min > retry_hold_max."""
        from phx_home_analysis.config.settings import StealthExtractionConfig

        with pytest.raises(ValueError, match="captcha_retry_hold_min.*must be <="):
            StealthExtractionConfig(
                captcha_retry_hold_min=8.0,
                captcha_retry_hold_max=5.0,
            )

    def test_config_accepts_equal_min_and_max(self) -> None:
        """Verify config accepts timing ranges where min equals max."""
        from phx_home_analysis.config.settings import StealthExtractionConfig

        # Should not raise - equal min/max is valid (fixed timing)
        config = StealthExtractionConfig(
            captcha_initial_hold_min=2.0,
            captcha_initial_hold_max=2.0,
            captcha_retry_hold_min=5.0,
            captcha_retry_hold_max=5.0,
        )
        assert config.captcha_initial_hold_min == config.captcha_initial_hold_max
        assert config.captcha_retry_hold_min == config.captcha_retry_hold_max
        logger.info("Config accepts equal min/max timing values")

    def test_config_accepts_custom_positive_values(self) -> None:
        """Verify config accepts custom positive timing values."""
        from phx_home_analysis.config.settings import StealthExtractionConfig

        config = StealthExtractionConfig(
            captcha_initial_hold_min=0.5,
            captcha_initial_hold_max=1.0,
            captcha_retry_hold_min=3.0,
            captcha_retry_hold_max=10.0,
            captcha_refresh_wait=0.1,
        )
        assert config.captcha_initial_hold_min == 0.5
        assert config.captcha_initial_hold_max == 1.0
        assert config.captcha_retry_hold_min == 3.0
        assert config.captcha_retry_hold_max == 10.0
        assert config.captcha_refresh_wait == 0.1
        logger.info("Config accepts custom positive timing values")

    def test_from_env_loads_captcha_timing_overrides(self) -> None:
        """Verify from_env() respects CAPTCHA timing environment variables."""
        import os

        from phx_home_analysis.config.settings import StealthExtractionConfig

        # Set environment variables
        env_overrides = {
            "CAPTCHA_INITIAL_HOLD_MIN": "2.0",
            "CAPTCHA_INITIAL_HOLD_MAX": "3.0",
            "CAPTCHA_RETRY_HOLD_MIN": "5.0",
            "CAPTCHA_RETRY_HOLD_MAX": "7.0",
            "CAPTCHA_REFRESH_WAIT": "1.5",
        }

        # Store original values
        original_values = {k: os.environ.get(k) for k in env_overrides}

        try:
            # Set test values
            for key, value in env_overrides.items():
                os.environ[key] = value

            config = StealthExtractionConfig.from_env()

            assert config.captcha_initial_hold_min == 2.0, (
                f"Expected 2.0, got {config.captcha_initial_hold_min}"
            )
            assert config.captcha_initial_hold_max == 3.0, (
                f"Expected 3.0, got {config.captcha_initial_hold_max}"
            )
            assert config.captcha_retry_hold_min == 5.0, (
                f"Expected 5.0, got {config.captcha_retry_hold_min}"
            )
            assert config.captcha_retry_hold_max == 7.0, (
                f"Expected 7.0, got {config.captcha_retry_hold_max}"
            )
            assert config.captcha_refresh_wait == 1.5, (
                f"Expected 1.5, got {config.captcha_refresh_wait}"
            )
            logger.info("from_env() correctly loads CAPTCHA timing overrides")
        finally:
            # Restore original values
            for key, original in original_values.items():
                if original is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original

    def test_from_env_uses_defaults_for_invalid_values(self) -> None:
        """Verify from_env() uses defaults when env vars contain invalid floats."""
        import os

        from phx_home_analysis.config.settings import StealthExtractionConfig

        # Store original value
        original = os.environ.get("CAPTCHA_INITIAL_HOLD_MIN")

        try:
            os.environ["CAPTCHA_INITIAL_HOLD_MIN"] = "not_a_number"
            config = StealthExtractionConfig.from_env()

            # Should fall back to default
            assert config.captcha_initial_hold_min == 1.5, (
                f"Expected default 1.5, got {config.captcha_initial_hold_min}"
            )
            logger.info("from_env() uses defaults for invalid env var values")
        finally:
            if original is None:
                os.environ.pop("CAPTCHA_INITIAL_HOLD_MIN", None)
            else:
                os.environ["CAPTCHA_INITIAL_HOLD_MIN"] = original


class TestRegressionChecks:
    """Test 8: Regression Testing - Verify Existing Functionality Unchanged"""

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
