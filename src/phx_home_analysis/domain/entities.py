"""Domain entities for PHX Home Analysis.

This module defines the core Property entity with rich business logic,
computed properties, and analysis results.
"""

from dataclasses import dataclass, field

from .enums import CrimeRiskLevel, FloodZone, Orientation, SewerType, SolarStatus, Tier
from .value_objects import Address, RenovationEstimate, RiskAssessment, ScoreBreakdown


@dataclass
class Property:
    """Real estate property entity with complete analysis data.

    Represents a property listing with all data from CSV, enrichment sources,
    and computed analysis results including scoring and risk assessment.

    Note: Not frozen to allow mutation during pipeline processing.
    """

    # Address fields
    street: str
    city: str
    state: str
    zip_code: str
    full_address: str

    # Basic listing data (from CSV)
    price: str  # Formatted string like "$475,000"
    price_num: int | None  # None if unable to parse
    beds: int
    baths: float
    sqft: int
    price_per_sqft_raw: float  # From CSV calculation

    # County assessor data (from enrichment)
    lot_sqft: int | None = None
    year_built: int | None = None
    garage_spaces: int | None = None
    sewer_type: SewerType | None = None
    tax_annual: float | None = None  # Annual property tax (can have decimals)

    # HOA and location data (from enrichment)
    hoa_fee: float | None = None  # 0 = no HOA, number = monthly fee (float for precision)
    commute_minutes: int | None = None
    school_district: str | None = None
    school_rating: float | None = None  # GreatSchools 1-10 scale
    orientation: Orientation | None = None
    distance_to_grocery_miles: float | None = None
    distance_to_highway_miles: float | None = None

    # Arizona-specific features (from enrichment)
    solar_status: SolarStatus | None = None
    solar_lease_monthly: int | None = None
    has_pool: bool | None = None
    pool_equipment_age: int | None = None
    roof_age: int | None = None
    hvac_age: int | None = None

    # Geocoding data (from geocoding service)
    latitude: float | None = None
    longitude: float | None = None

    # Analysis results (populated by pipeline)
    kill_switch_passed: bool = False
    kill_switch_failures: list[str] = field(default_factory=list)
    score_breakdown: ScoreBreakdown | None = None
    tier: Tier | None = None
    risk_assessments: list[RiskAssessment] = field(default_factory=list)
    renovation_estimate: RenovationEstimate | None = None

    # Manual assessment fields (visual inspection from photos)
    kitchen_layout_score: float | None = None  # 0-10 scale
    master_suite_score: float | None = None  # 0-10 scale
    natural_light_score: float | None = None  # 0-10 scale
    high_ceilings_score: float | None = None  # 0-10 scale
    fireplace_present: bool | None = None
    laundry_area_score: float | None = None  # 0-10 scale
    aesthetics_score: float | None = None  # 0-10 scale
    backyard_utility_score: float | None = None  # 0-10 scale
    safety_neighborhood_score: float | None = None  # 0-10 scale
    parks_walkability_score: float | None = None  # 0-10 scale

    # Location - Crime/Safety
    violent_crime_index: float | None = None  # 0-100, 100=safest
    property_crime_index: float | None = None  # 0-100, 100=safest
    crime_risk_level: CrimeRiskLevel = CrimeRiskLevel.UNKNOWN

    # Location - Flood Zone
    flood_zone: FloodZone = FloodZone.UNKNOWN
    flood_zone_panel: str | None = None
    flood_insurance_required: bool | None = None

    # Location - Walk/Transit/Bike Scores
    walk_score: int | None = None  # 0-100
    transit_score: int | None = None  # 0-100
    bike_score: int | None = None  # 0-100

    # Location - Noise
    noise_score: int | None = None  # 0-100, 100=quietest
    noise_sources: list[str] | None = field(default=None)

    # Location - Zoning
    zoning_code: str | None = None
    zoning_description: str | None = None
    zoning_category: str | None = None  # residential, commercial, industrial, mixed

    # Demographics
    census_tract: str | None = None
    median_household_income: int | None = None
    median_home_value: int | None = None

    # Schools - Enhanced
    elementary_rating: float | None = None  # 1-10
    middle_rating: float | None = None  # 1-10
    high_rating: float | None = None  # 1-10
    school_count_1mi: int | None = None

    def __post_init__(self) -> None:
        """Validate and normalize data after initialization."""
        # Ensure full_address is set
        if not self.full_address:
            self.full_address = f"{self.street}, {self.city}, {self.state} {self.zip_code}"

        # Normalize enum values if passed as strings
        if self.sewer_type and isinstance(self.sewer_type, str):
            try:
                self.sewer_type = SewerType(self.sewer_type.lower())
            except ValueError:
                self.sewer_type = SewerType.UNKNOWN

        if self.solar_status and isinstance(self.solar_status, str):
            try:
                self.solar_status = SolarStatus(self.solar_status.lower())
            except ValueError:
                self.solar_status = SolarStatus.UNKNOWN

        if self.orientation and isinstance(self.orientation, str):
            self.orientation = Orientation.from_string(self.orientation)

        if self.tier and isinstance(self.tier, str):
            self.tier = Tier(self.tier.lower())

    # Computed properties - Address

    @property
    def address(self) -> Address:
        """Address value object for this property.

        Returns:
            Address value object
        """
        return Address(
            street=self.street,
            city=self.city,
            state=self.state,
            zip_code=self.zip_code,
        )

    @property
    def short_address(self) -> str:
        """Short address format for display.

        Returns:
            Street and city only
        """
        return f"{self.street}, {self.city}"

    # Computed properties - Basic metrics

    @property
    def price_per_sqft(self) -> float:
        """Computed price per square foot.

        Returns:
            Price per sqft, or 0 if sqft is 0/None
        """
        if not self.sqft or self.sqft == 0:
            return 0.0
        return self.price_num / self.sqft

    @property
    def has_hoa(self) -> bool:
        """Whether property has HOA fees.

        Returns:
            True if hoa_fee > 0, False if 0 or None
        """
        return self.hoa_fee is not None and self.hoa_fee > 0

    @property
    def age_years(self) -> int | None:
        """Property age in years from year_built.

        Assumes current year is 2025 (Dec 2025 analysis).

        Returns:
            Age in years, or None if year_built unknown
        """
        if not self.year_built:
            return None
        return 2025 - self.year_built

    # Computed properties - Scoring

    @property
    def total_score(self) -> float:
        """Total weighted score across all sections.

        Returns:
            Total score (0-500 pts), or 0 if not yet scored
        """
        if not self.score_breakdown:
            return 0.0
        return self.score_breakdown.total_score

    @property
    def is_unicorn(self) -> bool:
        """Whether property is classified as Unicorn tier.

        Returns:
            True if tier is UNICORN
        """
        return self.tier == Tier.UNICORN

    @property
    def is_contender(self) -> bool:
        """Whether property is classified as Contender tier.

        Returns:
            True if tier is CONTENDER
        """
        return self.tier == Tier.CONTENDER

    @property
    def is_failed(self) -> bool:
        """Whether property failed kill switches.

        Returns:
            True if tier is FAILED or kill_switch_passed is False
        """
        return self.tier == Tier.FAILED or not self.kill_switch_passed

    # Cached financial data (set by service layer, not computed in domain)
    # These fields are populated by MonthlyCostEstimator service externally
    _monthly_costs_cache: dict[str, float] | None = field(default=None, repr=False)

    @property
    def monthly_costs(self) -> dict[str, float]:
        """Cached monthly costs breakdown.

        NOTE: This returns cached data set by the service layer.
        Use MonthlyCostEstimator.estimate(property) to populate this cache
        or to get fresh cost estimates.

        Includes:
        - Mortgage payment (30-year, $50k down, 7% rate estimate)
        - Property tax
        - HOA fee
        - Solar lease (if applicable)
        - Pool maintenance estimate (if pool present)

        Returns:
            Dict mapping cost category to monthly amount, or empty dict if not cached
        """
        if self._monthly_costs_cache is None:
            # Return empty dict - caller should use MonthlyCostEstimator service
            return {}
        return self._monthly_costs_cache

    def set_monthly_costs(self, costs: dict[str, float]) -> None:
        """Set cached monthly costs (called by service layer).

        Args:
            costs: Dict mapping cost category to monthly amount
        """
        self._monthly_costs_cache = costs

    @property
    def total_monthly_cost(self) -> float:
        """Total estimated monthly cost.

        Returns:
            Sum of all monthly costs, or 0 if not cached
        """
        if not self._monthly_costs_cache:
            return 0.0
        return sum(self._monthly_costs_cache.values())

    @property
    def effective_price(self) -> float:
        """Effective price including renovation estimates.

        Returns:
            Purchase price + total renovation costs
        """
        if not self.renovation_estimate:
            return float(self.price_num)
        return float(self.price_num) + self.renovation_estimate.total

    # Computed properties - Risk analysis

    @property
    def high_risks(self) -> list[RiskAssessment]:
        """List of high-risk items requiring attention.

        Returns:
            RiskAssessment objects with HIGH risk level
        """
        return [r for r in self.risk_assessments if r.is_high_risk]

    @property
    def risk_count_by_level(self) -> dict[str, int]:
        """Count of risks by level.

        Returns:
            Dict mapping risk level name to count
        """
        from collections import Counter

        levels = [r.level.value for r in self.risk_assessments]
        return dict(Counter(levels))

    # String representation

    def __str__(self) -> str:
        """String representation shows address and key stats."""
        tier_str = self.tier.label if self.tier else "Unscored"
        return (
            f"{self.full_address} | "
            f"{self.beds}bd/{self.baths}ba | "
            f"{self.sqft} sqft | "
            f"{self.price} | "
            f"{tier_str}"
        )

    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return (
            f"Property(address='{self.full_address}', "
            f"price={self.price_num}, "
            f"beds={self.beds}, "
            f"baths={self.baths}, "
            f"sqft={self.sqft}, "
            f"tier={self.tier})"
        )


