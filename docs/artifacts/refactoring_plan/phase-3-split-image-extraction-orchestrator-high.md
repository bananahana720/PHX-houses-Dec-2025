# Phase 3: Split Image Extraction Orchestrator (HIGH)

### Problem Statement

`orchestrator.py` (693 lines) handles multiple responsibilities:
- State persistence (load/save)
- Directory management
- Parallel processing coordination
- Statistics tracking
- Image deduplication coordination
- Manifest management

### Solution

Split into focused managers:

```
services/image_extraction/
├── orchestrator.py           # Slim coordinator (< 200 lines)
├── state_manager.py          # State persistence (< 100 lines)
├── extraction_stats.py       # Statistics tracking (< 100 lines)
├── manifest_manager.py       # Manifest I/O (< 100 lines)
└── parallel_coordinator.py   # Async coordination (< 150 lines)
```

### Implementation Steps

#### Step 3.1: Extract state_manager.py

```python
"""State persistence for resumable extraction."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class ExtractionState:
    """Persistent state for resumable extraction."""

    completed_properties: set[str] = field(default_factory=set)
    failed_properties: set[str] = field(default_factory=set)
    last_updated: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "completed_properties": list(self.completed_properties),
            "failed_properties": list(self.failed_properties),
            "last_updated": self.last_updated or datetime.now().astimezone().isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ExtractionState":
        return cls(
            completed_properties=set(data.get("completed_properties", [])),
            failed_properties=set(data.get("failed_properties", [])),
            last_updated=data.get("last_updated"),
        )


class StateManager:
    """Manages extraction state persistence."""

    def __init__(self, state_path: Path):
        self.state_path = state_path
        self._state: Optional[ExtractionState] = None

    def load(self) -> ExtractionState:
        """Load state from disk."""
        if self.state_path.exists():
            with open(self.state_path, "r") as f:
                data = json.load(f)
                return ExtractionState.from_dict(data)
        return ExtractionState()

    def save(self, state: ExtractionState) -> None:
        """Save state to disk."""
        with open(self.state_path, "w") as f:
            json.dump(state.to_dict(), f, indent=2)

    def mark_completed(self, property_address: str) -> None:
        """Mark property as completed."""
        state = self.load()
        state.completed_properties.add(property_address)
        state.failed_properties.discard(property_address)
        self.save(state)

    def mark_failed(self, property_address: str) -> None:
        """Mark property as failed."""
        state = self.load()
        state.failed_properties.add(property_address)
        self.save(state)

    def is_completed(self, property_address: str) -> bool:
        """Check if property was already processed."""
        state = self.load()
        return property_address in state.completed_properties
```

#### Step 3.2: Extract extraction_stats.py

```python
"""Statistics tracking for image extraction."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SourceStats:
    """Statistics for a single image source."""

    source: str
    properties_processed: int = 0
    properties_failed: int = 0
    images_found: int = 0
    images_downloaded: int = 0
    images_failed: int = 0
    duplicates_detected: int = 0


@dataclass
class ExtractionResult:
    """Results from image extraction process."""

    total_properties: int = 0
    properties_completed: int = 0
    properties_failed: int = 0
    properties_skipped: int = 0
    total_images: int = 0
    unique_images: int = 0
    duplicate_images: int = 0
    failed_downloads: int = 0
    by_source: dict[str, SourceStats] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    @property
    def duration_seconds(self) -> float:
        if not self.start_time or not self.end_time:
            return 0.0
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success_rate(self) -> float:
        if self.total_properties == 0:
            return 0.0
        return (self.properties_completed / self.total_properties) * 100

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "total_properties": self.total_properties,
            "properties_completed": self.properties_completed,
            "properties_failed": self.properties_failed,
            "properties_skipped": self.properties_skipped,
            "total_images": self.total_images,
            "unique_images": self.unique_images,
            "duplicate_images": self.duplicate_images,
            "failed_downloads": self.failed_downloads,
            "by_source": {
                name: {
                    "properties_processed": stats.properties_processed,
                    "properties_failed": stats.properties_failed,
                    "images_found": stats.images_found,
                    "images_downloaded": stats.images_downloaded,
                    "images_failed": stats.images_failed,
                    "duplicates_detected": stats.duplicates_detected,
                }
                for name, stats in self.by_source.items()
            },
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "success_rate": self.success_rate,
        }


class StatsTracker:
    """Tracks extraction statistics."""

    def __init__(self):
        self._result = ExtractionResult()
        self._result.start_time = datetime.now()

    def record_property_completed(self, source: str, images_found: int, images_downloaded: int):
        """Record successful property processing."""
        self._result.properties_completed += 1
        self._ensure_source_stats(source)
        self._result.by_source[source].properties_processed += 1
        self._result.by_source[source].images_found += images_found
        self._result.by_source[source].images_downloaded += images_downloaded

    def record_property_failed(self, source: str):
        """Record failed property processing."""
        self._result.properties_failed += 1
        self._ensure_source_stats(source)
        self._result.by_source[source].properties_failed += 1

    def record_duplicate(self, source: str):
        """Record duplicate image detection."""
        self._result.duplicate_images += 1
        self._ensure_source_stats(source)
        self._result.by_source[source].duplicates_detected += 1

    def finalize(self) -> ExtractionResult:
        """Finalize and return results."""
        self._result.end_time = datetime.now()
        return self._result

    def _ensure_source_stats(self, source: str):
        if source not in self._result.by_source:
            self._result.by_source[source] = SourceStats(source=source)
```

