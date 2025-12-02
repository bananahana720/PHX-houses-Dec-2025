"""Property archiver service for data lifecycle management.

This module provides the PropertyArchiver class for archiving property data
from the active enrichment_data.json file to the archive directory.

Archive Workflow:
    1. Validate property exists in enrichment_data.json
    2. Create archive file in data/archive/{property_hash}_{date}.json
    3. Remove property from enrichment_data.json
    4. Update any related state files

Usage:
    from phx_home_analysis.services.lifecycle import PropertyArchiver

    archiver = PropertyArchiver()

    # Archive single property
    result = archiver.archive_property("4732 W Davis Rd, Glendale, AZ 85306")
    if result.success:
        print(f"Archived to: {result.archive_path}")

    # Batch archive
    addresses = ["123 Main St, Phoenix, AZ", "456 Oak Ave, Tempe, AZ"]
    batch_result = archiver.archive_batch(addresses)
    print(batch_result.summary())
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import ArchiveResult, BatchArchiveResult, PropertyStatus

logger = logging.getLogger(__name__)

# Default paths
DEFAULT_ENRICHMENT_PATH = Path("data/enrichment_data.json")
DEFAULT_ARCHIVE_DIR = Path("data/archive")


def compute_property_hash(address: str) -> str:
    """Compute property hash from address.

    Uses MD5 hash of lowercase address, truncated to 8 characters.
    This matches the project's standard property identification scheme.

    Args:
        address: Full property address.

    Returns:
        8-character hex hash.
    """
    return hashlib.md5(address.lower().encode()).hexdigest()[:8]


class PropertyArchiver:
    """Service for archiving property data.

    Moves property records from active enrichment data to archive directory,
    maintaining complete history while keeping active data lean.

    Supports single property and batch archival with atomic file operations
    to prevent data loss.

    Attributes:
        enrichment_path: Path to active enrichment_data.json.
        archive_dir: Directory for archive files.

    Example:
        # Archive single property
        archiver = PropertyArchiver()
        result = archiver.archive_property("123 Main St, Phoenix, AZ 85001")
        if result.success:
            print(f"Archived: {result.archive_path}")

        # Batch archive with custom paths (for testing)
        archiver = PropertyArchiver(
            enrichment_path=Path("test/data.json"),
            archive_dir=Path("test/archive")
        )
        batch_result = archiver.archive_batch(["addr1", "addr2"])
    """

    def __init__(
        self,
        enrichment_path: Path | str | None = None,
        archive_dir: Path | str | None = None,
    ) -> None:
        """Initialize the property archiver.

        Args:
            enrichment_path: Path to enrichment_data.json.
                Defaults to data/enrichment_data.json.
            archive_dir: Directory for archive files.
                Defaults to data/archive/.
        """
        self.enrichment_path = (
            Path(enrichment_path) if enrichment_path else DEFAULT_ENRICHMENT_PATH
        )
        self.archive_dir = Path(archive_dir) if archive_dir else DEFAULT_ARCHIVE_DIR

        logger.debug(
            f"PropertyArchiver initialized: enrichment={self.enrichment_path}, "
            f"archive_dir={self.archive_dir}"
        )

    def _load_enrichment_data(self) -> list[dict[str, Any]]:
        """Load property data from enrichment_data.json.

        Returns:
            List of property dictionaries.

        Raises:
            FileNotFoundError: If enrichment file doesn't exist.
            json.JSONDecodeError: If file contains invalid JSON.
        """
        if not self.enrichment_path.exists():
            raise FileNotFoundError(
                f"Enrichment file not found: {self.enrichment_path}"
            )

        with open(self.enrichment_path, encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            raise ValueError(
                f"Expected list of properties, got {type(data).__name__}"
            )

        return data

    def _save_enrichment_data(
        self,
        data: list[dict[str, Any]],
        create_backup: bool = True,
    ) -> Path | None:
        """Save property data to enrichment_data.json atomically.

        Uses atomic write pattern to prevent corruption.

        Args:
            data: List of property dictionaries to save.
            create_backup: Whether to create backup before saving.

        Returns:
            Path to backup file if created, None otherwise.
        """
        from ...utils.file_ops import atomic_json_save

        backup_path = atomic_json_save(
            self.enrichment_path,
            data,
            create_backup=create_backup,
        )

        logger.debug(f"Saved {len(data)} properties to {self.enrichment_path}")
        return backup_path

    def _find_property_index(
        self,
        properties: list[dict[str, Any]],
        full_address: str,
    ) -> int | None:
        """Find property index in list by address.

        Args:
            properties: List of property dictionaries.
            full_address: Address to search for.

        Returns:
            Index of matching property or None if not found.
        """
        address_lower = full_address.lower()

        for idx, prop in enumerate(properties):
            prop_address = prop.get("full_address", "")
            if prop_address.lower() == address_lower:
                return idx

        return None

    def _create_archive_file(
        self,
        property_data: dict[str, Any],
        archive_date: datetime,
    ) -> Path:
        """Create archive file for a property.

        Creates archive directory if needed and writes property data
        to a dated archive file.

        Args:
            property_data: Property dictionary to archive.
            archive_date: Date to include in filename.

        Returns:
            Path to created archive file.
        """
        # Ensure archive directory exists
        self.archive_dir.mkdir(parents=True, exist_ok=True)

        # Generate archive filename
        full_address = property_data.get("full_address", "unknown")
        property_hash = compute_property_hash(full_address)
        date_str = archive_date.strftime("%Y%m%d")
        archive_filename = f"{property_hash}_{date_str}.json"
        archive_path = self.archive_dir / archive_filename

        # Add archive metadata
        archived_data = {
            **property_data,
            "archived_at": archive_date.isoformat(),
            "status": PropertyStatus.ARCHIVED.value,
            "property_hash": property_hash,
        }

        # Write archive file (atomic)
        temp_path = archive_path.with_suffix(".json.tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(archived_data, f, indent=2, ensure_ascii=False)
            temp_path.replace(archive_path)
        except Exception:
            if temp_path.exists():
                temp_path.unlink()
            raise

        logger.debug(f"Created archive file: {archive_path}")
        return archive_path

    def property_exists(self, full_address: str) -> bool:
        """Check if property exists in enrichment data.

        Args:
            full_address: Address to check.

        Returns:
            True if property exists in enrichment_data.json.
        """
        try:
            properties = self._load_enrichment_data()
            return self._find_property_index(properties, full_address) is not None
        except (FileNotFoundError, json.JSONDecodeError):
            return False

    def archive_property(
        self,
        full_address: str,
        archive_date: datetime | None = None,
    ) -> ArchiveResult:
        """Archive a single property.

        Moves property from enrichment_data.json to archive directory.
        Operation is atomic - either both operations succeed or neither does.

        Args:
            full_address: Address of property to archive.
            archive_date: Date for archive timestamp.
                Defaults to current datetime.

        Returns:
            ArchiveResult with operation details.
        """
        archive_date = archive_date or datetime.now()
        property_hash = compute_property_hash(full_address)

        logger.info(f"Archiving property: {full_address} [{property_hash}]")

        # Load current data
        try:
            properties = self._load_enrichment_data()
        except FileNotFoundError as e:
            logger.error(f"Enrichment file not found: {e}")
            return ArchiveResult(
                success=False,
                full_address=full_address,
                property_hash=property_hash,
                error_message=f"Enrichment file not found: {self.enrichment_path}",
            )
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in enrichment file: {e}")
            return ArchiveResult(
                success=False,
                full_address=full_address,
                property_hash=property_hash,
                error_message=f"Invalid JSON in enrichment file: {e}",
            )

        # Find property
        prop_index = self._find_property_index(properties, full_address)
        if prop_index is None:
            logger.warning(f"Property not found: {full_address}")
            return ArchiveResult(
                success=False,
                full_address=full_address,
                property_hash=property_hash,
                error_message="Property not found in enrichment data",
            )

        # Extract property data
        property_data = properties[prop_index]

        # Create archive file first (fail-fast)
        try:
            archive_path = self._create_archive_file(property_data, archive_date)
        except OSError as e:
            logger.error(f"Failed to create archive file: {e}")
            return ArchiveResult(
                success=False,
                full_address=full_address,
                property_hash=property_hash,
                error_message=f"Failed to create archive file: {e}",
            )

        # Remove from enrichment data
        properties.pop(prop_index)

        # Save updated enrichment data
        try:
            self._save_enrichment_data(properties)
        except OSError as e:
            # Rollback: delete archive file
            logger.error(f"Failed to save enrichment data, rolling back: {e}")
            try:
                archive_path.unlink()
            except OSError:
                pass
            return ArchiveResult(
                success=False,
                full_address=full_address,
                property_hash=property_hash,
                error_message=f"Failed to save enrichment data: {e}",
            )

        logger.info(f"Successfully archived: {full_address} -> {archive_path}")

        return ArchiveResult(
            success=True,
            full_address=full_address,
            property_hash=property_hash,
            archive_path=str(archive_path),
            archived_at=archive_date,
        )

    def archive_batch(
        self,
        addresses: list[str],
        archive_date: datetime | None = None,
    ) -> BatchArchiveResult:
        """Archive multiple properties.

        Archives each property in sequence. Individual failures don't
        stop the batch operation.

        Args:
            addresses: List of property addresses to archive.
            archive_date: Date for archive timestamps.
                Defaults to current datetime.

        Returns:
            BatchArchiveResult with aggregated results.
        """
        archive_date = archive_date or datetime.now()
        started_at = datetime.now()

        logger.info(f"Starting batch archive of {len(addresses)} properties")

        result = BatchArchiveResult(
            total_requested=len(addresses),
            started_at=started_at,
        )

        for address in addresses:
            archive_result = self.archive_property(address, archive_date)
            result.results.append(archive_result)

            if archive_result.success:
                result.success_count += 1
            else:
                result.failure_count += 1

        result.completed_at = datetime.now()

        logger.info(
            f"Batch archive complete: {result.success_count}/{result.total_requested} "
            f"succeeded ({result.success_rate:.1f}%)"
        )

        return result

    def archive_stale_properties(
        self,
        threshold_days: int = 30,
        archive_date: datetime | None = None,
    ) -> BatchArchiveResult:
        """Archive all stale properties.

        Convenience method that combines staleness detection with archival.

        Args:
            threshold_days: Days after which property is considered stale.
            archive_date: Date for archive timestamps.

        Returns:
            BatchArchiveResult with archival results.
        """
        from .staleness import StalenessDetector

        logger.info(f"Archiving stale properties (threshold={threshold_days}d)")

        detector = StalenessDetector(
            enrichment_path=self.enrichment_path,
            threshold_days=threshold_days,
        )

        stale_addresses = detector.get_stale_addresses()

        if not stale_addresses:
            logger.info("No stale properties found")
            return BatchArchiveResult(
                total_requested=0,
                started_at=datetime.now(),
                completed_at=datetime.now(),
            )

        return self.archive_batch(stale_addresses, archive_date)

    def list_archives(self) -> list[Path]:
        """List all archive files.

        Returns:
            List of paths to archive files, sorted by modification time.
        """
        if not self.archive_dir.exists():
            return []

        archives = list(self.archive_dir.glob("*.json"))
        return sorted(archives, key=lambda p: p.stat().st_mtime, reverse=True)

    def get_archive(self, property_hash: str) -> dict[str, Any] | None:
        """Retrieve archived property data by hash.

        Finds the most recent archive file for a given property hash.

        Args:
            property_hash: 8-character property hash.

        Returns:
            Property dictionary if found, None otherwise.
        """
        if not self.archive_dir.exists():
            return None

        # Find matching archives (could be multiple dates)
        pattern = f"{property_hash}_*.json"
        archives = sorted(
            self.archive_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

        if not archives:
            return None

        # Return most recent
        with open(archives[0], encoding="utf-8") as f:
            return json.load(f)

    def restore_property(
        self,
        property_hash: str,
    ) -> ArchiveResult:
        """Restore an archived property back to enrichment data.

        Moves property from archive back to active enrichment_data.json.

        Args:
            property_hash: 8-character property hash of archived property.

        Returns:
            ArchiveResult with restoration details.
        """
        logger.info(f"Restoring property: {property_hash}")

        # Find archive
        archived_data = self.get_archive(property_hash)
        if not archived_data:
            return ArchiveResult(
                success=False,
                full_address="unknown",
                property_hash=property_hash,
                error_message=f"No archive found for hash: {property_hash}",
            )

        full_address = archived_data.get("full_address", "unknown")

        # Remove archive metadata
        restore_data = {
            k: v for k, v in archived_data.items()
            if k not in ("archived_at", "status", "property_hash")
        }

        # Load current enrichment data
        try:
            properties = self._load_enrichment_data()
        except FileNotFoundError:
            properties = []
        except json.JSONDecodeError as e:
            return ArchiveResult(
                success=False,
                full_address=full_address,
                property_hash=property_hash,
                error_message=f"Invalid JSON in enrichment file: {e}",
            )

        # Check for duplicate
        if self._find_property_index(properties, full_address) is not None:
            return ArchiveResult(
                success=False,
                full_address=full_address,
                property_hash=property_hash,
                error_message="Property already exists in enrichment data",
            )

        # Add to enrichment data
        properties.append(restore_data)

        try:
            self._save_enrichment_data(properties)
        except OSError as e:
            return ArchiveResult(
                success=False,
                full_address=full_address,
                property_hash=property_hash,
                error_message=f"Failed to save enrichment data: {e}",
            )

        # Remove archive file
        pattern = f"{property_hash}_*.json"
        for archive_file in self.archive_dir.glob(pattern):
            try:
                archive_file.unlink()
                logger.debug(f"Removed archive file: {archive_file}")
            except OSError as e:
                logger.warning(f"Failed to remove archive file {archive_file}: {e}")

        logger.info(f"Successfully restored: {full_address}")

        return ArchiveResult(
            success=True,
            full_address=full_address,
            property_hash=property_hash,
            archived_at=datetime.now(),
        )

    def __str__(self) -> str:
        """String representation."""
        return (
            f"PropertyArchiver(enrichment={self.enrichment_path}, "
            f"archive_dir={self.archive_dir})"
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"PropertyArchiver("
            f"enrichment_path={self.enrichment_path!r}, "
            f"archive_dir={self.archive_dir!r})"
        )
