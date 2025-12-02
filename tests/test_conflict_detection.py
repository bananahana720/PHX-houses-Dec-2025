"""Test conflict detection logic for county data extraction.

This script tests the EnrichmentMergeService class that handles
should_update_field and merge_parcel logic without making actual API calls.
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the service and models
from phx_home_analysis.services.county_data import ParcelData
from phx_home_analysis.services.enrichment import EnrichmentMergeService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Create a service instance for testing
# Note: A default LineageTracker is created internally to ensure lineage is always tracked
merge_service = EnrichmentMergeService()


def test_should_update_field():
    """Test the should_update_field method with various scenarios."""
    print("\n" + "=" * 60)
    print("Testing should_update_field()")
    print("=" * 60)

    # Test 1: Manual research should be preserved
    print("\n1. Manual research preservation:")
    entry = {"lot_sqft": 8000, "lot_sqft_source": "manual_research"}
    should_update, reason = merge_service.should_update_field(entry, "lot_sqft", 8500)
    assert not should_update, "Manual research should be preserved"
    assert "manual" in reason.lower(), "Reason should mention manual research"
    print(f"   Result: {should_update} - {reason}")

    # Test 2: Web research should be preserved
    print("\n2. Web research preservation:")
    entry = {"sewer_type": "city", "sewer_type_source": "web_research"}
    should_update, reason = merge_service.should_update_field(entry, "sewer_type", "septic")
    assert not should_update, "Web research should be preserved"
    print(f"   Result: {should_update} - {reason}")

    # Test 3: No existing value - should update
    print("\n3. No existing value:")
    entry = {}
    should_update, reason = merge_service.should_update_field(entry, "lot_sqft", 8000)
    assert should_update, "Should update when no existing value"
    assert reason == "No existing value"
    print(f"   Result: {should_update} - {reason}")

    # Test 4: Values match - no update needed
    print("\n4. Values match:")
    entry = {"year_built": 1980}
    should_update, reason = merge_service.should_update_field(entry, "year_built", 1980)
    assert not should_update, "Should not update when values match"
    assert reason == "Values match"
    print(f"   Result: {should_update} - {reason}")

    # Test 5: County override for non-manual data
    print("\n5. County override (non-manual):")
    entry = {"garage_spaces": 1, "garage_spaces_source": "listing"}
    should_update, reason = merge_service.should_update_field(entry, "garage_spaces", 2)
    assert should_update, "Should update non-manual data with county data"
    print(f"   Result: {should_update} - {reason}")

    # Test 6: County override when no source specified
    print("\n6. County override (no source):")
    entry = {"has_pool": False}
    should_update, reason = merge_service.should_update_field(entry, "has_pool", True)
    assert should_update, "Should update when no source specified"
    print(f"   Result: {should_update} - {reason}")

    print("\nAll should_update_field tests passed!")


def test_merge_parcel_into_enrichment():
    """Test the merge_parcel method of EnrichmentMergeService."""
    print("\n" + "=" * 60)
    print("Testing merge_parcel()")
    print("=" * 60)

    # Create a mock parcel data
    parcel = ParcelData(
        apn="123-45-678",
        full_address="4732 W Davis Rd, Glendale, AZ 85306",
        lot_sqft=8712,
        year_built=1973,
        garage_spaces=2,
        sewer_type="city",
        has_pool=True,
        tax_annual=1850,
    )

    # Test 1: New property (no existing data)
    print("\n1. New property (no existing data):")
    existing = {}
    result = merge_service.merge_parcel(existing, parcel.full_address, parcel, update_only=False)
    conflicts = result.to_legacy_dict()
    assert len(conflicts["new_fields"]) == 6, "Should add 6 new fields"
    assert len(conflicts["preserved_manual"]) == 0, "No manual fields to preserve"
    print(f"   New fields: {conflicts['new_fields']}")

    # Test 2: Existing property with manual research
    print("\n2. Existing property with manual research:")
    existing = {
        parcel.full_address: {
            "lot_sqft": 8000,
            "lot_sqft_source": "manual_research",
            "year_built": 1973,
            "garage_spaces": 2,
            "sewer_type": "city",
            "has_pool": True,
            "tax_annual": None,
        }
    }
    result = merge_service.merge_parcel(existing, parcel.full_address, parcel, update_only=False)
    entry = result.updated_entry
    conflicts = result.to_legacy_dict()
    assert entry["lot_sqft"] == 8000, "Manual lot_sqft should be preserved"
    assert len(conflicts["preserved_manual"]) == 1, "Should preserve 1 manual field"
    assert conflicts["preserved_manual"][0]["field"] == "lot_sqft"
    print(f"   Preserved: {entry['lot_sqft']} (manual)")
    print(f"   Conflicts: {conflicts}")

    # Test 3: Update-only mode
    print("\n3. Update-only mode (fill missing only):")
    existing = {
        parcel.full_address: {
            "lot_sqft": 8000,
            "year_built": 1973,
            "tax_annual": None,
        }
    }
    result = merge_service.merge_parcel(existing, parcel.full_address, parcel, update_only=True)
    entry = result.updated_entry
    conflicts = result.to_legacy_dict()
    assert entry["lot_sqft"] == 8000, "Existing lot_sqft should not be updated"
    assert entry["tax_annual"] == 1850, "Missing tax_annual should be filled"
    print(f"   lot_sqft: {entry['lot_sqft']} (unchanged)")
    print(f"   tax_annual: {entry['tax_annual']} (filled)")

    # Test 4: County override for non-manual data
    print("\n4. County override (non-manual conflict):")
    existing = {
        parcel.full_address: {
            "lot_sqft": 8000,
            "lot_sqft_source": "listing",
            "year_built": 1975,  # Different from county
            "garage_spaces": 1,  # Different from county
        }
    }
    result = merge_service.merge_parcel(existing, parcel.full_address, parcel, update_only=False)
    entry = result.updated_entry
    conflicts = result.to_legacy_dict()
    assert entry["lot_sqft"] == 8712, "County data should override listing data"
    assert entry["year_built"] == 1973, "County year_built should win"
    assert entry["garage_spaces"] == 2, "County garage_spaces should win"
    assert len(conflicts["updated"]) >= 2, "Should have updated conflicts"
    print(f"   lot_sqft: 8000 -> {entry['lot_sqft']} (county override)")
    print(f"   year_built: 1975 -> {entry['year_built']} (county override)")
    print(f"   Updated conflicts: {len(conflicts['updated'])}")

    print("\nAll merge_parcel tests passed!")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("County Data Conflict Detection Tests")
    print("=" * 60)

    try:
        test_should_update_field()
        test_merge_parcel_into_enrichment()

        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        return 0
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
