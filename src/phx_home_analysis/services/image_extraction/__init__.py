"""Image extraction service module for PHX Home Analysis.

This module provides functionality to:
- Extract property images from multiple sources (Zillow, Redfin, Phoenix MLS, Maricopa Assessor)
- Deduplicate images using perceptual hashing
- Standardize images to PNG format with consistent dimensions
- Download and cache images with format conversion (webp/png to jpg)
- AI-powered image categorization using Claude Vision
- Category-based organization with symlink views
- Track extraction progress and maintain image manifests
- URL-level tracking for incremental extraction on re-runs
- Cache cleanup for images older than 14 days
- Run history logging for audit trails

Main components:
- ImageExtractionOrchestrator: Coordinates extraction across all sources
- ImageDownloader: Downloads images with caching and format conversion (E2.S4)
- ImageManifest: Tracks downloaded images for cache detection (E2.S4)
- ImageDeduplicator: Detects duplicate images using pHash
- ImageStandardizer: Converts and resizes images to standard format
- ImageCategorizer: AI-powered image categorization (Claude Vision)
- CategorizationService: High-level categorization workflow
- CategoryIndex: Fast lookups by category
- SymlinkViewBuilder: Creates category-based directory views
- URLTracker: Tracks individual URLs for incremental extraction
- RunLogger: Logs run history for auditing
- StateManager: Manages extraction state persistence for resumable operations
- StatsTracker: Tracks extraction statistics
- Extractors: Source-specific image extraction implementations
"""

from .categorization_service import CategorizationService, CategorizationStats
from .categorizer import (
    CategoryResult,
    ImageCategorizer,
    ImageLocation,
    ImageSubject,
)
from .category_index import CategoryIndex
from .deduplicator import ImageDeduplicator
from .downloader import (
    CleanupResult,
    DownloadResult,
    ImageDownloader,
    ImageManifest,
    ImageManifestEntry,
    download_property_images,
    normalize_address_for_folder,
)
from .extraction_stats import ExtractionResult, SourceStats, StatsTracker
from .naming import ImageName, generate_image_name, is_categorized_filename
from .orchestrator import ImageExtractionOrchestrator
from .reconciliation import (
    DataReconciler,
    ReconciliationReport,
    run_reconciliation,
)
from .run_logger import PropertyChanges, RunLog, RunLogger
from .standardizer import ImageStandardizer
from .state_manager import ExtractionState, StateManager
from .symlink_views import SymlinkViewBuilder
from .url_tracker import URLEntry, URLTracker
from .validators import (
    AddressMismatchError,
    DataIntegrityError,
    DuringExtractionAssertions,
    HashMismatchError,
    MissingFileError,
    PreExtractionValidator,
    ValidationResult,
    compute_property_hash,
)

__all__ = [
    # Orchestration
    "ImageExtractionOrchestrator",
    # Downloading & Caching (E2.S4)
    "ImageDownloader",
    "ImageManifest",
    "ImageManifestEntry",
    "DownloadResult",
    "CleanupResult",
    "download_property_images",
    "normalize_address_for_folder",
    # Categorization
    "ImageCategorizer",
    "CategorizationService",
    "CategorizationStats",
    "CategoryResult",
    "ImageLocation",
    "ImageSubject",
    "CategoryIndex",
    "SymlinkViewBuilder",
    # Naming
    "ImageName",
    "generate_image_name",
    "is_categorized_filename",
    # Processing
    "ImageDeduplicator",
    "ImageStandardizer",
    # State & Tracking
    "ExtractionState",
    "StateManager",
    "URLTracker",
    "URLEntry",
    # Run Logging
    "RunLogger",
    "RunLog",
    "PropertyChanges",
    # Stats
    "ExtractionResult",
    "SourceStats",
    "StatsTracker",
    # Data Quality & Validation (E2.S4)
    "PreExtractionValidator",
    "DuringExtractionAssertions",
    "DataIntegrityError",
    "AddressMismatchError",
    "HashMismatchError",
    "MissingFileError",
    "ValidationResult",
    "compute_property_hash",
    "DataReconciler",
    "ReconciliationReport",
    "run_reconciliation",
]
