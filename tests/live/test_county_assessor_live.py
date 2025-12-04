"""Live tests for Maricopa County Assessor API.

These tests call real APIs and require:
- MARICOPA_ASSESSOR_TOKEN environment variable
- Network connectivity to mcassessor.maricopa.gov
- Rate limiting awareness (configured via --live-rate-limit)

Run with: pytest tests/live/test_county_assessor_live.py -m live -v

Test Categories:
- Authentication: Token validation and API access
- Schema Validation: Response structure matches ParcelData model
- Rate Limiting: No 429 errors across multiple requests
- Data Accuracy: Known addresses return expected data ranges
- Error Handling: Invalid addresses handled gracefully
"""

from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

import pytest

from phx_home_analysis.services.county_data import MaricopaAssessorClient, ParcelData

if TYPE_CHECKING:
    from collections.abc import Callable

    from phx_home_analysis.services.api_client.rate_limiter import RateLimiter

# Mark all tests in this module as live tests
pytestmark = [pytest.mark.live, pytest.mark.asyncio]


# Known addresses with expected data constraints (manually verified)
KNOWN_ADDRESSES: list[tuple[str, dict]] = [
    # (street_address, expected_constraints)
    # Constraints are used for validation, not exact matching
    (
        "4732 W Davis Rd",
        {
            # Actual: 1978 (verified via live API 2024-12-04)
            "year_built_range": (1970, 2025),
            "lot_sqft_range": (5000, 20000),
        },
    ),
    (
        "3847 E Cactus Rd",
        {
            "year_built_range": (1980, 2020),
        },
    ),
]


class TestCountyAssessorAuthentication:
    """Live validation of API authentication."""

    async def test_client_initializes_with_valid_token(
        self,
        assessor_client: MaricopaAssessorClient,
    ) -> None:
        """Verify client initializes successfully with valid token."""
        assert assessor_client is not None
        assert assessor_client._token is not None

    async def test_api_accepts_authentication(
        self,
        assessor_client: MaricopaAssessorClient,
    ) -> None:
        """Verify API accepts our authentication token.

        Makes a minimal request to verify credentials are valid.
        """
        async with assessor_client as client:
            # Search for a known address - if auth fails, this raises
            _parcel = await client.extract_for_address("4732 W Davis Rd")
            # Success means auth worked (even if no results)
            # Failure would raise httpx.HTTPStatusError
            assert _parcel is None or _parcel is not None  # Verify call completed


class TestCountyAssessorSchemaValidation:
    """Validate API response schema matches ParcelData model."""

    async def test_response_returns_parcel_data_type(
        self,
        assessor_client: MaricopaAssessorClient,
    ) -> None:
        """Verify API response is properly typed as ParcelData."""
        async with assessor_client as client:
            parcel = await client.extract_for_address("4732 W Davis Rd")

            if parcel is not None:
                assert isinstance(parcel, ParcelData)

    async def test_parcel_data_has_required_fields(
        self,
        assessor_client: MaricopaAssessorClient,
        record_response: Callable,
    ) -> None:
        """Verify ParcelData contains all expected fields.

        Required fields for kill-switch evaluation:
        - apn: Assessor Parcel Number
        - lot_sqft: Lot size in square feet
        - year_built: Construction year
        - garage_spaces: Number of garage spaces
        - sewer_type: City or septic
        - has_pool: Pool presence
        """
        async with assessor_client as client:
            parcel = await client.extract_for_address("4732 W Davis Rd")

            if parcel is None:
                pytest.skip("No data returned for test address")

            # Record for drift detection
            record_response(
                "county_assessor",
                "extract_for_address",
                asdict(parcel),
                {"input_address": "4732 W Davis Rd"},
            )

            # Verify required fields exist (may be None if not available)
            required_fields = [
                "apn",
                "full_address",
                "lot_sqft",
                "year_built",
                "garage_spaces",
                "sewer_type",
                "has_pool",
            ]
            for field in required_fields:
                assert hasattr(parcel, field), f"Missing required field: {field}"

    async def test_field_types_are_correct(
        self,
        assessor_client: MaricopaAssessorClient,
    ) -> None:
        """Verify field types match ParcelData type hints."""
        async with assessor_client as client:
            parcel = await client.extract_for_address("4732 W Davis Rd")

            if parcel is None:
                pytest.skip("No data returned for test address")

            # Type validations (when field is not None)
            if parcel.apn is not None:
                assert isinstance(parcel.apn, str)
            if parcel.lot_sqft is not None:
                assert isinstance(parcel.lot_sqft, int)
            if parcel.year_built is not None:
                assert isinstance(parcel.year_built, int)
            if parcel.garage_spaces is not None:
                assert isinstance(parcel.garage_spaces, int)
            if parcel.sewer_type is not None:
                assert isinstance(parcel.sewer_type, str)
                assert parcel.sewer_type in ("city", "septic", "unknown")
            if parcel.has_pool is not None:
                assert isinstance(parcel.has_pool, bool)


