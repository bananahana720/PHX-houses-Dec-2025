"""Demonstration of kill-switch verdict explanation system.

This script shows how to use the new explanation features to generate
human-readable verdict explanations for property evaluation.
"""

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.domain.enums import SewerType
from phx_home_analysis.services.kill_switch import KillSwitchFilter


def demo_pass_property():
    """Demo: Property that passes all criteria."""
    print("=" * 70)
    print("DEMO 1: Property PASSES all criteria")
    print("=" * 70)

    property = Property(
        street="123 Perfect St",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="123 Perfect St, Phoenix, AZ 85001",
        price="$400,000",
        price_num=400000,
        beds=4,
        baths=2.5,
        sqft=2000,
        price_per_sqft_raw=200.0,
        lot_sqft=8500,
        year_built=2010,
        hoa_fee=0,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
    )

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(
        property
    )

    print(f"\nVerdict: {verdict.value}")
    print(f"Severity: {severity}")
    print(f"Failures: {len(failures)}")
    print("\n" + explanation.to_text())


def demo_warning_property():
    """Demo: Property with warnings (soft failures below threshold)."""
    print("\n" + "=" * 70)
    print("DEMO 2: Property WARNING - soft failures approaching threshold")
    print("=" * 70)

    property = Property(
        address="456 Almost St, Phoenix, AZ 85002",
        city="Phoenix",
        state="AZ",
        zipcode="85002",
        price=350000,
        beds=4,
        baths=2.0,
        sqft=1800,
        lot_sqft=5000,  # Too small (fail: severity 1.0)
        year_built=2024,  # New build (fail: severity 2.0)
        hoa_fee=0,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
    )
    # Total severity: 1.0 + 2.0 = 3.0 (should be WARNING just under threshold)

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(
        property
    )

    print(f"\nVerdict: {verdict.value}")
    print(f"Severity: {severity}")
    print(f"Failures: {len(failures)}")
    print("\n" + explanation.to_text())


def demo_soft_fail_property():
    """Demo: Property fails due to soft severity threshold."""
    print("\n" + "=" * 70)
    print("DEMO 3: Property FAILS - soft severity exceeds threshold")
    print("=" * 70)

    property = Property(
        address="789 Marginal St, Phoenix, AZ 85003",
        city="Phoenix",
        state="AZ",
        zipcode="85003",
        price=320000,
        beds=4,
        baths=2.0,
        sqft=1700,
        lot_sqft=5000,  # Too small (fail: severity 1.0)
        year_built=2024,  # New build (fail: severity 2.0)
        hoa_fee=0,
        garage_spaces=1,  # Only 1 car (fail: severity 1.5)
        sewer_type=SewerType.CITY,
    )
    # Total severity: 1.0 + 2.0 + 1.5 = 4.5 (FAIL threshold exceeded)

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(
        property
    )

    print(f"\nVerdict: {verdict.value}")
    print(f"Severity: {severity}")
    print(f"Failures: {len(failures)}")
    print("\n" + explanation.to_text())


def demo_hard_fail_property():
    """Demo: Property fails due to hard criterion (instant fail)."""
    print("\n" + "=" * 70)
    print("DEMO 4: Property FAILS - hard criterion violation (HOA)")
    print("=" * 70)

    property = Property(
        address="999 Dealbreaker Ln, Phoenix, AZ 85004",
        city="Phoenix",
        state="AZ",
        zipcode="85004",
        price=380000,
        beds=4,
        baths=2.5,
        sqft=2100,
        lot_sqft=9000,
        year_built=2015,
        hoa_fee=250,  # HOA fee (HARD FAIL)
        garage_spaces=2,
        sewer_type=SewerType.CITY,
    )

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(
        property
    )

    print(f"\nVerdict: {verdict.value}")
    print(f"Severity: {severity}")
    print(f"Failures: {len(failures)}")
    print("\n" + explanation.to_text())


def demo_multiple_hard_fails():
    """Demo: Property fails multiple hard criteria."""
    print("\n" + "=" * 70)
    print("DEMO 5: Property FAILS - multiple hard criteria violations")
    print("=" * 70)

    property = Property(
        address="111 Nope Ave, Phoenix, AZ 85005",
        city="Phoenix",
        state="AZ",
        zipcode="85005",
        price=280000,
        beds=3,  # Too few bedrooms (HARD FAIL)
        baths=1.5,  # Too few bathrooms (HARD FAIL)
        sqft=1400,
        lot_sqft=6000,
        year_built=2018,
        hoa_fee=150,  # HOA fee (HARD FAIL)
        garage_spaces=1,
        sewer_type=SewerType.SEPTIC,
    )

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(
        property
    )

    print(f"\nVerdict: {verdict.value}")
    print(f"Severity: {severity}")
    print(f"Failures: {len(failures)}")
    print("\n" + explanation.to_text())


def demo_json_export():
    """Demo: Export explanation as JSON."""
    print("\n" + "=" * 70)
    print("DEMO 6: JSON export of verdict explanation")
    print("=" * 70)

    property = Property(
        address="222 API Test Dr, Phoenix, AZ 85006",
        city="Phoenix",
        state="AZ",
        zipcode="85006",
        price=360000,
        beds=4,
        baths=2.0,
        sqft=1900,
        lot_sqft=16000,  # Too large (fail: severity 1.0)
        year_built=2024,  # New build (fail: severity 2.0)
        hoa_fee=0,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
    )

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(
        property
    )

    print(f"\nVerdict: {verdict.value}")
    print("\nJSON Export:")
    import json

    print(json.dumps(explanation.to_dict(), indent=2))


if __name__ == "__main__":
    demo_pass_property()
    demo_warning_property()
    demo_soft_fail_property()
    demo_hard_fail_property()
    demo_multiple_hard_fails()
    demo_json_export()

    print("\n" + "=" * 70)
    print("All demonstrations complete!")
    print("=" * 70)
