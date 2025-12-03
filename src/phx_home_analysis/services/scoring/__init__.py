"""Property scoring service.

This module provides the complete scoring system for PHX Home Analysis:
- Base abstractions for scoring strategies
- Concrete strategies for all scoring criteria
- PropertyScorer orchestrator for applying strategies
- ScoringExplainer for human-readable score explanations
- CostEfficiencyScorer for monthly cost burden analysis

Scoring System Overview:
    Section A: Location & Environment (250 pts max)
        - School District Rating (42 pts)
        - Noise Level (30 pts)
        - Crime Index (47 pts)
        - Supermarket Proximity (23 pts)
        - Parks & Walkability (23 pts)
        - Sun Orientation (25 pts)
        - Flood Risk (23 pts)
        - Walk/Transit (22 pts)
        - Air Quality (15 pts)

    Section B: Lot & Systems (175 pts max)
        - Roof Condition/Age (45 pts)
        - Backyard Utility (35 pts)
        - Plumbing/Electrical (35 pts)
        - Pool Condition (20 pts)
        - Cost Efficiency (35 pts)
        - Solar Status (5 pts)

    Section C: Interior & Features (180 pts max)
        - Kitchen Layout (40 pts)
        - Master Suite (35 pts)
        - Natural Light (30 pts)
        - High Ceilings (25 pts)
        - Fireplace (20 pts)
        - Laundry Area (20 pts)
        - Overall Aesthetics (10 pts)

    Total Maximum Score: 605 points

Tier Classifications:
    - UNICORN: >480 points (exceptional properties, 80%+)
    - CONTENDER: 360-480 points (strong candidates, 60-80%)
    - PASS: <360 points (meets minimum criteria, <60%)
    - FAILED: Kill switch failure (not scored)

Usage:
    >>> from phx_home_analysis.services.scoring import PropertyScorer
    >>> from phx_home_analysis.domain import Property
    >>>
    >>> # Score single property
    >>> scorer = PropertyScorer()
    >>> property = Property(...)
    >>> score_breakdown = scorer.score(property)
    >>> print(f"Total: {score_breakdown.total_score}/605")
    >>>
    >>> # Score with explanation
    >>> breakdown, explanation = scorer.score_with_explanation(property)
    >>> print(explanation.to_text())  # Markdown output
    >>>
    >>> # Score all properties
    >>> properties = load_properties()
    >>> scored = scorer.score_all(properties)
    >>> unicorns = [p for p in scored if p.is_unicorn]
"""

from .base import ScoringStrategy
from .explanation import (
    FullScoreExplanation,
    ScoreExplanation,
    ScoringExplainer,
    SectionExplanation,
)
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
    # Explanation classes
    "ScoringExplainer",
    "FullScoreExplanation",
    "SectionExplanation",
    "ScoreExplanation",
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
