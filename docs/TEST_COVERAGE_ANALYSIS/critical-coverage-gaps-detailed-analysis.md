# Critical Coverage Gaps - Detailed Analysis

### 1. Pipeline Orchestrator (34% coverage)

**Location:** `src/phx_home_analysis/pipeline/orchestrator.py`
**Coverage:** 34% (31/91 statements covered)
**Missing:** Lines 82-109, 162-191, 200, 223-283, 297-304, 319, 337-340

**Critical Methods Missing Tests:**
```python
# Line 82-109: run() - Main pipeline execution
def run(self) -> PipelineResult:
    """Execute complete pipeline workflow."""
    # NOT TESTED for error handling, incomplete data, etc.

# Line 162-191: analyze_single() - Single property analysis
def analyze_single(self, address: str) -> Property | None:
    """Analyze single property by address."""
    # NO TESTS for address parsing, not-found scenarios

# Line 223-283: _process_properties() - Internal batch processing
def _process_properties(self, properties: list[Property]) -> None:
    """Process batch of properties through pipeline."""
    # NO ASYNC TESTS, no error recovery tests
```

**Impact:** Main entry point has 66% uncovered code

**Test Recommendations:**
```python
# tests/integration/test_pipeline_full.py
class TestPipelineOrchestrator:
    """Test complete pipeline orchestrator."""

    @pytest.mark.asyncio
    async def test_run_complete_workflow(self, mock_csv_repo, mock_enrichment_repo):
        """Test complete pipeline execution from start to finish."""
        # Setup
        pipeline = AnalysisPipeline(
            property_repo=mock_csv_repo,
            enrichment_repo=mock_enrichment_repo
        )

        # Execute
        result = pipeline.run()

        # Verify
        assert result.total_properties > 0
        assert result.passed_count >= 0
        assert len(result.failed) >= 0
        assert result.execution_time_seconds > 0

    def test_run_with_empty_properties(self):
        """Test pipeline handles empty property list gracefully."""
        mock_repo = MagicMock()
        mock_repo.load_all.return_value = []

        pipeline = AnalysisPipeline(property_repo=mock_repo)
        result = pipeline.run()

        assert result.total_properties == 0
        assert len(result.failed) == 0

    def test_run_with_mixed_valid_invalid_data(self):
        """Test pipeline with incomplete property data."""
        # Properties with missing required fields
        incomplete_props = [
            Property(..., price_num=None),  # Missing price
            Property(..., beds=None),       # Missing beds
        ]

        pipeline = AnalysisPipeline(
            property_repo=MagicMock(load_all=lambda: incomplete_props)
        )
        result = pipeline.run()

        # Should handle gracefully, not crash
        assert isinstance(result, PipelineResult)

    def test_analyze_single_property_found(self):
        """Test analyzing single property by address."""
        pipeline = AnalysisPipeline()

        result = pipeline.analyze_single(
            "4732 W Davis Rd, Glendale, AZ 85306"
        )

        assert result is not None
        assert result.full_address == "4732 W Davis Rd, Glendale, AZ 85306"

    def test_analyze_single_property_not_found(self):
        """Test analyzing non-existent property."""
        pipeline = AnalysisPipeline()

        result = pipeline.analyze_single("999 Nonexistent St, Phoenix, AZ 00000")

        assert result is None

    def test_pipeline_preserves_property_references(self):
        """Test that pipeline doesn't lose property data during processing."""
        pipeline = AnalysisPipeline()
        result = pipeline.run()

        # All properties should maintain original data
        all_props = result.unicorns + result.contenders + result.passed + result.failed
        for prop in all_props:
            assert prop.full_address is not None
            assert prop.price_num is not None or prop.price is not None

    def test_pipeline_output_csv_generation(self, tmp_path):
        """Test that pipeline generates ranked CSV output."""
        config = AppConfig.default(base_dir=str(tmp_path))
        pipeline = AnalysisPipeline(config=config)

        result = pipeline.run()

        # Output CSV should exist
        output_file = Path(tmp_path) / "phx_homes_ranked.csv"
        assert output_file.exists()

        # CSV should have content
        lines = output_file.read_text().split('\n')
        assert len(lines) > 1  # Header + data
```

