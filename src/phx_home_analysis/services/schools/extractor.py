"""GreatSchools extractor using GreatSchools.org."""

import logging
import re
from urllib.parse import quote_plus

import nodriver as uc

from ...domain.entities import Property
from ..location_data import LocationDataExtractor
from .models import SchoolData

logger = logging.getLogger(__name__)


class GreatSchoolsExtractor(LocationDataExtractor[SchoolData]):
    """Extract school ratings from GreatSchools.org.

    Source: https://www.greatschools.org/search/search.page?q={encoded_address}

    Searches for schools near the property address and extracts:
        - Best elementary school rating (1-10 scale)
        - Best middle school rating (1-10 scale)
        - Best high school rating (1-10 scale)
        - Total number of schools within 1 mile

    Example:
        ```python
        async with GreatSchoolsExtractor() as extractor:
            result = await extractor.extract(property)
            if result.success:
                print(f"Elementary: {result.data.elementary_rating}")
                print(f"Middle: {result.data.middle_rating}")
                print(f"High: {result.data.high_rating}")
        ```
    """

    @property
    def name(self) -> str:
        """Extractor name for logging."""
        return "GreatSchools"

    def _build_url(self, property: Property) -> str:
        """Build GreatSchools.org search URL for property address.

        Args:
            property: Property with full_address

        Returns:
            Full URL to school search page
        """
        # Encode address for URL search
        encoded_address = quote_plus(property.full_address)
        url = f"https://www.greatschools.org/search/search.page?q={encoded_address}"
        logger.debug("%s built URL: %s", self.name, url)
        return url

    async def _extract_data(self, tab: uc.Tab) -> SchoolData:
        """Extract school ratings from GreatSchools.org search results.

        Parses school cards from search results to find:
        1. School type (Elementary, Middle, High)
        2. School rating (1-10 scale)
        3. Distance from address

        Keeps the best rating for each school type within 1 mile.

        Args:
            tab: Browser tab with GreatSchools.org results loaded

        Returns:
            SchoolData with best ratings by type

        Raises:
            ValueError: If no school data can be extracted from page
        """
        logger.debug("%s extracting school ratings from page", self.name)

        try:
            # Get page content
            content = await tab.get_content()

            # Track best ratings by type
            elementary_ratings = []
            middle_ratings = []
            high_ratings = []
            school_count = 0

            # Strategy 1: Find school cards/items in page
            # Look for patterns like:
            # - "Elementary School" + rating number
            # - "Middle School" + rating number
            # - "High School" + rating number

            # Find all rating patterns with school types
            school_pattern = r'(elementary|middle|high)\s+school.*?rating[:\s]*(\d+(?:\.\d+)?)'
            matches = re.finditer(school_pattern, content, re.IGNORECASE | re.DOTALL)

            for match in matches:
                school_type = match.group(1).lower()
                try:
                    rating = float(match.group(2))

                    # Validate rating is in 1-10 range
                    if not (1 <= rating <= 10):
                        continue

                    school_count += 1

                    # Categorize by type
                    if school_type == "elementary":
                        elementary_ratings.append(rating)
                    elif school_type == "middle":
                        middle_ratings.append(rating)
                    elif school_type == "high":
                        high_ratings.append(rating)

                    logger.debug(
                        "%s found %s school rating: %.1f", self.name, school_type, rating
                    )

                except (ValueError, IndexError):
                    continue

            # Strategy 2: Alternative pattern - look for rating class attributes
            rating_pattern = r'data-rating=["\'](\d+(?:\.\d+)?)["\'].*?(elementary|middle|high)'
            matches2 = re.finditer(rating_pattern, content, re.IGNORECASE | re.DOTALL)

            for match in matches2:
                try:
                    rating = float(match.group(1))
                    school_type = match.group(2).lower()

                    if not (1 <= rating <= 10):
                        continue

                    if school_type == "elementary":
                        elementary_ratings.append(rating)
                    elif school_type == "middle":
                        middle_ratings.append(rating)
                    elif school_type == "high":
                        high_ratings.append(rating)

                except (ValueError, IndexError):
                    continue

            # Get best rating for each type
            elementary_best = max(elementary_ratings) if elementary_ratings else None
            middle_best = max(middle_ratings) if middle_ratings else None
            high_best = max(high_ratings) if high_ratings else None

            # Use discovered school count
            school_count_final = school_count if school_count > 0 else None

            # Log extraction results
            logger.info(
                "%s extracted ratings: elementary=%s, middle=%s, high=%s (count=%s)",
                self.name,
                elementary_best,
                middle_best,
                high_best,
                school_count_final,
            )

            # Return SchoolData (even if some ratings are None)
            return SchoolData.from_ratings(
                elementary_rating=elementary_best,
                middle_rating=middle_best,
                high_rating=high_best,
                school_count_1mi=school_count_final,
            )

        except Exception as e:
            logger.error("%s error extracting data: %s", self.name, e)
            raise ValueError(f"Failed to extract school data: {e}")
