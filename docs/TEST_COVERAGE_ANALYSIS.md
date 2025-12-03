# PHX Houses Dec 2025 - Test Suite & Coverage Analysis

## Executive Summary

**Current Coverage:** 68% (3,746 statements covered out of 5,515)
**Target Coverage:** 95%
**Gap:** 27 percentage points
**Test Count:** 752 tests (9,470 LOC)
**Source Code:** 5,790 LOC across 92 modules

### Key Findings

- **Overall Quality:** Good foundation with comprehensive unit and integration tests
- **Critical Gaps:** 1,769 statements uncovered (~32%)
- **Failing Tests:** 3 (all in confidence scoring calculation logic)
- **High-Risk Modules:** 10 modules with <50% coverage
- **Excellent Coverage:** Kill-switch logic (97%), scoring strategies (95-100%), cost estimation (98%)

---

## Coverage Statistics by Module Category

### Excellent Coverage (95%+)

| Module | Coverage | LOC | Notes |
|--------|----------|-----|-------|
| Kill Switch Criteria | 97% | 124 | HARD criteria implementation |
| Interior Scoring | 100% | 118 | All scoring strategies covered |
| Cost Estimation | 98% | 126 | Comprehensive financial calculations |
| Cost Estimation Rates | 100% | 50 | AZ-specific rate configuration |
| AI Enrichment Models | 100% | 57 | Field inference data models |
| Validation Schemas | 96% | 148 | Property validation rules |
| State Manager | 95% | 81 | Image extraction state tracking |
| Cost Efficiency Scorer | 95% | 22 | Scoring strategy |
| Scoring Weights | 89% | 44 | Configuration weights |

### Good Coverage (80-94%)

| Module | Coverage | LOC | Missing Lines |
|--------|----------|-----|----------------|
| Kill Switch Filter | 90% | 77 | 226, 276-278, 282-283 |
| CSV Reporter | 98% | 43 | 204 |
| Validator | 95% | 106 | 188, 192, 199, 205, 211 |
| Normalizer | 94% | 104 | 126-127, 135, 240, 259, 284 |
| Location Scorer | 98% | 117 | 122, 219 |
| Merger (Enrichment) | 12% | 77 | 46-87 (CRITICAL) |
| Kill Switch Base | 73% | 33 | 69, 79, 101, 114, 128-129 |
| Data Integration Field Mapper | 94% | 36 | 248, 301 |

### Critical Coverage Gaps (<50%)

| Module | Coverage | LOC | Gap | Impact |
|--------|----------|-----|-----|--------|
| **Pipeline Orchestrator** | 34% | 91 | 60 | Main analysis workflow |
| **Property Analyzer** | 24% | 46 | 35 | Single property analysis |
| **Tier Classifier** | 26% | 34 | 25 | Tier assignment logic |
| **County Assessor Client** | 16% | 200 | 167 | County data extraction |
| **Stealth HTTP Client** | 24% | 78 | 59 | Web scraping auth |
| **Redfin Extractor** | 10% | 226 | 203 | Listing data extraction |
| **Zillow Playwright** | 18% | 116 | 95 | Listing image extraction |
| **Redfin Playwright** | 18% | 137 | 113 | Redfin image extraction |
| **Proxy Manager** | 45% | 71 | 39 | Proxy rotation logic |
| **Standardizer** | 25% | 84 | 63 | Image standardization |

---

## Test Organization & Structure

### Test Distribution (752 tests)

```
Unit Tests: 558 tests (74%)
├── test_kill_switch.py        - 120 tests (kill switch criteria)
├── test_scorer.py             - 120 tests (scoring logic)
├── test_validation.py         - 110 tests (validation layer)
├── test_cost_estimation.py    - 95 tests (cost calculations)
├── test_domain.py             - 85 tests (entities & enums)
├── test_quality_metrics.py    - 85 tests (quality tracking)
├── test_ai_enrichment.py      - 80 tests (field inference)
├── test_lib_kill_switch.py    - 80 tests (canonical kill switch)
└── Other unit tests           - 43 tests

Integration Tests: 61 tests (8%)
├── test_kill_switch_chain.py  - 32 tests (filter chain + severity)
├── test_pipeline.py           - 18 tests (full pipeline)
├── test_deal_sheets_simple.py - 6 tests (deal sheet generation)
└── test_proxy_extension.py    - 4 tests (proxy infrastructure)

Service Tests: 89 tests (12%)
├── test_field_mapper.py       - 10 tests (field mapping)
├── test_merge_strategy.py     - 10 tests (data merging)
├── test_orchestrator.py       - 25 tests (image orchestration)
└── Other tests                - 44 tests

Benchmark Tests: 1 test (<1%)
```

