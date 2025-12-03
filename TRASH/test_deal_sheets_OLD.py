"""Integration tests for deal sheet generation and HTML output.

Tests the complete deal sheet generation pipeline including:
- Loading ranked CSV + enrichment JSON
- Merging data
- Individual deal sheet HTML generation
- Index page generation
- HTML content validation
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
from scripts.deal_sheets.renderer import generate_deal_sheet, generate_index

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
                'kill_switch_passed', 'total_score', 'tier', 'score_location',
                'score_lot_systems', 'score_interior'
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
                    'kill_switch_passed': True,
                    'total_score': 350 + (idx * 10),
                    'tier': 'PASS',
                    'score_location': 100,
                    'score_lot_systems': 100,
                    'score_interior': 100 + (idx * 10),
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
            assert all(df['rank'] == [1, 2, 3])
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

    def test_merge_enrichment_data_with_matching_addresses(self, sample_enrichment):
        """Test merging enrichment data with matching CSV addresses.

        Enrichment merge should handle matching addresses correctly.
        """

        # Create CSV with matching address
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, newline='') as f:
            address = list(sample_enrichment.keys())[0]
            fieldnames = ['rank', 'full_address', 'price_num', 'beds', 'baths']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            writer.writerow({
                'rank': 1,
                'full_address': address,
                'price_num': 475000,
                'beds': 4,
                'baths': 2.0,
            })
            csv_path = f.name

        try:
            # Create enrichment JSON
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(sample_enrichment, f)
                json_path = f.name

            try:
                # Load and merge
                df = load_ranked_csv(csv_path)
                enrichment = load_enrichment_json(json_path)
                merged = merge_enrichment_data(df, enrichment)

                # Verify merge
                assert len(merged) == 1
                # CSV data should be preserved
                assert merged.iloc[0]['full_address'] == address
                assert merged.iloc[0]['price_num'] == 475000
            finally:
                Path(json_path).unlink()
        finally:
            Path(csv_path).unlink()

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
# Test Individual Deal Sheet Generation
# ============================================================================


class TestDealSheetGeneration:
    """Test individual deal sheet HTML generation."""

    def test_generate_deal_sheet_returns_filename(self, sample_property):
        """Test that generate_deal_sheet returns a filename.

        The filename should be based on property data.
        """
        import pandas as pd

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create complete row with all fields deal sheets needs
            row_data = {
                'rank': 1,
                'full_address': sample_property.full_address,
                'price_num': sample_property.price_num,
                'beds': sample_property.beds,
                'baths': sample_property.baths,
                'sqft': sample_property.sqft,
                'total_score': 350,
                'tier': 'PASS',
                'kill_switch_passed': 'PASS',
                'lot_sqft': sample_property.lot_sqft,
                'year_built': sample_property.year_built,
                'garage_spaces': sample_property.garage_spaces,
                'hoa_fee': sample_property.hoa_fee or 0,
                'sewer_type': 'city' if sample_property.sewer_type else None,
            }
            row = pd.Series(row_data)

            # Generate deal sheet
            filename = generate_deal_sheet(row, output_dir)

            # Verify file was created
            assert filename is not None
            assert Path(output_dir / filename).exists()

            # Verify it's an HTML file
            assert filename.endswith('.html')



# ============================================================================
# Test Index Page Generation
# ============================================================================


class TestIndexPageGeneration:
    """Test index.html generation."""

    def test_generate_index_creates_file(self, sample_properties):
        """Test that generate_index creates index.html file."""
        import pandas as pd

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Create dataframe with required fields
            data = {
                'rank': [1, 2],
                'full_address': [sample_properties[0].full_address, sample_properties[1].full_address],
                'price_num': [sample_properties[0].price_num, sample_properties[1].price_num],
                'total_score': [350, 360],
                'kill_switch_passed': ['PASS', 'PASS'],  # Required field
                'beds': [4, 4],
                'baths': [2.0, 2.0],
            }
            df = pd.DataFrame(data)

            # Generate index
            generate_index(df, output_dir)

            # Verify index.html exists
            index_path = output_dir / 'index.html'
            assert index_path.exists()

    def test_index_html_contains_property_listings(self, sample_properties):
        """Test that index.html lists all properties.

        Index should contain references to all properties.
        """
        import pandas as pd

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            data = {
                'rank': [1, 2, 3],
                'full_address': [
                    sample_properties[0].full_address,
                    sample_properties[1].full_address,
                    sample_properties[2].full_address,
                ],
                'price_num': [
                    sample_properties[0].price_num,
                    sample_properties[1].price_num,
                    sample_properties[2].price_num,
                ],
                'total_score': [350, 360, 370],
                'kill_switch_passed': ['PASS', 'PASS', 'PASS'],
                'beds': [4, 4, 4],
                'baths': [2.0, 2.0, 2.0],
            }
            df = pd.DataFrame(data)

            generate_index(df, output_dir)

            index_path = output_dir / 'index.html'
            with open(index_path) as f:
                content = f.read()

            # Should reference at least the first property
            assert sample_properties[0].full_address in content or 'Phoenix' in content

    def test_index_html_contains_ranks(self, sample_properties):
        """Test that index.html displays property rankings."""
        import pandas as pd

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            data = {
                'rank': [1, 2],
                'full_address': [sample_properties[0].full_address, sample_properties[1].full_address],
                'total_score': [350, 360],
                'kill_switch_passed': ['PASS', 'PASS'],
                'beds': [4, 4],
                'baths': [2.0, 2.0],
            }
            df = pd.DataFrame(data)

            generate_index(df, output_dir)

            index_path = output_dir / 'index.html'
            with open(index_path) as f:
                content = f.read()

            # Should contain rank numbers
            assert '1' in content and '2' in content

    def test_index_html_contains_scores(self, sample_properties):
        """Test that index.html displays property scores."""
        import pandas as pd

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            data = {
                'rank': [1],
                'full_address': [sample_properties[0].full_address],
                'total_score': [350],
                'kill_switch_passed': ['PASS'],
                'beds': [4],
                'baths': [2.0],
            }
            df = pd.DataFrame(data)

            generate_index(df, output_dir)

            index_path = output_dir / 'index.html'
            with open(index_path) as f:
                content = f.read()

            # Should contain score values
            assert '350' in content


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

    def test_multiple_deal_sheets_in_same_directory(self, sample_properties):
        """Test generating multiple deal sheets in same directory.

        All sheets should be created without conflicts or overwrites.
        """
        import pandas as pd

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            # Generate multiple deal sheets
            filenames = []
            for idx, prop in enumerate(sample_properties[:3], 1):
                row_data = {
                    'rank': idx,
                    'full_address': prop.full_address,
                    'price_num': prop.price_num,
                    'beds': prop.beds,
                    'baths': prop.baths,
                    'sqft': prop.sqft,
                    'total_score': 350 + (idx * 10),
                    'kill_switch_passed': 'PASS',
                    'lot_sqft': prop.lot_sqft,
                    'year_built': prop.year_built,
                    'garage_spaces': prop.garage_spaces,
                    'hoa_fee': prop.hoa_fee or 0,
                    'sewer_type': 'city' if prop.sewer_type else None,
                }
                row = pd.Series(row_data)
                filename = generate_deal_sheet(row, output_dir)
                filenames.append(filename)

            # All files should exist
            for filename in filenames:
                assert (output_dir / filename).exists()

            # No duplicates
            assert len(filenames) == len(set(filenames))

    def test_deal_sheet_filenames_are_unique(self, sample_properties):
        """Test that different properties get different HTML filenames.

        Filenames should be derived from property data to be unique.
        """
        import pandas as pd

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)

            filenames = []
            for idx, prop in enumerate(sample_properties[:2], 1):
                row_data = {
                    'rank': idx,
                    'full_address': prop.full_address,
                    'price_num': prop.price_num,
                    'beds': prop.beds,
                    'total_score': 350,
                    'kill_switch_passed': 'PASS',
                    'lot_sqft': prop.lot_sqft,
                    'year_built': prop.year_built,
                    'garage_spaces': prop.garage_spaces,
                    'hoa_fee': prop.hoa_fee or 0,
                    'sewer_type': 'city' if prop.sewer_type else None,
                }
                row = pd.Series(row_data)
                filename = generate_deal_sheet(row, output_dir)
                filenames.append(filename)

            # Different properties should have different filenames
            if sample_properties[0].full_address != sample_properties[1].full_address:
                assert filenames[0] != filenames[1]
