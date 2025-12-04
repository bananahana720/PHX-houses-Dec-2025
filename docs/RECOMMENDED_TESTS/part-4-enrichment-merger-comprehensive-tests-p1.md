# Part 4: Enrichment Merger Comprehensive Tests (P1)

**File:** `tests/services/test_enrichment_merger_comprehensive.py` (NEW)

```python
"""Comprehensive tests for EnrichmentMerger service."""

import pytest
from phx_home_analysis.services.enrichment import EnrichmentMerger
from phx_home_analysis.domain import (
    Property,
    EnrichmentData,
    SewerType,
    Orientation,
    SolarStatus,
)


class TestEnrichmentMergerBasic:
    """Test basic merge operations."""

    def test_merge_county_assessor_data(self, sample_property):
        """Test merging county assessor fields."""
        merger = EnrichmentMerger()

        enrichment = EnrichmentData(
            lot_sqft=12000,
            year_built=2015,
            garage_spaces=2,
        )

        result = merger.merge(sample_property, enrichment)

        assert result.lot_sqft == 12000
        assert result.year_built == 2015
        assert result.garage_spaces == 2

    def test_merge_hoa_and_tax_data(self, sample_property):
        """Test merging HOA and tax information."""
        merger = EnrichmentMerger()

        enrichment = EnrichmentData(
            hoa_fee=150,
            tax_annual=2400,
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
            commute_minutes=25,
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
            hvac_age=7,
        )

        result = merger.merge(sample_property, enrichment)

        assert result.solar_status == SolarStatus.OWNED
        assert result.has_pool is True
        assert result.pool_equipment_age == 5
        assert result.roof_age == 3
        assert result.hvac_age == 7


class TestEnrichmentMergerNullHandling:
    """Test null/None value handling."""

    def test_merge_preserves_none_values(self, sample_property):
        """Test that None values in enrichment don't overwrite existing data."""
        original_roof_age = sample_property.roof_age

        merger = EnrichmentMerger()
        enrichment = EnrichmentData(roof_age=None)

        result = merger.merge(sample_property, enrichment)

        # Should preserve original value
        assert result.roof_age == original_roof_age

    def test_merge_all_none_enrichment(self, sample_property):
        """Test merging all-None enrichment data."""
        original_lot = sample_property.lot_sqft
        original_year = sample_property.year_built

        merger = EnrichmentMerger()
        enrichment = EnrichmentData(
            lot_sqft=None,
            year_built=None,
            garage_spaces=None,
        )

        result = merger.merge(sample_property, enrichment)

        # Original data should be unchanged
        assert result.lot_sqft == original_lot
        assert result.year_built == original_year

    def test_merge_selective_enrichment(self, sample_property):
        """Test merging only specific fields."""
        merger = EnrichmentMerger()

        enrichment = EnrichmentData(
            lot_sqft=15000,
            year_built=None,  # Don't update
            garage_spaces=3,  # Update
        )

        result = merger.merge(sample_property, enrichment)

        assert result.lot_sqft == 15000
        assert result.garage_spaces == 3
        # year_built unchanged


class TestEnrichmentMergerEnumConversions:
    """Test enum conversion logic."""

    @pytest.mark.parametrize("sewer_str,expected_enum", [
        ("city", SewerType.CITY),
        ("septic", SewerType.SEPTIC),
        ("unknown", SewerType.UNKNOWN),
    ])
    def test_merge_sewer_type_conversion(self, sample_property, sewer_str, expected_enum):
        """Test string to enum conversion for sewer type."""
        merger = EnrichmentMerger()

        enrichment = EnrichmentData(sewer_type=sewer_str)
        result = merger.merge(sample_property, enrichment)

        assert result.sewer_type == expected_enum

    @pytest.mark.parametrize("orient_str,expected_enum", [
        ("N", Orientation.N),
        ("S", Orientation.S),
        ("E", Orientation.E),
        ("W", Orientation.W),
    ])
    def test_merge_orientation_conversion(self, sample_property, orient_str, expected_enum):
        """Test string to enum conversion for orientation."""
        merger = EnrichmentMerger()

        enrichment = EnrichmentData(orientation=orient_str)
        result = merger.merge(sample_property, enrichment)

        assert result.orientation == expected_enum

    @pytest.mark.parametrize("solar_str,expected_enum", [
        ("owned", SolarStatus.OWNED),
        ("leased", SolarStatus.LEASED),
        ("none", SolarStatus.NONE),
    ])
    def test_merge_solar_status_conversion(self, sample_property, solar_str, expected_enum):
        """Test string to enum conversion for solar status."""
        merger = EnrichmentMerger()

        enrichment = EnrichmentData(solar_status=solar_str)
        result = merger.merge(sample_property, enrichment)

        assert result.solar_status == expected_enum


class TestEnrichmentMergerBatch:
    """Test batch merge operations."""

    def test_merge_batch_multiple_properties(self):
        """Test merging enrichment into multiple properties."""
        merger = EnrichmentMerger()

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

        enrichment_lookup = {
            "123 Main St, Phoenix, AZ 85001": EnrichmentData(lot_sqft=12000),
            # "456 Oak Ave" not in enrichment
        }

        original_lot_2 = properties[1].lot_sqft
        results = merger.merge_batch(properties, enrichment_lookup)

        # First property enriched
        assert results[0].lot_sqft == 12000
        # Second property unchanged
        assert results[1].lot_sqft == original_lot_2

    def test_merge_batch_empty_enrichment(self):
        """Test batch merge with no enrichment data."""
        merger = EnrichmentMerger()

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
        ]

        results = merger.merge_batch(properties, {})

        # Properties should be returned unchanged
        assert len(results) == 1
        assert results[0] == properties[0]
```

---
