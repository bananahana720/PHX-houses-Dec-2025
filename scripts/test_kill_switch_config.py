"""Test script for kill switch YAML config loading.

Demonstrates the new KillSwitchFilter class with YAML configuration.
"""


# Requires: uv pip install -e .
from scripts.lib.kill_switch import KillSwitchFilter, KillSwitchVerdict


def main():
    """Test kill switch filter with default and custom configs."""
    print("=" * 80)
    print("Kill Switch Config Test")
    print("=" * 80)

    # Test 1: Default configuration (hardcoded)
    print("\n1. Testing with default configuration (hardcoded):")
    print("-" * 80)
    filter_default = KillSwitchFilter()
    print(filter_default.get_summary())

    # Test 2: YAML configuration
    print("\n\n2. Testing with YAML configuration:")
    print("-" * 80)
    filter_yaml = KillSwitchFilter(config_path='config/buyer_criteria.yaml')
    print(filter_yaml.get_summary())

    # Test 3: Evaluate sample properties
    print("\n\n3. Testing property evaluation:")
    print("-" * 80)

    # Sample property that passes all criteria
    property_pass = {
        'hoa_fee': 0,
        'beds': 4,
        'baths': 2.5,
        'sewer_type': 'city',
        'year_built': 2015,
        'garage_spaces': 2,
        'lot_sqft': 10000,
    }

    # Sample property with hard failure (HOA)
    property_hard_fail = {
        'hoa_fee': 100,
        'beds': 4,
        'baths': 2.5,
        'sewer_type': 'city',
        'year_built': 2015,
        'garage_spaces': 2,
        'lot_sqft': 10000,
    }

    # Sample property with soft failures (warning threshold)
    property_warning = {
        'hoa_fee': 0,
        'beds': 4,
        'baths': 2.5,
        'sewer_type': 'city',
        'year_built': 2015,
        'garage_spaces': 1,  # Fails garage (severity 1.5)
        'lot_sqft': 10000,
    }

    # Sample property with multiple soft failures (fail threshold)
    property_soft_fail = {
        'hoa_fee': 0,
        'beds': 4,
        'baths': 2.5,
        'sewer_type': 'septic',  # Fails sewer (severity 2.5)
        'year_built': 2015,
        'garage_spaces': 1,  # Fails garage (severity 1.5)
        'lot_sqft': 10000,
    }

    test_cases = [
        ("Property that passes all criteria", property_pass, KillSwitchVerdict.PASS),
        ("Property with hard failure (HOA)", property_hard_fail, KillSwitchVerdict.FAIL),
        ("Property with warning (garage only)", property_warning, KillSwitchVerdict.WARNING),
        ("Property with soft fail (sewer + garage)", property_soft_fail, KillSwitchVerdict.FAIL),
    ]

    for description, prop, expected_verdict in test_cases:
        print(f"\nTest: {description}")
        verdict, severity, failures, results = filter_yaml.evaluate(prop)
        print(f"  Verdict: {verdict.value}")
        print(f"  Severity: {severity}")
        print(f"  Expected: {expected_verdict.value}")
        print(f"  Match: {'✓' if verdict == expected_verdict else '✗'}")
        if failures:
            print("  Failures:")
            for failure in failures:
                print(f"    - {failure}")

    print("\n" + "=" * 80)
    print("Test complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
