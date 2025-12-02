"""Field inference and tagging for missing property data.

This module provides the core triage workflow for identifying and attempting
to resolve missing property fields through programmatic means before falling
back to AI inference.

Triage Workflow:
1. Tag missing fields using FieldTagger
2. Attempt web scraping (Zillow, Redfin) for each missing field
3. Attempt Maricopa County Assessor API lookup
4. If both fail, mark field for Claude AI inference

The workflow prioritizes programmatic resolution to minimize AI calls and
maximize data reliability.
"""

from typing import Any, Dict, List, Optional

from .models import ConfidenceLevel, FieldInference, TriageResult


class FieldTagger:
    """Identify and tag fields that need inference.

    Analyzes property data dictionaries to find missing required fields
    that need to be inferred from external sources.

    Attributes:
        REQUIRED_FIELDS: List of field names required for complete property analysis

    Example:
        >>> tagger = FieldTagger()
        >>> missing = tagger.tag_missing_fields({"beds": 4, "baths": None})
        >>> "baths" in missing
        True
    """

    REQUIRED_FIELDS: List[str] = [
        "beds",
        "baths",
        "sqft",
        "lot_sqft",
        "year_built",
        "garage_spaces",
        "sewer_type",
        "has_pool",
    ]

    def tag_missing_fields(self, property_data: Dict[str, Any]) -> List[str]:
        """Identify fields that are missing or None in property data.

        Args:
            property_data: Dictionary of property attributes

        Returns:
            List of field names that are missing or have None values

        Example:
            >>> tagger = FieldTagger()
            >>> data = {"beds": 4, "baths": 2.0, "sqft": None, "lot_sqft": 8000}
            >>> tagger.tag_missing_fields(data)
            ['sqft', 'year_built', 'garage_spaces', 'sewer_type', 'has_pool']
        """
        missing = []
        for field in self.REQUIRED_FIELDS:
            if property_data.get(field) is None:
                missing.append(field)
        return missing

    def get_required_fields(self) -> List[str]:
        """Get the list of required fields.

        Returns:
            Copy of the REQUIRED_FIELDS list
        """
        return self.REQUIRED_FIELDS.copy()


