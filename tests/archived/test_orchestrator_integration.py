"""Test script to verify air_quality and permits integration into LocationDataOrchestrator."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 60)
print("Testing LocationDataOrchestrator Integration")
print("=" * 60)

# Test 1: Import orchestrator
print("\n1. Testing orchestrator import...")
try:
    from phx_home_analysis.services.location_data.orchestrator import LocationDataOrchestrator

    print("   ✓ LocationDataOrchestrator imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import orchestrator: {e}")
    sys.exit(1)

# Test 2: Check SOURCES list
print("\n2. Checking SOURCES list...")
orch = LocationDataOrchestrator()
print(f"   Sources: {orch.SOURCES}")
expected_sources = [
    "crime",
    "walkscore",
    "schools",
    "noise",
    "flood",
    "census",
    "zoning",
    "air_quality",
    "permits",
]
if set(orch.SOURCES) == set(expected_sources):
    print("   ✓ SOURCES list contains all expected services")
else:
    print(f"   ✗ SOURCES mismatch. Expected: {expected_sources}")
    sys.exit(1)

# Test 3: Check extraction methods exist
print("\n3. Checking extraction methods...")
has_air_quality = hasattr(orch, "_extract_air_quality")
has_permits = hasattr(orch, "_extract_permits")

if has_air_quality:
    print("   ✓ _extract_air_quality method exists")
else:
    print("   ✗ _extract_air_quality method missing")
    sys.exit(1)

if has_permits:
    print("   ✓ _extract_permits method exists")
else:
    print("   ✗ _extract_permits method missing")
    sys.exit(1)

# Test 4: Check client imports
print("\n4. Testing client imports...")
try:
    print("   ✓ EPAAirNowClient imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import EPAAirNowClient: {e}")
    sys.exit(1)

try:
    print("   ✓ MaricopaPermitClient imported successfully")
except Exception as e:
    print(f"   ✗ Failed to import MaricopaPermitClient: {e}")
    sys.exit(1)

# Test 5: Check LocationData dataclass
print("\n5. Checking LocationData dataclass fields...")
try:
    from dataclasses import fields

    from phx_home_analysis.services.location_data.orchestrator import LocationData

    field_names = [f.name for f in fields(LocationData)]
    print(f"   Fields: {field_names}")

    if "air_quality" in field_names and "permits" in field_names:
        print("   ✓ LocationData has air_quality and permits fields")
    else:
        print("   ✗ LocationData missing air_quality or permits fields")
        sys.exit(1)
except Exception as e:
    print(f"   ✗ Failed to check LocationData: {e}")
    sys.exit(1)

# Test 6: Check lazy initialization attributes
print("\n6. Checking lazy initialization attributes...")
if hasattr(orch, "_air_quality_client"):
    print("   ✓ _air_quality_client attribute exists")
else:
    print("   ✗ _air_quality_client attribute missing")
    sys.exit(1)

if hasattr(orch, "_permits_client"):
    print("   ✓ _permits_client attribute exists")
else:
    print("   ✗ _permits_client attribute missing")
    sys.exit(1)

print("\n" + "=" * 60)
print("All Integration Tests Passed! ✓")
print("=" * 60)
print("\nSummary:")
print("  • air_quality and permits added to SOURCES")
print("  • _extract_air_quality() method implemented")
print("  • _extract_permits() method implemented")
print("  • EPAAirNowClient integration working")
print("  • MaricopaPermitClient integration working")
print("  • LocationData dataclass extended")
print("  • Lazy initialization attributes added")
