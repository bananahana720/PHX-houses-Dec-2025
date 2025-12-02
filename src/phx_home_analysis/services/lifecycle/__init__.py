"""Property lifecycle management service.

This module provides tools for managing property data lifecycle including
staleness detection, archival workflows, and status tracking.

Lifecycle Management Overview:
- Staleness Detection: Identify properties with outdated data (>30 days)
- Archival: Move inactive properties to archive directory
- Status Tracking: Track property state (active, sold, delisted, archived)

Property Status Flow:
    ACTIVE -> SOLD (property sold)
    ACTIVE -> DELISTED (listing removed)
    ACTIVE -> ARCHIVED (manually archived or stale)
    SOLD/DELISTED -> ARCHIVED (cleanup after resolution)

Staleness Threshold:
    Default: 30 days since last_updated
    Configurable via StalenessDetector(threshold_days=N)

Archive Structure:
    data/archive/{property_hash}_{date}.json

Usage:
    from phx_home_analysis.services.lifecycle import (
        StalenessDetector,
        PropertyArchiver,
        PropertyLifecycle,
        PropertyStatus,
        StalenessReport,
    )

    # Check for stale properties
    detector = StalenessDetector()
    report = detector.analyze()
    if report.has_stale_properties:
        print(report.summary())

    # Archive a property
    archiver = PropertyArchiver()
    result = archiver.archive_property("123 Main St, Phoenix, AZ 85001")
    if result.success:
        print(f"Archived to: {result.archive_path}")

    # Archive all stale properties
    batch_result = archiver.archive_stale_properties(threshold_days=30)
    print(batch_result.summary())

    # Check individual property lifecycle
    lifecycle = detector.check_property_staleness("123 Main St, Phoenix, AZ")
    if lifecycle and lifecycle.is_stale():
        print(f"Property is {lifecycle.staleness_days} days stale")

CLI Integration:
    # Generate staleness report
    detector = StalenessDetector(threshold_days=14)
    print(detector.summary())

    # Batch archive stale properties
    archiver = PropertyArchiver()
    result = archiver.archive_stale_properties(threshold_days=30)
    print(result.summary())
"""

from .archiver import PropertyArchiver, compute_property_hash
from .models import (
    ArchiveResult,
    BatchArchiveResult,
    PropertyLifecycle,
    PropertyStatus,
    StalenessReport,
)
from .staleness import StalenessDetector

__all__ = [
    # Models
    "PropertyStatus",
    "PropertyLifecycle",
    "StalenessReport",
    "ArchiveResult",
    "BatchArchiveResult",
    # Services
    "StalenessDetector",
    "PropertyArchiver",
    # Utilities
    "compute_property_hash",
]
