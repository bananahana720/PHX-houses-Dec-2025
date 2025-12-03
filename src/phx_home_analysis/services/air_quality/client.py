"""EPA AirNow API client for air quality data extraction.

API Documentation: https://docs.airnowapi.org/
Rate Limits: 500 requests/hour for registered API keys
Data Refresh: Hourly observations

Required Environment Variable:
    AIRNOW_API_KEY - Register at https://docs.airnowapi.org/account/request/
"""

import asyncio
import logging
import os
import time
from typing import Any

import httpx

from .models import AirQualityData

logger = logging.getLogger(__name__)

# EPA AirNow API endpoint
AIRNOW_API_BASE = "https://www.airnowapi.org/aq/observation/latLong/current/"


class EPAAirNowClient:
    """HTTP client for EPA AirNow air quality API.

    Provides async access to current air quality observations by coordinates.
    Uses HTTP/2 when available, with rate limiting and error handling.

    Example:
        ```python
        async with EPAAirNowClient() as client:
            data = await client.get_air_quality(33.4484, -112.0740)
            if data:
                print(f"AQI: {data.aqi_value} ({data.aqi_category})")
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: float = 30.0,
        rate_limit_seconds: float = 0.5,
    ):
        """Initialize the AirNow client.

        Args:
            api_key: AirNow API key (or use AIRNOW_API_KEY env var)
            timeout: Request timeout in seconds
            rate_limit_seconds: Minimum seconds between API calls
        """
        self._api_key = api_key or os.getenv("AIRNOW_API_KEY")
        self._timeout = timeout
        self._rate_limit_seconds = rate_limit_seconds
        self._last_call = 0.0
        self._http: httpx.AsyncClient | None = None

        if not self._api_key:
            logger.warning(
                "AIRNOW_API_KEY not set - air quality extraction disabled. "
                "Register at https://docs.airnowapi.org/account/request/"
            )

    async def __aenter__(self) -> "EPAAirNowClient":
        """Async context manager entry with HTTP/2 support."""
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

    @property
    def is_configured(self) -> bool:
        """Check if API key is configured."""
        return bool(self._api_key)

    async def get_air_quality(
        self, lat: float, lng: float, distance: int = 25
    ) -> AirQualityData | None:
        """Get current air quality for coordinates.

        Args:
            lat: Latitude
            lng: Longitude
            distance: Search radius in miles (default 25)

        Returns:
            AirQualityData if successful, None if error or unconfigured
        """
        if not self._api_key:
            logger.debug("AirNow API key not configured, skipping")
            return None

        if not self._http:
            logger.error("Client not initialized - use async context manager")
            return None

        await self._apply_rate_limit()

        params = {
            "format": "application/json",
            "latitude": lat,
            "longitude": lng,
            "distance": distance,
            "API_KEY": self._api_key,
        }

        try:
            response = await self._http.get(AIRNOW_API_BASE, params=params)
            response.raise_for_status()
            data = response.json()

            return self._parse_response(data, lat, lng)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.error("AirNow rate limit exceeded (500/hour)")
            elif e.response.status_code == 401:
                logger.error("AirNow API key invalid or expired")
            else:
                logger.error("AirNow HTTP error %d: %s", e.response.status_code, e)
            return None
        except httpx.RequestError as e:
            logger.error("AirNow request error: %s", e)
            return None
        except Exception as e:
            logger.error("AirNow unexpected error: %s", e)
            return None

    def _parse_response(
        self, data: list[dict[str, Any]], lat: float, lng: float
    ) -> AirQualityData | None:
        """Parse AirNow API response.

        The API returns a list of observations, typically one per pollutant.
        We return the observation with the highest AQI (worst air quality).

        Args:
            data: API response (list of observation dicts)
            lat: Request latitude
            lng: Request longitude

        Returns:
            AirQualityData for highest AQI observation, or None if empty
        """
        if not data:
            logger.debug("No air quality observations for (%.4f, %.4f)", lat, lng)
            return None

        try:
            # Find observation with highest AQI
            max_aqi_obs = max(data, key=lambda x: x.get("AQI", 0))

            aqi = self._safe_int(max_aqi_obs.get("AQI"))
            pollutant = max_aqi_obs.get("ParameterName")
            area = max_aqi_obs.get("ReportingArea")

            logger.debug(
                "AirNow: AQI=%s (%s) for %s at (%.4f, %.4f)",
                aqi,
                pollutant,
                area,
                lat,
                lng,
            )

            return AirQualityData.from_api_response(
                aqi=aqi,
                pollutant=pollutant,
                area=area,
                lat=lat,
                lng=lng,
            )

        except Exception as e:
            logger.error("Error parsing AirNow response: %s", e)
            return None

    async def get_air_quality_batch(
        self, coordinates: list[tuple[float, float]]
    ) -> list[AirQualityData | None]:
        """Get air quality for multiple coordinates.

        Args:
            coordinates: List of (lat, lng) tuples

        Returns:
            List of AirQualityData (or None for failures)
        """
        results = []
        for lat, lng in coordinates:
            result = await self.get_air_quality(lat, lng)
            results.append(result)
        return results

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        """Safely convert value to int."""
        if value is None:
            return None
        try:
            return int(value)
        except (ValueError, TypeError):
            return None