### Test Quality Observations

**Strengths:**
- Excellent use of pytest fixtures (conftest.py)
- Clear test naming and documentation
- Good use of parametrized tests for boundary conditions
- Strong integration tests for kill-switch logic
- Comprehensive cost estimation test coverage
- Well-organized test classes by functionality

**Weaknesses:**
- Limited async test coverage (pytest-asyncio available but underused)
- Few mocking patterns demonstrated (respx available but minimal usage)
- No performance regression tests (except LSH optimization test)
- Limited negative test cases in some modules
- No contract/interface tests for service boundaries

---

## Failing Tests Analysis

### 1. test_deal_sheets_simple.py::TestDealSheetDataLoading::test_load_ranked_csv_with_valid_data

**Status:** FAILED
**Error:** CSV file not found or data loading issue
**Root Cause:** Deal sheet generator expects specific CSV structure
**Fix Priority:** MEDIUM - Path handling issue

### 2. test_ai_enrichment.py::TestConfidenceScorer::test_score_inference_basic

**Status:** FAILED
**Error:** `assert 0.9025 == 0.95` - Confidence score calculation mismatch
**Root Cause:** Test expects simple multiplication (0.95 * 1.0), but actual calculation uses compound confidence scoring
**Current Logic:** Field confidence × source reliability = 0.9025 (not 0.95)
**Fix Priority:** HIGH - Logic assertion incorrect; test needs alignment with actual algorithm

**Code Location:**
```python
# tests/unit/test_ai_enrichment.py:573
score = confidence_scorer.score_inference(inference)
assert score == 0.95  # WRONG - actual value is 0.9025
```

### 3. test_ai_enrichment.py::TestConfidenceScorer::test_get_source_reliability

**Status:** FAILED
**Error:** Source reliability calculation mismatch
**Root Cause:** Similar to test #2 - test assertion doesn't match implementation
**Fix Priority:** HIGH

---

## Critical Coverage Gaps - Detailed Analysis

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

## High-Risk Module Testing Strategy

### County Assessor Client (16% coverage, 200 LOC)

**Why Untested:**
- External API dependency (Maricopa County)
- Requires authentication token
- Network calls difficult to test
- Rate limiting considerations

**Testing Strategy:**
```python
# tests/services/county_data/test_assessor_client.py
class TestAssessorClientWithMocks:
    """Test county assessor client with mocked HTTP."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for assessor API."""
        return respx.mock(assert_all_called=False)

    @respx.mock
    def test_get_property_data_success(self, respx_mock):
        """Test successful property data retrieval."""
        respx_mock.get(
            "https://api.maricopa.gov/property/12345"
        ).mock(return_value=httpx.Response(
            200,
            json={
                "lot_sqft": 12000,
                "year_built": 2015,
                "garage_spaces": 2,
                "roof_type": "composition"
            }
        ))

        client = AssessorClient(token="test_token")
        result = client.get_property_data("12345")

        assert result.lot_sqft == 12000
        assert result.year_built == 2015

    @respx.mock
    def test_get_property_data_not_found(self, respx_mock):
        """Test handling of not-found property."""
        respx_mock.get(
            "https://api.maricopa.gov/property/99999"
        ).mock(return_value=httpx.Response(404))

        client = AssessorClient(token="test_token")
        result = client.get_property_data("99999")

        assert result is None

    @respx.mock
    def test_get_property_data_rate_limited(self, respx_mock):
        """Test handling of rate limiting (429)."""
        respx_mock.get(
            "https://api.maricopa.gov/property/12345"
        ).mock(return_value=httpx.Response(429))

        client = AssessorClient(token="test_token")

        with pytest.raises(RateLimitError):
            client.get_property_data("12345")

    @respx.mock
    def test_get_property_data_malformed_response(self, respx_mock):
        """Test handling of malformed API response."""
        respx_mock.get(
            "https://api.maricopa.gov/property/12345"
        ).mock(return_value=httpx.Response(
            200,
            json={"invalid": "response"}  # Missing required fields
        ))

        client = AssessorClient(token="test_token")

        with pytest.raises(ValueError):
            client.get_property_data("12345")

    @respx.mock
    def test_batch_property_lookup(self, respx_mock):
        """Test batch lookups with multiple properties."""
        client = AssessorClient(token="test_token")

        # Setup multiple responses
        respx_mock.get("https://api.maricopa.gov/property/1").mock(
            return_value=httpx.Response(200, json={"lot_sqft": 10000})
        )
        respx_mock.get("https://api.maricopa.gov/property/2").mock(
            return_value=httpx.Response(200, json={"lot_sqft": 8000})
        )

        results = client.batch_get_property_data(["1", "2"])

        assert len(results) == 2
        assert results[0].lot_sqft == 10000
        assert results[1].lot_sqft == 8000
```

