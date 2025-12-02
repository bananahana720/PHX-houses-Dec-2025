"""Maricopa County Assessor API client for property data extraction.

Supports two API modes:
1. Official API (requires MARICOPA_ASSESSOR_TOKEN) - Complete property data
2. ArcGIS Public API (no auth) - Basic data fallback (lot size, year built, coordinates)
"""

import asyncio
import logging
import os
import re
from typing import Optional
from urllib.parse import quote

import httpx

from .models import ParcelData

logger = logging.getLogger(__name__)

# API endpoints
OFFICIAL_API_BASE = "https://mcassessor.maricopa.gov"
ARCGIS_API_BASE = "https://gis.mcassessor.maricopa.gov/arcgis/rest/services/MaricopaDynamicQueryService/MapServer"


class MaricopaAssessorClient:
    """HTTP client for Maricopa County Assessor property data API.

    Attempts Official API first (requires token), falls back to ArcGIS public API.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        timeout: float = 30.0,
        rate_limit_seconds: float = 1.5,
    ):
        """Initialize client.

        Args:
            token: API token (defaults to MARICOPA_ASSESSOR_TOKEN env var)
            timeout: Request timeout in seconds
            rate_limit_seconds: Delay between API calls
        """
        self._token = token or os.getenv("MARICOPA_ASSESSOR_TOKEN")
        self._timeout = timeout
        self._rate_limit_seconds = rate_limit_seconds
        self._last_call = 0.0
        self._http: Optional[httpx.AsyncClient] = None

        if not self._token:
            logger.warning(
                "MARICOPA_ASSESSOR_TOKEN not set - will use ArcGIS fallback only"
            )

    async def __aenter__(self) -> "MaricopaAssessorClient":
        """Async context manager entry."""
        self._http = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, *args) -> None:
        """Async context manager exit."""
        if self._http:
            await self._http.aclose()

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between API calls."""
        import time

        elapsed = time.time() - self._last_call
        if elapsed < self._rate_limit_seconds:
            await asyncio.sleep(self._rate_limit_seconds - elapsed)
        self._last_call = time.time()

    async def search_apn(self, street: str) -> Optional[str]:
        """Search for APN by street address.

        Args:
            street: Street address (e.g., "4732 W Davis Rd")

        Returns:
            APN if found, None otherwise
        """
        await self._apply_rate_limit()

        # Try Official API first
        if self._token:
            apn = await self._search_official_api(street)
            if apn:
                return apn

        # Fallback to ArcGIS
        return await self._search_arcgis(street)

    async def _search_official_api(self, street: str) -> Optional[str]:
        """Search via Official API."""
        url = f"{OFFICIAL_API_BASE}/search/property/"
        params = {"q": street}
        headers = {"AUTHORIZATION": self._token}

        try:
            response = await self._http.get(url, params=params, headers=headers)

            if response.status_code == 401:
                logger.warning("Official API auth failed, token may be invalid")
                return None

            if response.status_code == 429:
                logger.warning("Official API rate limited")
                return None

            response.raise_for_status()
            data = response.json()

            results = data.get("Results", []) or data.get("results", [])
            if results:
                return results[0].get("APN") or results[0].get("apn")

        except httpx.HTTPError as e:
            logger.debug(f"Official API search failed: {e}")

        return None

    async def _search_arcgis(self, street: str) -> Optional[str]:
        """Search via ArcGIS public API."""
        # Build LIKE query for address
        # Escape special characters and build pattern
        street_clean = street.replace("'", "''")
        where_clause = f"PHYSICAL_ADDRESS LIKE '%{street_clean}%'"

        url = f"{ARCGIS_API_BASE}/3/query"
        params = {
            "where": where_clause,
            "outFields": "APN,PHYSICAL_ADDRESS",
            "returnGeometry": "false",
            "f": "json",
            "resultRecordCount": 5,
        }

        try:
            response = await self._http.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])
            if features:
                return features[0].get("attributes", {}).get("APN")

        except httpx.HTTPError as e:
            logger.debug(f"ArcGIS search failed: {e}")

        return None

    async def get_parcel_data(self, apn: str) -> Optional[ParcelData]:
        """Get complete parcel data by APN.

        Args:
            apn: Assessor Parcel Number

        Returns:
            ParcelData with all available fields
        """
        await self._apply_rate_limit()

        # Try Official API first for complete data
        if self._token:
            data = await self._get_official_parcel(apn)
            if data:
                return data

        # Fallback to ArcGIS for basic data
        return await self._get_arcgis_parcel(apn)

    async def _get_official_parcel(self, apn: str) -> Optional[ParcelData]:
        """Get parcel data from Official API."""
        headers = {"AUTHORIZATION": self._token}

        try:
            # Get parcel details
            url = f"{OFFICIAL_API_BASE}/parcel/{apn}"
            response = await self._http.get(url, headers=headers)
            response.raise_for_status()
            parcel = response.json()

            # Get residential details (has year built, garage, pool, etc.)
            await self._apply_rate_limit()
            res_url = f"{OFFICIAL_API_BASE}/parcel/{apn}/residential-details"
            try:
                res_response = await self._http.get(res_url, headers=headers)
                residential = res_response.json() if res_response.status_code == 200 else {}
            except Exception:
                residential = {}

            # Valuation data is in the main parcel response under 'Valuations' array
            valuation = parcel.get("Valuations", [{}])[0] if parcel.get("Valuations") else {}

            return self._map_official_response(apn, parcel, residential, valuation)

        except httpx.HTTPError as e:
            logger.debug(f"Official API parcel fetch failed: {e}")
            return None

    async def _get_arcgis_parcel(self, apn: str) -> Optional[ParcelData]:
        """Get parcel data from ArcGIS public API (limited fields)."""
        url = f"{ARCGIS_API_BASE}/3/query"
        params = {
            "where": f"APN='{apn}'",
            "outFields": "APN,PHYSICAL_ADDRESS,LAND_SIZE,CONST_YEAR,FCV_CUR,LPV_CUR,LATITUDE,LONGITUDE,LIVING_SPACE",
            "returnGeometry": "false",
            "f": "json",
        }

        try:
            response = await self._http.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])
            if not features:
                return None

            attrs = features[0].get("attributes", {})
            return self._map_arcgis_response(attrs)

        except httpx.HTTPError as e:
            logger.debug(f"ArcGIS parcel fetch failed: {e}")
            return None

    def _map_official_response(
        self,
        apn: str,
        parcel: dict,
        residential: dict,
        valuation: dict,
    ) -> ParcelData:
        """Map Official API response to ParcelData.

        Field sources:
        - parcel: Main /parcel/{apn} response
        - residential: /parcel/{apn}/residential-details response
        - valuation: First entry from parcel['Valuations'] array
        """
        # Lot size from residential-details or main parcel
        lot_sqft = self._safe_int(
            residential.get("LotSize")
            or parcel.get("LotSize")
        )

        # Year built from residential-details
        year_built = self._safe_int(
            residential.get("ConstructionYear")
            or residential.get("OriginalConstructionYear")
        )

        # Garage from residential-details
        garage = self._safe_int(
            residential.get("NumberOfGarages")
        )

        # Pool - if Pool field has a value (sqft), property has a pool
        pool_sqft = residential.get("Pool")
        has_pool = pool_sqft is not None and pool_sqft != "" and pool_sqft != "0"

        # Livable sqft from residential-details
        livable_sqft = self._safe_int(residential.get("LivableSpace"))

        # Bath estimate from fixtures (typically 3 fixtures per full bath)
        bath_fixtures = self._safe_int(residential.get("BathFixtures"))
        baths = bath_fixtures / 3.0 if bath_fixtures else None

        # Full cash value from valuation
        fcv = self._safe_int(valuation.get("FullCashValue"))

        # Limited property value (used for tax calculation)
        lpv = self._safe_int(
            valuation.get("LimitedPropertyValue")
            or valuation.get("AssessedLPV")
        )

        # Tax area code (can be used to estimate tax rate)
        # Actual annual tax requires Treasurer API, not available here

        # Roof and exterior info
        roof_type = residential.get("RoofType")
        exterior_wall = residential.get("ExteriorWalls")

        # Address from main parcel
        address = parcel.get("PropertyAddress", "")

        # Sewer type not available in API - remains None
        sewer = None

        return ParcelData(
            apn=apn,
            full_address=address,
            lot_sqft=lot_sqft,
            year_built=year_built,
            garage_spaces=garage,
            sewer_type=sewer,  # Not available from API
            has_pool=has_pool,
            beds=None,  # Not directly available
            baths=baths,
            tax_annual=None,  # Requires Treasurer API
            full_cash_value=fcv,
            limited_value=lpv,
            livable_sqft=livable_sqft,
            roof_type=roof_type,
            exterior_wall_type=exterior_wall,
            source="maricopa_official",
        )

    def _map_arcgis_response(self, attrs: dict) -> ParcelData:
        """Map ArcGIS response to ParcelData (limited fields)."""
        # Parse formatted values
        fcv_str = attrs.get("FCV_CUR", "")
        fcv = self._parse_currency(fcv_str)

        lpv_str = attrs.get("LPV_CUR", "")
        lpv = self._parse_currency(lpv_str)

        return ParcelData(
            apn=attrs.get("APN", ""),
            full_address=attrs.get("PHYSICAL_ADDRESS", ""),
            lot_sqft=self._safe_int(attrs.get("LAND_SIZE")),
            year_built=self._safe_int(attrs.get("CONST_YEAR")),
            livable_sqft=self._safe_int(attrs.get("LIVING_SPACE")),
            full_cash_value=fcv,
            limited_value=lpv,
            latitude=self._safe_float(attrs.get("LATITUDE")),
            longitude=self._safe_float(attrs.get("LONGITUDE")),
            source="maricopa_arcgis",
            # Fields NOT available from ArcGIS:
            garage_spaces=None,
            sewer_type=None,
            has_pool=None,
            beds=None,
            baths=None,
            tax_annual=None,
        )

    async def extract_for_address(self, street: str) -> Optional[ParcelData]:
        """Extract parcel data for a street address.

        Combines search and data extraction.

        Args:
            street: Street address

        Returns:
            ParcelData if found, None otherwise
        """
        apn = await self.search_apn(street)
        if not apn:
            logger.info(f"No APN found for: {street}")
            return None

        logger.info(f"Found APN {apn} for {street}")
        return await self.get_parcel_data(apn)

    def _normalize_sewer(self, raw: str) -> Optional[str]:
        """Normalize sewer type to 'city' or 'septic'."""
        if not raw:
            return None
        raw_lower = raw.lower()
        if "city" in raw_lower or "municipal" in raw_lower or "public" in raw_lower:
            return "city"
        if "septic" in raw_lower or "private" in raw_lower:
            return "septic"
        return None

    def _parse_currency(self, value: str) -> Optional[int]:
        """Parse currency string like '     89,900' to int."""
        if not value:
            return None
        # Remove non-numeric except digits
        cleaned = re.sub(r"[^\d]", "", value)
        return int(cleaned) if cleaned else None

    @staticmethod
    def _safe_int(value) -> Optional[int]:
        """Safely convert to int."""
        if value is None:
            return None
        try:
            # Handle string numbers
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return None
            return int(float(value))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_float(value) -> Optional[float]:
        """Safely convert to float."""
        if value is None:
            return None
        try:
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    return None
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _safe_bool(value) -> Optional[bool]:
        """Safely convert to bool."""
        if value is None:
            return None
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "y", "1")
        if isinstance(value, (int, float)):
            return bool(value)
        return None
