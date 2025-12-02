"""Base class for location data extractors using nodriver.

This module provides abstract base classes for extracting structured location
data (schools, crime, walk scores, noise) using stealth browser automation.
"""

import asyncio
import logging
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

import nodriver as uc

from ...config.settings import StealthExtractionConfig
from ...domain.entities import Property
from ..infrastructure import BrowserPool

logger = logging.getLogger(__name__)

T = TypeVar("T")  # Generic type for extracted data


@dataclass
class ExtractionResult(Generic[T]):
    """Result of a location data extraction.

    Attributes:
        success: Whether extraction succeeded
        data: Extracted data object (None if failed)
        error: Error message if extraction failed
        source_url: URL data was extracted from
    """
    success: bool
    data: T | None = None
    error: str | None = None
    source_url: str | None = None


class LocationDataExtractor(ABC, Generic[T]):
    """Abstract base for location data extractors using nodriver.

    Template method pattern similar to StealthBrowserExtractor but for
    structured data extraction rather than images.

    Subclasses implement:
        - name: Human-readable extractor name
        - _build_url(): Build URL to fetch from
        - _extract_data(): Parse structured data from loaded page

    Base class handles:
        - Browser pool management
        - Human-like navigation delays
        - Error handling and logging
        - Resource cleanup

    Example:
        ```python
        class CrimeDataExtractor(LocationDataExtractor[CrimeData]):
            @property
            def name(self) -> str:
                return "CrimeData"

            def _build_url(self, property: Property) -> str:
                return f"https://example.com/crime/{property.zip_code}"

            async def _extract_data(self, tab: uc.Tab) -> CrimeData:
                # Extract and parse data from page
                return CrimeData(...)
        ```
    """

    def __init__(
        self,
        config: StealthExtractionConfig | None = None,
        cache_days: int = 30,
    ):
        """Initialize location data extractor.

        Args:
            config: Stealth extraction configuration (loaded from env if None)
            cache_days: Number of days to cache extracted data
        """
        self.config = config or StealthExtractionConfig.from_env()
        self.cache_days = cache_days
        self._browser_pool = BrowserPool(
            proxy_url=self.config.proxy_url,
            headless=self.config.browser_headless,
            viewport_width=self.config.viewport_width,
            viewport_height=self.config.viewport_height,
        )

        logger.info(
            "%s extractor initialized: headless=%s, proxy=%s",
            self.name,
            self.config.browser_headless,
            "enabled" if self.config.is_configured else "disabled",
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable extractor name for logging.

        Returns:
            Extractor name (e.g., "CrimeData", "WalkScore")
        """
        pass

    @abstractmethod
    def _build_url(self, property: Property) -> str:
        """Build URL to fetch data from for given property.

        Args:
            property: Property entity with address/location data

        Returns:
            Full URL to navigate to
        """
        pass

    @abstractmethod
    async def _extract_data(self, tab: uc.Tab) -> T:
        """Extract structured data from loaded page.

        Args:
            tab: Browser tab with page loaded

        Returns:
            Extracted data object

        Raises:
            Exception: If data extraction fails
        """
        pass

    async def extract(self, property: Property) -> ExtractionResult[T]:
        """Extract location data for property.

        Template method that orchestrates:
        1. Build URL from property
        2. Navigate with stealth techniques
        3. Extract structured data
        4. Handle errors and cleanup

        Args:
            property: Property to extract data for

        Returns:
            ExtractionResult with data or error
        """
        url = self._build_url(property)
        logger.info("%s extracting for: %s", self.name, property.full_address)
        logger.debug("%s URL: %s", self.name, url)

        tab = None
        try:
            # Navigate with human delays
            tab = await self._navigate_with_stealth(url)

            # Extract data from page
            data = await self._extract_data(tab)

            logger.info("%s extraction successful for %s", self.name, property.full_address)
            return ExtractionResult(success=True, data=data, source_url=url)

        except Exception as e:
            logger.error("%s extraction failed for %s: %s", self.name, property.full_address, e)
            return ExtractionResult(success=False, error=str(e), source_url=url)

        finally:
            # Always close the tab
            if tab:
                try:
                    await tab.close()
                except Exception as e:
                    logger.warning("%s error closing tab: %s", self.name, e)

    async def _navigate_with_stealth(self, url: str) -> uc.Tab:
        """Navigate to URL with stealth techniques and human delays.

        Args:
            url: URL to navigate to

        Returns:
            Browser tab ready for interaction

        Raises:
            Exception: If navigation fails
        """
        logger.debug("%s navigating to: %s", self.name, url)

        # Add initial delay to appear more human-like
        await self._human_delay()

        # Get browser and create new tab
        browser = await self._browser_pool.get_browser()
        tab = await browser.get(url)

        # Wait for page to stabilize
        await self._human_delay()

        logger.debug("%s navigation complete", self.name)
        return tab

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

    async def close(self) -> None:
        """Close browser resources."""
        logger.info("%s closing resources", self.name)
        await self._browser_pool.close()
        logger.info("%s resources closed", self.name)
