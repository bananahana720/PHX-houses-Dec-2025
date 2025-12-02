"""Image deduplication service using perceptual hashing.

Provides duplicate detection across all downloaded images using pHash
and dHash algorithms to identify visually similar images regardless
of compression, resizing, or minor edits.

Performance Optimization:
    Uses Locality Sensitive Hashing (LSH) to reduce duplicate detection
    from O(n^2) to O(n) by bucketing similar hashes together. Only checks
    candidate matches from the same buckets instead of all stored hashes.

Security:
    Uses atomic file writes to prevent corruption from crashes/interrupts.
"""

import json
import logging
from collections import defaultdict
from io import BytesIO
from pathlib import Path

import imagehash
from PIL import Image

from ...domain.value_objects import PerceptualHash

logger = logging.getLogger(__name__)


class DeduplicationError(Exception):
    """Raised when image deduplication fails."""

    pass


class ImageDeduplicator:
    """Perceptual hash-based image deduplication with LSH optimization.

    Uses multiple hash algorithms for robust duplicate detection:
    - pHash (perceptual hash): Primary similarity metric, robust to scaling/compression
    - dHash (difference hash): Secondary confirmation, good for detecting crops

    The hash index is persisted to disk for cross-session deduplication.

    LSH Implementation:
        64-bit perceptual hash is split into bands (default: 8 bands of 8 bits each).
        Images are bucketed by band signatures for O(1) average-case candidate lookup.
        The LSH structure is rebuilt in-memory on load and updated on registration.
    """

    def __init__(
        self,
        hash_index_path: Path,
        similarity_threshold: int = 8,
        num_bands: int = 8,
    ):
        """Initialize deduplicator with hash index location.

        Args:
            hash_index_path: Path to JSON file storing hash index
            similarity_threshold: Maximum Hamming distance to consider duplicate (0-64)
            num_bands: Number of LSH bands for bucketing (default: 8)
        """
        self._index_path = hash_index_path
        self._threshold = similarity_threshold
        self._num_bands = num_bands
        self._band_size = 64 // num_bands  # bits per band
        self._hash_index: dict[str, dict] = self._load_index()
        self._lsh_buckets: dict[int, dict[str, set[str]]] = self._build_lsh_buckets()

    def _load_index(self) -> dict[str, dict]:
        """Load hash index from disk.

        Returns:
            Dict mapping image_id to hash data
        """
        if self._index_path.exists():
            try:
                with open(self._index_path) as f:
                    data = json.load(f)
                    logger.info(f"Loaded {len(data.get('images', {}))} hashes from index")
                    return data
            except (OSError, json.JSONDecodeError) as e:
                logger.warning(f"Failed to load hash index: {e}")

        return {"version": "1.0.0", "images": {}}

    def _save_index(self) -> None:
        """Persist hash index to disk atomically.

        Security: Uses temp file + rename to prevent corruption from crashes.
        """
        import os
        import tempfile

        self._index_path.parent.mkdir(parents=True, exist_ok=True)

        fd, temp_path = tempfile.mkstemp(dir=self._index_path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._hash_index, f, indent=2)
            os.replace(temp_path, self._index_path)  # Atomic on POSIX and Windows
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def _build_lsh_buckets(self) -> dict[int, dict[str, set[str]]]:
        """Build LSH bucket structure from existing hash index.

        LSH bucketing divides the 64-bit perceptual hash into bands, where each band
        acts as a bucket key. Similar images will share bucket keys for most bands,
        enabling fast candidate lookup.

        Returns:
            Dict mapping band_index -> {bucket_key -> set(image_ids)}
        """
        buckets: dict[int, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))

        for image_id, stored_data in self._hash_index.get("images", {}).items():
            phash_str = stored_data.get("phash")
            if not phash_str:
                continue

            # Add to LSH buckets
            band_keys = self._compute_band_keys(phash_str)
            for band_idx, band_key in enumerate(band_keys):
                buckets[band_idx][band_key].add(image_id)

        logger.info(f"Built LSH index with {len(buckets)} bands")
        return buckets

    def _compute_band_keys(self, phash_str: str) -> list[str]:
        """Compute LSH band keys for a perceptual hash.

        Splits the 64-character hex hash string into bands and extracts
        the substring for each band as the bucket key.

        Args:
            phash_str: 64-character perceptual hash string

        Returns:
            List of band keys (substrings of phash_str)
        """
        band_keys = []
        chars_per_band = len(phash_str) // self._num_bands

        for i in range(self._num_bands):
            start = i * chars_per_band
            end = start + chars_per_band
            band_keys.append(phash_str[start:end])

        return band_keys

    def _get_candidate_images(self, phash_str: str) -> set[str]:
        """Get candidate image IDs for duplicate checking using LSH.

        Queries all LSH buckets and returns the union of image IDs that share
        at least one band with the query hash. This reduces the search space
        from O(n) to O(k) where k is the average bucket size.

        Args:
            phash_str: Perceptual hash string to query

        Returns:
            Set of candidate image IDs to check for duplicates
        """
        candidates = set()
        band_keys = self._compute_band_keys(phash_str)

        for band_idx, band_key in enumerate(band_keys):
            if band_idx in self._lsh_buckets and band_key in self._lsh_buckets[band_idx]:
                candidates.update(self._lsh_buckets[band_idx][band_key])

        return candidates

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

    def is_duplicate(self, phash: PerceptualHash) -> tuple[bool, str | None]:
        """Check if image with given hash is a duplicate using LSH-optimized lookup.

        Uses LSH bucketing to retrieve only candidate matches instead of checking
        all stored hashes. Reduces complexity from O(n) to O(k) where k is the
        average bucket size.

        Args:
            phash: PerceptualHash to check against index

        Returns:
            Tuple of (is_duplicate, original_image_id_or_none)
        """
        # Get candidate image IDs using LSH
        candidates = self._get_candidate_images(phash.phash)

        # Only check candidates instead of all images
        for image_id in candidates:
            stored_data = self._hash_index["images"].get(image_id)
            if not stored_data:
                continue

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
                            f"dhash_distance={dhash_distance}, "
                            f"checked {len(candidates)} candidates (LSH optimization)"
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
        """Register a new image hash in the index and update LSH buckets.

        Args:
            image_id: Unique identifier for the image
            phash: PerceptualHash to register
            property_address: Property the image belongs to
            source: Image source identifier
        """
        # Update hash index
        self._hash_index.setdefault("images", {})[image_id] = {
            "phash": phash.phash,
            "dhash": phash.dhash,
            "property_address": property_address,
            "source": source,
        }

        # Update LSH buckets for fast lookup
        band_keys = self._compute_band_keys(phash.phash)
        for band_idx, band_key in enumerate(band_keys):
            self._lsh_buckets[band_idx][band_key].add(image_id)

        self._save_index()
        logger.debug(f"Registered hash for image {image_id} with LSH buckets")

    def remove_hash(self, image_id: str) -> bool:
        """Remove a hash from the index and LSH buckets.

        Args:
            image_id: Image ID to remove

        Returns:
            True if removed, False if not found
        """
        if image_id in self._hash_index.get("images", {}):
            # Get hash before removing to clean up LSH buckets
            stored_data = self._hash_index["images"][image_id]
            phash_str = stored_data.get("phash")

            # Remove from hash index
            del self._hash_index["images"][image_id]

            # Remove from LSH buckets
            if phash_str:
                band_keys = self._compute_band_keys(phash_str)
                for band_idx, band_key in enumerate(band_keys):
                    if band_idx in self._lsh_buckets and band_key in self._lsh_buckets[band_idx]:
                        self._lsh_buckets[band_idx][band_key].discard(image_id)
                        # Clean up empty buckets
                        if not self._lsh_buckets[band_idx][band_key]:
                            del self._lsh_buckets[band_idx][band_key]

            self._save_index()
            return True
        return False

    def get_stats(self) -> dict:
        """Get statistics about the hash index including LSH metrics.

        Returns:
            Dict with index statistics and LSH performance metrics
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

        # LSH bucket statistics
        total_buckets = sum(len(band_buckets) for band_buckets in self._lsh_buckets.values())
        bucket_sizes = [
            len(image_set)
            for band_buckets in self._lsh_buckets.values()
            for image_set in band_buckets.values()
        ]
        avg_bucket_size = sum(bucket_sizes) / len(bucket_sizes) if bucket_sizes else 0

        return {
            "total_images": len(images),
            "by_source": by_source,
            "unique_properties": len(by_property),
            "threshold": self._threshold,
            "lsh": {
                "num_bands": self._num_bands,
                "total_buckets": total_buckets,
                "avg_bucket_size": round(avg_bucket_size, 2),
                "max_bucket_size": max(bucket_sizes) if bucket_sizes else 0,
            },
        }

    def clear_index(self) -> None:
        """Clear all hashes from index and LSH buckets."""
        self._hash_index = {"version": "1.0.0", "images": {}}
        self._lsh_buckets = defaultdict(lambda: defaultdict(set))
        self._save_index()
        logger.info("Cleared hash index and LSH buckets")
