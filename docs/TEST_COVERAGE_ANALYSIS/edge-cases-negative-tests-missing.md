# Edge Cases & Negative Tests Missing

### Kill Switch Logic Edge Cases

```python
def test_kill_switch_with_boundary_values(self):
    """Test kill switch evaluation at exact boundaries."""
    # LOT SIZE: 7000-15000 requirement
    props = [
        Property(..., lot_sqft=6999),   # Just below min
        Property(..., lot_sqft=7000),   # Exactly at min
        Property(..., lot_sqft=15000),  # Exactly at max
        Property(..., lot_sqft=15001),  # Just above max
    ]

    for prop in props:
        result = kill_switch.check_lot_size(prop)
        # Each should behave correctly at boundary

def test_kill_switch_with_special_values(self):
    """Test kill switch with special numeric values."""
    props = [
        Property(..., lot_sqft=0),          # Zero lot size
        Property(..., lot_sqft=-1000),      # Negative (invalid)
        Property(..., lot_sqft=9999999),    # Very large
        Property(..., garage_spaces=0.5),   # Fractional garage?
    ]

def test_kill_switch_severity_accumulation_boundary(self):
    """Test severity exactly at 1.5 and 3.0 thresholds."""
    # Severity 1.5 = WARNING threshold
    # Severity 3.0 = FAIL threshold

    # Test: 1.49999 → PASS
    # Test: 1.5 → WARNING
    # Test: 2.9999 → WARNING
    # Test: 3.0 → FAIL
```

### Scoring Strategy Edge Cases

```python
def test_scoring_with_null_values(self):
    """Test scoring handles None/null values gracefully."""
    prop = Property(
        school_rating=None,
        distance_to_grocery_miles=None,
        kitchen_layout_score=None,
    )

    scorer = PropertyScorer()
    breakdown = scorer.score(prop)

    # Should not crash, should use defaults
    assert breakdown.total_score >= 0

def test_scoring_with_extreme_values(self):
    """Test scoring with extreme/unrealistic values."""
    prop = Property(
        price_num=999_999_999,      # Very high price
        sqft=10,                     # Tiny house
        roof_age=100,                # Very old roof
        school_rating=10.5,          # Above max?
    )

    scorer = PropertyScorer()
    breakdown = scorer.score(prop)

    # Should normalize/clamp values appropriately

def test_cost_estimation_edge_cases(self):
    """Test cost estimation with edge case values."""
    cases = [
        {"sqft": 0, "price": 100000},       # Zero sqft
        {"sqft": 1000, "price": 0},         # Zero price
        {"sqft": 1000, "price": -50000},    # Negative price
        {"sqft": 10000000, "price": 1000},  # Huge sqft
    ]

    for case in cases:
        prop = Property(**case)
        estimate = cost_estimator.estimate(prop)
        # Should handle gracefully
```

---
