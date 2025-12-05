"""Categorization service for organizing extracted images.

Provides a separate service layer for AI-powered image categorization
that can be run after extraction or independently on existing images.

This service:
1. Loads images from the extraction manifest
2. Categorizes them using Claude Vision (optional, requires API key)
3. Renames files using the categorized naming convention
4. Updates the category index for fast lookups
5. Creates symlink views for easy browsing

Usage:
    # After extraction
    service = CategorizationService(base_dir)
    await service.categorize_all()  # Categorize all uncategorized images

    # Query images by category
    kitchen_images = service.get_images_by_category(subject="kitchen")
    exterior_images = service.get_images_by_category(location="ext")
"""

import json
import logging
import os
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .categorizer import CategoryResult, ImageCategorizer, ImageLocation, ImageSubject
from .category_index import CategoryIndex
from .naming import generate_image_name, is_categorized_filename
from .symlink_views import SymlinkViewBuilder

logger = logging.getLogger(__name__)


class CategorizationStats:
    """Statistics for a categorization run."""

    def __init__(self) -> None:
        self.total_images: int = 0
        self.categorized: int = 0
        self.already_categorized: int = 0
        self.failed: int = 0
        self.by_location: dict[str, int] = {}
        self.by_subject: dict[str, int] = {}
        self.errors: list[str] = []
        self.start_time: datetime | None = None
        self.end_time: datetime | None = None

    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "total_images": self.total_images,
            "categorized": self.categorized,
            "already_categorized": self.already_categorized,
            "failed": self.failed,
            "by_location": self.by_location,
            "by_subject": self.by_subject,
            "errors": self.errors[:10],  # Limit errors
            "duration_seconds": self.duration_seconds,
        }


