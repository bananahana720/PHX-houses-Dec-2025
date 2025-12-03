"""Schema versioning for data files.

This module provides schema version detection, migration, and metadata management
for property data files (enrichment_data.json, etc.).

Usage:
    from phx_home_analysis.services.schema import (
        SchemaVersion,
        SchemaMetadata,
        SchemaMigrator,
    )

    # Detect version
    migrator = SchemaMigrator()
    version = migrator.get_version(data)

    # Migrate if needed
    if version != SchemaVersion.current():
        data = migrator.migrate(data, SchemaVersion.current())

    # Add version metadata
    data = migrator.add_version_metadata(data)
"""

from .versioning import SchemaMetadata, SchemaMigrator, SchemaVersion

__all__ = [
    "SchemaVersion",
    "SchemaMetadata",
    "SchemaMigrator",
]
