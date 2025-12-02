"""Configuration module for PHX Home Analysis pipeline.

This module provides all configuration settings for the home analysis pipeline,
including file paths, buyer criteria, scoring weights, and Arizona-specific context.
"""

from .settings import (
    ArizonaContext,
    AppConfig,
    BuyerProfile,
    MapConfig,
    ProjectPaths,
)
from .scoring_weights import ScoringWeights, TierThresholds

__all__ = [
    "AppConfig",
    "ArizonaContext",
    "BuyerProfile",
    "MapConfig",
    "ProjectPaths",
    "ScoringWeights",
    "TierThresholds",
]
