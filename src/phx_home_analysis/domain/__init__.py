"""Domain models for PHX Home Analysis.

This module exports all domain entities, value objects, and enums for
use throughout the application.
"""

# Entities
from .entities import Property, EnrichmentData

# Value Objects
from .value_objects import (
    Address,
    Score,
    RiskAssessment,
    ScoreBreakdown,
    RenovationEstimate,
)

# Enums
from .enums import (
    RiskLevel,
    Tier,
    SolarStatus,
    SewerType,
    Orientation,
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