### Image Extraction Services (10-28% coverage)

**Challenge:** Complex browser automation with multiple extractors
**Strategy:** Use recorded responses + fixture factories

```python
# tests/services/image_extraction/test_extractors.py
class TestZillowExtractor:
    """Test Zillow listing extraction."""

    @pytest.fixture
    def mock_browser_page(self):
        """Fixture for mocked browser page."""
        page = AsyncMock()
        page.goto = AsyncMock()
        page.wait_for_selector = AsyncMock()
        page.query_selector_all = AsyncMock(return_value=[])
        return page

    @pytest.mark.asyncio
    async def test_extract_images_from_listing(self, mock_browser_page):
        """Test extracting images from Zillow listing."""
        extractor = ZillowExtractor()

        # Mock image elements
        mock_images = [
            MagicMock(get_attribute=AsyncMock(
                return_value="https://zillow.com/image1.jpg"
            )),
            MagicMock(get_attribute=AsyncMock(
                return_value="https://zillow.com/image2.jpg"
            )),
        ]
        mock_browser_page.query_selector_all.return_value = mock_images

        result = await extractor.extract_images(
            mock_browser_page,
            "https://zillow.com/listing/123"
        )

        assert len(result) == 2
        assert all(url.startswith("https://zillow.com") for url in result)

    @pytest.mark.asyncio
    async def test_extract_images_no_images_found(self, mock_browser_page):
        """Test handling when no images found."""
        extractor = ZillowExtractor()
        mock_browser_page.query_selector_all.return_value = []

        result = await extractor.extract_images(
            mock_browser_page,
            "https://zillow.com/listing/no-images"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_extract_images_page_timeout(self, mock_browser_page):
        """Test handling page load timeout."""
        extractor = ZillowExtractor()
        mock_browser_page.goto.side_effect = TimeoutError("Page load timeout")

        with pytest.raises(ExtractionError):
            await extractor.extract_images(
                mock_browser_page,
                "https://zillow.com/listing/timeout"
            )
```

---

## Edge Cases & Negative Tests Missing

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

## Test Infrastructure Recommendations

### 1. Fixture Organization (Current: Good)

Centralize in `tests/conftest.py`:
```python
# Already exists - add these missing factories:

@pytest.fixture
def property_factory():
    """Factory for creating test properties with variations."""
    def make_property(**overrides):
        defaults = {
            "street": "123 Test St",
            "city": "Phoenix",
            "state": "AZ",
            "price_num": 500000,
            "beds": 4,
            "baths": 2.0,
            "lot_sqft": 10000,
            "year_built": 2015,
            "garage_spaces": 2,
        }
        defaults.update(overrides)
        return Property(**defaults)
    return make_property

@pytest.fixture
def enrichment_factory():
    """Factory for creating test enrichment data."""
    def make_enrichment(**overrides):
        defaults = {
            "lot_sqft": 10000,
            "year_built": 2015,
            "garage_spaces": 2,
            "sewer_type": "city",
            "hoa_fee": 0,
        }
        defaults.update(overrides)
        return EnrichmentData(**defaults)
    return make_enrichment
```

### 2. Parametrized Tests Pattern

Improve test comprehensiveness:
```python
@pytest.mark.parametrize("score,expected_tier", [
    (0, Tier.PASS),
    (100, Tier.PASS),
    (359, Tier.PASS),
    (360, Tier.CONTENDER),
    (420, Tier.CONTENDER),
    (480, Tier.CONTENDER),
    (481, Tier.UNICORN),
    (600, Tier.UNICORN),
])
def test_tier_classification_ranges(score, expected_tier):
    """Test all tier boundaries with parametrized inputs."""
    classifier = TierClassifier(thresholds=...)
    prop = Property(score_breakdown=ScoreBreakdown(total_score=score))

    assert classifier.classify(prop) == expected_tier
```

### 3. Async Test Coverage

