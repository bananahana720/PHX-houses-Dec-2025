"""URL tracking for new image detection.

Provides URL-level tracking to detect new images added to listings on re-runs.
Tracks URL history, content changes, and enables incremental extraction by
identifying which URLs are new vs. already processed.

Architecture:
    - Each URL is tracked with its first/last seen timestamps
    - Content hash enables detection of changed images at same URL
    - Status tracking (active, removed, stale) enables lifecycle management
    - Atomic file writes prevent corruption during crashes
"""

import json
import logging
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

logger = logging.getLogger(__name__)

# URL status type
URLStatus = Literal["new", "known", "stale", "content_changed", "removed"]


@dataclass
class URLEntry:
    """Metadata for a tracked image URL.

    Tracks the lifecycle of an image URL from first discovery through
    potential removal or content changes.

    Attributes:
        image_id: UUID of the downloaded image
        property_hash: 8-char hash of property address
        first_seen: ISO timestamp when URL first discovered
        last_seen: ISO timestamp when URL last checked
        content_hash: Hash of image content for change detection
        source: Image source (zillow, redfin, etc.)
        status: Current status (active, removed, stale)
    """

    image_id: str
    property_hash: str
    first_seen: str
    last_seen: str
    content_hash: str
    source: str = ""
    status: str = "active"  # active, removed, stale

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dict representation
        """
        return {
            "image_id": self.image_id,
            "property_hash": self.property_hash,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "content_hash": self.content_hash,
            "source": self.source,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "URLEntry":
        """Create URLEntry from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            URLEntry instance
        """
        return cls(
            image_id=data["image_id"],
            property_hash=data["property_hash"],
            first_seen=data["first_seen"],
            last_seen=data["last_seen"],
            content_hash=data["content_hash"],
            source=data.get("source", ""),
            status=data.get("status", "active"),
        )


@dataclass
class URLTracker:
    """Tracks URLs to detect new/changed images.

    Provides URL-level tracking that enables:
    - Detection of new images added to listings
    - Detection of images removed from listings
    - Detection of content changes at same URL
    - Efficient skip of already-processed URLs

    The tracker is persisted to JSON for cross-session tracking.

    Attributes:
        urls: Dict mapping URL -> URLEntry
        version: Schema version for migrations
        last_updated: ISO timestamp of last modification
    """

    urls: dict[str, URLEntry] = field(default_factory=dict)
    version: str = "1.0.0"
    last_updated: str | None = None

    @classmethod
    def load(cls, path: Path) -> "URLTracker":
        """Load URL tracker from JSON file.

        Creates empty tracker if file doesn't exist.

        Args:
            path: Path to JSON file

        Returns:
            URLTracker instance
        """
        if path.exists():
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)

                urls = {}
                for url, entry_data in data.get("urls", {}).items():
                    urls[url] = URLEntry.from_dict(entry_data)

                tracker = cls(
                    urls=urls,
                    version=data.get("version", "1.0.0"),
                    last_updated=data.get("last_updated"),
                )

                logger.info(f"Loaded URL tracker with {len(urls)} tracked URLs")
                return tracker

            except (OSError, json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load URL tracker: {e}")

        return cls()

    def save(self, path: Path) -> None:
        """Save URL tracker to JSON file with atomic write.

        Uses atomic write (write to temp, then rename) to prevent
        corruption during crashes.

        Args:
            path: Path to JSON file
        """
        self.last_updated = datetime.now().astimezone().isoformat()

        data = {
            "version": self.version,
            "last_updated": self.last_updated,
            "total_urls": len(self.urls),
            "urls": {url: entry.to_dict() for url, entry in self.urls.items()},
        }

        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file, then rename
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".json",
                dir=path.parent,
                delete=False,
                encoding="utf-8",
            ) as tmp:
                json.dump(data, tmp, indent=2)
                tmp_path = Path(tmp.name)

            # Atomic rename (on same filesystem)
            tmp_path.replace(path)
            logger.debug(f"Saved URL tracker with {len(self.urls)} URLs")

        except OSError as e:
            logger.error(f"Failed to save URL tracker: {e}")
            # Clean up temp file if it exists
            if "tmp_path" in locals():
                tmp_path.unlink(missing_ok=True)
            raise

    def check_url(self, url: str, content_hash: str | None = None) -> tuple[URLStatus, str | None]:
        """Check URL status and determine if processing is needed.

        Returns status indicating whether URL needs processing:
        - "new": URL never seen before, needs download
        - "known": URL already processed, skip download
        - "stale": URL not seen recently, may need refresh
        - "content_changed": URL exists but content hash differs
        - "removed": URL was previously active but marked removed

        Args:
            url: Image URL to check
            content_hash: Optional content hash for change detection

        Returns:
            Tuple of (status, existing_image_id or None)
        """
        if url not in self.urls:
            return "new", None

        entry = self.urls[url]

        # Check if marked as removed
        if entry.status == "removed":
            return "removed", entry.image_id

        # Check for content change if hash provided
        if content_hash and entry.content_hash != content_hash:
            return "content_changed", entry.image_id

        # Check if stale (not seen in last 7 days)
        if entry.last_seen:
            try:
                last_seen = datetime.fromisoformat(entry.last_seen)
                age_days = (datetime.now().astimezone() - last_seen).days
                if age_days > 7:
                    return "stale", entry.image_id
            except (ValueError, TypeError):
                pass

        return "known", entry.image_id

    def register_url(
        self,
        url: str,
        image_id: str,
        property_hash: str,
        content_hash: str,
        source: str = "",
    ) -> None:
        """Register a new or updated URL.

        Creates new entry or updates existing entry with latest information.

        Args:
            url: Image URL
            image_id: UUID of downloaded image
            property_hash: 8-char hash of property address
            content_hash: Hash of image content
            source: Image source identifier
        """
        now = datetime.now().astimezone().isoformat()

        if url in self.urls:
            # Update existing entry
            entry = self.urls[url]
            entry.last_seen = now
            entry.content_hash = content_hash
            entry.status = "active"
            # Keep original image_id unless content changed
            if entry.content_hash != content_hash:
                entry.image_id = image_id
            logger.debug(f"Updated URL entry: {url[:60]}...")
        else:
            # Create new entry
            self.urls[url] = URLEntry(
                image_id=image_id,
                property_hash=property_hash,
                first_seen=now,
                last_seen=now,
                content_hash=content_hash,
                source=source,
                status="active",
            )
            logger.debug(f"Registered new URL: {url[:60]}...")

    def mark_removed(self, url: str) -> None:
        """Mark URL as removed from listing.

        Called when a previously-tracked URL is no longer present in
        the listing. Does not delete the entry to preserve history.

        Args:
            url: URL to mark as removed
        """
        if url in self.urls:
            self.urls[url].status = "removed"
            self.urls[url].last_seen = datetime.now().astimezone().isoformat()
            logger.debug(f"Marked URL as removed: {url[:60]}...")

    def mark_active(self, url: str) -> None:
        """Mark URL as active (seen in current run).

        Updates last_seen timestamp and ensures status is active.

        Args:
            url: URL to mark as active
        """
        if url in self.urls:
            self.urls[url].status = "active"
            self.urls[url].last_seen = datetime.now().astimezone().isoformat()

    def get_urls_for_property(self, property_hash: str) -> list[str]:
        """Get all known URLs for a property.

        Returns both active and removed URLs for the property.

        Args:
            property_hash: 8-char property hash

        Returns:
            List of URLs associated with this property
        """
        return [
            url
            for url, entry in self.urls.items()
            if entry.property_hash == property_hash
        ]

    def get_active_urls_for_property(self, property_hash: str) -> list[str]:
        """Get only active URLs for a property.

        Excludes removed URLs.

        Args:
            property_hash: 8-char property hash

        Returns:
            List of active URLs for this property
        """
        return [
            url
            for url, entry in self.urls.items()
            if entry.property_hash == property_hash and entry.status == "active"
        ]

    def detect_removed_urls(self, property_hash: str, current_urls: set[str]) -> list[str]:
        """Detect URLs that were previously active but not in current listing.

        Compares known URLs for a property against the current set of URLs
        from the listing. Any previously-active URL not in the current set
        is marked as removed.

        Args:
            property_hash: 8-char property hash
            current_urls: Set of URLs currently in the listing

        Returns:
            List of URLs that were removed
        """
        removed = []
        known_urls = self.get_active_urls_for_property(property_hash)

        for url in known_urls:
            if url not in current_urls:
                self.mark_removed(url)
                removed.append(url)

        if removed:
            logger.info(f"Detected {len(removed)} removed URLs for property {property_hash}")

        return removed

    def get_stats(self) -> dict:
        """Get statistics about tracked URLs.

        Returns:
            Dict with tracking statistics
        """
        by_status = {"active": 0, "removed": 0, "stale": 0}
        by_source: dict[str, int] = {}
        by_property: dict[str, int] = {}

        for entry in self.urls.values():
            by_status[entry.status] = by_status.get(entry.status, 0) + 1
            by_source[entry.source] = by_source.get(entry.source, 0) + 1
            by_property[entry.property_hash] = by_property.get(entry.property_hash, 0) + 1

        return {
            "total_urls": len(self.urls),
            "by_status": by_status,
            "by_source": by_source,
            "unique_properties": len(by_property),
            "version": self.version,
            "last_updated": self.last_updated,
        }

    def clear(self) -> None:
        """Clear all tracked URLs."""
        self.urls.clear()
        logger.info("Cleared URL tracker")
