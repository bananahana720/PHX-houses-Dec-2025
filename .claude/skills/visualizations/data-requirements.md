# Visualization Data Requirements

This reference file details the data requirements for each visualization type.

## Value Spotter Requirements

```python
required_columns = [
    "full_address",
    "price",
    "total_score",
    "kill_switch_passed",
    "lot_sqft",  # For color gradient
    "city",
    "beds",
    "baths"
]

# Source: data/phx_homes_ranked.csv
```

## Radar Chart Requirements

```python
required_fields = {
    # Raw 1-10 scores from enrichment
    "school_rating",
    "safety_neighborhood_score",
    "parks_walkability_score",
    "kitchen_layout_score",
    "master_suite_score",
    "natural_light_score",
    "high_ceilings_score",
    "fireplace_score",
    "laundry_area_score",
    "aesthetics_score",
    # Derived scores
    "orientation",  # Convert to 1-10
    "distance_to_grocery_miles",  # Convert to 1-10
    "distance_to_highway_miles",  # Convert to 1-10
    "roof_age",  # Convert to 1-10
}

# Source: data/enrichment_data.json
```

## Golden Zone Map Requirements

```python
required_fields = {
    "full_address",
    "latitude",
    "longitude",
    "tier",  # UNICORN, CONTENDER, PASS, FAILED
    "total_score",
    "price",
}

# Source: data/phx_homes_ranked.csv (must be geocoded)
```

## Normalization Functions

```python
def normalize_score(raw_score: float, max_score: float) -> float:
    """Normalize to 0-10 scale for radar chart."""
    return (raw_score / max_score) * 10

def distance_to_score(distance_miles: float, max_good: float = 2.0) -> float:
    """Convert distance to 1-10 score (lower distance = higher score)."""
    if distance_miles <= max_good:
        return 10.0
    elif distance_miles >= max_good * 5:
        return 1.0
    else:
        return 10 - ((distance_miles - max_good) / (max_good * 4)) * 9
```

## Value Zone Definition

```python
VALUE_ZONE_CRITERIA = {
    "min_score": 365,      # Above 60%
    "max_price": 550000,   # Below $550k
    "kill_switch": "PASS"  # Must pass
}
```

## Quadrant Analysis

```
                    |
  OVERPRICED        |  PREMIUM
  (Low Score,       |  (High Score,
   High Price)      |   High Price)
                    |
--------------------+--------------------
                    |
  BUDGET            |  VALUE ZONE *
  (Low Score,       |  (High Score,
   Low Price)       |   Low Price)
                    |
```
