"""Simplified demonstration of kill-switch verdict explanation system.

This script shows how to use the new explanation features to generate
human-readable verdict explanations for property evaluation.
"""

import sys

sys.path.insert(0, 'src')

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.domain.enums import SewerType
from phx_home_analysis.services.kill_switch import KillSwitchFilter


def create_property(street, hoa_fee=0, beds=4, baths=2.0, lot_sqft=8500, year_built=2010,
                    garage_spaces=2, sewer_type=SewerType.CITY):
    """Helper to create Property with standard defaults."""
    return Property(
        street=street,
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address=f"{street}, Phoenix, AZ 85001",
        price="$400,000",
        price_num=400000,
        beds=beds,
        baths=baths,
        sqft=2000,
        price_per_sqft_raw=200.0,
        lot_sqft=lot_sqft,
        year_built=year_built,
        hoa_fee=hoa_fee,
        garage_spaces=garage_spaces,
        sewer_type=sewer_type,
    )


def demo_pass_property():
    """Demo: Property that passes all criteria."""
    print("=" * 70)
    print("DEMO 1: Property PASSES all criteria")
    print("=" * 70)

    property = create_property("123 Perfect St")

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(property)

    print(f"\nVerdict: {verdict.value}")
    print(f"Severity: {severity}")
    print(f"Failures: {len(failures)}")
    print("\n" + explanation.to_text())


def demo_warning_property():
    """Demo: Property with warnings (soft failures below threshold)."""
    print("\n" + "=" * 70)
    print("DEMO 2: Property WARNING - soft failures approaching threshold")
    print("=" * 70)

    # lot_sqft=5000 (too small: severity 1.0) + year_built=2024 (new: severity 2.0)
    # Total: 3.0 (just at threshold - may be WARNING or FAIL depending on threshold)
    property = create_property("456 Almost St", lot_sqft=5000, year_built=2024)

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(property)

    print(f"\nVerdict: {verdict.value}")
    print(f"Severity: {severity}")
    print(f"Failures: {len(failures)}")
    print("\n" + explanation.to_text())


def demo_soft_fail_property():
    """Demo: Property fails due to soft severity threshold."""
    print("\n" + "=" * 70)
    print("DEMO 3: Property FAILS - soft severity exceeds threshold")
    print("=" * 70)

    # lot_sqft=5000 (too small: severity 1.0) + year_built=2024 (new: severity 2.0)
    # + garage_spaces=1 (only 1: severity 1.5) = 4.5 total (FAIL)
    property = create_property("789 Marginal St", lot_sqft=5000, year_built=2024, garage_spaces=1)

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(property)

    print(f"\nVerdict: {verdict.value}")
    print(f"Severity: {severity}")
    print(f"Failures: {len(failures)}")
    print("\n" + explanation.to_text())


def demo_hard_fail_property():
    """Demo: Property fails due to hard criterion (instant fail)."""
    print("\n" + "=" * 70)
    print("DEMO 4: Property FAILS - hard criterion violation (HOA)")
    print("=" * 70)

    property = create_property("999 Dealbreaker Ln", hoa_fee=250)

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(property)

    print(f"\nVerdict: {verdict.value}")
    print(f"Severity: {severity}")
    print(f"Failures: {len(failures)}")
    print("\n" + explanation.to_text())


def demo_multiple_hard_fails():
    """Demo: Property fails multiple hard criteria."""
    print("\n" + "=" * 70)
    print("DEMO 5: Property FAILS - multiple hard criteria violations")
    print("=" * 70)

    property = create_property("111 Nope Ave", hoa_fee=150, beds=3, baths=1.5,
                               garage_spaces=1, sewer_type=SewerType.SEPTIC)

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(property)

    print(f"\nVerdict: {verdict.value}")
    print(f"Severity: {severity}")
    print(f"Failures: {len(failures)}")
    print("\n" + explanation.to_text())


def demo_json_export():
    """Demo: Export explanation as JSON."""
    print("\n" + "=" * 70)
    print("DEMO 6: JSON export of verdict explanation")
    print("=" * 70)

    property = create_property("222 API Test Dr", lot_sqft=16000, year_built=2024)

    filter_service = KillSwitchFilter()
    verdict, severity, failures, explanation = filter_service.evaluate_with_explanation(property)

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
