#!/usr/bin/env python3
"""Demonstration script for the Reporter layer.

Shows how to use HtmlReportGenerator, CsvReporter, and ConsoleReporter
with sample property data.
"""

from pathlib import Path

# Requires: uv pip install -e .
from phx_home_analysis.domain.entities import Property
from phx_home_analysis.domain.enums import Orientation, RiskLevel, SewerType, SolarStatus, Tier
from phx_home_analysis.domain.value_objects import (
    RenovationEstimate,
    RiskAssessment,
    Score,
    ScoreBreakdown,
)
from phx_home_analysis.reporters import (
    ConsoleReporter,
    CsvReporter,
    HtmlReportGenerator,
    RiskCsvReporter,
)


def create_sample_properties():
    """Create sample properties for demonstration."""

    # Unicorn property
    prop1 = Property(
        street="123 Unicorn Lane",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="123 Unicorn Lane, Phoenix, AZ 85001",
        price="$475,000",
        price_num=475000,
        beds=4,
        baths=2.5,
        sqft=2400,
        price_per_sqft_raw=197.92,
        lot_sqft=9000,
        year_built=2010,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        hoa_fee=0,
        school_rating=8.5,
        orientation=Orientation.N,
        solar_status=SolarStatus.OWNED,
        has_pool=True,
        roof_age=5,
        hvac_age=8,
        kill_switch_passed=True,
        tier=Tier.UNICORN,
        score_breakdown=ScoreBreakdown(
            location_scores=[
                Score("School District", 8.5, 50),
                Score("Quietness", 8.0, 50),
                Score("Sun Orientation", 10.0, 30),
            ],
            systems_scores=[
                Score("Roof Condition", 7.0, 50),
                Score("HVAC", 6.0, 40),
            ],
            interior_scores=[
                Score("Kitchen Layout", 9.0, 40),
                Score("Master Suite", 8.5, 40),
            ],
        ),
        risk_assessments=[
            RiskAssessment("Noise", RiskLevel.LOW, "Quiet location"),
            RiskAssessment("Infrastructure", RiskLevel.LOW, "Modern construction"),
            RiskAssessment("Solar", RiskLevel.POSITIVE, "Owned solar - value add"),
            RiskAssessment("Cooling Cost", RiskLevel.LOW, "North-facing - best orientation"),
            RiskAssessment("Schools", RiskLevel.LOW, "Strong school district"),
            RiskAssessment("Lot Size", RiskLevel.LOW, "Comfortable lot size"),
        ],
        renovation_estimate=RenovationEstimate(
            roof=5000,
            hvac=3000,
            pool=0,
            other=2000,
        ),
    )

    # Contender property
    prop2 = Property(
        street="456 Contender Ave",
        city="Scottsdale",
        state="AZ",
        zip_code="85250",
        full_address="456 Contender Ave, Scottsdale, AZ 85250",
        price="$525,000",
        price_num=525000,
        beds=4,
        baths=3.0,
        sqft=2600,
        price_per_sqft_raw=201.92,
        lot_sqft=8500,
        year_built=2005,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        hoa_fee=0,
        school_rating=7.0,
        orientation=Orientation.E,
        solar_status=SolarStatus.NONE,
        has_pool=False,
        roof_age=12,
        hvac_age=10,
        kill_switch_passed=True,
        tier=Tier.CONTENDER,
        score_breakdown=ScoreBreakdown(
            location_scores=[
                Score("School District", 7.0, 50),
                Score("Quietness", 6.0, 50),
            ],
            systems_scores=[
                Score("Roof Condition", 5.0, 50),
                Score("HVAC", 5.0, 40),
            ],
            interior_scores=[
                Score("Kitchen Layout", 7.0, 40),
                Score("Master Suite", 7.5, 40),
            ],
        ),
        risk_assessments=[
            RiskAssessment("Noise", RiskLevel.MEDIUM, "Some highway noise possible"),
            RiskAssessment("Infrastructure", RiskLevel.LOW, "Modern construction"),
            RiskAssessment("Solar", RiskLevel.LOW, "No solar complications"),
            RiskAssessment("Cooling Cost", RiskLevel.LOW, "East-facing - good"),
            RiskAssessment("Schools", RiskLevel.MEDIUM, "Average schools"),
            RiskAssessment("Lot Size", RiskLevel.LOW, "Comfortable lot size"),
        ],
        renovation_estimate=RenovationEstimate(
            roof=10000,
            hvac=8000,
            pool=0,
            other=5000,
        ),
    )

    # Pass tier property
    prop3 = Property(
        street="789 Pass Blvd",
        city="Tempe",
        state="AZ",
        zip_code="85281",
        full_address="789 Pass Blvd, Tempe, AZ 85281",
        price="$450,000",
        price_num=450000,
        beds=4,
        baths=2.0,
        sqft=2200,
        price_per_sqft_raw=204.55,
        lot_sqft=7500,
        year_built=2000,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        hoa_fee=0,
        school_rating=6.5,
        orientation=Orientation.S,
        solar_status=SolarStatus.NONE,
        has_pool=True,
        roof_age=15,
        hvac_age=12,
        kill_switch_passed=True,
        tier=Tier.PASS,
        score_breakdown=ScoreBreakdown(
            location_scores=[
                Score("School District", 6.5, 50),
                Score("Quietness", 5.0, 50),
            ],
            systems_scores=[
                Score("Roof Condition", 4.0, 50),
                Score("HVAC", 4.5, 40),
            ],
            interior_scores=[
                Score("Kitchen Layout", 6.0, 40),
                Score("Master Suite", 6.5, 40),
            ],
        ),
        risk_assessments=[
            RiskAssessment("Noise", RiskLevel.MEDIUM, "Moderate traffic noise"),
            RiskAssessment("Infrastructure", RiskLevel.LOW, "Modern construction"),
            RiskAssessment("Solar", RiskLevel.LOW, "No solar complications"),
            RiskAssessment("Cooling Cost", RiskLevel.MEDIUM, "South-facing - moderate"),
            RiskAssessment("Schools", RiskLevel.MEDIUM, "Average schools"),
            RiskAssessment("Lot Size", RiskLevel.MEDIUM, "Near minimum requirement"),
        ],
        renovation_estimate=RenovationEstimate(
            roof=15000,
            hvac=8000,
            pool=5000,
            other=3000,
        ),
    )

    return [prop1, prop2, prop3]