class CategorizationService:
    """Service for AI-powered image categorization.

    Works with extracted images to:
    - Categorize images using Claude Vision
    - Rename files with category information
    - Maintain a category index for fast lookups
    - Create symlink views for browsing

    Can be run independently of extraction, enabling:
    - Categorization after extraction completes
    - Re-categorization with updated model
    - Manual override of categories
    """

    def __init__(
        self,
        base_dir: Path,
        anthropic_api_key: str | None = None,
        enable_symlinks: bool = True,
    ):
        """Initialize categorization service.

        Args:
            base_dir: Base directory for images (data/images)
            anthropic_api_key: API key for Claude (falls back to env var)
            enable_symlinks: Whether to create symlink views
        """
        self.base_dir = Path(base_dir)
        self.api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.enable_symlinks = enable_symlinks

        # Directory structure
        self.processed_dir = self.base_dir / "processed"
        self.metadata_dir = self.base_dir / "metadata"
        self.categorized_dir = self.base_dir / "categorized"

        # Create directories
        for directory in [self.processed_dir, self.metadata_dir, self.categorized_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Load manifest
        self.manifest_path = self.metadata_dir / "image_manifest.json"
        self.manifest = self._load_manifest()

        # Initialize category index
        self.category_index = CategoryIndex(
            index_path=self.metadata_dir / "category_index.json"
        )

        # Initialize symlink builder if enabled
        self.symlink_builder: SymlinkViewBuilder | None = None
        if enable_symlinks:
            self.symlink_builder = SymlinkViewBuilder(
                source_dir=self.processed_dir,
                views_dir=self.categorized_dir,
            )

    def _load_manifest(self) -> dict[str, list[dict]]:
        """Load extraction manifest."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path) as f:
                    data = json.load(f)
                    from typing import cast
                    return cast(dict[str, list[dict[Any, Any]]], data.get("properties", {}))
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load manifest: {e}")
        return {}

    def _save_manifest(self) -> None:
        """Save updated manifest."""
        data = {
            "version": "1.0.0",
            "last_updated": datetime.now().astimezone().isoformat(),
            "properties": self.manifest,
        }
        with open(self.manifest_path, "w") as f:
            json.dump(data, f, indent=2)

    @property
    def is_api_available(self) -> bool:
        """Check if Claude API is available for categorization."""
        return self.api_key is not None and len(self.api_key) > 0

    def get_uncategorized_images(self) -> list[tuple[str, str, dict]]:
        """Get list of images that haven't been categorized.

        Returns:
            List of (property_address, image_path, image_metadata) tuples
        """
        uncategorized = []

        for address, images in self.manifest.items():
            for img in images:
                local_path = img.get("local_path", "")
                filename = Path(local_path).name

                # Check if already categorized (has category in metadata or follows naming)
                if img.get("category") or is_categorized_filename(filename):
                    continue

                uncategorized.append((address, local_path, img))

        return uncategorized

    async def categorize_all(
        self,
        force: bool = False,
        progress_callback: Any | None = None,
    ) -> CategorizationStats:
        """Categorize all images in the manifest.

        Args:
            force: Re-categorize even if already categorized
            progress_callback: Optional callback(completed, total)

        Returns:
            CategorizationStats with results
        """
        stats = CategorizationStats()
        stats.start_time = datetime.now().astimezone()

        if not self.is_api_available:
            logger.warning("Anthropic API key not configured - skipping AI categorization")
            logger.info("Images can still be manually categorized or renamed")
            stats.errors.append("API key not configured")
            stats.end_time = datetime.now().astimezone()
            return stats

        # Collect images to categorize
        images_to_process = []
        for address, images in self.manifest.items():
            for img in images:
                stats.total_images += 1

                # Check if already categorized
                if not force and img.get("category"):
                    stats.already_categorized += 1
                    continue

                local_path = img.get("local_path", "")
                full_path = self.base_dir / local_path

                if full_path.exists():
                    images_to_process.append((address, img, full_path))

        logger.info(
            f"Found {len(images_to_process)} images to categorize "
            f"({stats.already_categorized} already done)"
        )

        if not images_to_process:
            stats.end_time = datetime.now().astimezone()
            return stats

        # Process in batches using the categorizer
        async with ImageCategorizer(api_key=self.api_key) as categorizer:
            for i, (address, img_meta, img_path) in enumerate(images_to_process):
                try:
                    # Categorize image
                    result = await categorizer.categorize(img_path)

                    if result.error:
                        logger.warning(f"Categorization error for {img_path}: {result.error}")
                        stats.failed += 1
                        stats.errors.append(f"{img_path.name}: {result.error}")
                        continue

                    # Update manifest with category
                    img_meta["category"] = result.to_dict()

                    # Rename file if needed
                    new_path = await self._rename_image(
                        address=address,
                        current_path=img_path,
                        category=result,
                        source=img_meta.get("source", "unknown"),
                    )

                    if new_path:
                        # Update paths in metadata
                        img_meta["local_path"] = str(new_path.relative_to(self.base_dir))
                        img_meta["categorized_filename"] = new_path.name

                    # Add to category index
                    self.category_index.add(
                        image_id=img_meta["image_id"],
                        property_hash=img_path.parent.name,
                        location=result.location.value,
                        subject=result.subject.value,
                        metadata={
                            "filename": new_path.name if new_path else img_path.name,
                            "confidence": result.confidence,
                            "features": result.features_detected,
                        },
                    )

                    # Update symlinks if enabled
                    if self.symlink_builder and new_path:
                        self.symlink_builder.update_for_image(
                            image_id=img_meta["image_id"],
                            property_hash=img_path.parent.name,
                            location=result.location.value,
                            subject=result.subject.value,
                            filename=new_path.name,
                        )

                    # Update stats
                    stats.categorized += 1
                    loc_key = result.location.value
                    subj_key = result.subject.value
                    stats.by_location[loc_key] = stats.by_location.get(loc_key, 0) + 1
                    stats.by_subject[subj_key] = stats.by_subject.get(subj_key, 0) + 1

                    logger.debug(
                        f"Categorized {img_path.name} -> {result.location.value}/{result.subject.value} "
                        f"({result.confidence:.0%})"
                    )

                    # Progress callback
                    if progress_callback:
                        progress_callback(i + 1, len(images_to_process))

                except Exception as e:
                    logger.error(f"Failed to categorize {img_path}: {e}")
                    stats.failed += 1
                    stats.errors.append(f"{img_path.name}: {str(e)}")

                # Periodic save
                if (i + 1) % 10 == 0:
                    self._save_manifest()
                    self.category_index.save()

        # Final save
        self._save_manifest()
        self.category_index.save()

        stats.end_time = datetime.now().astimezone()

        logger.info(
            f"Categorization complete: {stats.categorized} categorized, "
            f"{stats.failed} failed, {stats.already_categorized} skipped"
        )

        return stats

    async def _rename_image(
        self,
        address: str,
        current_path: Path,
        category: CategoryResult,
        source: str,
    ) -> Path | None:
        """Rename image file with category information.

        Args:
            address: Property address
            current_path: Current file path
            category: Categorization result
            source: Image source

        Returns:
            New path if renamed, None otherwise
        """
        # Generate property hash from directory name
        property_hash = current_path.parent.name

        # Get existing filenames in directory
        existing_names = [f.name for f in current_path.parent.glob("*.png")]

        try:
            # Generate new filename
            image_name = generate_image_name(
                property_hash=property_hash,
                category=category,
                source=source,
                listing_date=date.today(),
                existing_names=existing_names,
            )

            new_path = current_path.parent / image_name.filename

            # Skip if already has the right name
            if new_path == current_path:
                return current_path

            # Rename file
            shutil.move(str(current_path), str(new_path))
            logger.debug(f"Renamed: {current_path.name} -> {new_path.name}")

            return new_path

        except Exception as e:
            logger.warning(f"Failed to rename {current_path}: {e}")
            return None

    def get_images_by_category(
        self,
        location: str | ImageLocation | None = None,
        subject: str | ImageSubject | None = None,
        property_hash: str | None = None,
    ) -> list[dict]:
        """Get images by category.

        Args:
            location: Filter by location (ext, int, sys, feat)
            subject: Filter by subject (kitchen, master, pool, etc.)
            property_hash: Filter by property

        Returns:
            List of image metadata dicts
        """
        # Convert enums
        if isinstance(location, ImageLocation):
            location = location.value
        if isinstance(subject, ImageSubject):
            subject = subject.value

        # Get image IDs from index
        if property_hash:
            image_ids = self.category_index.get_for_property(
                property_hash=property_hash,
                location=location,
                subject=subject,
            )
        else:
            image_ids = self.category_index.get_by_category(
                location=location,
                subject=subject,
            )

        # Get full metadata from manifest
        results = []
        for image_id in image_ids:
            meta = self.category_index.get_metadata(image_id)
            if meta:
                results.append(meta)

        return results

    def get_category_stats(self) -> dict:
        """Get statistics about categorized images.

        Returns:
            Dict with category statistics
        """
        return self.category_index.get_stats()

    def rebuild_symlink_views(self) -> dict:
        """Rebuild all symlink views from the category index.

        Returns:
            Dict with rebuild statistics
        """
        if not self.symlink_builder:
            return {"error": "Symlink views disabled"}

        return self.symlink_builder.rebuild_all(self.category_index)

    def cleanup_views(self) -> dict:
        """Clean up stale symlinks and empty directories.

        Returns:
            Dict with cleanup statistics
        """
        if not self.symlink_builder:
            return {"error": "Symlink views disabled"}

        stale_removed = self.symlink_builder.cleanup_stale_links()
        empty_removed = self.symlink_builder.cleanup_empty_directories()

        return {
            "stale_links_removed": stale_removed,
            "empty_dirs_removed": empty_removed,
        }

    def set_category(
        self,
        image_id: str,
        location: str | ImageLocation,
        subject: str | ImageSubject,
        confidence: float = 1.0,
    ) -> bool:
        """Manually set category for an image.

        Args:
            image_id: Image ID to categorize
            location: Location category
            subject: Subject type
            confidence: Confidence score (default 1.0 for manual)

        Returns:
            True if successful
        """
        # Convert enums
        if isinstance(location, ImageLocation):
            location = location.value
        if isinstance(subject, ImageSubject):
            subject = subject.value

        # Find image in manifest
        for address, images in self.manifest.items():
            for img in images:
                if img.get("image_id") == image_id:
                    # Update category
                    img["category"] = {
                        "location": location,
                        "subject": subject,
                        "confidence": confidence,
                        "model_version": "manual",
                        "categorized_at": datetime.now().astimezone().isoformat(),
                    }

                    # Update index
                    local_path = img.get("local_path", "")
                    property_hash = Path(local_path).parent.name

                    # Remove old category if exists
                    self.category_index.remove(image_id)

                    # Add new category
                    self.category_index.add(
                        image_id=image_id,
                        property_hash=property_hash,
                        location=location,
                        subject=subject,
                        metadata={"manual": True},
                    )

                    self._save_manifest()
                    self.category_index.save()

                    return True

        return False


# Convenience function for standalone use
async def categorize_images(
    base_dir: Path,
    force: bool = False,
) -> CategorizationStats:
    """Categorize all images in the given directory.

    Args:
        base_dir: Base directory for images
        force: Re-categorize even if already done

    Returns:
        CategorizationStats with results
    """
    service = CategorizationService(base_dir)
    return await service.categorize_all(force=force)