### 2. Property Analyzer (24% coverage)

**Location:** `src/phx_home_analysis/services/analysis/property_analyzer.py`
**Coverage:** 24% (11/46 statements covered)
**Missing:** Lines 77-117 (critical analysis methods)

**Missing Tests:**
```python
class TestPropertyAnalyzer:
    """Test property analysis workflow."""

    def test_analyze_property_full_workflow(self, sample_property):
        """Test complete property analysis (enrich→filter→score→classify)."""
        analyzer = PropertyAnalyzer(
            enrichment_merger=EnrichmentMerger(),
            kill_switch_filter=KillSwitchFilter(),
            scorer=PropertyScorer(),
            tier_classifier=TierClassifier(thresholds={})
        )

        enrichment_lookup = {
            sample_property.full_address: EnrichmentData(
                lot_sqft=10000,
                year_built=2020,
                garage_spaces=2
            )
        }

        result = analyzer.analyze(sample_property, enrichment_lookup)

        # Should update property with all analysis results
        assert result.kill_switch_passed is not None
        assert result.score_breakdown is not None
        assert result.tier is not None

    def test_analyze_property_no_enrichment_available(self, sample_property):
        """Test property analysis when enrichment data not found."""
        analyzer = PropertyAnalyzer(...)

        result = analyzer.analyze(sample_property, {})  # Empty enrichment

        # Should still analyze property without enrichment
        assert result is not None
        # Kill switches should still evaluate (may fail without lot size)
        assert result.kill_switch_passed is not None

    def test_analyze_property_failed_kill_switch_skips_scoring(self):
        """Test that failed kill-switch properties skip scoring."""
        analyzer = PropertyAnalyzer(...)

        # Property with HOA fee (fails kill-switch)
        prop = Property(..., hoa_fee=200)

        result = analyzer.analyze(prop, {})

        assert result.kill_switch_passed is False
        # Should NOT have score if failed kill-switch
        # (or has 0 score)

    def test_analyze_batch_properties(self):
        """Test analyzing multiple properties in batch."""
        analyzer = PropertyAnalyzer(...)

        properties = [
            Property(..., full_address="123 Main St, Phoenix, AZ 85001"),
            Property(..., full_address="456 Oak Ave, Phoenix, AZ 85001"),
        ]

        enrichment_lookup = {
            "123 Main St, Phoenix, AZ 85001": EnrichmentData(...),
            "456 Oak Ave, Phoenix, AZ 85001": EnrichmentData(...),
        }

        results = analyzer.analyze_batch(properties, enrichment_lookup)

        assert len(results) == 2
        for result in results:
            assert result.kill_switch_passed is not None
```

### 3. Tier Classifier (26% coverage)

**Location:** `src/phx_home_analysis/services/classification/tier_classifier.py`
**Coverage:** 26% (9/34 statements covered)
**Missing:** Lines 43-44, 63-75, 86-99, 112-121

