"""Walk Score extractor using WalkScore.com."""

import logging
import re
from urllib.parse import quote_plus

import nodriver as uc

from ...domain.entities import Property
from ..location_data import LocationDataExtractor
from .models import WalkScoreData

logger = logging.getLogger(__name__)


class WalkScoreExtractor(LocationDataExtractor[WalkScoreData]):
    """Extract Walk Score, Transit Score, and Bike Score from WalkScore.com.

    Source: https://www.walkscore.com/score/{encoded_address}

    Extracts three mobility scores (0-100 scale):
        - Walk Score: Walkability based on nearby amenities
        - Transit Score: Public transit availability
        - Bike Score: Bikeability based on infrastructure and terrain

    Example:
        ```python
        async with WalkScoreExtractor() as extractor:
            result = await extractor.extract(property)
            if result.success:
                print(f"Walk Score: {result.data.walk_score}")
                print(f"Transit Score: {result.data.transit_score}")
                print(f"Bike Score: {result.data.bike_score}")
        ```
    """

    @property
    def name(self) -> str:
        """Extractor name for logging."""
        return "WalkScore"

    def _build_url(self, property: Property) -> str:
        """Build WalkScore.com URL for property address.

        Args:
            property: Property with full_address

        Returns:
            Full URL to walk score page
        """
        # Encode address for URL: "123 Main St, Phoenix, AZ 85001"
        encoded_address = quote_plus(property.full_address)
        url = f"https://www.walkscore.com/score/{encoded_address}"
        logger.debug("%s built URL: %s", self.name, url)
        return url

    async def _extract_data(self, tab: uc.Tab) -> WalkScoreData:
        """Extract walk, transit, and bike scores from WalkScore.com page.

        Looks for score values using multiple strategies:
        1. Search for numeric scores in score display elements
        2. Parse from structured data (JSON-LD)
        3. Extract from page text patterns

        Args:
            tab: Browser tab with WalkScore.com page loaded

        Returns:
            WalkScoreData with extracted scores

        Raises:
            ValueError: If no scores can be extracted from page
        """
        logger.debug("%s extracting scores from page", self.name)

        try:
            # Get page content
            content = await tab.get_content()

            # Strategy 1: Look for score numbers in common patterns
            walk_score = self._extract_score(content, r"walk\s*score[:\s]*(\d+)")
            transit_score = self._extract_score(content, r"transit\s*score[:\s]*(\d+)")
            bike_score = self._extract_score(content, r"bike\s*score[:\s]*(\d+)")

            # Strategy 2: Try data attributes or JSON
            if walk_score is None:
                walk_score = self._extract_score(content, r"walkscore[\"']?\s*:\s*(\d+)")
            if transit_score is None:
                transit_score = self._extract_score(content, r"transitscore[\"']?\s*:\s*(\d+)")
            if bike_score is None:
                bike_score = self._extract_score(content, r"bikescore[\"']?\s*:\s*(\d+)")

            # Strategy 3: Try class-based selectors (common WalkScore pattern)
            if walk_score is None:
                walk_score = self._extract_score(content, r"class=[\"']walk-score[\"'][^>]*>(\d+)")
            if transit_score is None:
                transit_score = self._extract_score(
                    content, r"class=[\"']transit-score[\"'][^>]*>(\d+)"
                )
            if bike_score is None:
                bike_score = self._extract_score(content, r"class=[\"']bike-score[\"'][^>]*>(\d+)")

            # Log extraction results
            logger.info(
                "%s extracted scores: walk=%s, transit=%s, bike=%s",
                self.name,
                walk_score,
                transit_score,
                bike_score,
            )

            # Return WalkScoreData (even if some scores are None)
            return WalkScoreData.from_scores(
                walk_score=walk_score,
                transit_score=transit_score,
                bike_score=bike_score,
            )

        except Exception as e:
            logger.error("%s error extracting data: %s", self.name, e)
            raise ValueError(f"Failed to extract walk score data: {e}")

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
                    logger.debug(
                        "%s found score: %d (pattern: %s)", self.name, value, pattern[:30]
                    )
                    return value
                else:
                    logger.warning(
                        "%s invalid score %d (out of range 0-100)", self.name, value
                    )
            except (ValueError, IndexError):
                pass
        return None
