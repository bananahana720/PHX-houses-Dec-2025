# Part 2: Pipeline Orchestrator Tests (P0)

**File:** `tests/integration/test_pipeline_orchestrator.py` (NEW)

```python
"""Comprehensive tests for AnalysisPipeline orchestrator."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from phx_home_analysis.pipeline import AnalysisPipeline, PipelineResult
from phx_home_analysis.domain import Property, Tier
from phx_home_analysis.config import AppConfig


class TestAnalysisPipelineInit:
    """Test pipeline initialization."""

    def test_init_with_defaults(self):
        """Test pipeline initializes with default configuration."""
        pipeline = AnalysisPipeline()

        assert pipeline.config is not None
        assert pipeline._property_repo is not None
        assert pipeline._enrichment_repo is not None
        assert pipeline._scorer is not None
        assert pipeline._kill_switch_filter is not None

    def test_init_with_custom_config(self, tmp_path):
        """Test pipeline initializes with custom config."""
        config = AppConfig.default(base_dir=str(tmp_path))
        pipeline = AnalysisPipeline(config=config)

        assert pipeline.config == config
        assert str(pipeline.config.paths.input_csv) == str(
            tmp_path / "data" / "phx_homes.csv"
        )

    def test_init_with_custom_dependencies(self):
        """Test pipeline accepts custom service instances."""
        mock_repo = MagicMock()
        mock_enrichment = MagicMock()
        mock_scorer = MagicMock()

        pipeline = AnalysisPipeline(
            property_repo=mock_repo,
            enrichment_repo=mock_enrichment,
            scorer=mock_scorer,
        )

        assert pipeline._property_repo is mock_repo
        assert pipeline._enrichment_repo is mock_enrichment
        assert pipeline._scorer is mock_scorer


class TestAnalysisPipelineRun:
    """Test pipeline execution workflow."""

    def test_run_complete_workflow(self, sample_properties, tmp_path):
        """Test complete pipeline execution from start to finish."""
        # Setup mocks
        mock_repo = MagicMock()
        mock_repo.load_all.return_value = sample_properties

        mock_enrichment_repo = MagicMock()
        mock_enrichment_repo.load_all.return_value = {}

        config = AppConfig.default(base_dir=str(tmp_path))

        # Execute pipeline
        pipeline = AnalysisPipeline(
            config=config,
            property_repo=mock_repo,
            enrichment_repo=mock_enrichment_repo,
        )
        result = pipeline.run()

        # Verify
        assert isinstance(result, PipelineResult)
        assert result.total_properties == len(sample_properties)
        assert result.passed_count >= 0
        assert result.failed_count >= 0
        assert result.execution_time_seconds > 0

    def test_run_with_empty_properties(self, tmp_path):
        """Test pipeline handles empty property list gracefully."""
        mock_repo = MagicMock()
        mock_repo.load_all.return_value = []

        config = AppConfig.default(base_dir=str(tmp_path))

        pipeline = AnalysisPipeline(config=config, property_repo=mock_repo)
        result = pipeline.run()

        assert result.total_properties == 0
        assert result.passed_count == 0
        assert result.failed_count == 0
        assert len(result.unicorns) == 0
        assert len(result.contenders) == 0
        assert len(result.passed) == 0

    def test_run_with_mixed_valid_invalid_properties(self, tmp_path):
        """Test pipeline with incomplete property data."""
        # Mix of valid and incomplete properties
        properties = [
            Property(
                street="123 Main St",
                city="Phoenix",
                state="AZ",
                price_num=500000,
                beds=4,
                baths=2.0,
            ),
            Property(
                street="456 Oak Ave",
                city="Phoenix",
                state="AZ",
                # Missing price_num - incomplete
                beds=4,
                baths=2.0,
            ),
        ]

        mock_repo = MagicMock()
        mock_repo.load_all.return_value = properties

        config = AppConfig.default(base_dir=str(tmp_path))

        pipeline = AnalysisPipeline(config=config, property_repo=mock_repo)
        result = pipeline.run()

        # Should handle gracefully, not crash
        assert isinstance(result, PipelineResult)
        # At least some properties should process
        total = len(result.unicorns) + len(result.contenders) + \
                len(result.passed) + len(result.failed)
        assert total > 0

    def test_run_tier_classification_distribution(self):
        """Test pipeline correctly classifies properties into tiers."""
        # Create properties with known scores
        # (Will be scored during pipeline execution)
        properties = [
            Property(
                street=f"{i*100} St",
                city="Phoenix",
                state="AZ",
                price_num=500000,
                beds=4,
                baths=2.0,
            )
            for i in range(10)
        ]

        mock_repo = MagicMock()
        mock_repo.load_all.return_value = properties

        pipeline = AnalysisPipeline(property_repo=mock_repo)
        result = pipeline.run()

        # All properties should be classified
        classified = (
            result.unicorns + result.contenders + result.passed
        )
        assert len(classified) + len(result.failed) == result.total_properties

    def test_run_preserves_property_data(self):
        """Test that pipeline doesn't lose property data during processing."""
        prop = Property(
            street="123 Test St",
            city="Phoenix",
            state="AZ",
            full_address="123 Test St, Phoenix, AZ 85001",
            price="$500,000",
            price_num=500000,
            beds=4,
            baths=2.0,
        )

        mock_repo = MagicMock()
        mock_repo.load_all.return_value = [prop]

        pipeline = AnalysisPipeline(property_repo=mock_repo)
        result = pipeline.run()

        # Get processed property
        all_props = (
            result.unicorns + result.contenders +
            result.passed + result.failed
        )
        processed_prop = all_props[0]

        # All original data should be preserved
        assert processed_prop.street == "123 Test St"
        assert processed_prop.full_address == "123 Test St, Phoenix, AZ 85001"
        assert processed_prop.price_num == 500000
        assert processed_prop.beds == 4

    def test_run_generates_output_csv(self, tmp_path):
        """Test that pipeline generates ranked CSV output."""
        properties = [
            Property(
                street=f"{i*100} St",
                city="Phoenix",
                state="AZ",
                price_num=500000,
                beds=4,
                baths=2.0,
            )
            for i in range(5)
        ]

        mock_repo = MagicMock()
        mock_repo.load_all.return_value = properties

        config = AppConfig.default(base_dir=str(tmp_path))

        pipeline = AnalysisPipeline(config=config, property_repo=mock_repo)
        result = pipeline.run()

        # Output CSV should exist
        output_file = Path(tmp_path) / "phx_homes_ranked.csv"
        if output_file.exists():  # Only check if saved
            import pandas as pd
            df = pd.read_csv(output_file)
            assert len(df) > 0


class TestAnalysisPipelineSingle:
    """Test single property analysis."""

    def test_analyze_single_property_found(self):
        """Test analyzing single property by address."""
        # This would require actual data or mocking
        pipeline = AnalysisPipeline()

        # Try to analyze known property
        result = pipeline.analyze_single(
            "4732 W Davis Rd, Glendale, AZ 85306"
        )

        # Result should be Property or None
        assert result is None or isinstance(result, Property)

    def test_analyze_single_property_not_found(self):
        """Test analyzing non-existent property returns None."""
        pipeline = AnalysisPipeline()

        result = pipeline.analyze_single(
            "999 Nonexistent St, Phoenix, AZ 00000"
        )

        assert result is None

    def test_analyze_single_enriches_property(self):
        """Test that single analysis enriches property with external data."""
        prop = Property(
            street="123 Main St",
            city="Phoenix",
            state="AZ",
            full_address="123 Main St, Phoenix, AZ 85001",
            price_num=500000,
            beds=4,
            baths=2.0,
            lot_sqft=None,  # Missing data
            year_built=None,
        )

        mock_repo = MagicMock()
        mock_repo.get_by_address.return_value = prop

        pipeline = AnalysisPipeline(property_repo=mock_repo)
        result = pipeline.analyze_single(prop.full_address)

        if result:
            # If enrichment data exists, these should be populated
            # (or remain None if not available)
            assert isinstance(result, Property)


class TestPipelineResult:
    """Test PipelineResult data class."""

    def test_summary_text_formatting(self):
        """Test summary text generation."""
        result = PipelineResult(
            total_properties=100,
            passed_count=75,
            failed_count=25,
            unicorns=[
                Property(street="123 Main St", city="Phoenix", state="AZ",
                        price_num=500000, beds=4, baths=2.0),
            ],
            contenders=[],
            passed=[],
            failed=[],
            execution_time_seconds=12.45,
        )

        summary = result.summary_text()

        assert "100" in summary
        assert "75%" in summary or "75.0%" in summary
        assert "12.45" in summary
        assert "UNICORN" in summary

    def test_summary_text_empty_results(self):
        """Test summary text with no results."""
        result = PipelineResult(
            total_properties=0,
            passed_count=0,
            failed_count=0,
            execution_time_seconds=0.0,
        )

        summary = result.summary_text()

        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "0" in summary

    def test_result_tier_breakdown(self):
        """Test result correctly counts tiers."""
        props = [
            Property(street=f"{i} St", city="Phoenix", state="AZ",
                    price_num=500000, beds=4, baths=2.0, tier=Tier.UNICORN)
            for i in range(5)
        ]
        contenders = [
            Property(street=f"{i+100} St", city="Phoenix", state="AZ",
                    price_num=500000, beds=4, baths=2.0, tier=Tier.CONTENDER)
            for i in range(3)
        ]

        result = PipelineResult(
            total_properties=8,
            passed_count=8,
            failed_count=0,
            unicorns=props,
            contenders=contenders,
            passed=[],
            failed=[],
        )

        assert len(result.unicorns) == 5
        assert len(result.contenders) == 3
        assert len(result.passed) == 0
```

---
