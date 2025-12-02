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
    OrientationScorer,
    ParksWalkabilityScorer,
    QuietnessScorer,
    SafetyScorer,
    SchoolDistrictScorer,
    SupermarketScorer,
)
from .systems import (
    BackyardUtilityScorer,
    PlumbingElectricalScorer,
    PoolConditionScorer,
    RoofConditionScorer,
)

# Location strategies (Section A: 230 pts max)
LOCATION_STRATEGIES = [
    SchoolDistrictScorer,
    QuietnessScorer,
    SafetyScorer,
    SupermarketScorer,
    ParksWalkabilityScorer,
    OrientationScorer,
]

# Systems strategies (Section B: 180 pts max)
SYSTEMS_STRATEGIES = [
    RoofConditionScorer,
    BackyardUtilityScorer,
    PlumbingElectricalScorer,
    PoolConditionScorer,
    CostEfficiencyScorer,
]

# Interior strategies (Section C: 190 pts max)
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
    "QuietnessScorer",
    "SafetyScorer",
    "SupermarketScorer",
    "ParksWalkabilityScorer",
    "OrientationScorer",
    # Systems strategies
    "RoofConditionScorer",
    "BackyardUtilityScorer",
    "PlumbingElectricalScorer",
    "PoolConditionScorer",
    "CostEfficiencyScorer",
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
