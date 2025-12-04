"""Configuration module for PHX Home Analysis pipeline.

This module provides all configuration settings for the home analysis pipeline,
including file paths, buyer criteria, scoring weights, and Arizona-specific context.

New Configuration System (E1.S1):
    The new ConfigLoader loads configuration from YAML files with validation:
    - config/scoring_weights.yaml - Scoring weights and tier thresholds
    - config/buyer_criteria.yaml - Kill-switch criteria

    Usage:
        >>> from phx_home_analysis.config import get_config
        >>> config = get_config()
        >>> config.scoring.section_weights.location.points
        250

Legacy Support:
    The old dataclass-based configuration (AppConfig, BuyerProfile, etc.) is
    still available for backward compatibility but is deprecated.
"""

from .loader import ConfigLoader, get_config, init_config, reset_config
from .scoring_weights import ScoringWeights, TierThresholds
from .settings import (
    AppConfig,
    ArizonaContext,
    BuyerProfile,
    ProjectPaths,
)

__all__ = [
    # New configuration system (preferred)
    "ConfigLoader",
    "get_config",
    "reset_config",
    "init_config",
    # Legacy configuration (deprecated, for backward compatibility)
    "AppConfig",
    "ArizonaContext",
    "BuyerProfile",
    "ProjectPaths",
    "ScoringWeights",
    "TierThresholds",
]
