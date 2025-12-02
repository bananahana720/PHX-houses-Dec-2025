"""Tests for reporter layer.

Validates HTML, CSV, and console report generation with proper template rendering.
"""

import csv

import pytest

from phx_home_analysis.domain.entities import Property
from phx_home_analysis.domain.enums import Orientation, RiskLevel, SewerType, SolarStatus, Tier
from phx_home_analysis.domain.value_objects import (
    RenovationEstimate,
    RiskAssessment,
    Score,
    ScoreBreakdown,
)
from phx_home_analysis.reporters import (
    ConsoleReporter,
    CsvReporter,
    HtmlReportGenerator,
    RiskCsvReporter,
)


@pytest.fixture
def sample_properties():
    """Create sample properties for testing."""
    # Property 1: Unicorn tier, passing
    prop1 = Property(
        street="123 Unicorn Lane",
        city="Phoenix",
        state="AZ",
        zip_code="85001",
        full_address="123 Unicorn Lane, Phoenix, AZ 85001",
        price="$475,000",
        price_num=475000,
        beds=4,
        baths=2.5,
        sqft=2400,
        price_per_sqft_raw=197.92,
        lot_sqft=9000,
        year_built=2010,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        hoa_fee=0,
        school_rating=8.5,
        orientation=Orientation.N,
        solar_status=SolarStatus.OWNED,
        has_pool=True,
        roof_age=5,
        hvac_age=8,
        kill_switch_passed=True,
        tier=Tier.UNICORN,
        score_breakdown=ScoreBreakdown(
            location_scores=[
                Score("School District", 8.5, 50),
                Score("Quietness", 8.0, 50),
                Score("Sun Orientation", 10.0, 30),
            ],
            systems_scores=[
                Score("Roof Condition", 7.0, 50),
                Score("HVAC", 6.0, 40),
            ],
            interior_scores=[
                Score("Kitchen Layout", 9.0, 40),
                Score("Master Suite", 8.5, 40),
            ],
        ),
        risk_assessments=[
            RiskAssessment("Noise", RiskLevel.LOW, "Quiet location"),
            RiskAssessment("Infrastructure", RiskLevel.LOW, "Modern construction"),
            RiskAssessment("Solar", RiskLevel.POSITIVE, "Owned solar - value add"),
            RiskAssessment("Cooling Cost", RiskLevel.LOW, "North-facing - best orientation"),
            RiskAssessment("Schools", RiskLevel.LOW, "Strong school district"),
            RiskAssessment("Lot Size", RiskLevel.LOW, "Comfortable lot size"),
        ],
        renovation_estimate=RenovationEstimate(
            roof=5000,
            hvac=3000,
            pool=0,
            other=2000,
        ),
    )

    # Property 2: Contender tier, passing
    prop2 = Property(
        street="456 Contender Ave",
        city="Scottsdale",
        state="AZ",
        zip_code="85250",
        full_address="456 Contender Ave, Scottsdale, AZ 85250",
        price="$525,000",
        price_num=525000,
        beds=4,
        baths=3.0,
        sqft=2600,
        price_per_sqft_raw=201.92,
        lot_sqft=8500,
        year_built=2005,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        hoa_fee=0,
        school_rating=7.0,
        orientation=Orientation.E,
        solar_status=SolarStatus.NONE,
        has_pool=False,
        roof_age=12,
        hvac_age=10,
        kill_switch_passed=True,
        tier=Tier.CONTENDER,
        score_breakdown=ScoreBreakdown(
            location_scores=[
                Score("School District", 7.0, 50),
                Score("Quietness", 6.0, 50),
            ],
            systems_scores=[
                Score("Roof Condition", 5.0, 50),
                Score("HVAC", 5.0, 40),
            ],
            interior_scores=[
                Score("Kitchen Layout", 7.0, 40),
                Score("Master Suite", 7.5, 40),
            ],
        ),
        risk_assessments=[
            RiskAssessment("Noise", RiskLevel.MEDIUM, "Some highway noise possible"),
            RiskAssessment("Infrastructure", RiskLevel.LOW, "Modern construction"),
            RiskAssessment("Solar", RiskLevel.LOW, "No solar complications"),
            RiskAssessment("Cooling Cost", RiskLevel.LOW, "East-facing - good"),
            RiskAssessment("Schools", RiskLevel.MEDIUM, "Average schools"),
            RiskAssessment("Lot Size", RiskLevel.LOW, "Comfortable lot size"),
        ],
        renovation_estimate=RenovationEstimate(
            roof=10000,
            hvac=8000,
            pool=0,
            other=5000,
        ),
    )

    # Property 3: Failed tier
    prop3 = Property(
        street="789 Failed St",
        city="Tempe",
        state="AZ",
        zip_code="85281",
        full_address="789 Failed St, Tempe, AZ 85281",
        price="$395,000",
        price_num=395000,
        beds=3,  # Fails beds >= 4
        baths=2.0,
        sqft=1800,
        price_per_sqft_raw=219.44,
        lot_sqft=6500,  # Fails lot size >= 7000
        year_built=2015,
        garage_spaces=2,
        sewer_type=SewerType.CITY,
        hoa_fee=150,  # Fails HOA == 0
        kill_switch_passed=False,
        kill_switch_failures=[
            "Beds: 3 < 4",
            "Lot size: 6500 < 7000",
            "HOA fee: $150 > $0",
        ],
        tier=Tier.FAILED,
    )

    return [prop1, prop2, prop3]