#### Step 3.3: Slim orchestrator.py

After extraction, orchestrator becomes:

```python
"""Image extraction orchestrator - slim coordinator."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import httpx

from ...domain.entities import Property
from ...domain.enums import ImageSource
from .state_manager import StateManager
from .extraction_stats import StatsTracker, ExtractionResult
from .manifest_manager import ManifestManager
from .deduplicator import ImageDeduplicator
from .standardizer import ImageStandardizer
from .extractors import (
    MaricopaAssessorExtractor,
    PhoenixMLSExtractor,
    ZillowExtractor,
    RedfinExtractor,
)
from .extractors.base import ImageExtractor

logger = logging.getLogger(__name__)


class ImageExtractionOrchestrator:
    """Coordinates image extraction across all sources."""

    def __init__(
        self,
        base_dir: Path,
        enabled_sources: Optional[list[ImageSource]] = None,
        max_concurrent_properties: int = 3,
        deduplication_threshold: int = 8,
        max_dimension: int = 1024,
    ):
        self.base_dir = Path(base_dir)
        self.enabled_sources = enabled_sources or list(ImageSource)
        self.max_concurrent = max_concurrent_properties

        # Directory structure
        self._setup_directories()

        # Delegate to specialized managers
        self.state_manager = StateManager(self.metadata_dir / "extraction_state.json")
        self.manifest_manager = ManifestManager(self.metadata_dir / "image_manifest.json")
        self.deduplicator = ImageDeduplicator(
            hash_index_path=self.metadata_dir / "hash_index.json",
            similarity_threshold=deduplication_threshold,
        )
        self.standardizer = ImageStandardizer(
            max_dimension=max_dimension,
            output_format="PNG",
        )

        self._http_client: Optional[httpx.AsyncClient] = None

    def _setup_directories(self):
        """Create directory structure."""
        self.processed_dir = self.base_dir / "processed"
        self.raw_dir = self.base_dir / "raw"
        self.metadata_dir = self.base_dir / "metadata"

        for directory in [self.processed_dir, self.raw_dir, self.metadata_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    async def extract_all(
        self,
        properties: list[Property],
        resume: bool = True,
    ) -> ExtractionResult:
        """Extract images for all properties."""
        stats = StatsTracker()

        # Filter already completed if resuming
        to_process = properties
        if resume:
            to_process = [
                p for p in properties
                if not self.state_manager.is_completed(p.full_address)
            ]

        # Process in batches
        extractors = self._create_extractors()

        async with httpx.AsyncClient() as client:
            self._http_client = client

            semaphore = asyncio.Semaphore(self.max_concurrent)
            tasks = [
                self._process_property(prop, extractors, semaphore, stats)
                for prop in to_process
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

        return stats.finalize()

    async def _process_property(
        self,
        property: Property,
        extractors: list[ImageExtractor],
        semaphore: asyncio.Semaphore,
        stats: StatsTracker,
    ):
        """Process single property with all extractors."""
        async with semaphore:
            for extractor in extractors:
                try:
                    urls = await extractor.extract_image_urls(property)
                    # Download, deduplicate, standardize, save
                    # ...simplified for brevity
                    stats.record_property_completed(extractor.name, len(urls), len(urls))
                    self.state_manager.mark_completed(property.full_address)
                except Exception as e:
                    logger.error(f"Failed: {property.full_address}: {e}")
                    stats.record_property_failed(extractor.name)
                    self.state_manager.mark_failed(property.full_address)

    def _create_extractors(self) -> list[ImageExtractor]:
        """Create extractor instances."""
        extractor_map = {
            ImageSource.MARICOPA_ASSESSOR: MaricopaAssessorExtractor,
            ImageSource.PHOENIX_MLS: PhoenixMLSExtractor,
            ImageSource.ZILLOW: ZillowExtractor,
            ImageSource.REDFIN: RedfinExtractor,
        }

        return [
            extractor_map[source](http_client=self._http_client)
            for source in self.enabled_sources
            if source in extractor_map
        ]
```

### Testing Strategy

1. Unit test each extracted manager class
2. Integration test orchestrator with mocked managers
3. Verify existing tests still pass

---
