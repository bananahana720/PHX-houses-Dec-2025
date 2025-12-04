"""Unit tests for deal sheet generation.

Tests:
- Score percentage calculations
- Tier badge assignment
- Tour checklist generation from warnings
- Image gallery path handling
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


class TestScorePercentageCalculations:
    """Test that score percentages are calculated correctly."""

    def test_location_score_percentage(self):
        """Location score should be calculated as score/250 * 100."""
        # 250 points max for Location (Section A)
        score = 175.0
        expected_percentage = (175.0 / 250.0) * 100
        assert expected_percentage == pytest.approx(70.0)

    def test_systems_score_percentage(self):
        """Systems score should be calculated as score/175 * 100."""
        # 175 points max for Systems (Section B)
        score = 140.0
        expected_percentage = (140.0 / 175.0) * 100
        assert expected_percentage == pytest.approx(80.0)

    def test_interior_score_percentage(self):
        """Interior score should be calculated as score/180 * 100."""
        # 180 points max for Interior (Section C)
        score = 126.0
        expected_percentage = (126.0 / 180.0) * 100
        assert expected_percentage == pytest.approx(70.0)

    def test_total_score_percentage(self):
        """Total score should be calculated as score/605 * 100."""
        # 605 points max total (250 + 175 + 180)
        score = 484.0  # Unicorn threshold (80%)
        expected_percentage = (484.0 / 605.0) * 100
        assert expected_percentage == pytest.approx(80.0, rel=0.01)


class TestTierBadgeAssignment:
    """Test tier classification based on score."""

    def test_unicorn_tier(self):
        """Score >= 484 (80%+) should be Unicorn."""
        from src.phx_home_analysis.config.scoring_weights import TierThresholds

        thresholds = TierThresholds()
        assert thresholds.classify(484) == "Unicorn"
        assert thresholds.classify(605) == "Unicorn"

    def test_contender_tier(self):
        """Score 363-483 (60-80%) should be Contender."""
        from src.phx_home_analysis.config.scoring_weights import TierThresholds

        thresholds = TierThresholds()
        assert thresholds.classify(363) == "Contender"
        assert thresholds.classify(400) == "Contender"
        assert thresholds.classify(483) == "Contender"

    def test_pass_tier(self):
        """Score < 363 (<60%) should be Pass."""
        from src.phx_home_analysis.config.scoring_weights import TierThresholds

        thresholds = TierThresholds()
        assert thresholds.classify(362) == "Pass"
        assert thresholds.classify(200) == "Pass"
        assert thresholds.classify(0) == "Pass"


class TestTourChecklistGeneration:
    """Test tour checklist generation from kill-switch warnings and property data."""

    def test_generate_checklist_from_failed_kill_switch(self):
        """Failed kill-switch should generate checklist item."""
        from scripts.deal_sheets.renderer import generate_tour_checklist

        kill_switches = {
            "HOA": {
                "passed": False,
                "label": "HARD FAIL",
                "description": "$200/mo",
                "is_hard": True,
                "severity_weight": 0,
            },
            "_summary": {"verdict": "FAIL", "severity_score": 0},
        }
        row_dict = {"year_built": 2020, "has_pool": False}

        checklist = generate_tour_checklist(kill_switches, row_dict)

        # Should have at least one item for the HOA failure
        hoa_items = [i for i in checklist if "HOA" in i["title"]]
        assert len(hoa_items) == 1
        assert hoa_items[0]["severity"] == "fail"
        assert hoa_items[0]["priority"] == "high"

    def test_generate_checklist_from_unknown_status(self):
        """Unknown status should generate checklist item with warning."""
        from scripts.deal_sheets.renderer import generate_tour_checklist

        kill_switches = {
            "Sewer": {
                "passed": True,
                "label": "UNKNOWN",
                "description": "Unknown",
                "is_hard": True,
                "severity_weight": 0,
            },
            "_summary": {"verdict": "PASS", "severity_score": 0},
        }
        row_dict = {"year_built": 2020, "has_pool": False}

        checklist = generate_tour_checklist(kill_switches, row_dict)

        sewer_items = [i for i in checklist if "Sewer" in i["title"]]
        assert len(sewer_items) == 1
        assert sewer_items[0]["severity"] == "warning"

    def test_generate_checklist_for_old_home(self):
        """Home > 15 years should generate HVAC inspection item."""
        from scripts.deal_sheets.renderer import generate_tour_checklist

        kill_switches = {"_summary": {"verdict": "PASS", "severity_score": 0}}
        row_dict = {"year_built": 2000, "has_pool": False}

        checklist = generate_tour_checklist(kill_switches, row_dict)

        hvac_items = [i for i in checklist if "HVAC" in i["title"]]
        assert len(hvac_items) == 1
        assert "HVAC" in hvac_items[0]["title"]

    def test_generate_checklist_for_very_old_home(self):
        """Home > 20 years should generate HVAC + roof items."""
        from scripts.deal_sheets.renderer import generate_tour_checklist

        kill_switches = {"_summary": {"verdict": "PASS", "severity_score": 0}}
        row_dict = {"year_built": 1995, "has_pool": False}

        checklist = generate_tour_checklist(kill_switches, row_dict)

        hvac_items = [i for i in checklist if "HVAC" in i["title"]]
        roof_items = [i for i in checklist if "Roof" in i["title"]]
        assert len(hvac_items) == 1
        assert len(roof_items) == 1

    def test_generate_checklist_for_pool(self):
        """Pool property should generate pool equipment check."""
        from scripts.deal_sheets.renderer import generate_tour_checklist

        kill_switches = {"_summary": {"verdict": "PASS", "severity_score": 0}}
        row_dict = {"year_built": 2020, "has_pool": True, "pool_equipment_age": 10}

        checklist = generate_tour_checklist(kill_switches, row_dict)

        pool_items = [i for i in checklist if "Pool" in i["title"]]
        assert len(pool_items) == 1

    def test_generate_checklist_for_solar_lease(self):
        """Solar lease should generate high priority warning."""
        from scripts.deal_sheets.renderer import generate_tour_checklist

        kill_switches = {"_summary": {"verdict": "PASS", "severity_score": 0}}
        row_dict = {"year_built": 2020, "has_pool": False, "solar_status": "Leased"}

        checklist = generate_tour_checklist(kill_switches, row_dict)

        solar_items = [i for i in checklist if "Solar" in i["title"]]
        assert len(solar_items) == 1
        assert solar_items[0]["priority"] == "high"
        assert solar_items[0]["severity"] == "fail"


class TestImageGallery:
    """Test image gallery functionality."""

    def test_get_property_images_no_lookup(self):
        """Should return empty list when lookup file doesn't exist."""
        from scripts.deal_sheets.renderer import (
            _load_address_folder_lookup,
            get_property_images,
        )

        # Clear lru_cache before test
        _load_address_folder_lookup.cache_clear()

        with patch.object(Path, "exists", return_value=False):
            images = get_property_images("123 Main St, Phoenix, AZ 85001")
            assert images == []

    def test_get_property_images_address_not_found(self):
        """Should return empty list when address not in lookup."""
        from scripts.deal_sheets.renderer import (
            _load_address_folder_lookup,
            get_property_images,
        )

        # Clear lru_cache before test
        _load_address_folder_lookup.cache_clear()

        # Mock the lookup to have a different address
        with patch.object(Path, "exists", return_value=True):
            with patch(
                "builtins.open",
                create=True,
            ) as mock_open:
                import json

                mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(
                    {
                        "mappings": {
                            "Other Address": {
                                "folder": "abc123",
                                "path": "data/property_images/processed/abc123/",
                            }
                        }
                    }
                )

                images = get_property_images("123 Main St, Phoenix, AZ 85001")
                assert images == []

    def test_inspection_tip_hoa(self):
        """Should return correct inspection tip for HOA."""
        from scripts.deal_sheets.renderer import _get_inspection_tip

        tip = _get_inspection_tip("HOA")
        assert "HOA documents" in tip
        assert "CC&Rs" in tip

    def test_inspection_tip_unknown(self):
        """Should return generic tip for unknown criterion."""
        from scripts.deal_sheets.renderer import _get_inspection_tip

        tip = _get_inspection_tip("UnknownCriterion")
        assert "Verify with seller" in tip


