"""Example usage of ImageExtractionOrchestrator.

Demonstrates how to:
1. Initialize the orchestrator with configuration
2. Extract images for properties
3. Resume interrupted extractions
4. Get statistics and results
"""

import asyncio
import logging
from pathlib import Path

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.domain.enums import ImageSource
from phx_home_analysis.services.image_extraction.orchestrator import (
    ImageExtractionOrchestrator,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def create_sample_properties() -> list[Property]:
    """Create sample properties for testing.

    Returns:
        List of Property instances
    """
    return [
        Property(
            street="123 Main St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="123 Main St, Phoenix, AZ 85001",
            price="$475,000",
            price_num=475000,
            beds=4,
            baths=2.5,
            sqft=2500,
            price_per_sqft_raw=190.0,
        ),
        Property(
            street="456 Oak Ave",
            city="Scottsdale",
            state="AZ",
            zip_code="85251",
            full_address="456 Oak Ave, Scottsdale, AZ 85251",
            price="$525,000",
            price_num=525000,
            beds=4,
            baths=3.0,
            sqft=2800,
            price_per_sqft_raw=187.5,
        ),
    ]


async def example_basic_extraction():
    """Example: Basic image extraction for all sources."""
    logger.info("=" * 60)
    logger.info("Example 1: Basic Image Extraction")
    logger.info("=" * 60)

    # Initialize orchestrator
    orchestrator = ImageExtractionOrchestrator(
        base_dir=Path("data/images"),
        enabled_sources=list(ImageSource),  # All sources
        max_concurrent_properties=2,
        deduplication_threshold=8,
        max_dimension=1024,
    )

    # Create sample properties
    properties = create_sample_properties()

    # Extract images
    result = await orchestrator.extract_all(
        properties=properties,
        resume=False,  # Start fresh
    )

    # Print results
    logger.info("\n" + "=" * 60)
    logger.info("Extraction Results")
    logger.info("=" * 60)
    logger.info(f"Total Properties: {result.total_properties}")
    logger.info(f"Completed: {result.properties_completed}")
    logger.info(f"Failed: {result.properties_failed}")
    logger.info(f"Skipped: {result.properties_skipped}")
    logger.info(f"Total Images: {result.total_images}")
    logger.info(f"Unique Images: {result.unique_images}")
    logger.info(f"Duplicates: {result.duplicate_images}")
    logger.info(f"Failed Downloads: {result.failed_downloads}")
    logger.info(f"Duration: {result.duration_seconds:.2f}s")
    logger.info(f"Success Rate: {result.success_rate:.1f}%")

    # Print per-source stats
    logger.info("\nBy Source:")
    for source_name, stats in result.by_source.items():
        logger.info(f"  {source_name}:")
        logger.info(f"    Properties Processed: {stats.properties_processed}")
        logger.info(f"    Images Found: {stats.images_found}")
        logger.info(f"    Images Downloaded: {stats.images_downloaded}")
        logger.info(f"    Duplicates: {stats.duplicates_detected}")
        logger.info(f"    Failed: {stats.images_failed}")


async def example_selective_sources():
    """Example: Extract from only specific sources."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 2: Selective Sources (Zillow + Redfin only)")
    logger.info("=" * 60)

    # Initialize with only web sources
    orchestrator = ImageExtractionOrchestrator(
        base_dir=Path("data/images"),
        enabled_sources=[ImageSource.ZILLOW, ImageSource.REDFIN],
        max_concurrent_properties=3,
    )

    properties = create_sample_properties()

    result = await orchestrator.extract_all(
        properties=properties,
        resume=False,
    )

    logger.info(f"\nExtracted {result.unique_images} unique images from:")
    for source_name in result.by_source:
        logger.info(f"  - {source_name}")


async def example_resume_extraction():
    """Example: Resume interrupted extraction."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 3: Resume Interrupted Extraction")
    logger.info("=" * 60)

    orchestrator = ImageExtractionOrchestrator(
        base_dir=Path("data/images"),
    )

    properties = create_sample_properties()

    # First run (simulated interruption)
    logger.info("Starting initial extraction...")
    result1 = await orchestrator.extract_all(
        properties=properties[:1],  # Only first property
        resume=False,
    )
    logger.info(f"First run: {result1.properties_completed} properties completed")

    # Resume with more properties
    logger.info("\nResuming extraction with additional properties...")
    result2 = await orchestrator.extract_all(
        properties=properties,  # All properties
        resume=True,  # Skip already completed
    )
    logger.info(f"Resume run: {result2.properties_skipped} skipped (already done)")
    logger.info(f"Resume run: {result2.properties_completed} newly completed")


