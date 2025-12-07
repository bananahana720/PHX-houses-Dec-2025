"""Verification script for AirQualityScorer integration."""

from src.phx_home_analysis.config.scoring_weights import ScoringWeights
from src.phx_home_analysis.services.scoring.strategies import LOCATION_STRATEGIES
from src.phx_home_analysis.services.scoring.strategies.location import AirQualityScorer

# Verify weights
print("=== Weight Verification ===")
print(f"school_district: {ScoringWeights.school_district} (expected: 42)")
print(f"crime_index: {ScoringWeights.crime_index} (expected: 47)")
print(f"supermarket_proximity: {ScoringWeights.supermarket_proximity} (expected: 23)")
print(f"parks_walkability: {ScoringWeights.parks_walkability} (expected: 23)")
print(f"flood_risk: {ScoringWeights.flood_risk} (expected: 23)")
print(f"walk_transit: {ScoringWeights.walk_transit} (expected: 22)")
print(f"air_quality: {ScoringWeights.air_quality} (expected: 15)")

# Verify AirQualityScorer in strategies
scorer_names = [s.__name__ for s in LOCATION_STRATEGIES]
print("\n=== Strategy Verification ===")
print(f"AirQualityScorer in LOCATION_STRATEGIES: {'AirQualityScorer' in scorer_names}")
print(f"Total strategies: {len(LOCATION_STRATEGIES)} (expected: 9)")
print(f"Strategy list: {', '.join(scorer_names)}")

# Verify AirQualityScorer weight property
air_quality_scorer = AirQualityScorer()
print("\n=== AirQualityScorer Instance Check ===")
print(f"AirQualityScorer.weight: {air_quality_scorer.weight} (expected: 15)")
print(f"AirQualityScorer.name: {air_quality_scorer.name}")
print(f"AirQualityScorer.category: {air_quality_scorer.category}")

# Calculate total points
weights_instance = ScoringWeights()
section_a_fields = [
    "school_district",
    "quietness",
    "crime_index",
    "supermarket_proximity",
    "parks_walkability",
    "sun_orientation",
    "flood_risk",
    "walk_transit",
    "air_quality",
]
section_a_total = sum(getattr(weights_instance, k) for k in section_a_fields)
total_possible = weights_instance.total_possible_score

print("\n=== Point Total Verification ===")
print(f"Section A Total (manual): {section_a_total} (expected: 250)")
print(f"Section A Total (property): {weights_instance.section_a_max} (expected: 250)")
print(f"Section B Total: {weights_instance.section_b_max} (expected: 170)")
print(f"Section C Total: {weights_instance.section_c_max} (expected: 180)")
print(f"Overall Total: {total_possible} (expected: 600)")

print("\n=== Status ===")
all_checks_pass = (
    ScoringWeights.school_district == 42
    and ScoringWeights.crime_index == 47
    and ScoringWeights.supermarket_proximity == 23
    and ScoringWeights.parks_walkability == 23
    and ScoringWeights.flood_risk == 23
    and ScoringWeights.walk_transit == 22
    and ScoringWeights.air_quality == 15
    and "AirQualityScorer" in scorer_names
    and len(LOCATION_STRATEGIES) == 9
    and air_quality_scorer.weight == 15
    and section_a_total == 250
    and weights_instance.section_a_max == 250
    and total_possible == 600
)

if all_checks_pass:
    print("✓ PASS - All verifications successful!")
else:
    print("✗ FAIL - Some verifications failed!")
    exit(1)
