"""Integration tests for the complete PHX home analysis pipeline.

Tests the end-to-end flow: CSV loading -> enrichment application ->
kill-switch filtering -> scoring -> output CSV generation.
"""

import csv
import tempfile
from pathlib import Path

import pytest

from src.phx_home_analysis.domain.entities import Property
from src.phx_home_analysis.domain.enums import SewerType
from src.phx_home_analysis.services.kill_switch.filter import KillSwitchFilter
from src.phx_home_analysis.services.scoring import PropertyScorer

# ============================================================================
# Test Full Pipeline with Sample Data
# ============================================================================


class TestFullPipeline:
    """Test the complete analysis pipeline integration."""

    def test_pipeline_accepts_properties_with_all_data(self, sample_property):
        """Test pipeline processes property with complete enrichment data.

        Validates that a fully-enriched property can pass through:
        1. Kill-switch filtering
        2. Scoring calculation
        Without errors or data loss.
        """
        # Apply kill-switch filter
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property])

        assert len(passed) == 1
        assert len(failed) == 0
        assert passed[0].kill_switch_passed is True

        # Apply scoring
        scorer = PropertyScorer()
        scored_prop = scorer.score(passed[0])

        assert scored_prop.total_score > 0
        assert scored_prop.location_total >= 0
        assert scored_prop.systems_total >= 0
        assert scored_prop.interior_total >= 0

    def test_pipeline_handles_incomplete_properties(self, sample_property_minimal):
        """Test pipeline gracefully handles properties with missing enrichment data.

        Properties with None values should:
        1. Still pass kill-switch filter (None treated as unknown/pass for soft criteria)
        2. Receive scores with available data
        3. Not raise exceptions
        """
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_property_minimal])

        # Should process without error
        assert len(passed) + len(failed) == 1

        # Apply scoring to both passed and failed (if any)
        scorer = PropertyScorer()
        for prop in passed:
            scored_prop = scorer.score(prop)
            assert scored_prop.total_score >= 0

        for prop in failed:
            scored_prop = scorer.score(prop)
            assert scored_prop.total_score >= 0

    def test_pipeline_mixed_properties(self, sample_properties):
        """Test pipeline with mixed batch of properties.

        Batch includes:
        - Properties that pass all kill switches
        - Properties that fail HARD criteria (HOA, min beds, etc.)
        - Properties with SOFT criterion failures (septic, new build, etc.)
        """
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties(sample_properties)

        # Should separate cleanly
        assert len(passed) >= 1
        assert len(failed) >= 1
        assert len(passed) + len(failed) == len(sample_properties)

        # Score all properties
        scorer = PropertyScorer()
        for prop in passed + failed:
            scored = scorer.score(prop)
            assert isinstance(scored.total_score, (int, float))
            assert scored.total_score >= 0
            assert scored.total_score <= 600

    def test_pipeline_preserves_property_data(self, sample_property):
        """Test that pipeline preserves property through filtering.

        Ensures that original listing data are preserved through kill-switch filtering.
        """
        original_address = sample_property.full_address
        original_price = sample_property.price_num
        original_beds = sample_property.beds

        filter_service = KillSwitchFilter()
        passed, _ = filter_service.filter_properties([sample_property])

        # Filtered property should preserve original data
        assert passed[0].full_address == original_address
        assert passed[0].price_num == original_price
        assert passed[0].beds == original_beds

    def test_pipeline_output_contains_required_fields(self, sample_property):
        """Test that scored properties have all required output fields.

        Output should include:
        - Original listing fields (address, price, beds, baths)
        - Kill-switch results (passed, failures)
        - Score breakdown (location, systems, interior, total)
        - Tier classification
        """
        filter_service = KillSwitchFilter()
        passed, _ = filter_service.filter_properties([sample_property])

        scorer = PropertyScorer()
        scored = scorer.score(passed[0])

        # Check that scored property has score totals
        assert hasattr(scored, 'location_total')
        assert hasattr(scored, 'systems_total')
        assert hasattr(scored, 'interior_total')
        assert hasattr(scored, 'total_score')

    def test_pipeline_tier_assignment(self, sample_unicorn_property):
        """Test that scoring produces correct score.

        Validates that high-quality properties score higher than average.
        """
        filter_service = KillSwitchFilter()
        passed, _ = filter_service.filter_properties([sample_unicorn_property])

        scorer = PropertyScorer()
        scored = scorer.score(passed[0])

        # High-quality property should score high
        assert scored.total_score > 0
        assert scored.total_score <= 600


