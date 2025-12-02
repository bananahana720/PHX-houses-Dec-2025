"""FCC Geocoder for converting lat/lng to census tract."""

import asyncio
import logging
import time

import httpx

logger = logging.getLogger(__name__)

# FCC Census Block API
FCC_GEOCODER_ENDPOINT = "https://geo.fcc.gov/api/census/block/find"


class FCC_Geocoder:
    """FCC API geocoder to convert coordinates to census tract codes.

    Uses Federal Communications Commission Census Block Conversions API.
    Public API - no authentication required.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        rate_limit_seconds: float = 0.5,
    ):
        """Initialize geocoder.

        Args:
            timeout: Request timeout in seconds
            rate_limit_seconds: Delay between API calls
        """
        self._timeout = timeout
        self._rate_limit_seconds = rate_limit_seconds
        self._last_call = 0.0
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "FCC_Geocoder":
        """Async context manager entry with HTTP/2 support."""
        # Try HTTP/2, fall back to HTTP/1.1 if h2 not installed
        try:
            self._http = httpx.AsyncClient(
                timeout=self._timeout,
                http2=True,
                follow_redirects=True,  # Follow redirects for FCC API
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
                follow_redirects=True,  # Follow redirects for FCC API
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

    async def get_census_tract(self, lat: float, lng: float) -> str | None:
        """Get census tract FIPS code from coordinates.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            11-digit census tract FIPS code (state + county + tract), or None
        """
        await self._apply_rate_limit()

        params = {
            "latitude": lat,
            "longitude": lng,
            "censusYear": 2020,  # Use 2020 census geography
            "format": "json",
        }

        try:
            response = await self._http.get(FCC_GEOCODER_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()

            # Extract FIPS code from response
            block_fips = data.get("Block", {}).get("FIPS")
            if not block_fips:
                logger.debug(f"No census block found for ({lat}, {lng})")
                return None

            # Census tract is first 11 digits of block FIPS
            # Format: 2-digit state + 3-digit county + 6-digit tract = 11 digits
            # Block FIPS is 15 digits (tract + 4-digit block)
            tract_fips = block_fips[:11]

            logger.debug(f"Census tract for ({lat}, {lng}): {tract_fips}")
            return tract_fips

        except httpx.HTTPStatusError as e:
            logger.error(f"FCC Geocoder HTTP error {e.response.status_code}: {e}")
            return None
        except httpx.RequestError as e:
            logger.error(f"FCC Geocoder request error: {e}")
            return None
        except Exception as e:
            logger.error(f"FCC Geocoder unexpected error: {e}")
            return None

    def parse_tract_fips(self, tract_fips: str) -> tuple[str, str, str] | None:
        """Parse census tract FIPS into components.

        Args:
            tract_fips: 11-digit census tract FIPS code

        Returns:
            Tuple of (state_fips, county_fips, tract_code) or None if invalid
        """
        if not tract_fips or len(tract_fips) != 11:
            logger.warning(f"Invalid census tract FIPS: {tract_fips}")
            return None

        try:
            state_fips = tract_fips[:2]
            county_fips = tract_fips[2:5]
            tract_code = tract_fips[5:11]

            return state_fips, county_fips, tract_code

        except Exception as e:
            logger.error(f"Error parsing tract FIPS: {e}")
            return None
