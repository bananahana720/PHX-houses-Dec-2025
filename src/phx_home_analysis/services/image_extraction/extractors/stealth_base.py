"""Stealth browser-based extractor base class using nodriver and curl_cffi.

This module provides a base class for Zillow and Redfin extractors that need
to bypass PerimeterX and other anti-bot systems using stealth techniques.
"""

import asyncio
import logging
import random
from abc import abstractmethod
from typing import Optional

import httpx
import nodriver as uc

from ....config.settings import StealthExtractionConfig
from ....domain.entities import Property
from ....domain.enums import ImageSource
from ...infrastructure import BrowserPool, StealthHttpClient
from .base import ExtractionError, ImageExtractor, SourceUnavailableError

logger = logging.getLogger(__name__)


class StealthBrowserExtractor(ImageExtractor):
    """Abstract base class for stealth browser-based extraction.

    Extends ImageExtractor with nodriver browser automation and curl_cffi
    HTTP client for bypassing anti-bot systems like PerimeterX.

    Uses template method pattern:
    - Subclasses implement _build_search_url() and _extract_urls_from_page()
    - Base class handles navigation, CAPTCHA detection/solving, and delays

    Example:
        ```python
        class ZillowExtractor(StealthBrowserExtractor):
            @property
            def source(self) -> ImageSource:
                return ImageSource.ZILLOW

            def _build_search_url(self, property: Property) -> str:
                return f"https://zillow.com/homes/{property.full_address}"

            async def _extract_urls_from_page(self, tab: uc.Tab) -> list[str]:
                # Extract image URLs from page
                return urls
        ```
    """

    def __init__(
        self,
        http_client: Optional[httpx.AsyncClient] = None,
        timeout: float = 30.0,
        config: Optional[StealthExtractionConfig] = None,
    ):
        """Initialize stealth extractor with browser and HTTP client.

        Args:
            http_client: Shared httpx client (not used - maintained for compatibility)
            timeout: Request timeout in seconds
            config: Stealth extraction configuration (loaded from env if not provided)
        """
        # Call parent constructor (maintains compatibility but we don't use http_client)
        super().__init__(http_client=http_client, timeout=timeout)

        # Load config from environment if not provided
        self.config = config or StealthExtractionConfig.from_env()

        # Initialize browser pool
        self._browser_pool = BrowserPool(
            proxy_url=self.config.proxy_url,
            headless=self.config.browser_headless,
            viewport_width=self.config.viewport_width,
            viewport_height=self.config.viewport_height,
        )

        # Initialize stealth HTTP client
        self._stealth_client = StealthHttpClient(
            proxy_url=self.config.proxy_url,
            timeout=self.config.request_timeout,
            max_retries=self.config.max_retries,
        )

        logger.info(
            "%s initialized with stealth config: headless=%s, proxy=%s",
            self.name,
            self.config.browser_headless,
            "enabled" if self.config.is_configured else "disabled",
        )

    async def download_image(self, url: str) -> tuple[bytes, str]:
        """Download image using stealth HTTP client.

        Args:
            url: Image URL to download

        Returns:
            Tuple of (image_bytes, content_type)

        Raises:
            ImageDownloadError: If download fails after retries
        """
        logger.debug("%s downloading image: %s", self.name, url)
        return await self._stealth_client.download_image(url=url)

    async def close(self) -> None:
        """Close browser pool and HTTP client resources."""
        logger.info("%s closing resources", self.name)

        # Close browser pool
        await self._browser_pool.close()

        # Close stealth HTTP client
        await self._stealth_client.close()

        # Close parent's HTTP client if we own it
        await super().close()

        logger.info("%s resources closed", self.name)

    async def extract_image_urls(self, property: Property) -> list[str]:
        """Extract image URLs using stealth browser navigation.

        Template method that:
        1. Builds search URL (subclass implements)
        2. Navigates with stealth techniques
        3. Detects and attempts to solve CAPTCHAs
        4. Extracts URLs from page (subclass implements)

        Args:
            property: Property to find images for

        Returns:
            List of image URLs discovered

        Raises:
            SourceUnavailableError: If CAPTCHA solving fails
            ExtractionError: For other extraction failures
        """
        url = self._build_search_url(property)
        logger.info("%s extracting images for: %s", self.name, property.full_address)

        tab = await self._navigate_with_stealth(url)

        try:
            # Check for CAPTCHA
            if await self._check_for_captcha(tab):
                logger.warning("%s CAPTCHA detected for %s", self.name, url)

                # Attempt to solve CAPTCHA
                if not await self._attempt_captcha_solve(tab):
                    logger.error(
                        "%s CAPTCHA solving failed for %s", self.name, url
                    )
                    raise SourceUnavailableError(
                        self.source,
                        "CAPTCHA detected and solving failed",
                        retry_after=300,  # 5 minutes
                    )

                logger.info("%s CAPTCHA solved for %s", self.name, url)

            # Add human delay before extraction
            await self._human_delay()

            # Extract URLs from page (subclass implements)
            urls = await self._extract_urls_from_page(tab)

            logger.info(
                "%s extracted %d image URLs for %s",
                self.name,
                len(urls),
                property.full_address,
            )

            return urls

        finally:
            # Always close the tab
            try:
                await tab.close()
            except Exception as e:
                logger.warning("%s error closing tab: %s", self.name, e)

    @abstractmethod
    def _build_search_url(self, property: Property) -> str:
        """Build search URL for property listing.

        Args:
            property: Property to build URL for

        Returns:
            Full URL to navigate to
        """
        pass

    @abstractmethod
    async def _extract_urls_from_page(self, tab: uc.Tab) -> list[str]:
        """Extract image URLs from the current page.

        Args:
            tab: Browser tab with loaded page

        Returns:
            List of image URLs found
        """
        pass

    async def _navigate_with_stealth(self, url: str) -> uc.Tab:
        """Navigate to URL with stealth techniques and human delays.

        Args:
            url: URL to navigate to

        Returns:
            Browser tab ready for interaction

        Raises:
            ExtractionError: If navigation fails
        """
        logger.info("%s navigating to: %s", self.name, url)

        try:
            # Add initial delay to appear more human-like
            await self._human_delay()

            # Get browser and create new tab
            browser = await self._browser_pool.get_browser()
            tab = await browser.get(url)

            # Wait for page to stabilize
            await self._human_delay()

            logger.info("%s navigation complete", self.name)
            return tab

        except Exception as e:
            logger.error("%s navigation failed: %s", self.name, e)
            raise ExtractionError(f"Navigation failed for {url}: {e}")

    async def _check_for_captcha(self, tab: uc.Tab) -> bool:
        """Check if CAPTCHA is blocking the page (not just present in code).

        Only returns True if the page appears to be a CAPTCHA interstitial,
        not if CAPTCHA code exists in a valid property page.

        Detection strategy:
        1. If page content is small (<50KB), check for CAPTCHA indicators
        2. If page has property content indicators, assume CAPTCHA was passed

        Args:
            tab: Browser tab to check

        Returns:
            True if CAPTCHA is blocking content, False otherwise
        """
        try:
            # Get page content
            page_text = await tab.get_content()
            page_text_lower = page_text.lower()
            content_length = len(page_text)

            # If page has substantial content (>50KB), check for property indicators
            # This means the page loaded successfully even if CAPTCHA code exists
            if content_length > 50000:
                property_indicators = [
                    "zillowstatic.com",
                    "photos.zillow",
                    "property details",
                    "home details",
                    "beds",
                    "baths",
                    "sqft",
                    "redfin.com",
                    "listing",
                ]
                for indicator in property_indicators:
                    if indicator in page_text_lower:
                        logger.debug(
                            "%s page has property content (%d chars), "
                            "skipping CAPTCHA check",
                            self.name,
                            content_length,
                        )
                        return False

            # For small pages, check for CAPTCHA indicators
            captcha_indicators = [
                "press and hold",
                "px-captcha",
                "perimeterx",
            ]

            for indicator in captcha_indicators:
                if indicator in page_text_lower:
                    logger.warning(
                        "%s CAPTCHA indicator found: %s (page: %d chars)",
                        self.name,
                        indicator,
                        content_length,
                    )
                    return True

            return False

        except Exception as e:
            logger.warning("%s error checking for CAPTCHA: %s", self.name, e)
            # Assume no CAPTCHA if we can't check
            return False

    async def _attempt_captcha_solve(self, tab: uc.Tab) -> bool:
        """Attempt to solve Press & Hold CAPTCHA.

        Strategy:
        1. Find button element with "px-captcha" class or "Press & Hold" text
        2. Get element position
        3. Move mouse to element with human-like movement
        4. Mouse down, hold for random duration, mouse up
        5. Wait for page reload/change
        6. Verify CAPTCHA is gone

        Args:
            tab: Browser tab with CAPTCHA

        Returns:
            True if CAPTCHA solved, False otherwise
        """
        logger.info("%s attempting CAPTCHA solve", self.name)

        try:
            # Find CAPTCHA button
            # Try multiple selectors in order of specificity
            selectors = [
                "button[class*='px-captcha']",
                "div[class*='px-captcha'] button",
                "button:contains('Press & Hold')",
                "button:contains('Press and Hold')",
            ]

            element = None
            for selector in selectors:
                try:
                    # Query element (handle different nodriver API versions)
                    element = await tab.select(selector)
                    if element:
                        logger.debug(
                            "%s found CAPTCHA button with selector: %s",
                            self.name,
                            selector,
                        )
                        break
                except Exception:
                    continue

            if not element:
                logger.warning("%s could not find CAPTCHA button", self.name)
                return False

            # Get element position
            # Note: nodriver API may vary - adjust as needed
            try:
                rect = await element.get_box_model()
                if rect and "content" in rect:
                    # Get center of element
                    x = int(sum(rect["content"][0::2]) / 4)
                    y = int(sum(rect["content"][1::2]) / 4)
                else:
                    # Fallback position if can't get box model
                    logger.warning(
                        "%s could not get element position, using default",
                        self.name,
                    )
                    x, y = 640, 360  # Center of 1280x720 viewport
            except AttributeError:
                # Fallback if method not available
                logger.warning(
                    "%s get_box_model not available, using element click",
                    self.name,
                )
                x, y = None, None

            # Move mouse to element
            if x is not None and y is not None:
                await BrowserPool.human_mouse_move(tab, x, y)
                await self._human_delay()

            # Hold duration (random between config values)
            hold_duration = random.uniform(
                self.config.captcha_hold_min,
                self.config.captcha_hold_max,
            )

            logger.info(
                "%s pressing and holding CAPTCHA button for %.2fs",
                self.name,
                hold_duration,
            )

            # Perform press and hold
            try:
                # If we have coordinates, use mouse events
                if x is not None and y is not None:
                    await tab.mouse_down(x, y)
                    await asyncio.sleep(hold_duration)
                    await tab.mouse_up(x, y)
                else:
                    # Fallback: just click the element
                    await element.click()
                    await asyncio.sleep(hold_duration)

            except AttributeError:
                # Fallback if mouse methods not available
                logger.warning(
                    "%s mouse events not available, using element click",
                    self.name,
                )
                await element.click()
                await asyncio.sleep(hold_duration)

            # Wait for page to change (CAPTCHA solve typically triggers navigation)
            await asyncio.sleep(3.0)

            # Check if CAPTCHA is gone
            captcha_still_present = await self._check_for_captcha(tab)

            if captcha_still_present:
                logger.warning("%s CAPTCHA still present after solve attempt", self.name)
                return False

            logger.info("%s CAPTCHA solved successfully", self.name)
            return True

        except Exception as e:
            logger.error("%s error solving CAPTCHA: %s", self.name, e)
            return False

    async def _human_delay(self) -> None:
        """Sleep for random duration to simulate human behavior.

        Uses configured min/max delay values from StealthExtractionConfig.
        """
        delay = random.uniform(
            self.config.human_delay_min,
            self.config.human_delay_max,
        )
        logger.debug("%s human delay: %.2fs", self.name, delay)
        await asyncio.sleep(delay)
