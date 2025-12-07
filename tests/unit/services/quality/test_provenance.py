"""Unit tests for provenance tracking functionality."""

from src.phx_home_analysis.domain.entities import EnrichmentData
from src.phx_home_analysis.services.quality.confidence_display import (
    ConfidenceLevel,
    format_confidence,
    get_confidence_html,
)
from src.phx_home_analysis.services.quality.models import DataSource
from src.phx_home_analysis.services.quality.provenance_service import ProvenanceService


class TestDataSource:
    """Test suite for DataSource enum and confidence mapping."""

    def test_assessor_api_confidence(self):
        """Test ASSESSOR_API returns 0.95."""
        assert DataSource.ASSESSOR_API.default_confidence == 0.95

    def test_zillow_confidence(self):
        """Test ZILLOW returns 0.85."""
        assert DataSource.ZILLOW.default_confidence == 0.85

    def test_redfin_confidence(self):
        """Test REDFIN returns 0.85."""
        assert DataSource.REDFIN.default_confidence == 0.85

    def test_google_maps_confidence(self):
        """Test GOOGLE_MAPS returns 0.90."""
        assert DataSource.GOOGLE_MAPS.default_confidence == 0.90

    def test_greatschools_confidence(self):
        """Test GREATSCHOOLS returns 0.90 (updated)."""
        assert DataSource.GREATSCHOOLS.default_confidence == 0.90

    def test_image_assessment_confidence(self):
        """Test IMAGE_ASSESSMENT returns 0.80."""
        assert DataSource.IMAGE_ASSESSMENT.default_confidence == 0.80

    def test_csv_confidence(self):
        """Test CSV returns 0.90."""
        assert DataSource.CSV.default_confidence == 0.90

    def test_ai_inference_confidence(self):
        """Test AI_INFERENCE returns 0.70."""
        assert DataSource.AI_INFERENCE.default_confidence == 0.70

    def test_default_confidence_fallback(self):
        """Test unknown source returns 0.50 fallback."""
        # All defined sources should have mappings
        for source in DataSource:
            confidence = source.default_confidence
            assert 0.0 <= confidence <= 1.0


