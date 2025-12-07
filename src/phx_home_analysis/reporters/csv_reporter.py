"""CSV report generator for PHX Home Analysis.

Generates structured CSV files for data analysis and spreadsheet import.
"""

import csv
from pathlib import Path

from ..domain.entities import Property
from ..domain.enums import Tier
from .base import Reporter


class CsvReporter(Reporter):
    """Generate CSV reports from property analysis results.

    Produces CSV files with configurable columns for spreadsheet analysis.
    Supports both compact and detailed output formats.
    """

    DEFAULT_COLUMNS = [
        "rank",
        "full_address",
        "city",
        "price",
        "price_num",
        "beds",
        "baths",
        "sqft",
        "price_per_sqft",
        "kill_switch_passed",
        "tier",
        "total_score",
        "score_location",
        "score_systems",
        "score_interior",
    ]

    EXTENDED_COLUMNS = DEFAULT_COLUMNS + [
        "lot_sqft",
        "year_built",
        "garage_spaces",
        "sewer_type",
        "hoa_fee",
        "commute_minutes",
        "school_rating",
        "orientation",
        "distance_to_grocery_miles",
        "distance_to_highway_miles",
        "solar_status",
        "has_pool",
        "roof_age",
        "hvac_age",
    ]

    def __init__(
        self,
        columns: list[str] | None = None,
        include_extended: bool = False,
    ) -> None:
        """Initialize CSV reporter.

        Args:
            columns: List of column names to include. If None, uses DEFAULT_COLUMNS.
            include_extended: If True and columns is None, uses EXTENDED_COLUMNS.
        """
        if columns is not None:
            self.columns = columns
        elif include_extended:
            self.columns = self.EXTENDED_COLUMNS
        else:
            self.columns = self.DEFAULT_COLUMNS

    def generate(self, properties: list[Property], output_path: Path) -> None:
        """Generate CSV report from properties.

        Args:
            properties: List of Property entities to export
            output_path: Output CSV file path

        Raises:
            ValueError: If properties list is empty
        """
        if not properties:
            raise ValueError("Cannot generate CSV from empty properties list")

        # Sort by tier and score (best first)
        sorted_properties = sorted(
            properties,
            key=lambda p: (
                0 if p.tier == Tier.UNICORN else (1 if p.tier == Tier.CONTENDER else 2),
                -p.total_score,
            ),
        )

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()

            for rank, prop in enumerate(sorted_properties, start=1):
                row = self._property_to_row(prop, rank)
                writer.writerow(row)

    def _property_to_row(self, prop: Property, rank: int) -> dict:
        """Convert Property entity to CSV row dictionary.

        Args:
            prop: Property entity
            rank: Property rank (1-indexed)

        Returns:
            Dictionary mapping column names to values
        """
        # Build row with all possible fields
        row_data = {
            "rank": rank,
            "full_address": prop.full_address,
            "city": prop.city,
            "state": prop.state,
            "zip_code": prop.zip_code,
            "price": prop.price,
            "price_num": prop.price_num,
            "beds": prop.beds,
            "baths": prop.baths,
            "sqft": prop.sqft,
            "price_per_sqft": f"{prop.price_per_sqft:.2f}",
            "kill_switch_passed": "PASS" if prop.kill_switch_passed else "FAIL",
            "tier": prop.tier.label if prop.tier else "",
            "total_score": f"{prop.total_score:.1f}" if prop.score_breakdown else "",
            "score_location": (
                f"{prop.score_breakdown.location_total:.1f}" if prop.score_breakdown else ""
            ),
            "score_systems": (
                f"{prop.score_breakdown.systems_total:.1f}" if prop.score_breakdown else ""
            ),
            "score_interior": (
                f"{prop.score_breakdown.interior_total:.1f}" if prop.score_breakdown else ""
            ),
            # Extended fields
            "lot_sqft": prop.lot_sqft if prop.lot_sqft else "",
            "year_built": prop.year_built if prop.year_built else "",
            "garage_spaces": prop.garage_spaces if prop.garage_spaces else "",
            "sewer_type": prop.sewer_type.value if prop.sewer_type else "",
            "tax_annual": prop.tax_annual if prop.tax_annual else "",
            "hoa_fee": prop.hoa_fee if prop.hoa_fee is not None else "",
            "commute_minutes": prop.commute_minutes if prop.commute_minutes else "",
            "school_district": prop.school_district if prop.school_district else "",
            "school_rating": (f"{prop.school_rating:.1f}" if prop.school_rating else ""),
            "orientation": prop.orientation.value if prop.orientation else "",
            "distance_to_grocery_miles": (
                f"{prop.distance_to_grocery_miles:.1f}" if prop.distance_to_grocery_miles else ""
            ),
            "distance_to_highway_miles": (
                f"{prop.distance_to_highway_miles:.1f}" if prop.distance_to_highway_miles else ""
            ),
            "solar_status": prop.solar_status.value if prop.solar_status else "",
            "solar_lease_monthly": (prop.solar_lease_monthly if prop.solar_lease_monthly else ""),
            "has_pool": "Yes" if prop.has_pool else "No",
            "pool_equipment_age": (prop.pool_equipment_age if prop.pool_equipment_age else ""),
            "roof_age": prop.roof_age if prop.roof_age else "",
            "hvac_age": prop.hvac_age if prop.hvac_age else "",
        }

        # Return only requested columns
        return {col: row_data.get(col, "") for col in self.columns}


