"""Build category-based symlink views of images.

Creates virtual directory structures using symlinks for easy browsing
and analysis of images by category without duplicating files.

Directory structure:
    categorized/
    +-- by_location/
    |   +-- exterior/
    |   |   +-- front/
    |   |   +-- pool/
    |   |   +-- ...
    |   +-- interior/
    |   |   +-- kitchen/
    |   |   +-- master/
    |   |   +-- ...
    |   +-- systems/
    |   +-- features/
    +-- by_property/
    |   +-- ef7cd95f/
    |   |   +-- exterior/
    |   |   +-- interior/
    |   +-- ...
    +-- by_subject/
        +-- kitchen/
        +-- master/
        +-- pool/
        +-- ...

Platform notes:
- On Unix/macOS: Uses standard symlinks
- On Windows: Uses directory junctions or copies (symlinks require admin)
"""

import logging
import os
import shutil
from pathlib import Path

from .category_index import CategoryIndex

logger = logging.getLogger(__name__)


class SymlinkViewBuilder:
    """Creates virtual directory structure via symlinks for categorized images.

    Provides multiple view hierarchies for browsing images:
    - by_location: Group by ext/int/sys/feat, then subject
    - by_property: Group by property hash, then location
    - by_subject: Flat grouping by subject type

    Handles platform differences (Unix symlinks vs Windows junctions/copies).
    """

    def __init__(
        self,
        source_dir: Path,
        views_dir: Path,
        use_relative_links: bool = True,
    ):
        """Initialize symlink view builder.

        Args:
            source_dir: Directory containing original processed images
            views_dir: Directory to create symlink views in
            use_relative_links: Use relative paths in symlinks (default True)
        """
        self.source_dir = Path(source_dir)
        self.views_dir = Path(views_dir)
        self.use_relative_links = use_relative_links

        # Detect platform capabilities
        self._can_symlink = self._check_symlink_capability()

    def _check_symlink_capability(self) -> bool:
        """Check if symlinks are supported on this platform.

        Returns:
            True if symlinks can be created
        """
        if os.name == "nt":
            # Windows: try to create a test symlink
            test_dir = self.views_dir / ".symlink_test"
            test_link = self.views_dir / ".symlink_test_link"
            try:
                test_dir.mkdir(parents=True, exist_ok=True)
                if test_link.exists():
                    test_link.unlink()
                test_link.symlink_to(test_dir, target_is_directory=True)
                test_link.unlink()
                test_dir.rmdir()
                return True
            except (OSError, PermissionError):
                logger.warning(
                    "Symlinks not available on Windows without admin. Using file copies instead."
                )
                if test_dir.exists():
                    test_dir.rmdir()
                return False
        return True

    def build_views(
        self,
        index: CategoryIndex,
        views: list[str] | None = None,
    ) -> dict[str, int]:
        """Build symlink structure from category index.

        Args:
            index: CategoryIndex with image metadata
            views: List of views to build ('by_location', 'by_property', 'by_subject')
                   Defaults to all views

        Returns:
            Dict mapping view name to number of links created
        """
        views = views or ["by_location", "by_property", "by_subject"]
        results: dict[str, int] = {}

        if "by_location" in views:
            results["by_location"] = self._build_by_location_view(index)

        if "by_property" in views:
            results["by_property"] = self._build_by_property_view(index)

        if "by_subject" in views:
            results["by_subject"] = self._build_by_subject_view(index)

        logger.info(f"Built symlink views: {results}")
        return results

    def _build_by_location_view(self, index: CategoryIndex) -> int:
        """Build by_location view hierarchy.

        Structure: by_location/{location}/{subject}/{image}

        Args:
            index: CategoryIndex with image metadata

        Returns:
            Number of links created
        """
        view_dir = self.views_dir / "by_location"
        links_created = 0

        for image_id, metadata in index.iter_images():
            location = metadata.get("location", "unknown")
            subject = metadata.get("subject", "unknown")
            filename = metadata.get("filename")
            property_hash = metadata.get("property_hash")

            if not filename or not property_hash:
                continue

            # Source path
            source_path = self.source_dir / property_hash / filename

            if not source_path.exists():
                logger.debug(f"Source not found: {source_path}")
                continue

            # Target path in view
            target_dir = view_dir / location / subject
            target_path = target_dir / filename

            if self._create_link(source_path, target_path):
                links_created += 1

        return links_created

    def _build_by_property_view(self, index: CategoryIndex) -> int:
        """Build by_property view hierarchy.

        Structure: by_property/{property_hash}/{location}/{image}

        Args:
            index: CategoryIndex with image metadata

        Returns:
            Number of links created
        """
        view_dir = self.views_dir / "by_property"
        links_created = 0

        for image_id, metadata in index.iter_images():
            location = metadata.get("location", "unknown")
            filename = metadata.get("filename")
            property_hash = metadata.get("property_hash")

            if not filename or not property_hash:
                continue

            # Source path
            source_path = self.source_dir / property_hash / filename

            if not source_path.exists():
                continue

            # Target path in view
            target_dir = view_dir / property_hash / location
            target_path = target_dir / filename

            if self._create_link(source_path, target_path):
                links_created += 1

        return links_created

    def _build_by_subject_view(self, index: CategoryIndex) -> int:
        """Build by_subject view hierarchy.

        Structure: by_subject/{subject}/{image}

        Args:
            index: CategoryIndex with image metadata

        Returns:
            Number of links created
        """
        view_dir = self.views_dir / "by_subject"
        links_created = 0

        for image_id, metadata in index.iter_images():
            subject = metadata.get("subject", "unknown")
            filename = metadata.get("filename")
            property_hash = metadata.get("property_hash")

            if not filename or not property_hash:
                continue

            # Source path
            source_path = self.source_dir / property_hash / filename

            if not source_path.exists():
                continue

            # Target path in view
            target_dir = view_dir / subject
            target_path = target_dir / filename

            if self._create_link(source_path, target_path):
                links_created += 1

        return links_created

    def _create_link(self, source: Path, target: Path) -> bool:
        """Create symlink or copy depending on platform.

        Args:
            source: Source file path
            target: Target link path

        Returns:
            True if link/copy created successfully
        """
        try:
            # Create parent directory
            target.parent.mkdir(parents=True, exist_ok=True)

            # Skip if target exists
            if target.exists() or target.is_symlink():
                return False

            if self._can_symlink:
                # Use relative path if configured
                if self.use_relative_links:
                    rel_source = os.path.relpath(source, target.parent)
                    target.symlink_to(rel_source)
                else:
                    target.symlink_to(source.resolve())
            else:
                # Fall back to copy on Windows without symlink capability
                shutil.copy2(source, target)

            return True

        except (OSError, PermissionError) as e:
            logger.debug(f"Failed to create link {target}: {e}")
            return False

    def update_for_image(
        self,
        image_id: str,
        property_hash: str,
        location: str,
        subject: str,
        filename: str,
    ) -> int:
        """Add symlinks for a single newly categorized image.

        Args:
            image_id: Unique image identifier
            property_hash: Property identifier
            location: Location category
            subject: Subject type
            filename: Image filename

        Returns:
            Number of links created (0-3)
        """
        source_path = self.source_dir / property_hash / filename

        if not source_path.exists():
            logger.warning(f"Source not found for symlink: {source_path}")
            return 0

        links_created = 0

        # by_location view
        target = self.views_dir / "by_location" / location / subject / filename
        if self._create_link(source_path, target):
            links_created += 1

        # by_property view
        target = self.views_dir / "by_property" / property_hash / location / filename
        if self._create_link(source_path, target):
            links_created += 1

        # by_subject view
        target = self.views_dir / "by_subject" / subject / filename
        if self._create_link(source_path, target):
            links_created += 1

        return links_created

    def remove_for_image(
        self,
        property_hash: str,
        location: str,
        subject: str,
        filename: str,
    ) -> int:
        """Remove symlinks for an image.

        Args:
            property_hash: Property identifier
            location: Location category
            subject: Subject type
            filename: Image filename

        Returns:
            Number of links removed
        """
        links_removed = 0

        targets = [
            self.views_dir / "by_location" / location / subject / filename,
            self.views_dir / "by_property" / property_hash / location / filename,
            self.views_dir / "by_subject" / subject / filename,
        ]

        for target in targets:
            try:
                if target.exists() or target.is_symlink():
                    target.unlink()
                    links_removed += 1
            except OSError as e:
                logger.debug(f"Failed to remove link {target}: {e}")

        return links_removed

    def cleanup_stale_links(self) -> int:
        """Remove symlinks pointing to non-existent files.

        Returns:
            Number of stale links removed
        """
        removed = 0

        for view_name in ["by_location", "by_property", "by_subject"]:
            view_dir = self.views_dir / view_name

            if not view_dir.exists():
                continue

            for link_path in view_dir.rglob("*"):
                if link_path.is_symlink():
                    # Check if target exists
                    try:
                        target = link_path.resolve()
                        if not target.exists():
                            link_path.unlink()
                            removed += 1
                            logger.debug(f"Removed stale link: {link_path}")
                    except OSError:
                        # Broken link
                        try:
                            link_path.unlink()
                            removed += 1
                        except OSError:
                            pass

        if removed > 0:
            logger.info(f"Cleaned up {removed} stale symlinks")

        return removed

    def cleanup_empty_directories(self) -> int:
        """Remove empty directories in view structure.

        Returns:
            Number of directories removed
        """
        removed = 0

        for view_name in ["by_location", "by_property", "by_subject"]:
            view_dir = self.views_dir / view_name

            if not view_dir.exists():
                continue

            # Walk tree bottom-up
            for dirpath in sorted(
                view_dir.rglob("*"),
                key=lambda p: len(p.parts),
                reverse=True,
            ):
                if dirpath.is_dir():
                    try:
                        # rmdir only succeeds if empty
                        dirpath.rmdir()
                        removed += 1
                    except OSError:
                        # Not empty, skip
                        pass

        return removed

    def rebuild_all(self, index: CategoryIndex) -> dict[str, int]:
        """Rebuild all views from scratch.

        Clears existing views and recreates from index.

        Args:
            index: CategoryIndex with image metadata

        Returns:
            Dict with rebuild statistics
        """
        # Clear existing views
        for view_name in ["by_location", "by_property", "by_subject"]:
            view_dir = self.views_dir / view_name
            if view_dir.exists():
                shutil.rmtree(view_dir)

        # Build fresh
        results = self.build_views(index)
        results["rebuilt"] = True

        return results

    def get_stats(self) -> dict:
        """Get statistics about current view structure.

        Returns:
            Dict with view statistics
        """
        stats: dict[str, dict] = {}

        for view_name in ["by_location", "by_property", "by_subject"]:
            view_dir = self.views_dir / view_name

            if not view_dir.exists():
                stats[view_name] = {"exists": False, "links": 0}
                continue

            link_count = sum(1 for _ in view_dir.rglob("*") if _.is_file() or _.is_symlink())
            dir_count = sum(1 for _ in view_dir.rglob("*") if _.is_dir())

            stats[view_name] = {
                "exists": True,
                "links": link_count,
                "directories": dir_count,
            }

        stats["symlinks_supported"] = {"supported": self._can_symlink}
        return stats
