"""Category-based image index for fast lookups.

Provides O(1) lookups for images by category, enabling efficient queries like:
- Get all kitchen images for a property
- Get all exterior images across all properties
- Count images by category for statistics

Index structure supports multiple access patterns:
- By property + location + subject
- By location only (across all properties)
- By subject only (across all properties)
"""

import json
import logging
from collections import defaultdict
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from .categorizer import ImageLocation, ImageSubject
from .naming import ImageName

logger = logging.getLogger(__name__)


class CategoryIndex:
    """Index images by category for fast retrieval.

    Maintains multiple index structures for different query patterns:
    - categories: {location: {subject: [image_ids]}}
    - by_property: {property_hash: {location: {subject: [image_ids]}}}
    - by_location: {location: [image_ids]}
    - by_subject: {subject: [image_ids]}

    The index is persisted to JSON for cross-session use.
    """

    VERSION = "1.0.0"

    def __init__(self, index_path: Path | None = None):
        """Initialize category index.

        Args:
            index_path: Path to JSON file for persistence (optional)
        """
        self._index_path = index_path

        # Primary index: location -> subject -> image_ids
        self._categories: dict[str, dict[str, list[str]]] = defaultdict(
            lambda: defaultdict(list)
        )

        # Secondary index: property_hash -> location -> subject -> image_ids
        self._by_property: dict[str, dict[str, dict[str, list[str]]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(list))
        )

        # Flat indexes for cross-property queries
        self._by_location: dict[str, list[str]] = defaultdict(list)
        self._by_subject: dict[str, list[str]] = defaultdict(list)

        # Metadata tracking
        self._image_metadata: dict[str, dict] = {}
        self._last_updated: str | None = None

        # Load existing index if path provided
        if index_path and index_path.exists():
            self._load()

    def _load(self) -> None:
        """Load index from disk."""
        if not self._index_path or not self._index_path.exists():
            return

        try:
            with open(self._index_path) as f:
                data = json.load(f)

            # Validate version
            version = data.get("version", "1.0.0")
            if version != self.VERSION:
                logger.warning(f"Index version mismatch: {version} vs {self.VERSION}")

            # Load categories
            for location, subjects in data.get("categories", {}).items():
                for subject, image_ids in subjects.items():
                    self._categories[location][subject] = image_ids.copy()

            # Load by_property
            for prop_hash, locations in data.get("by_property", {}).items():
                for location, subjects in locations.items():
                    for subject, image_ids in subjects.items():
                        self._by_property[prop_hash][location][subject] = image_ids.copy()

            # Load flat indexes
            for location, image_ids in data.get("by_location", {}).items():
                self._by_location[location] = image_ids.copy()

            for subject, image_ids in data.get("by_subject", {}).items():
                self._by_subject[subject] = image_ids.copy()

            # Load metadata
            self._image_metadata = data.get("image_metadata", {})
            self._last_updated = data.get("last_updated")

            logger.info(
                f"Loaded category index: {len(self._image_metadata)} images, "
                f"{len(self._by_property)} properties"
            )

        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load category index: {e}")

    def save(self) -> None:
        """Persist index to disk."""
        if not self._index_path:
            return

        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        self._last_updated = datetime.now().astimezone().isoformat()

        data = {
            "version": self.VERSION,
            "last_updated": self._last_updated,
            "categories": {
                loc: dict(subjects)
                for loc, subjects in self._categories.items()
            },
            "by_property": {
                prop: {
                    loc: dict(subjects)
                    for loc, subjects in locations.items()
                }
                for prop, locations in self._by_property.items()
            },
            "by_location": dict(self._by_location),
            "by_subject": dict(self._by_subject),
            "image_metadata": self._image_metadata,
        }

        with open(self._index_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug("Saved category index")

    @classmethod
    def load(cls, path: Path) -> "CategoryIndex":
        """Load index from file.

        Args:
            path: Path to index JSON file

        Returns:
            CategoryIndex instance
        """
        return cls(index_path=path)

    def add(
        self,
        image_id: str,
        property_hash: str,
        location: str,
        subject: str,
        metadata: dict | None = None,
    ) -> None:
        """Add image to index.

        Args:
            image_id: Unique image identifier
            property_hash: Property identifier (8 chars)
            location: Location category (ext, int, sys, feat)
            subject: Subject type (kitchen, master, pool, etc.)
            metadata: Optional additional metadata for the image
        """
        # Add to primary index
        if image_id not in self._categories[location][subject]:
            self._categories[location][subject].append(image_id)

        # Add to property index
        if image_id not in self._by_property[property_hash][location][subject]:
            self._by_property[property_hash][location][subject].append(image_id)

        # Add to flat indexes
        if image_id not in self._by_location[location]:
            self._by_location[location].append(image_id)

        if image_id not in self._by_subject[subject]:
            self._by_subject[subject].append(image_id)

        # Store metadata
        self._image_metadata[image_id] = {
            "property_hash": property_hash,
            "location": location,
            "subject": subject,
            "added_at": datetime.now().astimezone().isoformat(),
            **(metadata or {}),
        }

    def add_from_filename(
        self,
        image_id: str,
        filename: str,
        metadata: dict | None = None,
    ) -> bool:
        """Add image to index by parsing categorized filename.

        Args:
            image_id: Unique image identifier
            filename: Categorized filename to parse
            metadata: Optional additional metadata

        Returns:
            True if added successfully, False if filename couldn't be parsed
        """
        try:
            image_name = ImageName.parse(filename)
            self.add(
                image_id=image_id,
                property_hash=image_name.property_hash,
                location=image_name.location,
                subject=image_name.subject,
                metadata={
                    "filename": filename,
                    "confidence": image_name.confidence,
                    "source": image_name.source,
                    "capture_date": image_name.capture_date.isoformat(),
                    **(metadata or {}),
                },
            )
            return True
        except ValueError as e:
            logger.warning(f"Failed to parse filename for indexing: {filename} - {e}")
            return False

    def remove(self, image_id: str) -> bool:
        """Remove image from all indexes.

        Args:
            image_id: Image ID to remove

        Returns:
            True if removed, False if not found
        """
        if image_id not in self._image_metadata:
            return False

        meta = self._image_metadata[image_id]
        location = meta["location"]
        subject = meta["subject"]
        property_hash = meta["property_hash"]

        # Remove from all indexes
        if image_id in self._categories.get(location, {}).get(subject, []):
            self._categories[location][subject].remove(image_id)

        if image_id in self._by_property.get(property_hash, {}).get(location, {}).get(subject, []):
            self._by_property[property_hash][location][subject].remove(image_id)

        if image_id in self._by_location.get(location, []):
            self._by_location[location].remove(image_id)

        if image_id in self._by_subject.get(subject, []):
            self._by_subject[subject].remove(image_id)

        del self._image_metadata[image_id]
        return True

    def get_by_category(
        self,
        location: str | ImageLocation | None = None,
        subject: str | ImageSubject | None = None,
    ) -> list[str]:
        """Get image IDs by category.

        Args:
            location: Filter by location (optional)
            subject: Filter by subject (optional)

        Returns:
            List of matching image IDs
        """
        # Convert enums to strings
        if isinstance(location, ImageLocation):
            location = location.value
        if isinstance(subject, ImageSubject):
            subject = subject.value

        # No filters - return all
        if location is None and subject is None:
            return list(self._image_metadata.keys())

        # Location only
        if location is not None and subject is None:
            return self._by_location.get(location, []).copy()

        # Subject only
        if location is None and subject is not None:
            return self._by_subject.get(subject, []).copy()

        # Both filters
        return self._categories.get(location, {}).get(subject, []).copy()

    def get_for_property(
        self,
        property_hash: str,
        location: str | ImageLocation | None = None,
        subject: str | ImageSubject | None = None,
    ) -> list[str]:
        """Get image IDs for a specific property.

        Args:
            property_hash: Property identifier
            location: Filter by location (optional)
            subject: Filter by subject (optional)

        Returns:
            List of matching image IDs
        """
        # Convert enums to strings
        if isinstance(location, ImageLocation):
            location = location.value
        if isinstance(subject, ImageSubject):
            subject = subject.value

        if property_hash not in self._by_property:
            return []

        prop_data = self._by_property[property_hash]

        # No filters - return all for property
        if location is None and subject is None:
            result = []
            for loc_data in prop_data.values():
                for image_ids in loc_data.values():
                    result.extend(image_ids)
            return result

        # Location only
        if location is not None and subject is None:
            result = []
            for image_ids in prop_data.get(location, {}).values():
                result.extend(image_ids)
            return result

        # Subject only
        if location is None and subject is not None:
            result = []
            for loc_data in prop_data.values():
                result.extend(loc_data.get(subject, []))
            return result

        # Both filters
        return prop_data.get(location, {}).get(subject, []).copy()

    def get_metadata(self, image_id: str) -> dict | None:
        """Get metadata for an image.

        Args:
            image_id: Image identifier

        Returns:
            Metadata dict or None if not found
        """
        return self._image_metadata.get(image_id)

    def get_stats(self) -> dict:
        """Get category distribution statistics.

        Returns:
            Dict with comprehensive statistics
        """
        total_images = len(self._image_metadata)
        total_properties = len(self._by_property)

        # Count by location
        by_location = {
            loc: len(ids) for loc, ids in self._by_location.items()
        }

        # Count by subject
        by_subject = {
            subj: len(ids) for subj, ids in self._by_subject.items()
        }

        # Images per property
        images_per_property = [
            sum(len(ids) for loc in locs.values() for ids in loc.values())
            for locs in self._by_property.values()
        ]
        avg_images_per_property = (
            sum(images_per_property) / len(images_per_property)
            if images_per_property else 0
        )

        # Top subjects
        top_subjects = sorted(
            by_subject.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:10]

        return {
            "total_images": total_images,
            "total_properties": total_properties,
            "by_location": by_location,
            "by_subject": by_subject,
            "avg_images_per_property": round(avg_images_per_property, 1),
            "top_subjects": dict(top_subjects),
            "last_updated": self._last_updated,
        }

    def get_all_properties(self) -> list[str]:
        """Get all property hashes in index.

        Returns:
            List of property hash strings
        """
        return list(self._by_property.keys())

    def get_all_locations(self) -> list[str]:
        """Get all location categories in index.

        Returns:
            List of location strings
        """
        return list(self._by_location.keys())

    def get_all_subjects(self) -> list[str]:
        """Get all subject types in index.

        Returns:
            List of subject strings
        """
        return list(self._by_subject.keys())

    def iter_images(self) -> Iterator[tuple[str, dict]]:
        """Iterate over all images with metadata.

        Yields:
            Tuples of (image_id, metadata_dict)
        """
        for image_id, metadata in self._image_metadata.items():
            yield image_id, metadata

    def has_image(self, image_id: str) -> bool:
        """Check if image is in index.

        Args:
            image_id: Image identifier to check

        Returns:
            True if image exists in index
        """
        return image_id in self._image_metadata

    def clear(self) -> None:
        """Clear all data from index."""
        self._categories = defaultdict(lambda: defaultdict(list))
        self._by_property = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self._by_location = defaultdict(list)
        self._by_subject = defaultdict(list)
        self._image_metadata = {}
        self._last_updated = None
        logger.info("Cleared category index")

    def __len__(self) -> int:
        """Return total number of indexed images."""
        return len(self._image_metadata)

    def __contains__(self, image_id: str) -> bool:
        """Check if image is in index."""
        return image_id in self._image_metadata