class RiskCsvReporter(Reporter):
    """Generate risk assessment CSV report.

    Specialized CSV reporter for risk analysis data with risk levels
    and descriptions across all categories.
    """

    def generate(self, properties: list[Property], output_path: Path) -> None:
        """Generate risk assessment CSV.

        Args:
            properties: List of Property entities with risk_assessments populated
            output_path: Output CSV file path

        Raises:
            ValueError: If properties list is empty
        """
        if not properties:
            raise ValueError("Cannot generate risk CSV from empty properties list")

        fieldnames = [
            "full_address",
            "price",
            "noise_risk",
            "noise_desc",
            "infrastructure_risk",
            "infrastructure_desc",
            "solar_risk",
            "solar_desc",
            "cooling_risk",
            "cooling_desc",
            "school_risk",
            "school_desc",
            "lot_risk",
            "lot_desc",
            "overall_risk_score",
        ]

        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for prop in properties:
                row = self._property_to_risk_row(prop)
                writer.writerow(row)

    def _property_to_risk_row(self, prop: Property) -> dict:
        """Convert Property to risk assessment CSV row.

        Args:
            prop: Property entity with risk_assessments

        Returns:
            Dictionary mapping risk columns to values
        """
        # Create lookup by category
        risk_lookup = {r.category: r for r in prop.risk_assessments}

        # Calculate overall risk score
        overall_score = sum(
            3 if r.level.value == "high" else (1 if r.level.value in ["medium", "unknown"] else 0)
            for r in prop.risk_assessments
        )

        return {
            "full_address": prop.full_address,
            "price": prop.price,
            "noise_risk": (
                risk_lookup["Noise"].level.value.upper() if "Noise" in risk_lookup else ""
            ),
            "noise_desc": (risk_lookup["Noise"].description if "Noise" in risk_lookup else ""),
            "infrastructure_risk": (
                risk_lookup["Infrastructure"].level.value.upper()
                if "Infrastructure" in risk_lookup
                else ""
            ),
            "infrastructure_desc": (
                risk_lookup["Infrastructure"].description if "Infrastructure" in risk_lookup else ""
            ),
            "solar_risk": (
                risk_lookup["Solar"].level.value.upper() if "Solar" in risk_lookup else ""
            ),
            "solar_desc": (risk_lookup["Solar"].description if "Solar" in risk_lookup else ""),
            "cooling_risk": (
                risk_lookup["Cooling Cost"].level.value.upper()
                if "Cooling Cost" in risk_lookup
                else ""
            ),
            "cooling_desc": (
                risk_lookup["Cooling Cost"].description if "Cooling Cost" in risk_lookup else ""
            ),
            "school_risk": (
                risk_lookup["Schools"].level.value.upper() if "Schools" in risk_lookup else ""
            ),
            "school_desc": (risk_lookup["Schools"].description if "Schools" in risk_lookup else ""),
            "lot_risk": (
                risk_lookup["Lot Size"].level.value.upper() if "Lot Size" in risk_lookup else ""
            ),
            "lot_desc": (risk_lookup["Lot Size"].description if "Lot Size" in risk_lookup else ""),
            "overall_risk_score": overall_score,
        }
