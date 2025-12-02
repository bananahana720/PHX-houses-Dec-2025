"""Image extraction service module for PHX Home Analysis.

This module provides functionality to:
- Extract property images from multiple sources (Zillow, Redfin, Phoenix MLS, Maricopa Assessor)
- Deduplicate images using perceptual hashing
- Standardize images to PNG format with consistent dimensions
- Track extraction progress and maintain image manifests

Main components:
- ImageExtractionOrchestrator: Coordinates extraction across all sources
- ImageDeduplicator: Detects duplicate images using pHash
- ImageStandardizer: Converts and resizes images to standard format
- StateManager: Manages extraction state persistence for resumable operations
- StatsTracker: Tracks extraction statistics
- Extractors: Source-specific image extraction implementations
"""

from .deduplicator import ImageDeduplicator
from .extraction_stats import ExtractionResult, SourceStats, StatsTracker
from .orchestrator import ImageExtractionOrchestrator
from .standardizer import ImageStandardizer
from .state_manager import ExtractionState, StateManager

__all__ = [
    "ImageDeduplicator",
    "ImageStandardizer",
    "ImageExtractionOrchestrator",
    "ExtractionState",
    "StateManager",
    "ExtractionResult",
    "SourceStats",
    "StatsTracker",
]