class TestScoringWeightsConstants:
    """Test that scoring weights match expected values."""

    def test_section_a_max(self):
        """Section A (Location) should total 250 points."""
        from src.phx_home_analysis.config.scoring_weights import ScoringWeights

        weights = ScoringWeights()
        assert weights.section_a_max == 250

    def test_section_b_max(self):
        """Section B (Systems) should total 175 points."""
        from src.phx_home_analysis.config.scoring_weights import ScoringWeights

        weights = ScoringWeights()
        assert weights.section_b_max == 175

    def test_section_c_max(self):
        """Section C (Interior) should total 180 points."""
        from src.phx_home_analysis.config.scoring_weights import ScoringWeights

        weights = ScoringWeights()
        assert weights.section_c_max == 180

    def test_total_possible_score(self):
        """Total possible score should be 605 (250 + 175 + 180)."""
        from src.phx_home_analysis.config.scoring_weights import ScoringWeights

        weights = ScoringWeights()
        assert weights.total_possible_score == 605


class TestGenerateDealSheet:
    """Test generate_deal_sheet function."""

    def test_generates_complete_html(self, tmp_path):
        """Test that generate_deal_sheet returns valid HTML."""
        import pandas as pd

        from scripts.deal_sheets.renderer import generate_deal_sheet

        sample_row = pd.Series(
            {
                "full_address": "123 Test St, Phoenix, AZ 85001",
                "rank": 1,
                "price_num": 450000,
                "price": 450000,
                "beds": 4,
                "baths": 2,
                "sqft": 2000,
                "lot_sqft": 8000,
                "year_built": 2010,
                "garage_spaces": 2,
                "hoa_fee": 0,
                "total_score": 480,
                "tier": "Contender",
                "section_a_score": 180,
                "section_b_score": 150,
                "section_c_score": 150,
                "score_location": 180,
                "score_lot_systems": 150,
                "score_interior": 150,
                "kill_switch_status": "PASS",
                "sewer_type": "city",
                "commute_minutes": 25,
                "school_rating": 7.5,
                "distance_to_grocery_miles": 1.2,
                "tax_annual": 3500,
            }
        )

        # Generate deal sheet to temp directory
        filename = generate_deal_sheet(sample_row, tmp_path)

        # Verify file was created
        output_file = tmp_path / filename
        assert output_file.exists()

        # Read and verify HTML content
        html_output = output_file.read_text(encoding="utf-8")

        assert "<html" in html_output
        assert "123 Test St" in html_output
        assert "$450,000" in html_output or "450,000" in html_output
        assert "480" in html_output
        assert "Contender" in html_output

    def test_handles_missing_fields_gracefully(self, tmp_path):
        """Test that generate_deal_sheet handles missing data without crashing."""
        import pandas as pd

        from scripts.deal_sheets.renderer import generate_deal_sheet

        # Minimal row with many missing fields but includes required template fields
        sample_row = pd.Series(
            {
                "full_address": "456 Minimal Ave, Scottsdale, AZ 85251",
                "rank": 2,
                "price_num": 300000,
                "beds": 3,
                "baths": 2,
                "sqft": 1500,
                "total_score": 300,
                "tier": "Pass",
                "kill_switch_status": "PASS",
                "commute_minutes": 0,
                "school_rating": 0,
                "distance_to_grocery_miles": 0,
                "tax_annual": 0,
            }
        )

        # Should not raise an exception
        filename = generate_deal_sheet(sample_row, tmp_path)

        # Verify file was created
        output_file = tmp_path / filename
        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestGenerateIndex:
    """Test generate_index function."""

    def test_generates_index_with_stats(self, tmp_path):
        """Test that generate_index returns HTML with stats."""
        import pandas as pd

        from scripts.deal_sheets.renderer import generate_index

        sample_df = pd.DataFrame(
            [
                {
                    "full_address": "123 Test St, Phoenix, AZ 85001",
                    "rank": 1,
                    "total_score": 500,
                    "tier": "Unicorn",
                    "kill_switch_status": "PASS",
                    "price_num": 500000,
                },
                {
                    "full_address": "456 Other Ave, Scottsdale, AZ 85251",
                    "rank": 2,
                    "total_score": 400,
                    "tier": "Contender",
                    "kill_switch_status": "PASS",
                    "price_num": 400000,
                },
            ]
        )

        generate_index(sample_df, tmp_path)

        # Verify index.html was created
        index_file = tmp_path / "index.html"
        assert index_file.exists()

        # Verify data.json was created
        json_file = tmp_path / "data.json"
        assert json_file.exists()

        # Read and verify HTML content
        html_output = index_file.read_text(encoding="utf-8")
        assert "<html" in html_output

        # Read and verify JSON content
        import json

        json_output = json.loads(json_file.read_text(encoding="utf-8"))
        assert "metadata" in json_output
        assert "properties" in json_output
        assert json_output["metadata"]["total_properties"] == 2
        assert len(json_output["properties"]) == 2

    def test_handles_single_property_dataframe(self, tmp_path):
        """Test that generate_index handles a single property dataframe."""
        import pandas as pd

        from scripts.deal_sheets.renderer import generate_index

        single_df = pd.DataFrame(
            [
                {
                    "full_address": "789 Single St, Phoenix, AZ 85001",
                    "rank": 1,
                    "total_score": 350,
                    "tier": "Pass",
                    "kill_switch_status": "PASS",
                    "price_num": 350000,
                }
            ]
        )

        # Should not raise an exception
        generate_index(single_df, tmp_path)

        # Verify files were created
        assert (tmp_path / "index.html").exists()
        assert (tmp_path / "data.json").exists()

        # Verify JSON content
        import json

        json_output = json.loads((tmp_path / "data.json").read_text(encoding="utf-8"))
        assert json_output["metadata"]["total_properties"] == 1


