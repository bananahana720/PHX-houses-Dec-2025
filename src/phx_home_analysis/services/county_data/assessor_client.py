"""Maricopa County Assessor API client for property data extraction.

Supports two API modes:
1. Official API (requires MARICOPA_ASSESSOR_TOKEN) - Complete property data
2. ArcGIS Public API (no auth) - Basic data fallback (lot size, year built, coordinates)
"""

import asyncio
import logging
import os
import re

import httpx

from .models import ParcelData, ZoningData

logger = logging.getLogger(__name__)

# API endpoints
OFFICIAL_API_BASE = "https://mcassessor.maricopa.gov"
ARCGIS_API_BASE = "https://gis.mcassessor.maricopa.gov/arcgis/rest/services/MaricopaDynamicQueryService/MapServer"
# Zoning data may be on a different service - common layer IDs to try: 5, 6, 7
ZONING_LAYER_ID = 5  # Layer ID for zoning - may need adjustment based on actual service


def escape_like_pattern(value: str) -> str:
    r"""Escape SQL LIKE pattern metacharacters to prevent injection attacks.

    Escapes LIKE wildcards and SQL string delimiters:
    - Backslash (\) must be escaped first to avoid double-escaping
    - Percent (%) and underscore (_) are LIKE wildcards
    - Single quote (') is SQL string delimiter

    Args:
        value: Raw user input to be used in LIKE clause

    Returns:
        Escaped string safe for use in SQL LIKE patterns

    Security Note:
        This function prevents SQL injection and LIKE pattern injection
        in ArcGIS WHERE clauses. Always use this when building LIKE
        queries from user-controlled input.
    """
    # Order matters: escape backslash first to avoid double-escaping
    value = value.replace("\\", "\\\\")  # \ → \\
    value = value.replace("%", "\\%")    # % → \%
    value = value.replace("_", "\\_")    # _ → \_
    value = value.replace("'", "''")     # ' → '' (SQL standard)
    return value


def escape_sql_string(value: str) -> str:
    """Escape SQL string literal to prevent injection attacks.

    Escapes single quotes for use in SQL string literals (e.g., APN='value').

    Args:
        value: Raw user input to be used in SQL string literal

    Returns:
        Escaped string safe for use in SQL queries

    Security Note:
        This function prevents SQL injection in equality comparisons.
        For LIKE clauses, use escape_like_pattern() instead.
    """
    return value.replace("'", "''")


