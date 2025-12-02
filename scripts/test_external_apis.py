"""Test script for Phase 3 external API clients.

Tests FEMA Flood, Census ACS, and Maricopa County zoning clients.
"""

import asyncio
import logging

from phx_home_analysis.services.census_data import CensusAPIClient
from phx_home_analysis.services.county_data import MaricopaAssessorClient
from phx_home_analysis.services.flood_data import FEMAFloodClient

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Test coordinates (Phoenix area)
TEST_LAT = 33.4484  # Central Phoenix
TEST_LNG = -112.0740


async def test_fema_flood_client():
    """Test FEMA flood zone client."""
    logger.info("\n=== Testing FEMA Flood Zone Client ===")

    async with FEMAFloodClient() as client:
        flood_data = await client.get_flood_zone(TEST_LAT, TEST_LNG)

        if flood_data:
            logger.info("✓ Flood data retrieved successfully")
            logger.info(f"  Zone: {flood_data.flood_zone.value.upper()}")
            logger.info(f"  Risk Level: {flood_data.risk_level}")
            logger.info(f"  Insurance Required: {flood_data.flood_insurance_required}")
            logger.info(f"  Panel: {flood_data.flood_zone_panel}")
            logger.info(f"  Description: {flood_data.description}")
        else:
            logger.warning("✗ No flood data found")


async def test_census_client():
    """Test Census ACS client."""
    logger.info("\n=== Testing Census ACS Client ===")

    async with CensusAPIClient() as client:
        demo_data = await client.get_demographic_data_by_coords(TEST_LAT, TEST_LNG)

        if demo_data:
            logger.info("✓ Census data retrieved successfully")
            logger.info(f"  Census Tract: {demo_data.census_tract}")
            logger.info(f"  Median Income: ${demo_data.median_household_income:,}" if demo_data.median_household_income else "  Median Income: N/A")
            logger.info(f"  Median Home Value: ${demo_data.median_home_value:,}" if demo_data.median_home_value else "  Median Home Value: N/A")
            logger.info(f"  Population: {demo_data.total_population:,}" if demo_data.total_population else "  Population: N/A")
            logger.info(f"  Income Tier: {demo_data.income_tier}")
            logger.info(f"  Description: {demo_data.description}")
        else:
            logger.warning("✗ No census data found")


async def test_zoning_client():
    """Test Maricopa County zoning client."""
    logger.info("\n=== Testing Maricopa County Zoning Client ===")

    async with MaricopaAssessorClient() as client:
        zoning_data = await client.get_zoning_data(TEST_LAT, TEST_LNG)

        if zoning_data:
            logger.info("✓ Zoning data retrieved successfully")
            logger.info(f"  Zoning Code: {zoning_data.zoning_code}")
            logger.info(f"  Description: {zoning_data.zoning_description}")
            logger.info(f"  Category: {zoning_data.zoning_category}")
            logger.info(f"  Is Residential: {zoning_data.is_residential}")
        else:
            logger.warning("✗ No zoning data found (may need to adjust layer ID)")


async def test_all_clients():
    """Test all Phase 3 API clients."""
    logger.info("Testing Phase 3 External API Clients")
    logger.info(f"Test Location: ({TEST_LAT}, {TEST_LNG})")

    try:
        await test_fema_flood_client()
        await test_census_client()
        await test_zoning_client()

        logger.info("\n=== Test Complete ===")
        logger.info("All clients tested. Check results above.")

    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)


async def test_enrichment_dict_format():
    """Test that data models produce valid enrichment dicts."""
    logger.info("\n=== Testing Enrichment Dict Format ===")

    async with FEMAFloodClient() as flood_client:
        flood_data = await flood_client.get_flood_zone(TEST_LAT, TEST_LNG)
        if flood_data:
            logger.info(f"Flood enrichment dict: {flood_data.to_enrichment_dict()}")

    async with CensusAPIClient() as census_client:
        demo_data = await census_client.get_demographic_data_by_coords(TEST_LAT, TEST_LNG)
        if demo_data:
            logger.info(f"Census enrichment dict: {demo_data.to_enrichment_dict()}")

    async with MaricopaAssessorClient() as assessor_client:
        zoning_data = await assessor_client.get_zoning_data(TEST_LAT, TEST_LNG)
        if zoning_data:
            logger.info(f"Zoning enrichment dict: {zoning_data.to_enrichment_dict()}")


if __name__ == "__main__":
    asyncio.run(test_all_clients())
    asyncio.run(test_enrichment_dict_format())