class TestXssSecurity:
    """Test XSS protection in checklist generation."""

    def test_escape_html_escapes_special_characters(self):
        """Test that _escape_html properly escapes HTML special characters."""
        from scripts.deal_sheets.renderer import _escape_html

        # Test various special characters
        # Note: html.escape() escapes single quotes as &#x27;
        result = _escape_html("<script>alert('XSS')</script>")
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result
        assert "<script>" not in result
        assert _escape_html("a & b") == "a &amp; b"
        assert _escape_html('"quoted"') == "&quot;quoted&quot;"
        assert _escape_html("normal text") == "normal text"

    def test_checklist_escapes_malicious_input(self):
        """Test that malicious input in kill_switches is escaped."""
        from scripts.deal_sheets.renderer import generate_tour_checklist

        # Simulate malicious input in kill-switch data
        kill_switches = {
            "<script>alert('XSS')</script>": {
                "passed": False,
                "label": "FAIL",
                "description": "<img src=x onerror=alert('XSS')>",
                "is_hard": False,
                "severity_weight": 1.0,
            },
            "_summary": {"verdict": "FAIL", "severity_score": 1.0},
        }
        row_dict = {"year_built": 2020, "has_pool": False}

        checklist = generate_tour_checklist(kill_switches, row_dict)

        # Verify the malicious content is escaped
        malicious_item = checklist[0]
        assert "<script>" not in malicious_item["title"]
        assert "&lt;script&gt;" in malicious_item["title"]
        assert "<img" not in malicious_item["detail"]
        assert "&lt;img" in malicious_item["detail"]


class TestDynamicYearCalculation:
    """Test that year calculations use current year dynamically."""

    def test_age_calculation_uses_current_year(self):
        """Test that home age is calculated from current year, not hardcoded."""
        from datetime import datetime

        from scripts.deal_sheets.renderer import generate_tour_checklist

        current_year = datetime.now().year
        test_year = current_year - 25  # 25 years old home

        kill_switches = {"_summary": {"verdict": "PASS", "severity_score": 0}}
        row_dict = {"year_built": test_year, "has_pool": False}

        checklist = generate_tour_checklist(kill_switches, row_dict)

        # Should generate HVAC and Roof items for 25-year-old home
        hvac_items = [i for i in checklist if "HVAC" in i["title"]]
        roof_items = [i for i in checklist if "Roof" in i["title"]]

        assert len(hvac_items) == 1
        assert len(roof_items) == 1

        # Verify the age is correct (25 years)
        assert "25 years old" in hvac_items[0]["detail"]
        assert "25 years old" in roof_items[0]["detail"]