@dataclass
class EnrichmentData:
    """Enrichment data for a property from external research.

    This is a data transfer object used to load enrichment from JSON
    and merge into Property entities.
    """

    full_address: str

    # County assessor data
    lot_sqft: int | None = None
    year_built: int | None = None
    garage_spaces: int | None = None
    sewer_type: str | None = None
    tax_annual: float | None = None  # Annual property tax (float for precision)

    # HOA and location data
    hoa_fee: float | None = None  # Monthly HOA fee (float for precision)
    commute_minutes: int | None = None
    school_district: str | None = None
    school_rating: float | None = None
    orientation: str | None = None
    distance_to_grocery_miles: float | None = None
    distance_to_highway_miles: float | None = None

    # Arizona-specific features
    solar_status: str | None = None
    solar_lease_monthly: int | None = None
    has_pool: bool | None = None
    pool_equipment_age: int | None = None
    roof_age: int | None = None
    hvac_age: int | None = None

    # Manual assessment fields (visual inspection)
    kitchen_layout_score: float | None = None
    master_suite_score: float | None = None
    natural_light_score: float | None = None
    high_ceilings_score: float | None = None
    fireplace_present: bool | None = None
    laundry_area_score: float | None = None
    aesthetics_score: float | None = None
    backyard_utility_score: float | None = None
    safety_neighborhood_score: float | None = None
    parks_walkability_score: float | None = None

    # Location - Crime/Safety
    violent_crime_index: float | None = None
    property_crime_index: float | None = None
    crime_risk_level: str | None = None

    # Location - Flood Zone
    flood_zone: str | None = None
    flood_zone_panel: str | None = None
    flood_insurance_required: bool | None = None

    # Location - Walk/Transit/Bike Scores
    walk_score: int | None = None
    transit_score: int | None = None
    bike_score: int | None = None

    # Location - Noise
    noise_score: int | None = None
    noise_sources: list[str] | None = None

    # Location - Zoning
    zoning_code: str | None = None
    zoning_description: str | None = None
    zoning_category: str | None = None

    # Demographics
    census_tract: str | None = None
    median_household_income: int | None = None
    median_home_value: int | None = None

    # Schools - Enhanced
    elementary_rating: float | None = None
    middle_rating: float | None = None
    high_rating: float | None = None
    school_count_1mi: int | None = None