class TestCsvReporter:
    """Tests for CsvReporter."""

    def test_generate_default_columns(self, sample_properties, tmp_path):
        """Test CSV generation with default columns."""
        output_path = tmp_path / "test_output.csv"
        reporter = CsvReporter()

        reporter.generate(sample_properties, output_path)

        assert output_path.exists()

        # Read and validate CSV
        with open(output_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert "rank" in rows[0]
        assert "full_address" in rows[0]
        assert "total_score" in rows[0]

        # Verify ranking (Unicorn > Contender > Failed)
        assert rows[0]["full_address"] == "123 Unicorn Lane, Phoenix, AZ 85001"
        assert rows[1]["full_address"] == "456 Contender Ave, Scottsdale, AZ 85250"
        assert rows[2]["full_address"] == "789 Failed St, Tempe, AZ 85281"

    def test_generate_extended_columns(self, sample_properties, tmp_path):
        """Test CSV generation with extended columns."""
        output_path = tmp_path / "test_extended.csv"
        reporter = CsvReporter(include_extended=True)

        reporter.generate(sample_properties, output_path)

        # Read and validate
        with open(output_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert "lot_sqft" in rows[0]
        assert "year_built" in rows[0]
        assert "solar_status" in rows[0]

        # Validate extended data
        assert rows[0]["lot_sqft"] == "9000"
        assert rows[0]["year_built"] == "2010"
        assert rows[0]["solar_status"] == "owned"

    def test_generate_custom_columns(self, sample_properties, tmp_path):
        """Test CSV generation with custom column selection."""
        output_path = tmp_path / "test_custom.csv"
        custom_columns = ["rank", "full_address", "price", "tier"]
        reporter = CsvReporter(columns=custom_columns)

        reporter.generate(sample_properties, output_path)

        # Read and validate
        with open(output_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Should only have custom columns
        assert set(rows[0].keys()) == set(custom_columns)

    def test_empty_properties_raises_error(self, tmp_path):
        """Test that empty properties list raises ValueError."""
        output_path = tmp_path / "test_empty.csv"
        reporter = CsvReporter()

        with pytest.raises(ValueError, match="empty properties list"):
            reporter.generate([], output_path)


class TestRiskCsvReporter:
    """Tests for RiskCsvReporter."""

    def test_generate_risk_csv(self, sample_properties, tmp_path):
        """Test risk assessment CSV generation."""
        output_path = tmp_path / "test_risk.csv"
        reporter = RiskCsvReporter()

        reporter.generate(sample_properties, output_path)

        assert output_path.exists()

        # Read and validate
        with open(output_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3

        # Check risk columns exist
        assert "noise_risk" in rows[0]
        assert "noise_desc" in rows[0]
        assert "overall_risk_score" in rows[0]

        # Validate risk data for first property
        assert rows[0]["noise_risk"] == "LOW"
        assert rows[0]["solar_risk"] == "POSITIVE"


class TestHtmlReportGenerator:
    """Tests for HtmlReportGenerator."""

    def test_initialization_default_template_dir(self):
        """Test reporter initializes with default template directory."""
        reporter = HtmlReportGenerator()

        assert reporter.template_dir.exists()
        assert reporter.template_dir.name == "templates"

    def test_initialization_custom_template_dir(self, tmp_path):
        """Test reporter initializes with custom template directory."""
        custom_dir = tmp_path / "custom_templates"
        custom_dir.mkdir()

        reporter = HtmlReportGenerator(template_dir=custom_dir)

        assert reporter.template_dir == custom_dir

    def test_initialization_invalid_template_dir(self, tmp_path):
        """Test reporter raises error for non-existent template directory."""
        invalid_path = tmp_path / "nonexistent" / "path"
        with pytest.raises(ValueError, match="Template directory not found"):
            HtmlReportGenerator(template_dir=invalid_path)

    def test_generate_risk_report(self, sample_properties, tmp_path):
        """Test risk report HTML generation."""
        output_path = tmp_path / "risk_report.html"
        reporter = HtmlReportGenerator()

        reporter.generate_risk_report(sample_properties, output_path)

        assert output_path.exists()

        # Validate HTML content
        html_content = output_path.read_text(encoding="utf-8")
        assert "Due Diligence Risk Report" in html_content
        assert "123 Unicorn Lane" in html_content
        assert "456 Contender Ave" in html_content

        # Check for risk badges
        assert "risk-badge" in html_content or "LOW" in html_content

    def test_generate_renovation_report(self, sample_properties, tmp_path):
        """Test renovation report HTML generation."""
        output_path = tmp_path / "renovation_report.html"
        reporter = HtmlReportGenerator()

        reporter.generate_renovation_report(sample_properties, output_path)

        assert output_path.exists()

        # Validate HTML content
        html_content = output_path.read_text(encoding="utf-8")
        assert "Renovation Gap Analysis" in html_content
        assert "123 Unicorn Lane" in html_content

        # Check for statistics
        assert "Total Properties" in html_content
        assert "Average Renovation" in html_content

    def test_empty_properties_raises_error(self, tmp_path):
        """Test that empty properties list raises ValueError."""
        output_path = tmp_path / "test.html"
        reporter = HtmlReportGenerator()

        with pytest.raises(ValueError, match="empty properties list"):
            reporter.generate_risk_report([], output_path)


class TestConsoleReporter:
    """Tests for ConsoleReporter."""

    def test_initialization_default(self):
        """Test console reporter initialization with defaults."""
        reporter = ConsoleReporter()

        assert reporter.use_color is True
        assert reporter.compact is False

    def test_initialization_no_color(self):
        """Test console reporter initialization without color."""
        reporter = ConsoleReporter(use_color=False)

        assert reporter.use_color is False

    def test_print_summary(self, sample_properties, capsys):
        """Test summary output prints to console."""
        reporter = ConsoleReporter(use_color=False)

        reporter.print_summary(sample_properties)

        captured = capsys.readouterr()
        assert "Phoenix Home Analysis Summary" in captured.out
        assert "Tier Distribution" in captured.out
        assert "Unicorn" in captured.out
        assert "Contender" in captured.out
        assert "Failed" in captured.out

    def test_print_detailed(self, sample_properties, capsys):
        """Test detailed output prints property information."""
        reporter = ConsoleReporter(use_color=False)

        reporter.print_detailed(sample_properties)

        captured = capsys.readouterr()
        assert "Detailed Property Analysis" in captured.out
        assert "123 Unicorn Lane" in captured.out
        assert "456 Contender Ave" in captured.out

    def test_generate_calls_print_summary(self, sample_properties, capsys, tmp_path):
        """Test generate method calls print_summary."""
        reporter = ConsoleReporter(use_color=False)
        output_path = tmp_path / "ignored.txt"

        reporter.generate(sample_properties, output_path)

        captured = capsys.readouterr()
        assert "Phoenix Home Analysis Summary" in captured.out

    def test_empty_properties_raises_error(self, tmp_path):
        """Test that empty properties list raises ValueError."""
        reporter = ConsoleReporter()
        output_path = tmp_path / "ignored.txt"

        with pytest.raises(ValueError, match="empty properties list"):
            reporter.generate([], output_path)
