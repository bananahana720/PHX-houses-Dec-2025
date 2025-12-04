# Part 3: Property Analyzer Tests (P0)

**File:** `tests/services/test_property_analyzer.py` (NEW)

```python
"""Tests for PropertyAnalyzer service."""

import pytest
from phx_home_analysis.services.analysis import PropertyAnalyzer
from phx_home_analysis.domain import Property, EnrichmentData, SewerType
from phx_home_analysis.services.enrichment import EnrichmentMerger
from phx_home_analysis.services.kill_switch import KillSwitchFilter
from phx_home_analysis.services.scoring import PropertyScorer
from phx_home_analysis.services.classification import TierClassifier


class TestPropertyAnalyzerInit:
    """Test analyzer initialization."""

    def test_init_with_services(self):
        """Test analyzer initializes with required services."""
        merger = EnrichmentMerger()
        filter_svc = KillSwitchFilter()
        scorer = PropertyScorer()
        classifier = TierClassifier(thresholds=scorer.thresholds)

        analyzer = PropertyAnalyzer(
            enrichment_merger=merger,
            kill_switch_filter=filter_svc,
            scorer=scorer,
            tier_classifier=classifier,
        )

        assert analyzer._merger is merger
        assert analyzer._filter is filter_svc
        assert analyzer._scorer is scorer
        assert analyzer._classifier is classifier


class TestPropertyAnalyzerWorkflow:
    """Test property analysis workflow."""

    def test_analyze_property_full_workflow(self, sample_property):
        """Test complete property analysis (enrich→filter→score→classify)."""
        merger = EnrichmentMerger()
        filter_svc = KillSwitchFilter()
        scorer = PropertyScorer()
        classifier = TierClassifier(thresholds=scorer.thresholds)

        analyzer = PropertyAnalyzer(
            enrichment_merger=merger,
            kill_switch_filter=filter_svc,
            scorer=scorer,
            tier_classifier=classifier,
        )

        enrichment = EnrichmentData(
            lot_sqft=12000,
            year_built=2015,
            garage_spaces=2,
            sewer_type="city",
            hoa_fee=0,
        )

        enrichment_lookup = {
            sample_property.full_address: enrichment
        }

        result = analyzer.analyze(sample_property, enrichment_lookup)

        # Should update property with all analysis results
        assert result.kill_switch_passed is not None
        assert result.score_breakdown is not None
        assert result.tier is not None

    def test_analyze_property_no_enrichment_available(self, sample_property):
        """Test property analysis when enrichment data not found."""
        merger = EnrichmentMerger()
        filter_svc = KillSwitchFilter()
        scorer = PropertyScorer()
        classifier = TierClassifier(thresholds=scorer.thresholds)

        analyzer = PropertyAnalyzer(
            enrichment_merger=merger,
            kill_switch_filter=filter_svc,
            scorer=scorer,
            tier_classifier=classifier,
        )

        # Empty enrichment lookup
        result = analyzer.analyze(sample_property, {})

        # Should still analyze property without enrichment
        assert result is not None
        # Kill switches should still evaluate
        assert result.kill_switch_passed is not None

    def test_analyze_property_failed_kill_switch_logs_failures(self):
        """Test that failed properties log all failure reasons."""
        prop = Property(
            street="123 Main St",
            city="Phoenix",
            state="AZ",
            price_num=500000,
            beds=2,  # Below minimum of 4
            baths=2.0,
            hoa_fee=200,  # HOA fails (hard criterion)
            sewer_type=SewerType.UNKNOWN,
        )

        analyzer = PropertyAnalyzer(
            enrichment_merger=EnrichmentMerger(),
            kill_switch_filter=KillSwitchFilter(),
            scorer=PropertyScorer(),
            tier_classifier=TierClassifier(thresholds=PropertyScorer().thresholds),
        )

        result = analyzer.analyze(prop, {})

        assert result.kill_switch_passed is False
        assert len(result.kill_switch_failures) > 0
        # Should have multiple failures recorded
        assert any("HOA" in str(f) for f in result.kill_switch_failures)
        assert any("bed" in str(f).lower() for f in result.kill_switch_failures)

    def test_analyze_property_with_enrichment_updates_fields(self):
        """Test that enrichment data is applied to property."""
        prop = Property(
            street="123 Main St",
            city="Phoenix",
            state="AZ",
            price_num=500000,
            beds=4,
            baths=2.0,
            lot_sqft=None,  # Will be enriched
            year_built=None,  # Will be enriched
        )

        enrichment = EnrichmentData(
            lot_sqft=12000,
            year_built=2015,
        )

        analyzer = PropertyAnalyzer(
            enrichment_merger=EnrichmentMerger(),
            kill_switch_filter=KillSwitchFilter(),
            scorer=PropertyScorer(),
            tier_classifier=TierClassifier(thresholds=PropertyScorer().thresholds),
        )

        result = analyzer.analyze(prop, {prop.full_address: enrichment})

        # Enrichment should be applied
        assert result.lot_sqft == 12000
        assert result.year_built == 2015

    def test_analyze_property_passed_gets_scored(self):
        """Test that passing properties get scored and classified."""
        prop = Property(
            street="123 Main St",
            city="Phoenix",
            state="AZ",
            price_num=500000,
            beds=4,
            baths=2.0,
            lot_sqft=10000,
            year_built=2015,
            garage_spaces=2,
            hoa_fee=0,
        )

        analyzer = PropertyAnalyzer(
            enrichment_merger=EnrichmentMerger(),
            kill_switch_filter=KillSwitchFilter(),
            scorer=PropertyScorer(),
            tier_classifier=TierClassifier(thresholds=PropertyScorer().thresholds),
        )

        result = analyzer.analyze(prop, {})

        # If passed kill switch, should have score and tier
        if result.kill_switch_passed:
            assert result.score_breakdown is not None
            assert result.total_score >= 0
            assert result.tier is not None

    def test_analyze_batch_properties(self):
        """Test analyzing multiple properties in batch."""
        properties = [
            Property(
                street="123 Main St",
                city="Phoenix",
                state="AZ",
                full_address="123 Main St, Phoenix, AZ 85001",
                price_num=500000,
                beds=4,
                baths=2.0,
            ),
            Property(
                street="456 Oak Ave",
                city="Phoenix",
                state="AZ",
                full_address="456 Oak Ave, Phoenix, AZ 85001",
                price_num=450000,
                beds=4,
                baths=2.0,
            ),
        ]

        analyzer = PropertyAnalyzer(
            enrichment_merger=EnrichmentMerger(),
            kill_switch_filter=KillSwitchFilter(),
            scorer=PropertyScorer(),
            tier_classifier=TierClassifier(thresholds=PropertyScorer().thresholds),
        )

        results = analyzer.analyze_batch(properties, {})

        assert len(results) == 2
        for result in results:
            assert result.kill_switch_passed is not None
```

---
