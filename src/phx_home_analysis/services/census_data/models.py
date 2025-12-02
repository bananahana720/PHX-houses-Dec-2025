"""Data models for Census ACS demographic data extraction."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DemographicData:
    """Census American Community Survey demographic data for a census tract.

    Contains key economic indicators from ACS 5-Year estimates.
    """

    census_tract: str  # 11-digit FIPS code (state + county + tract)
    median_household_income: int | None = None
    median_home_value: int | None = None
    total_population: int | None = None

    # Geographic identifiers
    state_fips: str | None = None
    county_fips: str | None = None
    tract_code: str | None = None

    # Metadata
    source: str = "census_acs5"
    survey_year: int = 2022  # Default to most recent 5-year estimates
    extracted_at: datetime = field(default_factory=datetime.utcnow)

    # Geocoding (original coordinates used for lookup)
    latitude: float | None = None
    longitude: float | None = None

    def to_enrichment_dict(self) -> dict:
        """Convert to enrichment data format for JSON serialization.

        Returns:
            Dictionary compatible with enrichment_data.json structure
        """
        return {
            "census_tract": self.census_tract,
            "median_household_income": self.median_household_income,
            "median_home_value": self.median_home_value,
            "census_total_population": self.total_population,
        }

    @property
    def income_tier(self) -> str:
        """Classify income tier based on median household income.

        Returns:
            Tier string: 'high', 'upper_middle', 'middle', 'lower_middle', 'low', or 'unknown'
        """
        if self.median_household_income is None:
            return "unknown"

        if self.median_household_income >= 125000:
            return "high"
        elif self.median_household_income >= 90000:
            return "upper_middle"
        elif self.median_household_income >= 60000:
            return "middle"
        elif self.median_household_income >= 40000:
            return "lower_middle"
        else:
            return "low"

    @property
    def description(self) -> str:
        """Get human-readable demographic description.

        Returns:
            Description of tract demographics
        """
        income_str = f"${self.median_household_income:,}" if self.median_household_income else "N/A"
        value_str = f"${self.median_home_value:,}" if self.median_home_value else "N/A"
        pop_str = f"{self.total_population:,}" if self.total_population else "N/A"

        return (
            f"Census Tract {self.census_tract}: "
            f"Median Income {income_str}, "
            f"Median Home Value {value_str}, "
            f"Population {pop_str}"
        )