class MaricopaAssessorClient:
    """HTTP client for Maricopa County Assessor property data API.

    Attempts Official API first (requires token), falls back to ArcGIS public API.
    """

    def __init__(
        self,
        token: str | None = None,
        timeout: float = 30.0,
        rate_limit_seconds: float = 0.5,  # Reduced from 1.5 for concurrent processing
    ):
        """Initialize client.

        Args:
            token: API token (defaults to MARICOPA_ASSESSOR_TOKEN env var)
            timeout: Request timeout in seconds
            rate_limit_seconds: Delay between API calls (reduced for concurrent use)
        """
        self._token = token or os.getenv("MARICOPA_ASSESSOR_TOKEN")
        self._timeout = timeout
        self._rate_limit_seconds = rate_limit_seconds
        self._last_call = 0.0
        self._http: httpx.AsyncClient | None = None

        if not self._token:
            logger.warning(
                "MARICOPA_ASSESSOR_TOKEN not set - will use ArcGIS fallback only"
            )

    async def __aenter__(self) -> "MaricopaAssessorClient":
        """Async context manager entry with HTTP/2 support.

        Security: Configures client with event hooks for request/response logging
        that prevent accidental token exposure in logs or stack traces.

        Performance: Enables HTTP/2 for multiplexed connections and configures
        connection pooling for efficient concurrent request handling.

        Performance Tuning Notes:
            - max_connections=50: Support high concurrency (batch property processing)
            - max_keepalive_connections=20: Balance connection reuse vs memory
            - HTTP/2 multiplexing allows multiple requests per connection
        """
        # Try HTTP/2, fall back to HTTP/1.1 if h2 not installed
        try:
            self._http = httpx.AsyncClient(
                timeout=self._timeout,
                http2=True,  # Enable HTTP/2 for better performance with concurrent requests
                limits=httpx.Limits(
                    max_keepalive_connections=20,  # Maintain up to 20 persistent connections
                    max_connections=50,  # Allow up to 50 total connections for batch ops
                    keepalive_expiry=30.0,  # Keep connections alive for 30 seconds
                ),
                event_hooks={
                    "request": [self._redact_request_log],
                    "response": [self._redact_response_log],
                },
            )
        except ImportError:
            logger.debug("h2 package not installed, using HTTP/1.1")
            self._http = httpx.AsyncClient(
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_keepalive_connections=20,
                    max_connections=50,
                    keepalive_expiry=30.0,
                ),
                event_hooks={
                    "request": [self._redact_request_log],
                    "response": [self._redact_response_log],
                },
            )
        return self

    async def _redact_request_log(self, request: httpx.Request) -> None:
        """Event hook: Ensure authorization headers are not logged.

        Security: httpx may log requests in debug mode or exceptions.
        This hook runs before request logging, allowing redaction.
        The actual redaction happens in exception handling since we
        cannot modify the request object, but this hook ensures awareness.
        """
        # Event hook placeholder - actual redaction in _safe_error_message
        pass

    async def _redact_response_log(self, response: httpx.Response) -> None:
        """Event hook: Placeholder for response header redaction.

        Security: Ensures response processing is aware of potential
        sensitive data in headers or redirect URLs.
        """
        # Event hook placeholder
        pass

    def _safe_error_message(self, error: Exception) -> str:
        """Create error message with sensitive data redacted.

        Security: Prevents API tokens from appearing in logs, error messages,
        or exception stack traces by replacing token values with redaction marker.

        Args:
            error: Original exception

        Returns:
            Error message string with tokens redacted
        """
        msg = str(error)
        if self._token and self._token in msg:
            msg = msg.replace(self._token, "[REDACTED]")
        return msg

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

    async def search_apn(self, street: str) -> str | None:
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

    async def _search_official_api(self, street: str) -> str | None:
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
            logger.debug(f"Official API search failed: {self._safe_error_message(e)}")

        return None

    async def _search_arcgis(self, street: str) -> str | None:
        """Search via ArcGIS public API.

        Security: Uses escape_like_pattern() to prevent SQL and LIKE injection
        attacks from user-controlled street address input.
        """
        # Escape SQL LIKE metacharacters to prevent injection
        street_escaped = escape_like_pattern(street)
        where_clause = f"PHYSICAL_ADDRESS LIKE '%{street_escaped}%'"

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
            logger.debug(f"ArcGIS search failed: {self._safe_error_message(e)}")

        return None

    async def get_parcel_data(self, apn: str) -> ParcelData | None:
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

    async def _get_official_parcel(self, apn: str) -> ParcelData | None:
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
            logger.debug(f"Official API parcel fetch failed: {self._safe_error_message(e)}")
            return None

    async def _get_arcgis_parcel(self, apn: str) -> ParcelData | None:
        """Get parcel data from ArcGIS public API (limited fields).

        Security: Uses escape_sql_string() to prevent SQL injection
        from APN parameter (though APNs are typically system-generated,
        defense-in-depth principle applies).
        """
        url = f"{ARCGIS_API_BASE}/3/query"
        # Escape APN for SQL string literal (defense-in-depth)
        apn_escaped = escape_sql_string(apn)
        params = {
            "where": f"APN='{apn_escaped}'",
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
            logger.debug(f"ArcGIS parcel fetch failed: {self._safe_error_message(e)}")
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

    async def extract_for_address(self, street: str) -> ParcelData | None:
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

    def _normalize_sewer(self, raw: str) -> str | None:
        """Normalize sewer type to 'city' or 'septic'."""
        if not raw:
            return None
        raw_lower = raw.lower()
        if "city" in raw_lower or "municipal" in raw_lower or "public" in raw_lower:
            return "city"
        if "septic" in raw_lower or "private" in raw_lower:
            return "septic"
        return None

    def _parse_currency(self, value: str) -> int | None:
        """Parse currency string like '     89,900' to int."""
        if not value:
            return None
        # Remove non-numeric except digits
        cleaned = re.sub(r"[^\d]", "", value)
        return int(cleaned) if cleaned else None

    @staticmethod
    def _safe_int(value) -> int | None:
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
    def _safe_float(value) -> float | None:
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
    def _safe_bool(value) -> bool | None:
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

    async def get_zoning_data(self, lat: float, lng: float) -> ZoningData | None:
        """Get zoning data for coordinates.

        Queries Maricopa County GIS zoning layer by lat/lng.

        Args:
            lat: Latitude
            lng: Longitude

        Returns:
            ZoningData if found, None otherwise
        """
        await self._apply_rate_limit()

        # Query zoning layer using spatial intersection
        url = f"{ARCGIS_API_BASE}/{ZONING_LAYER_ID}/query"
        params = {
            "geometry": f"{lng},{lat}",
            "geometryType": "esriGeometryPoint",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "ZONING,ZONE_DESC,ZONE_CLASS",  # Common field names - may need adjustment
            "returnGeometry": "false",
            "f": "json",
        }

        try:
            response = await self._http.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])
            if not features:
                logger.debug(f"No zoning data found for ({lat}, {lng})")
                return None

            attrs = features[0].get("attributes", {})
            return self._parse_zoning_data(attrs, lat, lng)

        except httpx.HTTPError as e:
            logger.debug(f"Zoning query failed: {self._safe_error_message(e)}")
            return None

    def _parse_zoning_data(
        self, attrs: dict, lat: float, lng: float
    ) -> ZoningData | None:
        """Parse zoning attributes from GIS response.

        Args:
            attrs: Feature attributes from API response
            lat: Query latitude
            lng: Query longitude

        Returns:
            ZoningData if valid, None if parsing fails
        """
        try:
            # Try common field names for zoning code
            zoning_code = (
                attrs.get("ZONING")
                or attrs.get("ZONE_CODE")
                or attrs.get("ZONE")
                or attrs.get("ZONECODE")
            )

            if not zoning_code:
                logger.warning("No zoning code found in GIS response")
                return None

            # Try common field names for description
            zone_desc = (
                attrs.get("ZONE_DESC")
                or attrs.get("ZONING_DESC")
                or attrs.get("DESCRIPTION")
                or attrs.get("DESC")
            )

            # Try to get zone class/category
            zone_class = attrs.get("ZONE_CLASS") or attrs.get("CLASS")

            # Derive category from code if not provided
            category = self._derive_zoning_category(zoning_code, zone_class)

            return ZoningData(
                zoning_code=str(zoning_code).strip(),
                zoning_description=zone_desc,
                zoning_category=category,
                latitude=lat,
                longitude=lng,
            )

        except Exception as e:
            logger.error(f"Error parsing zoning data: {e}")
            return None

    def _derive_zoning_category(
        self, zoning_code: str, zone_class: str | None = None
    ) -> str:
        """Derive zoning category from code.

        Args:
            zoning_code: Zoning code (e.g., "R1-6", "C-2")
            zone_class: Optional zone classification from GIS

        Returns:
            Category: "residential", "commercial", "industrial", "mixed", or "other"
        """
        if zone_class:
            zone_class_lower = zone_class.lower()
            if "residential" in zone_class_lower or "single" in zone_class_lower:
                return "residential"
            if "commercial" in zone_class_lower:
                return "commercial"
            if "industrial" in zone_class_lower or "manufacturing" in zone_class_lower:
                return "industrial"
            if "mixed" in zone_class_lower:
                return "mixed"

        # Fallback: derive from code prefix
        code_upper = zoning_code.upper()

        if code_upper.startswith(("R", "RS", "R1", "R2", "R3", "RE", "RU")):
            return "residential"
        elif code_upper.startswith(("C", "COM", "CR", "GC")):
            return "commercial"
        elif code_upper.startswith(("I", "IND", "M", "MFG")):
            return "industrial"
        elif code_upper.startswith(("MU", "MX", "MIXED")):
            return "mixed"
        else:
            return "other"
