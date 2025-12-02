"""Crime data extractor using BestPlaces.net."""

import logging
import re
from urllib.parse import quote_plus

import nodriver as uc

from ...domain.entities import Property
from ..location_data import LocationDataExtractor
from .models import CrimeData

logger = logging.getLogger(__name__)


class CrimeDataExtractor(LocationDataExtractor[CrimeData]):
    """Extract crime statistics from BestPlaces.net.

    Data is batched by ZIP code to reduce requests - all properties in the
    same ZIP share crime data.

    Primary source: https://www.bestplaces.net/crime/zip-code/arizona/{zip_code}
    Fallback source: https://www.areavibes.com/{city}-az/crime/

    Extracts:
        - Violent crime index (0-100, 100=safest)
        - Property crime index (0-100, 100=safest)
        - Computed crime risk level

    Example:
        ```python
        async with CrimeDataExtractor() as extractor:
            result = await extractor.extract(property)
            if result.success:
                print(f"Violent crime: {result.data.violent_crime_index}")
        ```
    """

    @property
    def name(self) -> str:
        """Extractor name for logging."""
        return "CrimeData"

    def _build_url(self, property: Property) -> str:
        """Build BestPlaces.net URL for property's ZIP code.

        Args:
            property: Property with zip_code

        Returns:
            Full URL to crime data page
        """
        zip_code = property.zip_code
        url = f"https://www.bestplaces.net/crime/zip-code/arizona/{zip_code}"
        logger.debug("%s built URL for ZIP %s: %s", self.name, zip_code, url)
        return url

    async def _extract_data(self, tab: uc.Tab) -> CrimeData:
        """Extract crime indices from BestPlaces.net page.

        Looks for crime index values in page content using multiple strategies:
        1. Search for text patterns like "Violent Crime Index: 85.2"
        2. Parse table rows with crime statistics
        3. Extract from structured data elements

        Args:
            tab: Browser tab with BestPlaces.net page loaded

        Returns:
            CrimeData with extracted indices

        Raises:
            ValueError: If crime data cannot be parsed from page
        """
        logger.debug("%s extracting crime data from page", self.name)

        try:
            # Get page content
            content = await tab.get_content()
            content_lower = content.lower()

            # Strategy 1: Look for crime index patterns in text
            violent_index = self._extract_index_from_text(
                content, r"violent\s+crime\s+index[:\s]*(\d+\.?\d*)"
            )
            property_index = self._extract_index_from_text(
                content, r"property\s+crime\s+index[:\s]*(\d+\.?\d*)"
            )

            # Strategy 2: Try alternative patterns (crime grade, safety score, etc.)
            if violent_index is None:
                violent_index = self._extract_index_from_text(
                    content, r"violent\s+crime[:\s]*(\d+\.?\d*)"
                )

            if property_index is None:
                property_index = self._extract_index_from_text(
                    content, r"property\s+crime[:\s]*(\d+\.?\d*)"
                )

            # Strategy 3: Check for "safer than X% of cities" format
            if violent_index is None or property_index is None:
                safer_match = re.search(
                    r"safer\s+than\s+(\d+)%", content_lower, re.IGNORECASE
                )
                if safer_match:
                    safer_pct = float(safer_match.group(1))
                    # Use safer percentage as proxy for both indices if missing
                    if violent_index is None:
                        violent_index = safer_pct
                    if property_index is None:
                        property_index = safer_pct

            # Log extraction results
            logger.info(
                "%s extracted indices: violent=%s, property=%s",
                self.name,
                violent_index,
                property_index,
            )

            # Return CrimeData (even if indices are None - lets caller decide)
            return CrimeData.from_indices(
                violent_crime_index=violent_index,
                property_crime_index=property_index,
            )

        except Exception as e:
            logger.error("%s error extracting data: %s", self.name, e)
            raise ValueError(f"Failed to extract crime data: {e}")

    def _extract_index_from_text(self, content: str, pattern: str) -> float | None:
        """Extract numeric index from text using regex pattern.

        Args:
            content: Page content to search
            pattern: Regex pattern with one capture group for the number

        Returns:
            Extracted float value or None if not found
        """
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            try:
                value = float(match.group(1))
                logger.debug("%s found index: %.1f (pattern: %s)", self.name, value, pattern[:30])
                return value
            except (ValueError, IndexError):
                pass
        return None

    def _build_fallback_url(self, property: Property) -> str:
        """Build AreaVibes.com fallback URL.

        Args:
            property: Property with city

        Returns:
            AreaVibes URL for city
        """
        city_encoded = quote_plus(property.city.lower().replace(" ", "-"))
        url = f"https://www.areavibes.com/{city_encoded}-az/crime/"
        logger.debug("%s built fallback URL: %s", self.name, url)
        return url