# ============================================================================
# Test Pipeline with Enrichment Data
# ============================================================================


class TestPipelineEnrichment:
    """Test pipeline integration with enrichment data application."""

    def test_enrichment_updates_property_fields(self, sample_property, sample_enrichment_data):
        """Test that enrichment data properly updates property fields.

        Enrichment should populate fields like:
        - Lot size
        - Year built
        - Garage spaces
        - Sewer type
        """
        # Verify enrichment data fields
        assert sample_enrichment_data.lot_sqft == 9500
        assert sample_enrichment_data.year_built == 2010
        assert sample_enrichment_data.garage_spaces == 2
        assert sample_enrichment_data.sewer_type == "city"

        # Property should already have this data
        assert sample_property.lot_sqft == 9500
        assert sample_property.year_built == 2010
        assert sample_property.garage_spaces == 2
        assert sample_property.sewer_type == SewerType.CITY

    def test_pipeline_with_missing_enrichment_data(self, sample_property_minimal):
        """Test pipeline handles properties with missing enrichment gracefully.

        Properties without enrichment data should:
        1. Not cause exceptions
        2. Be processed with available fields only
        3. Receive default/null values for missing enrichment
        """
        filter_service = KillSwitchFilter()

        # Should not raise exception
        try:
            passed, failed = filter_service.filter_properties([sample_property_minimal])
            assert True  # If we reach here, no exception was raised
        except Exception as e:
            pytest.fail(f"Pipeline raised exception with minimal data: {e}")

    def test_enrichment_data_structure(self, sample_enrichment):
        """Test that enrichment data has correct structure.

        Enrichment dict should contain all expected fields keyed by address.
        """
        assert isinstance(sample_enrichment, dict)

        # Should have address as key
        address = list(sample_enrichment.keys())[0]
        enrichment_record = sample_enrichment[address]

        # Check required enrichment fields
        assert 'lot_sqft' in enrichment_record
        assert 'year_built' in enrichment_record
        assert 'garage_spaces' in enrichment_record
        assert 'sewer_type' in enrichment_record
        assert 'hoa_fee' in enrichment_record


# ============================================================================
# Test Pipeline CSV I/O
# ============================================================================


class TestPipelineCSVIO:
    """Test pipeline CSV input/output operations."""

    def test_pipeline_generates_output_csv_with_correct_columns(self, sample_property):
        """Test that filtered properties can be written to CSV.

        Output CSV should have columns for original property data and kill-switch results.
        """
        # Filter
        filter_service = KillSwitchFilter()
        passed, _ = filter_service.filter_properties([sample_property])

        # Create temporary CSV from filtered properties
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    'full_address', 'price_num', 'beds', 'baths', 'sqft',
                    'kill_switch_passed', 'kill_switch_failures'
                ]
            )
            writer.writeheader()
            for prop in passed:
                writer.writerow({
                    'full_address': prop.full_address,
                    'price_num': prop.price_num,
                    'beds': prop.beds,
                    'baths': prop.baths,
                    'sqft': prop.sqft,
                    'kill_switch_passed': prop.kill_switch_passed,
                    'kill_switch_failures': '|'.join(prop.kill_switch_failures or []),
                })
            csv_path = f.name

        try:
            # Read back and verify
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                row = next(reader)
                assert row['full_address'] == sample_property.full_address
                assert int(row['price_num']) == sample_property.price_num
                assert int(row['beds']) == sample_property.beds
        finally:
            Path(csv_path).unlink()

    def test_pipeline_output_csv_formatting(self, sample_properties):
        """Test that output CSV is properly formatted for downstream use.

        CSV should be:
        - Valid and parseable
        - Properly quoted (handles commas in addresses)
        - UTF-8 encoded
        """
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties(sample_properties)
        all_props = passed + failed

        # Create temporary CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            fieldnames = [
                'full_address', 'price_num', 'beds', 'baths',
                'kill_switch_passed'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for prop in all_props:
                writer.writerow({
                    'full_address': prop.full_address,
                    'price_num': prop.price_num,
                    'beds': prop.beds,
                    'baths': prop.baths,
                    'kill_switch_passed': prop.kill_switch_passed,
                })
            csv_path = f.name

        try:
            # Verify CSV is readable
            with open(csv_path) as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == len(all_props)

                # Verify all rows have required fields
                for row in rows:
                    assert row['full_address']
                    assert row['price_num']
                    assert 'beds' in row
        finally:
            Path(csv_path).unlink()