def main():
    """Demonstrate all reporter types."""
    print("=" * 80)
    print("Reporter Layer Demonstration")
    print("=" * 80)
    print()

    # Create sample data
    print("Creating sample properties...")
    properties = create_sample_properties()
    print(f"Created {len(properties)} sample properties")
    print()

    # Output directory
    output_dir = Path(__file__).parent.parent / "reports" / "demo"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Console Reporter
    print("-" * 80)
    print("1. CONSOLE REPORTER")
    print("-" * 80)
    console_reporter = ConsoleReporter(use_color=True)
    console_reporter.print_summary(properties)
    print()

    # 2. CSV Reporter
    print("-" * 80)
    print("2. CSV REPORTER")
    print("-" * 80)
    csv_path = output_dir / "properties.csv"
    csv_reporter = CsvReporter(include_extended=True)
    csv_reporter.generate(properties, csv_path)
    print(f"Generated CSV report: {csv_path}")
    print()

    # 3. Risk CSV Reporter
    print("-" * 80)
    print("3. RISK CSV REPORTER")
    print("-" * 80)
    risk_csv_path = output_dir / "risk_assessment.csv"
    risk_csv_reporter = RiskCsvReporter()
    risk_csv_reporter.generate(properties, risk_csv_path)
    print(f"Generated risk CSV: {risk_csv_path}")
    print()

    # 4. HTML Risk Report
    print("-" * 80)
    print("4. HTML RISK REPORT")
    print("-" * 80)
    risk_html_path = output_dir / "risk_report.html"
    html_reporter = HtmlReportGenerator()
    html_reporter.generate_risk_report(properties, risk_html_path)
    print(f"Generated risk report: {risk_html_path}")
    print()

    # 5. HTML Renovation Report
    print("-" * 80)
    print("5. HTML RENOVATION REPORT")
    print("-" * 80)
    renovation_html_path = output_dir / "renovation_report.html"
    html_reporter.generate_renovation_report(properties, renovation_html_path)
    print(f"Generated renovation report: {renovation_html_path}")
    print()

    # Summary
    print("=" * 80)
    print("DEMONSTRATION COMPLETE")
    print("=" * 80)
    print(f"\nAll reports generated in: {output_dir}")
    print("\nGenerated files:")
    print(f"  - {csv_path.name}")
    print(f"  - {risk_csv_path.name}")
    print(f"  - {risk_html_path.name}")
    print(f"  - {renovation_html_path.name}")
    print("\nOpen the HTML files in a browser to view interactive reports.")
    print()


if __name__ == "__main__":
    main()
