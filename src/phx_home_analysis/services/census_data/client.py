"""Census Bureau American Community Survey (ACS) API client."""

import asyncio
import logging
import os
import time

import httpx

from .geocoder import FCC_Geocoder
from .models import DemographicData

logger = logging.getLogger(__name__)

# Census ACS 5-Year API
CENSUS_ACS5_ENDPOINT = "https://api.census.gov/data/2022/acs/acs5"

# Census variables
# https://api.census.gov/data/2022/acs/acs5/variables.html
CENSUS_VARIABLES = {
    "median_household_income": "B19013_001E",  # Median household income in past 12 months
    "median_home_value": "B25077_001E",  # Median home value
    "total_population": "B01003_001E",  # Total population
}


class CensusAPIClient:
    """HTTP client for Census Bureau ACS API.

    Queries demographic data by census tract.
    Optional API key increases rate limits (500/day without key, unlimited with key).
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
        rate_limit_seconds: float = 0.5,
    ):
        """Initialize client.

        Args:
            api_key: Census API key (defaults to CENSUS_API_KEY env var)
            timeout: Request timeout in seconds
            rate_limit_seconds: Delay between API calls
        """
        self._api_key = api_key or os.getenv("CENSUS_API_KEY")
        self._timeout = timeout
        self._rate_limit_seconds = rate_limit_seconds
        self._last_call = 0.0
        self._http: httpx.AsyncClient | None = None

        if not self._api_key:
            logger.warning(
                "CENSUS_API_KEY not set - rate limited to 500 requests/day. "
                "Get a free key at https://api.census.gov/data/key_signup.html"
            )

    async def __aenter__(self) -> "CensusAPIClient":
        """Async context manager entry with HTTP/2 support."""
        # Try HTTP/2, fall back to HTTP/1.1 if h2 not installed
        try:
            self._http = httpx.AsyncClient(
                timeout=self._timeout,
                http2=True,
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20,
                    keepalive_expiry=30.0,
                ),
            )
        except ImportError:
            logger.debug("h2 package not installed, using HTTP/1.1")
            self._http = httpx.AsyncClient(
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=10,
                    max_connections=20,
                    keepalive_expiry=30.0,
                ),
            )
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        if self._http:
            await self._http.aclose()

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between API calls."""
        elapsed = time.time() - self._last_call
        if elapsed < self._rate_limit_seconds:
            await asyncio.sleep(self._rate_limit_seconds - elapsed)
        self._last_call = time.time()

    async def get_tract_data(
        self, state_fips: str, county_fips: str, tract_code: str
    ) -> DemographicData | None:
        """Query demographic data for a census tract.

        Args:
            state_fips: 2-digit state FIPS code (e.g., "04" for Arizona)
            county_fips: 3-digit county FIPS code (e.g., "013" for Maricopa)
            tract_code: 6-digit tract code

        Returns:
            DemographicData if found, None if error
        """
        await self._apply_rate_limit()

        # Build query parameters
        get_vars = ",".join(CENSUS_VARIABLES.values())
        params = {
            "get": get_vars,
            "for": f"tract:{tract_code}",
            "in": f"state:{state_fips} county:{county_fips}",
        }

        # Add API key if available
        if self._api_key:
            params["key"] = self._api_key

        try:
            response = await self._http.get(CENSUS_ACS5_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()

            # Parse response
            return self._parse_census_response(data, state_fips, county_fips, tract_code)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("Census API rate limit exceeded - consider using API key")
            else:
                logger.error(f"Census API HTTP error {e.response.status_code}: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"Census API request error: {e}")
            return None
        except Exception as e:
            logger.error(f"Census API unexpected error: {e}")
            return None

    def _parse_census_response(
        self, data: list, state_fips: str, county_fips: str, tract_code: str
    ) -> DemographicData | None:
        """Parse Census API response.

        Args:
            data: Census API JSON response (list of lists)
            state_fips: State FIPS code
            county_fips: County FIPS code
            tract_code: Tract code

        Returns:
            DemographicData if valid, None if parsing fails
        """
        try:
            # Response format: [[header_row], [data_row]]
            if len(data) < 2:
                logger.warning("Empty Census API response")
                return None

            headers = data[0]
            values = data[1]

            # Build census tract FIPS
            census_tract = f"{state_fips}{county_fips}{tract_code}"

            # Extract values by position
            var_positions = {
                var_name: headers.index(var_code)
                for var_name, var_code in CENSUS_VARIABLES.items()
                if var_code in headers
            }

            median_income = self._safe_int(
                values[var_positions["median_household_income"]]
                if "median_household_income" in var_positions
                else None
            )

            median_value = self._safe_int(
                values[var_positions["median_home_value"]]
                if "median_home_value" in var_positions
                else None
            )

            total_pop = self._safe_int(
                values[var_positions["total_population"]]
                if "total_population" in var_positions
                else None
            )

            return DemographicData(
                census_tract=census_tract,
                median_household_income=median_income,
                median_home_value=median_value,
                total_population=total_pop,
                state_fips=state_fips,
                county_fips=county_fips,
                tract_code=tract_code,
            )

        except Exception as e:
            logger.error(f"Error parsing Census response: {e}")
            return None

    async def get_demographic_data_by_coords(
        self, lat: float, lng: float
    ) -> DemographicData | None:
        """Get demographic data for coordinates (convenience method).

        Combines FCC geocoding and Census data retrieval.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            DemographicData if found, None otherwise
        """
        # Get census tract from coordinates
        async with FCC_Geocoder() as geocoder:
            tract_fips = await geocoder.get_census_tract(lat, lng)
            if not tract_fips:
                return None

            components = geocoder.parse_tract_fips(tract_fips)
            if not components:
                return None

            state_fips, county_fips, tract_code = components

        # Get demographic data
        demo_data = await self.get_tract_data(state_fips, county_fips, tract_code)

        # Add coordinates to result
        if demo_data:
            demo_data.latitude = lat
            demo_data.longitude = lng

        return demo_data

    @staticmethod
    def _safe_int(value) -> int | None:
        """Safely convert to int, handling Census null values.

        Census API returns -666666666 for null/unavailable data.
        """
        if value is None:
            return None

        try:
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return None

            int_value = int(float(value))

            # Handle Census null codes
            if int_value < 0:  # -666666666 or other negative codes
                return None

            return int_value

        except (ValueError, TypeError):
            return None
