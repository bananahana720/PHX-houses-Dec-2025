"""Verification test for Property and EnrichmentData field alignment."""

from src.phx_home_analysis.domain.entities import EnrichmentData, Property


def test_field_alignment():
    """Verify Property has all EnrichmentData fields."""
    # Get field sets
    enrichment_fields = set(EnrichmentData.__dataclass_fields__.keys())
    property_fields = set(Property.__dataclass_fields__.keys())

    # Calculate differences
    missing_in_property = enrichment_fields - property_fields
    extra_in_property = property_fields - enrichment_fields

    # Display results
    print("=" * 70)
    print("PROPERTY vs ENRICHMENTDATA FIELD ALIGNMENT TEST")
    print("=" * 70)
    print()
    print(f"EnrichmentData fields: {len(enrichment_fields)}")
    print(f"Property fields: {len(property_fields)}")
    print()

    if missing_in_property:
        print(f"❌ MISSING in Property ({len(missing_in_property)} fields):")
        for field in sorted(missing_in_property):
            print(f"   - {field}")
        print()
    else:
        print("✅ Property has ALL EnrichmentData fields")
        print()

    if extra_in_property:
        print(f"ℹ️  EXTRA in Property ({len(extra_in_property)} fields):")
        print("   (These are expected - Property has additional domain fields)")
        for field in sorted(extra_in_property):
            print(f"   - {field}")
        print()

    # Final verdict
    print("=" * 70)
    if len(missing_in_property) == 0:
        print("✅ PASS - Property entity is complete")
        print()
        print("All EnrichmentData fields are present in Property.")
        print("The Property class can now accept all Phase 0-4 enrichment data.")
    else:
        print("❌ FAIL - Property entity is missing fields")
        print()
        print(f"Add {len(missing_in_property)} missing fields to Property class.")
    print("=" * 70)

    return len(missing_in_property) == 0


if __name__ == "__main__":
    success = test_field_alignment()
    exit(0 if success else 1)
