"""PHX Home Analysis - First-time home buyer analysis for Phoenix metropolitan area.

This package provides a complete data pipeline for analyzing Phoenix area home
listings against strict buyer criteria using automated kill-switch filtering
and weighted scoring across location, property systems, and interior features.

Main Components:
    - Config: Application configuration and scoring weights
    - Domain: Property entities, value objects, and enums
    - Repositories: Data persistence layer for CSV and JSON
    - Services: Kill-switch filtering and property scoring
    - Pipeline: Main orchestrator for complete analysis workflow

Quick Start:
    >>> from phx_home_analysis import AnalysisPipeline
    >>> pipeline = AnalysisPipeline()
    >>> result = pipeline.run()
    >>> print(result.summary_text())

For detailed documentation, see CLAUDE.md in the project root.
"""

# Config
from .config import (
    AppConfig,
    ArizonaContext,
    BuyerProfile,
    ProjectPaths,
    ScoringWeights,
    TierThresholds,
)

# Domain
from .domain import (
    Address,
    EnrichmentData,
    Orientation,
    Property,
    RenovationEstimate,
    RiskAssessment,
    RiskLevel,
    Score,
    ScoreBreakdown,
    SewerType,
    SolarStatus,
    Tier,
)

# Pipeline
from .pipeline import AnalysisPipeline, PipelineResult

# Repositories
from .repositories import (
    CsvPropertyRepository,
    DataLoadError,
    DataSaveError,
    EnrichmentRepository,
    JsonEnrichmentRepository,
    PropertyRepository,
)

# Services - Kill Switch
from .services.kill_switch import (
    CitySewerKillSwitch,
    KillSwitch,
    KillSwitchFilter,
    LotSizeKillSwitch,
    MinBathroomsKillSwitch,
    MinBedroomsKillSwitch,
    MinGarageKillSwitch,
    NoHoaKillSwitch,
    NoNewBuildKillSwitch,
)

# Services - Scoring
from .services.scoring import (
    ALL_STRATEGIES,
    INTERIOR_STRATEGIES,
    LOCATION_STRATEGIES,
    SYSTEMS_STRATEGIES,
    AestheticsScorer,
    BackyardUtilityScorer,
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
    PropertyScorer,
    QuietnessScorer,
    RoofConditionScorer,
    SafetyScorer,
    SchoolDistrictScorer,
    ScoringStrategy,
    SupermarketScorer,
)

__version__ = "1.0.0"

__all__ = [
    # Config
    "AppConfig",
    "ArizonaContext",
    "BuyerProfile",
    "ProjectPaths",
    "ScoringWeights",
    "TierThresholds",
    # Domain - Entities
    "Property",
    "EnrichmentData",
    # Domain - Value Objects
    "Address",
    "Score",
    "RiskAssessment",
    "ScoreBreakdown",
    "RenovationEstimate",
    # Domain - Enums
    "RiskLevel",
    "Tier",
    "SolarStatus",
    "SewerType",
    "Orientation",
    # Repositories
    "PropertyRepository",
    "EnrichmentRepository",
    "DataLoadError",
    "DataSaveError",
    "CsvPropertyRepository",
    "JsonEnrichmentRepository",
    # Services - Kill Switch
    "KillSwitch",
    "KillSwitchFilter",
    "NoHoaKillSwitch",
    "CitySewerKillSwitch",
    "MinGarageKillSwitch",
    "MinBedroomsKillSwitch",
    "MinBathroomsKillSwitch",
    "LotSizeKillSwitch",
    "NoNewBuildKillSwitch",
    # Services - Scoring
    "PropertyScorer",
    "ScoringStrategy",
    "SchoolDistrictScorer",
    "QuietnessScorer",
    "SafetyScorer",
    "SupermarketScorer",
    "ParksWalkabilityScorer",
    "OrientationScorer",
    "RoofConditionScorer",
    "BackyardUtilityScorer",
    "PlumbingElectricalScorer",
    "PoolConditionScorer",
    "KitchenLayoutScorer",
    "MasterSuiteScorer",
    "NaturalLightScorer",
    "HighCeilingsScorer",
    "FireplaceScorer",
    "LaundryAreaScorer",
    "AestheticsScorer",
    "LOCATION_STRATEGIES",
    "SYSTEMS_STRATEGIES",
    "INTERIOR_STRATEGIES",
    "ALL_STRATEGIES",
    # Pipeline
    "AnalysisPipeline",
    "PipelineResult",
]
