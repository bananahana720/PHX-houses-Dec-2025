# 8. Test Cases

### 8.1 Kill-Switch Edge Cases

#### 8.1.1 Solar Lease Tests

```python
# tests/unit/services/kill_switch/test_solar_lease.py

class TestSolarLeaseCriterion:

    def test_solar_owned_passes(self):
        """Owned solar should pass without severity."""
        prop = {"solar_status": "owned"}
        result = solar_lease_criterion.evaluate(prop)
        assert result.passed is True
        assert result.severity_weight == 0.0

    def test_solar_none_passes(self):
        """No solar should pass without severity."""
        prop = {"solar_status": "none"}
        result = solar_lease_criterion.evaluate(prop)
        assert result.passed is True
        assert result.severity_weight == 0.0

    def test_solar_leased_fails_with_severity(self):
        """Leased solar should fail with 2.5 severity."""
        prop = {"solar_status": "leased"}
        result = solar_lease_criterion.evaluate(prop)
        assert result.passed is False
        assert result.severity_weight == 2.5

    def test_solar_unknown_passes_with_flag(self):
        """Unknown solar status should pass with yellow flag."""
        prop = {"solar_status": "unknown"}
        result = solar_lease_criterion.evaluate(prop)
        assert result.passed is True
        assert result.severity_weight == 0.0
        assert result.flag == "YELLOW"

    def test_solar_leased_plus_septic_fails_threshold(self):
        """Leased solar (2.5) + septic (2.5) = 5.0 >= 3.0 threshold."""
        prop = {"solar_status": "leased", "sewer_type": "septic"}
        verdict, severity, failures, _ = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.FAIL
        assert severity == 5.0
        assert len(failures) == 2

    def test_solar_leased_alone_is_warning(self):
        """Leased solar alone (2.5) should be WARNING, not FAIL."""
        prop = {
            "solar_status": "leased",
            "sewer_type": "city",
            "year_built": 2010,
            "garage_spaces": 2,
            "lot_sqft": 10000,
            "beds": 4,
            "baths": 2,
            "hoa_fee": 0
        }
        verdict, severity, failures, _ = evaluate_kill_switches(prop)
        assert verdict == KillSwitchVerdict.WARNING
        assert severity == 2.5
```

### 8.2 Scoring Boundary Conditions

#### 8.2.1 HVAC Scoring Tests

```python
# tests/unit/services/scoring/test_hvac_scorer.py

class TestHvacConditionScorer:

    @pytest.mark.parametrize("hvac_age,expected_score", [
        (0, 25),    # Brand new - full points
        (5, 25),    # 5 years - still new category
        (6, 20),    # 6 years - good category
        (10, 20),   # 10 years - upper bound of good
        (11, 12),   # 11 years - aging category
        (15, 12),   # 15 years - upper bound of aging
        (16, 5),    # 16 years - replacement needed
        (25, 5),    # 25 years - definitely needs replacement
    ])
    def test_hvac_age_scoring(self, hvac_age, expected_score):
        """Test HVAC age scoring at boundary points."""
        prop = {"hvac_age": hvac_age}
        scorer = HvacConditionScorer()
        score = scorer.score(prop)
        assert score == expected_score

    def test_hvac_age_derived_from_year_built(self):
        """When hvac_age missing, derive from year_built."""
        prop = {"year_built": 2015}  # 10 years old in 2025
        scorer = HvacConditionScorer()
        score = scorer.score(prop)
        assert score == 20  # Good category (6-10 years)

    def test_hvac_age_unknown_returns_neutral(self):
        """Unknown HVAC age should return neutral score."""
        prop = {}  # No hvac_age, no year_built
        scorer = HvacConditionScorer()
        score = scorer.score(prop)
        assert score == 12.5  # Neutral (50% of 25)

    def test_hvac_install_year_takes_precedence(self):
        """hvac_install_year should override year_built derivation."""
        prop = {
            "year_built": 1990,      # House is 35 years old
            "hvac_install_year": 2020  # But HVAC replaced 5 years ago
        }
        scorer = HvacConditionScorer()
        score = scorer.score(prop)
        assert score == 25  # New category based on HVAC install
```

### 8.3 New Criteria Validation

#### 8.3.1 Total Score Validation

```python
# tests/unit/services/scoring/test_total_score.py

class TestTotalScoreCalculation:

    def test_section_totals_sum_to_600(self):
        """Verify all section weights sum to 600."""
        weights = ScoringWeights()
        assert weights.section_a_max == 225
        assert weights.section_b_max == 195
        assert weights.section_c_max == 180
        assert weights.total_possible_score == 600

    def test_perfect_score_is_600(self):
        """Property with perfect scores should total 600."""
        perfect_property = {
            # Section A: 225 pts
            "school_rating": 10,
            "distance_to_highway_miles": 5.0,
            "safety_score": 100,
            "distance_to_grocery_miles": 0.3,
            "parks_walkability_score": 10,
            "orientation": "north",
            "flood_zone": "X",
            "walk_score": 100,
            "transit_score": 100,
            "bike_score": 100,
            "air_quality_index": 30,

            # Section B: 195 pts
            "roof_age": 2,
            "lot_sqft": 12000,
            "sqft": 2000,
            "year_built": 2020,
            "has_pool": True,
            "pool_equipment_age": 2,
            "monthly_cost": 2800,
            "hvac_age": 2,  # NEW

            # Section C: 180 pts
            "kitchen_layout_score": 10,
            "master_suite_score": 10,
            "natural_light_score": 10,
            "high_ceilings_score": 10,
            "fireplace_score": 10,
            "laundry_area_score": 10,
            "aesthetics_score": 10,
        }

        scorer = PropertyScorer()
        result = scorer.score(perfect_property)
        assert result.total_score == 600
```

---
