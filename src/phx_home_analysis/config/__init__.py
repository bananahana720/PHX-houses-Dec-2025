"""Configuration module for PHX Home Analysis pipeline.

This module provides all configuration settings for the home analysis pipeline,
including file paths, buyer criteria, scoring weights, and Arizona-specific context.
"""

from .scoring_weights import ScoringWeights, TierThresholds
from .settings import (
    AppConfig,
    ArizonaContext,
    BuyerProfile,
    ProjectPaths,
)

__all__ = [
    "AppConfig",
    "ArizonaContext",
    "BuyerProfile",
    "ProjectPaths",
    "ScoringWeights",
    "TierThresholds",
]