**Missing Tests:**
```python
class TestTierClassifierLogic:
    """Test tier classification boundaries and edge cases."""

    def test_classify_unicorn_boundary_high(self):
        """Test unicorn tier at boundary (>480 points)."""
        classifier = TierClassifier(thresholds=Thresholds(...))

        # Exactly at boundary
        prop = Property(score_breakdown=ScoreBreakdown(total_score=481))
        tier = classifier.classify(prop)
        assert tier == Tier.UNICORN

    def test_classify_unicorn_boundary_low(self):
        """Test just below unicorn tier (480 points)."""
        classifier = TierClassifier(thresholds=Thresholds(...))

        prop = Property(score_breakdown=ScoreBreakdown(total_score=480))
        tier = classifier.classify(prop)
        assert tier == Tier.CONTENDER  # Not unicorn

    def test_classify_contender_range(self):
        """Test contender tier range (360-480 points)."""
        classifier = TierClassifier(thresholds=Thresholds(...))

        for score in [360, 420, 479]:
            prop = Property(score_breakdown=ScoreBreakdown(total_score=score))
            tier = classifier.classify(prop)
            assert tier == Tier.CONTENDER, f"Failed at {score}"

    def test_classify_pass_below_360(self):
        """Test PASS tier below 360 points."""
        classifier = TierClassifier(thresholds=Thresholds(...))

        for score in [0, 100, 359]:
            prop = Property(score_breakdown=ScoreBreakdown(total_score=score))
            tier = classifier.classify(prop)
            assert tier == Tier.PASS, f"Failed at {score}"

    def test_classify_zero_score(self):
        """Test property with zero score."""
        classifier = TierClassifier(thresholds=Thresholds(...))

        prop = Property(score_breakdown=ScoreBreakdown(total_score=0))
        tier = classifier.classify(prop)
        assert tier == Tier.PASS

    def test_classify_maximum_score(self):
        """Test property with maximum possible score (600)."""
        classifier = TierClassifier(thresholds=Thresholds(...))

        prop = Property(score_breakdown=ScoreBreakdown(total_score=600))
        tier = classifier.classify(prop)
        assert tier == Tier.UNICORN

    def test_classify_multiple_properties(self):
        """Test classifying multiple properties at once."""
        classifier = TierClassifier(thresholds=Thresholds(...))

        properties = [
            Property(score_breakdown=ScoreBreakdown(total_score=500)),
            Property(score_breakdown=ScoreBreakdown(total_score=400)),
            Property(score_breakdown=ScoreBreakdown(total_score=200)),
        ]

        classified = classifier.classify_all(properties)

        assert len(classified) == 3
        assert classified[0].tier == Tier.UNICORN
        assert classified[1].tier == Tier.CONTENDER
        assert classified[2].tier == Tier.PASS
```

### 4. Enrichment Merger (12% coverage)

**Location:** `src/phx_home_analysis/services/enrichment/merger.py`
**Coverage:** 12% (9/77 statements covered)
**Missing:** Lines 46-87 (critical merge logic)

