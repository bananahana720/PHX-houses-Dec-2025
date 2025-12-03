"""End-to-end test for AirQualityScorer with Property entity."""

from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.services.scoring.strategies.location import AirQualityScorer

# Create test properties with different AQI values
test_cases = [
    {"address": "Good Air (AQI=30)", "air_quality_aqi": 30, "expected_base": 10.0, "expected_weighted": 15.0},
    {"address": "Moderate Air (AQI=75)", "air_quality_aqi": 75, "expected_base": 8.0, "expected_weighted": 12.0},
    {"address": "Unhealthy Sensitive (AQI=125)", "air_quality_aqi": 125, "expected_base": 5.0, "expected_weighted": 7.5},
    {"address": "Unhealthy (AQI=175)", "air_quality_aqi": 175, "expected_base": 3.0, "expected_weighted": 4.5},
    {"address": "Hazardous (AQI=250)", "air_quality_aqi": 250, "expected_base": 1.0, "expected_weighted": 1.5},
    {"address": "No Data", "air_quality_aqi": None, "expected_base": 5.0, "expected_weighted": 7.5},  # Neutral
]

scorer = AirQualityScorer()
print("=== AirQualityScorer End-to-End Test ===")
print(f"Scorer weight: {scorer.weight} pts")
print(f"Scorer name: {scorer.name}")
print(f"Scorer category: {scorer.category}\n")

all_pass = True

for test in test_cases:
    # Create minimal property with only required fields
    property_dict = {
        "street": test["address"],
        "city": "Phoenix",
        "state": "AZ",
        "zip_code": "85001",
        "full_address": f"{test['address']}, Phoenix, AZ 85001",
        "price": "$400,000",
        "price_num": 400000,
        "beds": 4,
        "baths": 2.0,
        "sqft": 2000,
        "price_per_sqft_raw": 200.0,
        "year_built": 2020,
    }

    # Add air_quality_aqi if provided
    if test["air_quality_aqi"] is not None:
        property_dict["air_quality_aqi"] = test["air_quality_aqi"]

    prop = Property(**property_dict)

    # Calculate scores
    base_score = scorer.calculate_base_score(prop)
    score_obj = scorer.calculate_weighted_score(prop)
    weighted_score = score_obj.weighted_score

    # Verify
    base_pass = abs(base_score - test["expected_base"]) < 0.01
    weighted_pass = abs(weighted_score - test["expected_weighted"]) < 0.01
    test_pass = base_pass and weighted_pass

    status = "✓ PASS" if test_pass else "✗ FAIL"
    print(f"{status} | {test['address']:<30} | AQI={test['air_quality_aqi']!s:<5} | Base: {base_score:.1f}/{test['expected_base']:.1f} | Weighted: {weighted_score:.1f}/{test['expected_weighted']:.1f}")

    if not test_pass:
        all_pass = False

print("\n=== Final Result ===")
if all_pass:
    print("✓ ALL TESTS PASSED - AirQualityScorer is fully integrated and functional!")
else:
    print("✗ SOME TESTS FAILED - Review scorer logic")
    exit(1)
