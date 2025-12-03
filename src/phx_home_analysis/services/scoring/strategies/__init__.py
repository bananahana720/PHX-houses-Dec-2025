"""Scoring strategy implementations for all criteria.

This module exports all concrete scoring strategies organized by category:
- Location strategies (Section A)
- Systems strategies (Section B)
- Interior strategies (Section C)
"""

from .cost_efficiency import CostEfficiencyScorer
from .interior import (
    AestheticsScorer,
    FireplaceScorer,
    HighCeilingsScorer,
    KitchenLayoutScorer,
    LaundryAreaScorer,
    MasterSuiteScorer,
    NaturalLightScorer,
)
from .location import (
    AirQualityScorer,
    CrimeIndexScorer,
    FloodRiskScorer,
    NoiseLevelScorer,
    OrientationScorer,
    ParksWalkabilityScorer,
    QuietnessScorer,  # Deprecated, use NoiseLevelScorer
    SafetyScorer,  # Deprecated, use CrimeIndexScorer
    SchoolDistrictScorer,
    SupermarketScorer,
    WalkTransitScorer,
)
from .systems import (
    BackyardUtilityScorer,
    PlumbingElectricalScorer,
    PoolConditionScorer,
    RoofConditionScorer,
    SolarStatusScorer,
)

# Location strategies (Section A: 250 pts max)
LOCATION_STRATEGIES = [
    SchoolDistrictScorer,
    NoiseLevelScorer,  # Replaces QuietnessScorer (uses HowLoud API with highway fallback)
    CrimeIndexScorer,  # Replaces SafetyScorer
    SupermarketScorer,
    ParksWalkabilityScorer,
    OrientationScorer,
    FloodRiskScorer,
    WalkTransitScorer,
    AirQualityScorer,  # NEW - EPA AirNow AQI scoring
]

# Systems strategies (Section B: 175 pts max)
SYSTEMS_STRATEGIES = [
    RoofConditionScorer,
    BackyardUtilityScorer,
    PlumbingElectricalScorer,
    PoolConditionScorer,
    CostEfficiencyScorer,
    SolarStatusScorer,
]

# Interior strategies (Section C: 180 pts max)
INTERIOR_STRATEGIES = [
    KitchenLayoutScorer,
    MasterSuiteScorer,
    NaturalLightScorer,
    HighCeilingsScorer,
    FireplaceScorer,
    LaundryAreaScorer,
    AestheticsScorer,
]

# All strategies combined (600 pts max)
ALL_STRATEGIES = LOCATION_STRATEGIES + SYSTEMS_STRATEGIES + INTERIOR_STRATEGIES

__all__ = [
    # Location strategies
    "SchoolDistrictScorer",
    "NoiseLevelScorer",
    "QuietnessScorer",  # Deprecated, use NoiseLevelScorer
    "CrimeIndexScorer",
    "SafetyScorer",  # Deprecated, use CrimeIndexScorer
    "SupermarketScorer",
    "ParksWalkabilityScorer",
    "OrientationScorer",
    "FloodRiskScorer",
    "WalkTransitScorer",
    "AirQualityScorer",
    # Systems strategies
    "RoofConditionScorer",
    "BackyardUtilityScorer",
    "PlumbingElectricalScorer",
    "PoolConditionScorer",
    "CostEfficiencyScorer",
    "SolarStatusScorer",
    # Interior strategies
    "KitchenLayoutScorer",
    "MasterSuiteScorer",
    "NaturalLightScorer",
    "HighCeilingsScorer",
    "FireplaceScorer",
    "LaundryAreaScorer",
    "AestheticsScorer",
    # Strategy collections
    "LOCATION_STRATEGIES",
    "SYSTEMS_STRATEGIES",
    "INTERIOR_STRATEGIES",
    "ALL_STRATEGIES",
]
