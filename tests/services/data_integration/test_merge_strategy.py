"""Tests for data merge strategy and conflict resolution."""

from phx_home_analysis.services.data_integration import (
    DataSourcePriority,
    MergeStrategy,
    merge_property_data,
)


class TestDataSourcePriority:
    """Test data source priority levels."""

    def test_priority_ordering(self):
        """Test that priorities are ordered correctly."""
        assert DataSourcePriority.DEFAULT < DataSourcePriority.LISTING
        assert DataSourcePriority.LISTING < DataSourcePriority.COUNTY
        assert DataSourcePriority.COUNTY < DataSourcePriority.MANUAL

    def test_priority_values(self):
        """Test specific priority values."""
        assert DataSourcePriority.DEFAULT == 0
        assert DataSourcePriority.LISTING == 1
        assert DataSourcePriority.COUNTY == 2
        assert DataSourcePriority.MANUAL == 3


class TestMergeStrategy:
    """Test suite for MergeStrategy class."""

    def test_basic_merge_no_conflicts(self):
        """Test merging data with no overlapping fields."""
        strategy = MergeStrategy()

        manual = {"beds": 4, "hoa_fee": 0}
        county = {"year_built": 1978, "garage_spaces": 2}
        listing = {"price": 475000, "baths": 2.0}

        sources = {
            "manual": (manual, DataSourcePriority.MANUAL),
            "county": (county, DataSourcePriority.COUNTY),
            "listing": (listing, DataSourcePriority.LISTING),
        }

        merged, source_map = strategy.merge(sources)

        # All fields should be present
        assert merged["beds"] == 4
        assert merged["hoa_fee"] == 0
        assert merged["year_built"] == 1978
        assert merged["garage_spaces"] == 2
        assert merged["price"] == 475000
        assert merged["baths"] == 2.0

        # Source mapping should be correct
        assert source_map["beds"] == "manual"
        assert source_map["year_built"] == "county"
        assert source_map["price"] == "listing"

    def test_merge_with_conflicts_manual_wins(self):
        """Test that manual data wins over other sources."""
        strategy = MergeStrategy()

        manual = {"lot_sqft": 8069}
        county = {"lot_sqft": 8100}  # Different value
        listing = {"lot_sqft": 8000}  # Different value

        sources = {
            "manual": (manual, DataSourcePriority.MANUAL),
            "county": (county, DataSourcePriority.COUNTY),
            "listing": (listing, DataSourcePriority.LISTING),
        }

        merged, source_map = strategy.merge(sources)

        # Manual should win
        assert merged["lot_sqft"] == 8069
        assert source_map["lot_sqft"] == "manual"

    def test_merge_with_conflicts_county_over_listing(self):
        """Test that county data wins over listing data."""
        strategy = MergeStrategy()

        county = {"year_built": 1978}
        listing = {"year_built": 1980}  # Different value

        sources = {
            "county": (county, DataSourcePriority.COUNTY),
            "listing": (listing, DataSourcePriority.LISTING),
        }

        merged, source_map = strategy.merge(sources)

        # County should win
        assert merged["year_built"] == 1978
        assert source_map["year_built"] == "county"

    def test_merge_skips_none_values(self):
        """Test that None values are skipped."""
        strategy = MergeStrategy()

        manual = {"beds": 4, "lot_sqft": None}  # None value
        county = {"lot_sqft": 8069}  # Has value

        sources = {
            "manual": (manual, DataSourcePriority.MANUAL),
            "county": (county, DataSourcePriority.COUNTY),
        }

        merged, source_map = strategy.merge(sources)

        # County's non-None value should be used
        assert merged["lot_sqft"] == 8069
        assert source_map["lot_sqft"] == "county"
        assert merged["beds"] == 4

    def test_merge_with_defaults(self):
        """Test merging with default values."""
        strategy = MergeStrategy()

        listing = {"price": 475000, "beds": 4}
        defaults = {"hoa_fee": 0, "has_pool": False, "beds": 3}

        sources = {
            "listing": (listing, DataSourcePriority.LISTING),
        }

        merged, source_map = strategy.merge_with_defaults(sources, defaults)

        # Listing values
        assert merged["price"] == 475000
        assert merged["beds"] == 4  # Listing wins over default

        # Default values for missing fields
        assert merged["hoa_fee"] == 0
        assert merged["has_pool"] is False

        # Source tracking
        assert source_map["price"] == "listing"
        assert source_map["beds"] == "listing"
        assert source_map["hoa_fee"] == "defaults"


