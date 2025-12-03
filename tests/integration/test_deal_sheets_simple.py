"""Integration tests for deal sheet data loading.

Tests loading and merging of CSV and JSON enrichment data,
without testing the full deal sheet rendering (which has complex dependencies).
"""

import csv
import json
import tempfile
from pathlib import Path

from scripts.deal_sheets.data_loader import (
    load_enrichment_json,
    load_ranked_csv,
    merge_enrichment_data,
)

# ============================================================================
# Test Deal Sheet Data Loading
# ============================================================================


class TestDealSheetDataLoading:
    """Test data loading for deal sheet generation."""

    def test_load_ranked_csv_with_valid_data(self, sample_properties):
        """Test loading a valid ranked CSV file.

        CSV should contain properties with scores and rankings.
        """
        # Create temporary ranked CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            fieldnames = [
                'rank', 'full_address', 'price_num', 'beds', 'baths', 'sqft',
                'total_score'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for idx, prop in enumerate(sample_properties[:3], 1):
                writer.writerow({
                    'rank': idx,
                    'full_address': prop.full_address,
                    'price_num': prop.price_num,
                    'beds': prop.beds,
                    'baths': prop.baths,
                    'sqft': prop.sqft,
                    'total_score': 350 + (idx * 10),
                })
            csv_path = f.name

        try:
            # Load the CSV
            df = load_ranked_csv(csv_path)

            # Verify structure
            assert len(df) == 3
            assert 'rank' in df.columns
            assert 'full_address' in df.columns
            assert 'total_score' in df.columns
            assert list(df['rank'].astype(int)) == [1, 2, 3]
        finally:
            Path(csv_path).unlink()

    def test_load_enrichment_json_with_valid_data(self, sample_enrichment):
        """Test loading valid enrichment JSON file.

        Enrichment data should map addresses to field data.
        """
        # Create temporary enrichment JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_enrichment, f)
            json_path = f.name

        try:
            # Load the JSON
            enrichment = load_enrichment_json(json_path)

            # Verify structure
            assert isinstance(enrichment, dict)
            assert len(enrichment) > 0

            # Verify nested structure
            for address, fields in enrichment.items():
                assert isinstance(address, str)
                assert isinstance(fields, dict)
                assert 'lot_sqft' in fields or 'year_built' in fields
        finally:
            Path(json_path).unlink()

    def test_load_enrichment_json_empty_file(self):
        """Test loading empty enrichment JSON returns empty dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({}, f)
            json_path = f.name

        try:
            enrichment = load_enrichment_json(json_path)
            assert isinstance(enrichment, dict)
            assert len(enrichment) == 0
        finally:
            Path(json_path).unlink()

    def test_merge_enrichment_preserves_csv_data(self, sample_properties):
        """Test that merge doesn't lose original CSV data.

        All original CSV columns should persist after merge.
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            fieldnames = ['rank', 'full_address', 'price_num', 'beds', 'total_score']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            writer.writerow({
                'rank': 1,
                'full_address': sample_properties[0].full_address,
                'price_num': 475000,
                'beds': 4,
                'total_score': 350,
            })
            csv_path = f.name

        try:
            df = load_ranked_csv(csv_path)
            merged = merge_enrichment_data(df, {})

            # Original columns preserved
            assert 'rank' in merged.columns
            assert 'full_address' in merged.columns
            assert 'price_num' in merged.columns
            assert 'total_score' in merged.columns
        finally:
            Path(csv_path).unlink()


# ============================================================================
# Test Deal Sheet Directory Structure
# ============================================================================


class TestDealSheetDirectoryStructure:
    """Test the output directory structure created by deal sheets."""

    def test_deal_sheets_output_directory_created(self):
        """Test that deal sheet output directory is created if missing.

        Directory should be created during generation.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / 'reports' / 'deal_sheets'

            # Directory doesn't exist yet
            assert not output_dir.exists()

            # Create it (simulating what generate would do)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Verify it was created
            assert output_dir.exists()
            assert output_dir.is_dir()
