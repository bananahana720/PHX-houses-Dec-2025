"""Noise data extractor using HowLoud.com."""

import logging
import re
from urllib.parse import quote_plus

import nodriver as uc

from ...domain.entities import Property
from ..location_data import LocationDataExtractor
from .models import NoiseData

logger = logging.getLogger(__name__)


class HowLoudExtractor(LocationDataExtractor[NoiseData]):
    """Extract noise levels and sources from HowLoud.com.

    Source: https://howloud.com/search?q={encoded_address}

    Extracts:
        - Noise score (0-100, 100=quietest)
        - Noise sources (traffic, airport, local, etc.)

    Example:
        ```python
        async with HowLoudExtractor() as extractor:
            result = await extractor.extract(property)
            if result.success:
                print(f"Noise score: {result.data.noise_score}")
                print(f"Sources: {result.data.noise_sources}")
        ```
    """

    @property
    def name(self) -> str:
        """Extractor name for logging."""
        return "HowLoud"

    def _build_url(self, property: Property) -> str:
        """Build HowLoud.com search URL for property address.

        Args:
            property: Property with full_address

        Returns:
            Full URL to noise assessment page
        """
        # Encode address for URL search
        encoded_address = quote_plus(property.full_address)
        url = f"https://howloud.com/search?q={encoded_address}"
        logger.debug("%s built URL: %s", self.name, url)
        return url

    async def _extract_data(self, tab: uc.Tab) -> NoiseData:
        """Extract noise score and sources from HowLoud.com page.

        Looks for:
        1. Noise score (0-100 scale)
        2. Noise source indicators (traffic, airport, local, rail)

        Args:
            tab: Browser tab with HowLoud.com page loaded

        Returns:
            NoiseData with extracted score and sources

        Raises:
            ValueError: If no noise data can be extracted from page
        """
        logger.debug("%s extracting noise data from page", self.name)

        try:
            # Get page content
            content = await tab.get_content()
            content_lower = content.lower()

            # Strategy 1: Look for noise score in common patterns
            noise_score = self._extract_score(content, r"noise\s+score[:\s]*(\d+)")

            # Strategy 2: Try alternative patterns
            if noise_score is None:
                noise_score = self._extract_score(content, r"soundscore[:\s]*(\d+)")
            if noise_score is None:
                noise_score = self._extract_score(content, r"quiet\s+score[:\s]*(\d+)")
            if noise_score is None:
                # Look for data attributes
                noise_score = self._extract_score(content, r'data-noise=["\'](\d+)["\']')

            # Strategy 3: Extract noise sources
            noise_sources = []
            source_patterns = [
                (r"traffic\s+noise", "traffic"),
                (r"airport\s+noise", "airport"),
                (r"rail\s+noise", "rail"),
                (r"local\s+noise", "local"),
                (r"highway\s+noise", "highway"),
                (r"freeway\s+noise", "freeway"),
            ]

            for pattern, source_name in source_patterns:
                if re.search(pattern, content_lower):
                    noise_sources.append(source_name)
                    logger.debug("%s found noise source: %s", self.name, source_name)

            # Strategy 4: Check for quiet/loud indicators if no explicit score
            if noise_score is None:
                if "very quiet" in content_lower:
                    noise_score = 90  # Estimate for "very quiet"
                elif "quiet" in content_lower:
                    noise_score = 70  # Estimate for "quiet"
                elif "moderate" in content_lower:
                    noise_score = 50  # Estimate for "moderate"
                elif "loud" in content_lower:
                    noise_score = 30  # Estimate for "loud"

            # Log extraction results
            logger.info(
                "%s extracted data: score=%s, sources=%s",
                self.name,
                noise_score,
                noise_sources,
            )

            # Return NoiseData (even if score is None)
            return NoiseData.from_score(
                noise_score=noise_score,
                noise_sources=noise_sources,
            )

        except Exception as e:
            logger.error("%s error extracting data: %s", self.name, e)
            raise ValueError(f"Failed to extract noise data: {e}")

    def _extract_score(self, content: str, pattern: str) -> int | None:
        """Extract numeric score from content using regex pattern.

        Args:
            content: Page content to search
            pattern: Regex pattern with one capture group for the score

        Returns:
            Extracted integer score (0-100) or None if not found
        """
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                value = int(match.group(1))
                # Validate score is in 0-100 range
                if 0 <= value <= 100:
                    logger.debug("%s found score: %d (pattern: %s)", self.name, value, pattern[:30])
                    return value
                else:
                    logger.warning("%s invalid score %d (out of range 0-100)", self.name, value)
            except (ValueError, IndexError):
                pass
        return None