class FieldInferencer:
    """Orchestrate field inference through multiple sources.

    Manages the triage workflow that attempts to resolve missing property
    fields through programmatic means (web scraping, API calls) before
    falling back to AI inference.

    CURRENT STATUS: Stub Implementation
    -----------------------------------
    The programmatic inference methods (_try_programmatic_inference,
    _try_web_scrape_inference, _try_assessor_api_inference) are currently
    stub implementations that return None, causing all missing fields to
    fall through to AI inference. This is intentional for the initial
    implementation phase.

    When fully implemented, these methods will connect to:
    - Web scraping: src/phx_home_analysis/services/image_extraction/extractors/
      (ZillowExtractor, RedfinExtractor for beds, baths, sqft)
    - Assessor API: src/phx_home_analysis/services/county_data/assessor_client.py
      (MaricopaAssessorClient for lot_sqft, year_built, garage_spaces, has_pool)

    Triage Priority Order:
    1. Web scraping (Zillow, Redfin) - fast, direct listing data
    2. Maricopa County Assessor API - authoritative for lot/year/garage
    3. AI inference - fallback for unresolvable fields

    Field-Source Mapping:
    - beds, baths, sqft: Prefer web scraping (listing data)
    - lot_sqft, year_built: Prefer assessor API (authoritative)
    - garage_spaces, has_pool: Either source works
    - sewer_type: Manual verification often required (AI fallback)

    Attributes:
        tagger: FieldTagger instance for identifying missing fields

    Example:
        >>> inferencer = FieldInferencer()
        >>> results = await inferencer.infer_fields(
        ...     {"beds": 4, "baths": None},
        ...     "123 Main St, Phoenix, AZ 85001"
        ... )
        >>> len(results) > 0
        True
    """

    def __init__(self) -> None:
        """Initialize the FieldInferencer with a FieldTagger."""
        self.tagger = FieldTagger()

    async def infer_fields(
        self,
        property_data: Dict[str, Any],
        address: str,
    ) -> List[FieldInference]:
        """Attempt to infer all missing fields for a property.

        Executes the full triage workflow:
        1. Identify missing fields
        2. Attempt programmatic inference for each
        3. Mark unresolved fields for AI inference

        Args:
            property_data: Dictionary of known property attributes
            address: Full property address for lookups

        Returns:
            List of FieldInference objects, one per missing field
        """
        missing = self.tagger.tag_missing_fields(property_data)
        inferences: List[FieldInference] = []

        for field in missing:
            # Attempt programmatic resolution
            inference = await self._try_programmatic_inference(field, address)
            if inference is None:
                # Tag for AI inference
                inference = self._create_ai_pending_inference(field)
            inferences.append(inference)

        return inferences

    async def _try_programmatic_inference(
        self,
        field: str,
        address: str,
    ) -> Optional[FieldInference]:
        """Attempt to infer a field through web scraping or API calls.

        STUB: Returns None to trigger AI inference fallback.

        This method orchestrates the triage workflow by calling the appropriate
        source based on field type. Currently a pass-through stub that logs
        intended behavior but always returns None.

        Tries multiple sources in priority order:
        1. Web scraping (Zillow/Redfin) - good for beds, baths, sqft
        2. Assessor API - good for lot_sqft, year_built, garage_spaces, has_pool

        Args:
            field: Name of the field to infer
            address: Property address for lookups

        Returns:
            FieldInference if successful, None if all sources fail (always None for stub)

        Future Implementation:
            1. Check get_field_source_priority(field) for source order
            2. Try _try_web_scrape_inference() for listing fields
            3. Try _try_assessor_api_inference() for assessor fields
            4. Return first successful FieldInference or None

        Integration Points:
            - Web scraping: services/image_extraction/extractors/
            - Assessor API: services/county_data/assessor_client.py
        """
        # TODO: Implement source triage based on field type
        # Priority order from get_field_source_priority():
        # - beds, baths, sqft: web_scrape -> assessor_api -> ai_inference
        # - lot_sqft, year_built: assessor_api -> web_scrape -> ai_inference
        # - garage_spaces, has_pool: assessor_api -> web_scrape -> ai_inference
        # - sewer_type: web_scrape -> ai_inference (manual often required)

        # For now, all fields fall through to AI inference
        # This is intentional for the initial implementation phase
        return None

    async def _try_web_scrape_inference(
        self,
        field: str,
        address: str,
    ) -> Optional[FieldInference]:
        """Attempt to infer a field value via web scraping.

        STUB: Returns None to trigger AI inference fallback.

        This method would extract listing data from Zillow and Redfin using
        Playwright-based browser automation. Best for fields that appear in
        listing descriptions: beds, baths, sqft.

        Args:
            field: Name of the field to infer
            address: Property address for lookups

        Returns:
            FieldInference if web scraping succeeds, None otherwise (always None for stub)

        Future Implementation Should:
            1. Build a Property entity from address
            2. Use ZillowExtractor or RedfinExtractor to load listing page
            3. Parse listing details (beds, baths, sqft from page content)
            4. Return FieldInference with:
               - source="web_scrape"
               - confidence=0.9 (high for direct listing data)
               - confidence_level=ConfidenceLevel.HIGH

        Integration Point:
            src/phx_home_analysis/services/image_extraction/extractors/
            - ZillowExtractor (zillow_playwright.py) - Primary source
            - RedfinExtractor (redfin_playwright.py) - Fallback source

        Example Future Code:
            ```python
            from ..image_extraction.extractors import ZillowExtractor

            async with ZillowExtractor() as extractor:
                listing_data = await extractor.get_listing_details(property)
                if listing_data and field in listing_data:
                    return FieldInference(
                        field_name=field,
                        inferred_value=listing_data[field],
                        confidence=0.9,
                        confidence_level=ConfidenceLevel.HIGH,
                        source="web_scrape",
                        reasoning=f"Extracted from Zillow listing"
                    )
            ```
        """
        # TODO: Connect to ZillowExtractor/RedfinExtractor when async integration is needed
        # For now, all fields fall through to AI inference
        return None

    async def _try_assessor_api_inference(
        self,
        field: str,
        address: str,
    ) -> Optional[FieldInference]:
        """Attempt to infer a field from Maricopa County Assessor API.

        STUB: Returns None to trigger AI inference fallback.

        This method would query the Maricopa County Assessor API for authoritative
        property data. Best for official records: lot_sqft, year_built, garage_spaces,
        has_pool. Requires MARICOPA_ASSESSOR_TOKEN environment variable.

        Args:
            field: Name of the field to infer
            address: Property address for lookups

        Returns:
            FieldInference if API call succeeds, None otherwise (always None for stub)

        Future Implementation Should:
            1. Initialize MaricopaAssessorClient (uses token from env)
            2. Search for APN (parcel number) by street address
            3. Fetch ParcelData using the APN
            4. Map ParcelData fields to FieldInference:
               - parcel.lot_sqft -> lot_sqft
               - parcel.year_built -> year_built
               - parcel.garage_spaces -> garage_spaces
               - parcel.has_pool -> has_pool
            5. Return FieldInference with:
               - source="assessor_api"
               - confidence=0.95 (very high for official records)
               - confidence_level=ConfidenceLevel.VERY_HIGH

        Integration Point:
            src/phx_home_analysis/services/county_data/assessor_client.py
            - MaricopaAssessorClient - API client with rate limiting
            - ParcelData - Data model for API response

        Available Fields from Assessor API:
            - lot_sqft (authoritative)
            - year_built (authoritative)
            - garage_spaces (reliable)
            - has_pool (reliable)
            - livable_sqft, roof_type, full_cash_value (also available)

        NOT Available from Assessor API:
            - sewer_type (requires manual verification)
            - beds, baths (use web scraping instead)

        Example Future Code:
            ```python
            from ..county_data import MaricopaAssessorClient

            async with MaricopaAssessorClient() as client:
                apn = await client.search_apn(address)
                if apn:
                    parcel = await client.get_parcel_data(apn)
                    if parcel and hasattr(parcel, field):
                        return FieldInference(
                            field_name=field,
                            inferred_value=getattr(parcel, field),
                            confidence=0.95,
                            confidence_level=ConfidenceLevel.VERY_HIGH,
                            source="assessor_api",
                            reasoning=f"From Maricopa County Assessor (APN: {apn})"
                        )
            ```
        """
        # TODO: Connect to MaricopaAssessorClient when async integration is needed
        # Requires MARICOPA_ASSESSOR_TOKEN environment variable
        # For now, all fields fall through to AI inference
        return None

    def _create_ai_pending_inference(self, field: str) -> FieldInference:
        """Create an inference marked for AI processing.

        Creates a placeholder FieldInference that indicates the field
        could not be resolved programmatically and needs AI inference.

        Args:
            field: Name of the field that needs AI inference

        Returns:
            FieldInference with source="ai_pending" and no value
        """
        return FieldInference(
            field_name=field,
            inferred_value=None,
            confidence=0.0,
            confidence_level=ConfidenceLevel.LOW,
            source="ai_pending",
            reasoning="Requires AI inference - programmatic sources exhausted",
        )

    def create_triage_result(
        self,
        property_hash: str,
        inferences: List[FieldInference],
    ) -> TriageResult:
        """Create a TriageResult from a list of inferences.

        Args:
            property_hash: MD5 hash identifier for the property
            inferences: List of FieldInference objects

        Returns:
            TriageResult summarizing the inference outcomes
        """
        return TriageResult(
            property_hash=property_hash,
            inferences=inferences,
        )

    def get_field_source_priority(self, field: str) -> List[str]:
        """Get the preferred source order for a specific field.

        Different fields are better sourced from different places:
        - beds, baths, sqft: Listing sites have most accurate data
        - lot_sqft, year_built: Assessor API is authoritative
        - garage_spaces, has_pool: Assessor API, then listings
        - sewer_type: Often requires manual verification

        Args:
            field: Name of the field

        Returns:
            List of source names in priority order
        """
        # Fields best sourced from listings
        listing_fields = {"beds", "baths", "sqft"}

        # Fields best sourced from assessor
        assessor_fields = {"lot_sqft", "year_built"}

        # Fields that work from either
        hybrid_fields = {"garage_spaces", "has_pool"}

        # Fields that often need manual verification
        manual_fields = {"sewer_type"}

        if field in listing_fields:
            return ["web_scrape", "assessor_api", "ai_inference"]
        elif field in assessor_fields:
            return ["assessor_api", "web_scrape", "ai_inference"]
        elif field in hybrid_fields:
            return ["assessor_api", "web_scrape", "ai_inference"]
        elif field in manual_fields:
            return ["web_scrape", "ai_inference"]
        else:
            return ["web_scrape", "assessor_api", "ai_inference"]
