"""Image deduplication service using perceptual hashing.

Provides duplicate detection across all downloaded images using pHash
and dHash algorithms to identify visually similar images regardless
of compression, resizing, or minor edits.
"""

import json
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional

import imagehash
from PIL import Image

from ...domain.value_objects import PerceptualHash

logger = logging.getLogger(__name__)


class DeduplicationError(Exception):
    """Raised when image deduplication fails."""

    pass


class ImageDeduplicator:
    """Perceptual hash-based image deduplication.

    Uses multiple hash algorithms for robust duplicate detection:
    - pHash (perceptual hash): Primary similarity metric, robust to scaling/compression
    - dHash (difference hash): Secondary confirmation, good for detecting crops

    The hash index is persisted to disk for cross-session deduplication.
    """

    def __init__(
        self,
        hash_index_path: Path,
        similarity_threshold: int = 8,
    ):
        """Initialize deduplicator with hash index location.

        Args:
            hash_index_path: Path to JSON file storing hash index
            similarity_threshold: Maximum Hamming distance to consider duplicate (0-64)
        """
        self._index_path = hash_index_path
        self._threshold = similarity_threshold
        self._hash_index: dict[str, dict] = self._load_index()

    def _load_index(self) -> dict[str, dict]:
        """Load hash index from disk.

        Returns:
            Dict mapping image_id to hash data
        """
        if self._index_path.exists():
            try:
                with open(self._index_path, "r") as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('images', {}))} hashes from index")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load hash index: {e}")

        return {"version": "1.0.0", "images": {}}

    def _save_index(self) -> None:
        """Persist hash index to disk."""
        self._index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._index_path, "w") as f:
            json.dump(self._hash_index, f, indent=2)

    def compute_hash(self, image_data: bytes) -> PerceptualHash:
        """Compute perceptual hashes for image data.

        Args:
            image_data: Raw image bytes

        Returns:
            PerceptualHash value object with phash and dhash

        Raises:
            DeduplicationError: If image cannot be processed
        """
        try:
            img = Image.open(BytesIO(image_data))

            # Convert to RGB if necessary (handles RGBA, P mode, etc.)
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            # Compute hashes
            phash = str(imagehash.phash(img))
            dhash = str(imagehash.dhash(img))

            return PerceptualHash(phash=phash, dhash=dhash)

        except Exception as e:
            raise DeduplicationError(f"Failed to compute hash: {e}") from e

    def is_duplicate(
        self, phash: PerceptualHash
    ) -> tuple[bool, Optional[str]]:
        """Check if image with given hash is a duplicate.

        Args:
            phash: PerceptualHash to check against index

        Returns:
            Tuple of (is_duplicate, original_image_id_or_none)
        """
        for image_id, stored_data in self._hash_index.get("images", {}).items():
            stored_phash = stored_data.get("phash")
            stored_dhash = stored_data.get("dhash")

            if not stored_phash or not stored_dhash:
                continue

            try:
                stored_hash = PerceptualHash(phash=stored_phash, dhash=stored_dhash)

                # Primary check: phash similarity
                if phash.is_similar_to(stored_hash, threshold=self._threshold):
                    # Secondary confirmation: dhash should also be similar
                    dhash_distance = phash.dhash_distance(stored_hash)
                    if dhash_distance <= self._threshold + 2:  # Slightly more lenient
                        logger.debug(
                            f"Duplicate found: distance={phash.hamming_distance(stored_hash)}, "
                            f"dhash_distance={dhash_distance}"
                        )
                        return True, image_id

            except ValueError:
                # Invalid stored hash, skip
                continue

        return False, None

    def register_hash(
        self,
        image_id: str,
        phash: PerceptualHash,
        property_address: str,
        source: str,
    ) -> None:
        """Register a new image hash in the index.

        Args:
            image_id: Unique identifier for the image
            phash: PerceptualHash to register
            property_address: Property the image belongs to
            source: Image source identifier
        """
        self._hash_index.setdefault("images", {})[image_id] = {
            "phash": phash.phash,
            "dhash": phash.dhash,
            "property_address": property_address,
            "source": source,
        }
        self._save_index()
        logger.debug(f"Registered hash for image {image_id}")

    def remove_hash(self, image_id: str) -> bool:
        """Remove a hash from the index.

        Args:
            image_id: Image ID to remove

        Returns:
            True if removed, False if not found
        """
        if image_id in self._hash_index.get("images", {}):
            del self._hash_index["images"][image_id]
            self._save_index()
            return True
        return False

    def get_stats(self) -> dict:
        """Get statistics about the hash index.

        Returns:
            Dict with index statistics
        """
        images = self._hash_index.get("images", {})

        # Count by source
        by_source: dict[str, int] = {}
        by_property: dict[str, int] = {}

        for data in images.values():
            source = data.get("source", "unknown")
            prop = data.get("property_address", "unknown")
            by_source[source] = by_source.get(source, 0) + 1
            by_property[prop] = by_property.get(prop, 0) + 1

        return {
            "total_images": len(images),
            "by_source": by_source,
            "unique_properties": len(by_property),
            "threshold": self._threshold,
        }

    def clear_index(self) -> None:
        """Clear all hashes from index."""
        self._hash_index = {"version": "1.0.0", "images": {}}
        self._save_index()
        logger.info("Cleared hash index")