class TestMergePropertyData:
    """Test the convenience merge_property_data function."""

    def test_full_merge_all_sources(self):
        """Test merging with all sources provided."""
        manual = {"lot_sqft": 8069, "sewer_type": "city"}
        county = {"lot_sqft": 8100, "year_built": 1978, "garage_spaces": 2}
        listing = {"beds": 4, "baths": 2.0, "price": 475000}
        defaults = {"hoa_fee": 0, "has_pool": False}

        merged, sources = merge_property_data(manual, county, listing, defaults)

        # Manual wins for lot_sqft
        assert merged["lot_sqft"] == 8069
        assert sources["lot_sqft"] == "manual"

        # Manual's sewer_type
        assert merged["sewer_type"] == "city"
        assert sources["sewer_type"] == "manual"

        # County's year_built (no conflict)
        assert merged["year_built"] == 1978
        assert sources["year_built"] == "county"

        # Listing's price, beds, baths
        assert merged["price"] == 475000
        assert merged["beds"] == 4
        assert merged["baths"] == 2.0
        assert sources["price"] == "listing"

        # Defaults for missing fields
        assert merged["hoa_fee"] == 0
        assert merged["has_pool"] is False
        assert sources["hoa_fee"] == "defaults"

    def test_partial_merge_missing_sources(self):
        """Test merging with some sources missing."""
        county = {"year_built": 1978, "lot_sqft": 8069}
        listing = {"price": 475000}

        merged, sources = merge_property_data(
            manual_data=None, county_data=county, listing_data=listing, defaults=None
        )

        assert merged["year_built"] == 1978
        assert merged["lot_sqft"] == 8069
        assert merged["price"] == 475000
        assert sources["year_built"] == "county"
        assert sources["price"] == "listing"

    def test_empty_sources(self):
        """Test merging with empty sources."""
        merged, sources = merge_property_data()

        assert merged == {}
        assert sources == {}

    def test_real_world_example(self):
        """Test a real-world merge scenario from the project."""
        # Manual research data
        manual = {
            "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
            "sewer_type": "city",
            "hoa_fee": 0,
            "school_rating": 8.1,
            "safety_neighborhood_score": 3,
            "orientation": "south",
        }

        # County assessor data
        county = {
            "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
            "lot_sqft": 8069,
            "year_built": 1978,
            "garage_spaces": 2,
            "has_pool": True,
            "tax_annual": 1850,
        }

        # Listing data
        listing = {
            "full_address": "4732 W Davis Rd, Glendale, AZ 85306",
            "price": 475000,
            "beds": 4,
            "baths": 2.0,
            "sqft": 2241,
        }

        merged, sources = merge_property_data(manual, county, listing)

        # Verify manual wins for overlapping fields
        assert merged["sewer_type"] == "city"
        assert merged["hoa_fee"] == 0

        # Verify county data
        assert merged["lot_sqft"] == 8069
        assert merged["year_built"] == 1978
        assert merged["garage_spaces"] == 2

        # Verify listing data
        assert merged["price"] == 475000
        assert merged["beds"] == 4
        assert merged["baths"] == 2.0

        # Verify source tracking
        assert sources["sewer_type"] == "manual"
        assert sources["lot_sqft"] == "county"
        assert sources["price"] == "listing"

    def test_priority_with_conflicting_values(self):
        """Test that higher priority always wins even with conflicting values."""
        manual = {"beds": 4}
        county = {"beds": 3}
        listing = {"beds": 5}

        merged, sources = merge_property_data(manual, county, listing)

        # Manual should win despite all sources having different values
        assert merged["beds"] == 4
        assert sources["beds"] == "manual"