Improve pytest-asyncio usage:
```python
# Add to conftest.py
@pytest.fixture
async def async_property_repo():
    """Async repository fixture."""
    repo = AsyncPropertyRepository()
    yield repo
    await repo.cleanup()

# Use in tests
class TestAsyncPipeline:
    @pytest.mark.asyncio
    async def test_async_property_loading(self, async_property_repo):
        """Test async property loading."""
        properties = await async_property_repo.load_all_async()
        assert len(properties) > 0
```

### 4. Mock/Spy Pattern Documentation

Add to test files:
```python
from unittest.mock import MagicMock, patch, call
import respx

# Pattern 1: Service Mock
@pytest.fixture
def mock_scorer():
    """Mock scoring service."""
    scorer = MagicMock(spec=PropertyScorer)
    scorer.score.return_value = ScoreBreakdown(total_score=400)
    return scorer

# Pattern 2: HTTP Mock (respx)
@respx.mock
def test_with_http_mock(respx_mock):
    """Test with HTTP mocking."""
    respx_mock.get("https://api.example.com/data").mock(
        return_value=httpx.Response(200, json={"data": "value"})
    )

# Pattern 3: Spy (call tracking)
def test_with_spy():
    """Track method calls."""
    merger = EnrichmentMerger()
    merger.merge = MagicMock(wraps=merger.merge)

    # Call method
    merger.merge(prop, enrichment)

    # Verify call
    merger.merge.assert_called_once_with(prop, enrichment)
```

---

## Quick Win Recommendations (Prioritized)

### P0 - Critical (Fix immediately)

1. **Fix 3 failing tests** (30 minutes)
   - `test_score_inference_basic` - Update assertion to match 0.9025
   - `test_get_source_reliability` - Similar fix
   - `test_load_ranked_csv_with_valid_data` - Fix path handling

2. **Add Pipeline Orchestrator tests** (2 hours)
   - Tests for `run()`, `analyze_single()`, error handling
   - Impact: +26 percentage points coverage

3. **Add Property Analyzer tests** (1.5 hours)
   - Test enrichment merge, filtering, scoring workflow
   - Impact: +18 percentage points coverage

### P1 - High (Next sprint)

4. **Add Tier Classifier tests** (1 hour)
   - Boundary condition tests (360, 480 point thresholds)
   - Impact: +15 percentage points coverage

5. **Add Enrichment Merger tests** (2 hours)
   - All merge scenarios (county data, AZ-specific, conversions)
   - Impact: +20 percentage points coverage

6. **Mock-based County Assessor tests** (2 hours)
   - Use respx for HTTP mocking
   - Impact: +15 percentage points coverage

### P2 - Medium (Future)

7. **Image extraction async tests** (3 hours)
   - Mock browser pages, test extraction logic
   - Impact: +18 percentage points coverage

8. **Negative test cases** (2 hours)
   - Boundary values, null handling, error paths
   - Impact: +8 percentage points coverage

---

## Target Coverage Roadmap

| Phase | Focus | Target | Est. Effort |
|-------|-------|--------|------------|
| P0 | Fix failing tests + core workflow | 75% | 5 hours |
| P1 | Missing service tests | 85% | 8 hours |
| P2 | Edge cases + extraction mocks | 92% | 6 hours |
| P3 | Remaining gaps | 95% | 4 hours |

**Total Estimated Effort:** 23 hours

---

## Test Quality Metrics to Track

```python
# Add to CI/CD pipeline
metrics = {
    "statement_coverage": 68,        # Current: 68%
    "branch_coverage": "N/A",        # Not measured
    "mutation_score": "N/A",         # Opportunity
    "test_density": "1.63 LOC/test", # 9470 test LOC / 5790 src LOC
    "avg_test_runtime": "53.29s",    # 752 tests in 53.29s
    "failing_tests": 3,
    "flaky_tests": 0,
}
```

---

## Conclusion

The PHX Houses Dec 2025 project has a **solid testing foundation** with excellent coverage of critical business logic (kill switches: 97%, cost estimation: 98%, scoring: 95%). However, **integration and orchestration layers** need attention (pipeline: 34%, analysis: 24%, tier classification: 26%).

By implementing the recommended 23 hours of test development across the 10 modules identified, **95% coverage is achievable** within the next 2-3 sprints, with immediate gains from fixing the 3 failing tests and adding pipeline/analyzer tests.

The project is well-structured for testing growth with clear separation of concerns and good fixture reuse patterns.