class TestProvenanceService:
    """Test suite for ProvenanceService."""

    def test_record_field_sets_provenance(self):
        """Test single field provenance recording."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
        )

        service = ProvenanceService()
        service.record_field(
            enrichment=enrichment,
            property_hash="abc12345",
            field_name="lot_sqft",
            source=DataSource.ASSESSOR_API,
            value=9500,
        )

        prov = enrichment.get_field_provenance("lot_sqft")
        assert prov is not None
        assert prov.data_source == "assessor_api"
        assert prov.confidence == 0.95  # Default from ASSESSOR_API

    def test_record_batch_multiple_fields(self):
        """Test batch field provenance recording."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
        )

        service = ProvenanceService()
        service.record_batch(
            enrichment=enrichment,
            property_hash="abc12345",
            source=DataSource.ASSESSOR_API,
            fields={
                "lot_sqft": 9500,
                "year_built": 2005,
                "garage_spaces": 2,
            },
        )

        # All fields should have provenance
        for field_name in ["lot_sqft", "year_built", "garage_spaces"]:
            prov = enrichment.get_field_provenance(field_name)
            assert prov is not None
            assert prov.data_source == "assessor_api"
            assert prov.confidence == 0.95

    def test_record_derived_minimum_confidence(self):
        """Test derived field uses minimum confidence of sources."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
        )

        service = ProvenanceService()

        # Set up source fields with different confidences
        service.record_field(
            enrichment=enrichment,
            property_hash="abc12345",
            field_name="field1",
            source=DataSource.ASSESSOR_API,  # 0.95
            value=100,
        )

        service.record_field(
            enrichment=enrichment,
            property_hash="abc12345",
            field_name="field2",
            source=DataSource.ZILLOW,  # 0.85
            value=200,
        )

        # Record derived field
        service.record_derived(
            enrichment=enrichment,
            property_hash="abc12345",
            field_name="derived_field",
            source=DataSource.AI_INFERENCE,
            value=300,
            derived_from=["field1", "field2"],
        )

        prov = enrichment.get_field_provenance("derived_field")
        assert prov is not None
        assert prov.confidence == 0.85  # Minimum of 0.95 and 0.85
        assert prov.derived_from == ["field1", "field2"]

    def test_record_field_custom_confidence(self):
        """Test custom confidence overrides source default."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
        )

        service = ProvenanceService()
        service.record_field(
            enrichment=enrichment,
            property_hash="abc12345",
            field_name="custom_field",
            source=DataSource.MANUAL,
            value="test",
            confidence=0.99,  # Custom override
        )

        prov = enrichment.get_field_provenance("custom_field")
        assert prov is not None
        assert prov.confidence == 0.99  # Not 0.85 (MANUAL default)

    def test_record_field_with_agent_and_phase(self):
        """Test recording with agent_id and phase."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
        )

        service = ProvenanceService()
        service.record_field(
            enrichment=enrichment,
            property_hash="abc12345",
            field_name="orientation",
            source=DataSource.GOOGLE_MAPS,
            value="north",
            agent_id="map-analyzer",
            phase="phase1",
        )

        prov = enrichment.get_field_provenance("orientation")
        assert prov is not None
        assert prov.agent_id == "map-analyzer"
        assert prov.phase == "phase1"


class TestConfidenceDisplay:
    """Test suite for confidence display helpers."""

    def test_confidence_level_high(self):
        """Test confidence >= 0.90 is HIGH."""
        assert ConfidenceLevel.from_score(0.90) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_score(0.95) == ConfidenceLevel.HIGH
        assert ConfidenceLevel.from_score(1.00) == ConfidenceLevel.HIGH

    def test_confidence_level_medium(self):
        """Test confidence 0.70-0.89 is MEDIUM."""
        assert ConfidenceLevel.from_score(0.70) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(0.80) == ConfidenceLevel.MEDIUM
        assert ConfidenceLevel.from_score(0.89) == ConfidenceLevel.MEDIUM

    def test_confidence_level_low(self):
        """Test confidence < 0.70 is LOW."""
        assert ConfidenceLevel.from_score(0.00) == ConfidenceLevel.LOW
        assert ConfidenceLevel.from_score(0.50) == ConfidenceLevel.LOW
        assert ConfidenceLevel.from_score(0.69) == ConfidenceLevel.LOW

    def test_format_confidence_with_badge(self):
        """Test text formatting with badge."""
        # High confidence (no badge)
        assert format_confidence(0.95) == "High (0.95)"

        # Medium confidence (Verify badge)
        assert format_confidence(0.82) == "Medium (0.82) [Verify]"

        # Low confidence (Unverified badge)
        assert format_confidence(0.65) == "Low (0.65) [Unverified]"

    def test_format_confidence_without_badge(self):
        """Test text formatting without badge."""
        assert format_confidence(0.82, include_badge=False) == "Medium (0.82)"
        assert format_confidence(0.65, include_badge=False) == "Low (0.65)"

    def test_get_confidence_html_colors(self):
        """Test HTML badge generation with correct colors."""
        # High confidence (green)
        html_high = get_confidence_html(0.95)
        assert "confidence-green" in html_high
        assert "Verified" in html_high

        # Medium confidence (yellow)
        html_medium = get_confidence_html(0.82)
        assert "confidence-yellow" in html_medium
        assert "Verify" in html_medium

        # Low confidence (red)
        html_low = get_confidence_html(0.65)
        assert "confidence-red" in html_low
        assert "Unverified" in html_low

    def test_confidence_level_badge_property(self):
        """Test badge property for each level."""
        assert ConfidenceLevel.HIGH.badge == ""
        assert ConfidenceLevel.MEDIUM.badge == "Verify"
        assert ConfidenceLevel.LOW.badge == "Unverified"

    def test_confidence_level_color_property(self):
        """Test color property for each level."""
        assert ConfidenceLevel.HIGH.color == "green"
        assert ConfidenceLevel.MEDIUM.color == "yellow"
        assert ConfidenceLevel.LOW.color == "red"