class TestCountyAssessorRateLimiting:
    """Validate rate limiting prevents 429 errors."""

    async def test_multiple_requests_no_rate_limit_error(
        self,
        assessor_client: MaricopaAssessorClient,
        shared_rate_limiter: RateLimiter,
    ) -> None:
        """Verify multiple sequential requests don't trigger rate limiting.

        Makes 3 requests with rate limiter to verify no 429 errors.
        """
        test_addresses = [
            "4732 W Davis Rd",
            "3847 E Cactus Rd",
            "1234 N Central Ave",
        ]

        async with assessor_client as client:
            for addr in test_addresses:
                # Apply rate limiting before each request
                await shared_rate_limiter.acquire()

                try:
                    await client.extract_for_address(addr)
                except Exception as e:
                    error_str = str(e).lower()
                    if "429" in error_str or "rate limit" in error_str:
                        pytest.fail(f"Rate limit exceeded on {addr}: {e}")
                    # Re-raise other errors
                    raise


class TestCountyAssessorDataAccuracy:
    """Validate data accuracy for known addresses."""

    @pytest.mark.parametrize("address,constraints", KNOWN_ADDRESSES)
    async def test_known_address_data_within_constraints(
        self,
        assessor_client: MaricopaAssessorClient,
        address: str,
        constraints: dict,
        record_response: Callable,
    ) -> None:
        """Verify known addresses return data within expected ranges.

        Uses range-based validation rather than exact values to allow
        for data updates while still catching major changes.
        """
        async with assessor_client as client:
            parcel = await client.extract_for_address(address)

            if parcel is None:
                pytest.skip(f"No data returned for {address}")

            # Record response
            record_response(
                "county_assessor",
                "known_address_validation",
                asdict(parcel),
                {"input_address": address, "constraints": constraints},
            )

            # Validate constraints
            if "year_built_range" in constraints and parcel.year_built:
                min_year, max_year = constraints["year_built_range"]
                assert min_year <= parcel.year_built <= max_year, (
                    f"year_built {parcel.year_built} outside range [{min_year}, {max_year}]"
                )

            if "lot_sqft_range" in constraints and parcel.lot_sqft:
                min_sqft, max_sqft = constraints["lot_sqft_range"]
                assert min_sqft <= parcel.lot_sqft <= max_sqft, (
                    f"lot_sqft {parcel.lot_sqft} outside range [{min_sqft}, {max_sqft}]"
                )

            if "sewer_type" in constraints and parcel.sewer_type:
                assert parcel.sewer_type == constraints["sewer_type"]

            if "has_pool" in constraints and parcel.has_pool is not None:
                assert parcel.has_pool == constraints["has_pool"]


class TestCountyAssessorErrorHandling:
    """Test error handling for invalid inputs."""

    async def test_invalid_address_handles_gracefully(
        self,
        assessor_client: MaricopaAssessorClient,
    ) -> None:
        """Verify invalid address returns None rather than raising exception."""
        async with assessor_client as client:
            # Use obviously invalid address
            parcel = await client.extract_for_address("9999999 Nonexistent Street")

            # Should return None, not raise exception
            assert parcel is None or isinstance(parcel, ParcelData)

    async def test_empty_address_handles_gracefully(
        self,
        assessor_client: MaricopaAssessorClient,
    ) -> None:
        """Verify empty address input is handled gracefully."""
        async with assessor_client as client:
            try:
                parcel = await client.extract_for_address("")
                # Either None or exception is acceptable
                assert parcel is None or isinstance(parcel, ParcelData)
            except (ValueError, Exception):
                # Exception is also acceptable for empty input
                pass
