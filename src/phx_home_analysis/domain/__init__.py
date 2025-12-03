"""Domain models for PHX Home Analysis.

This module exports all domain entities, value objects, and enums for
use throughout the application.
"""

# Entities
from .entities import EnrichmentData, Property

# Enums
from .enums import (
    Orientation,
    RiskLevel,
    SewerType,
    SolarStatus,
    Tier,
)

# Value Objects
from .value_objects import (
    Address,
    RenovationEstimate,
    RiskAssessment,
    Score,
    ScoreBreakdown,
)

__all__ = [
    # Entities
    "Property",
    "EnrichmentData",
    # Value Objects
    "Address",
    "Score",
    "RiskAssessment",
    "ScoreBreakdown",
    "RenovationEstimate",
    # Enums
    "RiskLevel",
    "Tier",
    "SolarStatus",
    "SewerType",
    "Orientation",
]
