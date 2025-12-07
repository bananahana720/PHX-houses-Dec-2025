"""Maricopa County GIS client for building permit history.

API: Maricopa County Enterprise GIS - Building Permits Layer
Authentication: None required (public data)
Rate Limits: No documented limits, but be respectful

The GIS uses ArcGIS REST API with spatial queries.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

import httpx

from .models import Permit, PermitHistory, PermitType

logger = logging.getLogger(__name__)

# Maricopa County GIS endpoint for Building Permits
# Note: This endpoint may need verification - Maricopa has multiple GIS layers
MARICOPA_PERMITS_URL = (
    "https://gis.maricopa.gov/arcgis/rest/services/Planning/BuildingPermits/MapServer/0/query"
)

# Alternative: Query by parcel from Assessor (more reliable)
ASSESSOR_PERMITS_URL = "https://mcassessor.maricopa.gov/mcs/api/v1/parcel/{parcel}/permits"


class MaricopaPermitClient:
    """HTTP client for Maricopa County building permits.

    Provides access to building permit history for properties within
    Maricopa County, Arizona.

    Example:
        ```python
        async with MaricopaPermitClient() as client:
            history = await client.get_permit_history(33.4484, -112.0740)
            if history:
                print(f"Found {history.permit_count} permits")
                print(f"Last roof: {history.last_roof_permit_year}")
        ```
    """

    def __init__(
        self,
        timeout: float = 30.0,
        rate_limit_seconds: float = 0.5,
    ):
        """Initialize the permit client.

        Args:
            timeout: Request timeout in seconds
            rate_limit_seconds: Minimum seconds between API calls
        """
        self._timeout = timeout
        self._rate_limit_seconds = rate_limit_seconds
        self._last_call = 0.0
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "MaricopaPermitClient":
        """Async context manager entry."""
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

    async def get_permit_history(
        self, lat: float, lng: float, radius_meters: int = 50
    ) -> PermitHistory | None:
        """Get permit history for coordinates.

        Uses spatial query to find permits near the property location.

        Args:
            lat: Latitude
            lng: Longitude
            radius_meters: Search radius (default 50m to capture parcel)

        Returns:
            PermitHistory if successful, None if error or no data
        """
        if not self._http:
            logger.error("Client not initialized - use async context manager")
            return None

        await self._apply_rate_limit()

        # ArcGIS spatial query parameters
        params = {
            "f": "json",
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "inSR": "4326",  # WGS84
            "spatialRel": "esriSpatialRelIntersects",
            "distance": radius_meters,
            "units": "esriSRUnit_Meter",
            "outFields": "*",
            "returnGeometry": "false",
        }

        try:
            response = await self._http.get(MARICOPA_PERMITS_URL, params=params)
            response.raise_for_status()
            data = response.json()

            return self._parse_response(data, lat, lng)

        except httpx.HTTPStatusError as e:
            logger.error("Maricopa GIS HTTP error %d: %s", e.response.status_code, e)
            return None
        except httpx.RequestError as e:
            logger.error("Maricopa GIS request error: %s", e)
            return None
        except Exception as e:
            logger.error("Maricopa GIS unexpected error: %s", e)
            return None

    async def get_permit_history_by_parcel(self, parcel_number: str) -> PermitHistory | None:
        """Get permit history by parcel number (APN).

        More reliable than spatial query if parcel number is known.

        Args:
            parcel_number: Maricopa County APN (e.g., "123-45-678")

        Returns:
            PermitHistory if successful, None if error or no data
        """
        if not self._http:
            logger.error("Client not initialized - use async context manager")
            return None

        await self._apply_rate_limit()

        # Clean parcel number format
        clean_parcel = parcel_number.replace("-", "").replace(" ", "")

        url = ASSESSOR_PERMITS_URL.format(parcel=clean_parcel)

        try:
            response = await self._http.get(url)
            response.raise_for_status()
            data = response.json()

            return self._parse_assessor_response(data, parcel_number)

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug("No permits found for parcel %s", parcel_number)
                return PermitHistory(parcel_number=parcel_number, permits=[])
            logger.error("Assessor API HTTP error %d: %s", e.response.status_code, e)
            return None
        except httpx.RequestError as e:
            logger.error("Assessor API request error: %s", e)
            return None
        except Exception as e:
            logger.error("Assessor API unexpected error: %s", e)
            return None

    def _parse_response(self, data: dict[str, Any], lat: float, lng: float) -> PermitHistory | None:
        """Parse ArcGIS query response.

        Args:
            data: ArcGIS response dict with features
            lat: Request latitude
            lng: Request longitude

        Returns:
            PermitHistory with parsed permits
        """
        features = data.get("features", [])

        if not features:
            logger.debug("No permits found near (%.4f, %.4f)", lat, lng)
            return PermitHistory(latitude=lat, longitude=lng, permits=[])

        permits = []
        for feature in features:
            attrs = feature.get("attributes", {})
            permit = self._parse_permit_attributes(attrs)
            if permit:
                permits.append(permit)

        logger.debug("Found %d permits near (%.4f, %.4f)", len(permits), lat, lng)

        return PermitHistory(
            permits=permits,
            latitude=lat,
            longitude=lng,
            extracted_at=datetime.now(),
        )

    def _parse_assessor_response(
        self, data: dict[str, Any], parcel_number: str
    ) -> PermitHistory | None:
        """Parse Assessor API response.

        Args:
            data: Assessor API response
            parcel_number: Parcel number queried

        Returns:
            PermitHistory with parsed permits
        """
        permit_list = data.get("permits", data.get("data", []))

        if not permit_list:
            return PermitHistory(parcel_number=parcel_number, permits=[])

        permits = []
        for item in permit_list:
            permit = Permit(
                permit_number=item.get("permit_number") or item.get("permitNumber"),
                permit_type=PermitType.from_description(
                    item.get("description") or item.get("work_description")
                ),
                description=item.get("description") or item.get("work_description"),
                issue_date=self._parse_date(item.get("issue_date") or item.get("issueDate")),
                final_date=self._parse_date(item.get("final_date") or item.get("finalDate")),
                status=item.get("status"),
                valuation=self._safe_float(item.get("valuation") or item.get("value")),
            )
            permits.append(permit)

        return PermitHistory(
            permits=permits,
            parcel_number=parcel_number,
            extracted_at=datetime.now(),
        )

    def _parse_permit_attributes(self, attrs: dict[str, Any]) -> Permit | None:
        """Parse individual permit from ArcGIS attributes.

        Field names vary by GIS layer; this handles common patterns.
        """
        try:
            # Common ArcGIS field name patterns
            permit_num = (
                attrs.get("PERMIT_NUM") or attrs.get("PermitNumber") or attrs.get("PERMITNO")
            )

            description = (
                attrs.get("DESCRIPTION") or attrs.get("WorkDescription") or attrs.get("WORK_DESC")
            )

            issue_date = self._parse_epoch_date(
                attrs.get("ISSUE_DATE") or attrs.get("IssueDate") or attrs.get("ISSUED")
            )

            final_date = self._parse_epoch_date(
                attrs.get("FINAL_DATE") or attrs.get("FinalDate") or attrs.get("FINALED")
            )

            status = attrs.get("STATUS") or attrs.get("PermitStatus")

            valuation = self._safe_float(
                attrs.get("VALUATION") or attrs.get("Value") or attrs.get("JOB_VALUE")
            )

            return Permit(
                permit_number=permit_num,
                permit_type=PermitType.from_description(description),
                description=description,
                issue_date=issue_date,
                final_date=final_date,
                status=status,
                valuation=valuation,
            )

        except Exception as e:
            logger.warning("Failed to parse permit attributes: %s", e)
            return None

    def _parse_epoch_date(self, value: Any) -> str | None:
        """Parse ArcGIS epoch timestamp to ISO date string."""
        if value is None:
            return None
        try:
            # ArcGIS uses milliseconds since epoch
            if isinstance(value, (int, float)) and value > 1e10:
                dt = datetime.fromtimestamp(value / 1000)
                return dt.strftime("%Y-%m-%d")
            elif isinstance(value, str):
                return value[:10] if len(value) >= 10 else value
        except Exception:
            pass
        return None

    def _parse_date(self, value: Any) -> str | None:
        """Parse various date formats to ISO string."""
        if value is None:
            return None
        if isinstance(value, str):
            # Already ISO format
            if len(value) >= 10 and value[4] == "-":
                return value[:10]
            # MM/DD/YYYY format
            try:
                parts = value.split("/")
                if len(parts) == 3:
                    return f"{parts[2]}-{parts[0]:>02}-{parts[1]:>02}"
            except Exception:
                pass
        return None

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
