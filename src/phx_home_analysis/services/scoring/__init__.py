"""Property scoring service.

This module provides the complete scoring system for PHX Home Analysis:
- Base abstractions for scoring strategies
- Concrete strategies for all 18 scoring criteria
- PropertyScorer orchestrator for applying strategies
- CostEfficiencyScorer for monthly cost burden analysis

Scoring System Overview:
    Section A: Location & Environment (230 pts max)
        - School District Rating (50 pts)
        - Quietness/Noise Level (40 pts)
        - Safety/Neighborhood (50 pts)
        - Supermarket Proximity (30 pts)
        - Parks & Walkability (30 pts)
        - Sun Orientation (30 pts)

    Section B: Lot & Systems (180 pts max)
        - Roof Condition/Age (50 pts)
        - Backyard Utility (40 pts)
        - Plumbing/Electrical (40 pts)
        - Pool Condition (20 pts)
        - Cost Efficiency (30 pts)

    Section C: Interior & Features (190 pts max)
        - Kitchen Layout (40 pts)
        - Master Suite (40 pts)
        - Natural Light (30 pts)
        - High Ceilings (30 pts)
        - Fireplace (20 pts)
        - Laundry Area (20 pts)
        - Overall Aesthetics (10 pts)

    Total Maximum Score: 600 points

Tier Classifications:
    - UNICORN: >400 points (exceptional properties)
    - CONTENDER: 300-400 points (strong candidates)
    - PASS: <300 points (meets minimum criteria)
    - FAILED: Kill switch failure (not scored)

Usage:
    >>> from phx_home_analysis.services.scoring import PropertyScorer
    >>> from phx_home_analysis.domain import Property
    >>>
    >>> # Score single property
    >>> scorer = PropertyScorer()
    >>> property = Property(...)
    >>> score_breakdown = scorer.score(property)
    >>> print(f"Total: {score_breakdown.total_score}/600")
    >>>
    >>> # Score all properties
    >>> properties = load_properties()
    >>> scored = scorer.score_all(properties)
    >>> unicorns = [p for p in scored if p.is_unicorn]
"""

from .base import ScoringStrategy
from .scorer import PropertyScorer
from .strategies import (
    ALL_STRATEGIES,
    INTERIOR_STRATEGIES,
    LOCATION_STRATEGIES,
    SYSTEMS_STRATEGIES,
    AestheticsScorer,
    BackyardUtilityScorer,
    CostEfficiencyScorer,
    FireplaceScorer,
    HighCeilingsScorer,
    KitchenLayoutScorer,
    LaundryAreaScorer,
    MasterSuiteScorer,
    NaturalLightScorer,
    OrientationScorer,
    ParksWalkabilityScorer,
    PlumbingElectricalScorer,
    PoolConditionScorer,
    QuietnessScorer,
    RoofConditionScorer,
    SafetyScorer,
    SchoolDistrictScorer,
    SupermarketScorer,
)

__all__ = [
    # Main orchestrator
    "PropertyScorer",
    # Base abstraction
    "ScoringStrategy",
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