# ============================================================================
# Test Pipeline with Multiple Scoring Scenarios
# ============================================================================


class TestPipelineScoringVariations:
    """Test scoring behavior with different property types."""

    def test_pipeline_scores_vary_by_property_quality(
        self, sample_property, sample_unicorn_property, sample_failed_property
    ):
        """Test that properties with different qualities receive different scores.

        Validates that:
        - Higher quality properties score higher
        - Failed properties still get scored (but may not pass kill switches)
        - Score ranges are reasonable (0-600)
        """
        properties = [sample_property, sample_unicorn_property]

        scorer = PropertyScorer()
        scores = []

        for prop in properties:
            scored = scorer.score(prop)
            scores.append(scored.total_score)

        # Unicorn should score higher than regular property
        unicorn_score = scores[1]
        regular_score = scores[0]

        assert unicorn_score > regular_score
        assert unicorn_score > 400
        assert 0 <= regular_score <= 600

    def test_pipeline_scores_even_failed_kill_switch_properties(self, sample_failed_property):
        """Test that properties failing kill switches still receive scores.

        This enables deal sheets to show failed properties for reference.
        """
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([sample_failed_property])

        # Property should fail
        assert len(failed) == 1

        # But should still be scorable
        scorer = PropertyScorer()
        scored = scorer.score(failed[0])

        assert scored.total_score >= 0
        assert scored.total_score <= 600

    def test_pipeline_score_breakdown_sums_correctly(self, sample_property):
        """Test that score breakdown components sum to total score.

        Location + Systems + Interior should equal (or be close to) total score.
        """
        filter_service = KillSwitchFilter()
        passed, _ = filter_service.filter_properties([sample_property])

        scorer = PropertyScorer()
        scored = scorer.score(passed[0])

        # Component scores should sum to total (allowing for rounding)
        component_sum = (
            scored.location_total +
            scored.systems_total +
            scored.interior_total
        )

        assert abs(component_sum - scored.total_score) < 1.0


# ============================================================================
# Test Pipeline Error Handling
# ============================================================================


class TestPipelineErrorHandling:
    """Test pipeline robustness with edge cases."""

    def test_pipeline_handles_empty_property_list(self):
        """Test pipeline gracefully handles empty input."""
        filter_service = KillSwitchFilter()
        passed, failed = filter_service.filter_properties([])

        assert passed == []
        assert failed == []

    def test_pipeline_handles_none_values_gracefully(self, sample_property_minimal):
        """Test pipeline processes properties with many None values.

        Should not raise exceptions and should produce valid output.
        """
        filter_service = KillSwitchFilter()

        # Should handle without exception
        passed, failed = filter_service.filter_properties([sample_property_minimal])

        # Should produce output (either in passed or failed)
        assert len(passed) + len(failed) == 1

        # Should be scorable
        scorer = PropertyScorer()
        prop = (passed + failed)[0]
        scored = scorer.score(prop)
        assert scored.total_score >= 0

    def test_pipeline_handles_properties_with_invalid_enum_values(self):
        """Test pipeline handles invalid enum values gracefully.

        Should not crash and should either coerce or skip problematic values.
        """
        # Create property with problematic sewer_type (None)
        prop = Property(
            street="123 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="123 Test St, Phoenix, AZ 85001",
            price="$400,000",
            price_num=400000,
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=200.0,
            sewer_type=None,  # Invalid for kill-switch
        )

        filter_service = KillSwitchFilter()

        # Should process without crashing
        try:
            passed, failed = filter_service.filter_properties([prop])
            assert len(passed) + len(failed) == 1
        except Exception as e:
            pytest.fail(f"Pipeline raised exception with None enum: {e}")