async def example_get_property_images():
    """Example: Retrieve images for specific property."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 4: Get Images for Specific Property")
    logger.info("=" * 60)

    orchestrator = ImageExtractionOrchestrator(
        base_dir=Path("data/images"),
    )

    # Get images for a property
    property = create_sample_properties()[0]
    images = orchestrator.get_property_images(property)

    logger.info(f"Property: {property.full_address}")
    logger.info(f"Total Images: {len(images)}")

    for img in images:
        logger.info(f"\n  Image: {img.filename}")
        logger.info(f"    Source: {img.source}")
        logger.info(f"    Dimensions: {img.width}x{img.height}")
        logger.info(f"    Size: {img.size_kb:.1f} KB")
        logger.info(f"    Path: {img.local_path}")
        logger.info(f"    Hash: {img.phash[:8]}...")


async def example_get_statistics():
    """Example: Get overall extraction statistics."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 5: Overall Statistics")
    logger.info("=" * 60)

    orchestrator = ImageExtractionOrchestrator(
        base_dir=Path("data/images"),
    )

    stats = orchestrator.get_statistics()

    logger.info(f"Total Properties: {stats['total_properties']}")
    logger.info(f"Total Images: {stats['total_images']}")
    logger.info(f"Completed: {stats['completed_properties']}")
    logger.info(f"Failed: {stats['failed_properties']}")

    logger.info("\nImages by Source:")
    for source, count in stats["images_by_source"].items():
        logger.info(f"  {source}: {count}")

    logger.info("\nDeduplication Stats:")
    dedup_stats = stats["deduplication_stats"]
    logger.info(f"  Total Hashes: {dedup_stats['total_images']}")
    logger.info(f"  Unique Properties: {dedup_stats['unique_properties']}")
    logger.info(f"  Threshold: {dedup_stats['threshold']}")

    if stats["last_updated"]:
        logger.info(f"\nLast Updated: {stats['last_updated']}")


async def example_custom_configuration():
    """Example: Custom orchestrator configuration."""
    logger.info("\n" + "=" * 60)
    logger.info("Example 6: Custom Configuration")
    logger.info("=" * 60)

    # Highly concurrent with strict deduplication
    orchestrator = ImageExtractionOrchestrator(
        base_dir=Path("data/images_custom"),
        enabled_sources=[
            ImageSource.ZILLOW,
            ImageSource.REDFIN,
        ],
        max_concurrent_properties=5,  # High concurrency
        deduplication_threshold=5,  # Strict duplicate detection
        max_dimension=512,  # Smaller images
    )

    logger.info("Configuration:")
    logger.info(f"  Sources: {len(orchestrator.enabled_sources)}")
    logger.info(f"  Max Concurrent: {orchestrator.max_concurrent}")
    logger.info(f"  Dedup Threshold: {orchestrator.deduplicator._threshold}")
    logger.info(f"  Max Dimension: {orchestrator.standardizer.max_dimension}px")

    properties = create_sample_properties()
    result = await orchestrator.extract_all(properties)

    logger.info(f"\nExtracted {result.unique_images} images in {result.duration_seconds:.2f}s")


async def main():
    """Run all examples."""
    logger.info("Image Extraction Orchestrator Examples")
    logger.info("=" * 60)

    try:
        # Run examples
        await example_basic_extraction()
        await example_selective_sources()
        await example_resume_extraction()
        await example_get_property_images()
        await example_get_statistics()
        await example_custom_configuration()

        logger.info("\n" + "=" * 60)
        logger.info("All examples completed successfully!")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Error running examples: {e}", exc_info=True)


if __name__ == "__main__":
    # Run examples
    asyncio.run(main())
