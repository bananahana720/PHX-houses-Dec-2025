"""Unit tests for FieldProvenance and EnrichmentData provenance methods."""

from datetime import datetime

import pytest

from src.phx_home_analysis.domain.entities import EnrichmentData, FieldProvenance


class TestFieldProvenance:
    """Test suite for FieldProvenance dataclass."""

    def test_field_provenance_valid(self):
        """Test valid provenance object creation."""
        prov = FieldProvenance(
            data_source="assessor_api",
            confidence=0.95,
            fetched_at="2025-12-04T10:30:00",
            agent_id="county-api-agent",
            phase="phase0",
        )

        assert prov.data_source == "assessor_api"
        assert prov.confidence == 0.95
        assert prov.fetched_at == "2025-12-04T10:30:00"
        assert prov.agent_id == "county-api-agent"
        assert prov.phase == "phase0"
        assert prov.derived_from == []

    def test_field_provenance_confidence_range_valid(self):
        """Test confidence within valid range (0.0-1.0)."""
        # Test boundary values
        prov_zero = FieldProvenance(
            data_source="default",
            confidence=0.0,
            fetched_at="2025-12-04T10:30:00",
        )
        assert prov_zero.confidence == 0.0

        prov_one = FieldProvenance(
            data_source="assessor",
            confidence=1.0,
            fetched_at="2025-12-04T10:30:00",
        )
        assert prov_one.confidence == 1.0

    def test_field_provenance_confidence_range_invalid_high(self):
        """Test confidence rejects values above 1.0."""
        with pytest.raises(ValueError, match="Confidence must be 0.0-1.0"):
            FieldProvenance(
                data_source="test",
                confidence=1.5,
                fetched_at="2025-12-04T10:30:00",
            )

    def test_field_provenance_confidence_range_invalid_low(self):
        """Test confidence rejects values below 0.0."""
        with pytest.raises(ValueError, match="Confidence must be 0.0-1.0"):
            FieldProvenance(
                data_source="test",
                confidence=-0.1,
                fetched_at="2025-12-04T10:30:00",
            )

    def test_field_provenance_derived_from(self):
        """Test derived_from list for derived fields."""
        prov = FieldProvenance(
            data_source="ai_inference",
            confidence=0.75,
            fetched_at="2025-12-04T10:30:00",
            derived_from=["field1", "field2", "field3"],
        )

        assert prov.derived_from == ["field1", "field2", "field3"]


class TestEnrichmentDataProvenance:
    """Test suite for EnrichmentData provenance methods."""

    def test_enrichment_set_provenance(self):
        """Test setting provenance on EnrichmentData."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=9500,
            year_built=2005,
        )

        enrichment.set_field_provenance(
            field_name="lot_sqft",
            source="assessor_api",
            confidence=0.95,
            fetched_at="2025-12-04T10:30:00",
            agent_id="county-agent",
            phase="phase0",
        )

        prov = enrichment.get_field_provenance("lot_sqft")
        assert prov is not None
        assert prov.data_source == "assessor_api"
        assert prov.confidence == 0.95
        assert prov.agent_id == "county-agent"
        assert prov.phase == "phase0"

    def test_enrichment_get_provenance_nonexistent(self):
        """Test retrieving provenance for field without provenance."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
            lot_sqft=9500,
        )

        prov = enrichment.get_field_provenance("lot_sqft")
        assert prov is None

    def test_enrichment_low_confidence_fields(self):
        """Test identifying low confidence fields."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
        )

        # Add fields with varying confidence
        enrichment.set_field_provenance(
            field_name="lot_sqft",
            source="assessor_api",
            confidence=0.95,  # High
            fetched_at="2025-12-04T10:30:00",
        )

        enrichment.set_field_provenance(
            field_name="hoa_fee",
            source="zillow",
            confidence=0.75,  # Low
            fetched_at="2025-12-04T10:30:00",
        )

        enrichment.set_field_provenance(
            field_name="year_built",
            source="manual",
            confidence=0.85,  # Medium/High
            fetched_at="2025-12-04T10:30:00",
        )

        # Default threshold = 0.80
        low_confidence = enrichment.get_low_confidence_fields()
        assert "lot_sqft" not in low_confidence  # 0.95 >= 0.80
        assert "hoa_fee" in low_confidence  # 0.75 < 0.80
        assert "year_built" not in low_confidence  # 0.85 >= 0.80

    def test_enrichment_low_confidence_fields_custom_threshold(self):
        """Test low confidence identification with custom threshold."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
        )

        enrichment.set_field_provenance(
            field_name="orientation",
            source="google_maps",
            confidence=0.90,
            fetched_at="2025-12-04T10:30:00",
        )

        enrichment.set_field_provenance(
            field_name="school_rating",
            source="greatschools",
            confidence=0.85,
            fetched_at="2025-12-04T10:30:00",
        )

        # Custom threshold = 0.95
        low_confidence = enrichment.get_low_confidence_fields(threshold=0.95)
        assert "orientation" in low_confidence  # 0.90 < 0.95
        assert "school_rating" in low_confidence  # 0.85 < 0.95

    def test_enrichment_set_provenance_default_timestamp(self):
        """Test set_field_provenance generates timestamp when not provided."""
        enrichment = EnrichmentData(
            full_address="123 Main St, Phoenix, AZ 85001",
        )

        enrichment.set_field_provenance(
            field_name="garage_spaces",
            source="assessor_api",
            confidence=0.95,
            # No fetched_at provided
        )

        prov = enrichment.get_field_provenance("garage_spaces")
        assert prov is not None
        assert prov.fetched_at is not None
        # Verify it's a valid ISO timestamp
        datetime.fromisoformat(prov.fetched_at)