**Critical Gap - Missing Tests:**
```python
class TestEnrichmentMergerComprehensive:
    """Test all enrichment merge scenarios."""

    def test_merge_county_assessor_data(self, sample_property):
        """Test merging county assessor fields."""
        merger = EnrichmentMerger()

        enrichment = EnrichmentData(
            lot_sqft=12000,
            year_built=2015,
            garage_spaces=2,
            sewer_type="city"
        )

        result = merger.merge(sample_property, enrichment)

        assert result.lot_sqft == 12000
        assert result.year_built == 2015
        assert result.garage_spaces == 2
        assert result.sewer_type == SewerType.CITY

    def test_merge_hoa_and_tax_data(self, sample_property):
        """Test merging HOA and tax information."""
        merger = EnrichmentMerger()

        enrichment = EnrichmentData(
            hoa_fee=150,
            tax_annual=2400
        )

        result = merger.merge(sample_property, enrichment)

        assert result.hoa_fee == 150
        assert result.tax_annual == 2400

    def test_merge_location_data(self, sample_property):
        """Test merging location/distance data."""
        merger = EnrichmentMerger()

        enrichment = EnrichmentData(
            school_rating=8.5,
            distance_to_grocery_miles=0.3,
            distance_to_highway_miles=1.2,
            commute_minutes=25
        )

        result = merger.merge(sample_property, enrichment)

        assert result.school_rating == 8.5
        assert result.distance_to_grocery_miles == 0.3
        assert result.distance_to_highway_miles == 1.2
        assert result.commute_minutes == 25

    def test_merge_arizona_specific_features(self, sample_property):
        """Test merging AZ-specific property features."""
        merger = EnrichmentMerger()

        enrichment = EnrichmentData(
            solar_status="owned",
            has_pool=True,
            pool_equipment_age=5,
            roof_age=3,
            hvac_age=7
        )

        result = merger.merge(sample_property, enrichment)

        assert result.solar_status == SolarStatus.OWNED
        assert result.has_pool is True
        assert result.pool_equipment_age == 5
        assert result.roof_age == 3
        assert result.hvac_age == 7

    def test_merge_preserves_none_values(self, sample_property):
        """Test that None values in enrichment don't overwrite existing data."""
        original_roof_age = sample_property.roof_age

        merger = EnrichmentMerger()
        enrichment = EnrichmentData(roof_age=None)

        result = merger.merge(sample_property, enrichment)

        # Should preserve original value
        assert result.roof_age == original_roof_age

    def test_merge_batch_multiple_properties(self):
        """Test merging enrichment into multiple properties."""
        merger = EnrichmentMerger()

        properties = [
            Property(full_address="123 Main St, Phoenix, AZ 85001", ...),
            Property(full_address="456 Oak Ave, Phoenix, AZ 85001", ...),
        ]

        enrichment_lookup = {
            "123 Main St, Phoenix, AZ 85001": EnrichmentData(lot_sqft=12000),
            "456 Oak Ave, Phoenix, AZ 85001": EnrichmentData(lot_sqft=8000),
        }

        results = merger.merge_batch(properties, enrichment_lookup)

        assert len(results) == 2
        assert results[0].lot_sqft == 12000
        assert results[1].lot_sqft == 8000

    def test_merge_batch_partial_enrichment(self):
        """Test merging when enrichment data incomplete."""
        merger = EnrichmentMerger()

        properties = [
            Property(full_address="123 Main St, Phoenix, AZ 85001", ...),
            Property(full_address="456 Oak Ave, Phoenix, AZ 85001", ...),
        ]

        enrichment_lookup = {
            "123 Main St, Phoenix, AZ 85001": EnrichmentData(lot_sqft=12000),
            # "456 Oak Ave" not in enrichment
        }

        results = merger.merge_batch(properties, enrichment_lookup)

        # First property enriched
        assert results[0].lot_sqft == 12000
        # Second property unchanged
        assert results[1].lot_sqft == properties[1].lot_sqft

    def test_merge_sewer_type_conversion(self, sample_property):
        """Test string to enum conversion for sewer type."""
        merger = EnrichmentMerger()

        for sewer_str, expected_enum in [
            ("city", SewerType.CITY),
            ("septic", SewerType.SEPTIC),
            ("unknown", SewerType.UNKNOWN),
        ]:
            enrichment = EnrichmentData(sewer_type=sewer_str)
            result = merger.merge(sample_property, enrichment)
            assert result.sewer_type == expected_enum

    def test_merge_orientation_conversion(self, sample_property):
        """Test string to enum conversion for orientation."""
        merger = EnrichmentMerger()

        for orient_str, expected_enum in [
            ("N", Orientation.N),
            ("S", Orientation.S),
            ("E", Orientation.E),
            ("W", Orientation.W),
        ]:
            enrichment = EnrichmentData(orientation=orient_str)
            result = merger.merge(sample_property, enrichment)
            assert result.orientation == expected_enum

    def test_merge_solar_status_conversion(self, sample_property):
        """Test string to enum conversion for solar status."""
        merger = EnrichmentMerger()

        for solar_str, expected_enum in [
            ("owned", SolarStatus.OWNED),
            ("leased", SolarStatus.LEASED),
            ("none", SolarStatus.NONE),
        ]:
            enrichment = EnrichmentData(solar_status=solar_str)
            result = merger.merge(sample_property, enrichment)
            assert result.solar_status == expected_enum
```

---
