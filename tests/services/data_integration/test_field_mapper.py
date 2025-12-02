"""Tests for FieldMapper field name translation."""


from phx_home_analysis.services.data_integration import FieldMapper


class TestFieldMapper:
    """Test suite for FieldMapper class."""

    def test_to_canonical_basic_mapping(self):
        """Test basic field name translation to canonical."""
        mapper = FieldMapper()

        # Test listing source
        assert mapper.to_canonical("price_num", "listing") == "price"
        assert mapper.to_canonical("sqft", "listing") == "sqft"

        # Test enrichment source
        assert mapper.to_canonical("lot_size_sqft", "enrichment") == "lot_sqft"
        assert mapper.to_canonical("list_price", "enrichment") == "price"

        # Test county API source
        assert mapper.to_canonical("livable_sqft", "county_api") == "livable_sqft"
        assert mapper.to_canonical("lot_sqft", "county_api") == "lot_sqft"

    def test_to_canonical_passthrough(self):
        """Test that unknown fields pass through unchanged."""
        mapper = FieldMapper()

        # Unknown field should pass through
        assert mapper.to_canonical("unknown_field", "listing") == "unknown_field"

        # Unknown source should pass through
        assert mapper.to_canonical("beds", "unknown_source") == "beds"

    def test_from_canonical_basic_mapping(self):
        """Test translation from canonical to source-specific names."""
        mapper = FieldMapper()

        # County API: livable_sqft stays as livable_sqft
        assert mapper.from_canonical("livable_sqft", "county_api") == "livable_sqft"

        # Listing: when multiple fields map to same canonical, last one wins
        # Both "price" and "price_num" map to "price", so reverse returns "price_num"
        assert mapper.from_canonical("price", "listing") == "price_num"

        # Enrichment: both "lot_sqft" and "lot_size_sqft" map to "lot_sqft"
        # Reverse mapping returns "lot_size_sqft" (defined last)
        assert mapper.from_canonical("lot_sqft", "enrichment") == "lot_size_sqft"

        # Fields not in reverse mapping pass through unchanged
        assert mapper.from_canonical("unknown_field", "listing") == "unknown_field"

    def test_translate_dict_to_canonical(self):
        """Test translating entire dictionary to canonical names."""
        mapper = FieldMapper()

        # Enrichment data with aliases
        enrichment_data = {
            "lot_size_sqft": 8069,
            "list_price": 475000,
            "year_built": 1978,
        }

        canonical = mapper.translate_dict(enrichment_data, "enrichment", to_canonical=True)

        assert canonical["lot_sqft"] == 8069
        assert canonical["price"] == 475000
        assert canonical["year_built"] == 1978
        assert "lot_size_sqft" not in canonical
        assert "list_price" not in canonical

    def test_translate_dict_from_canonical(self):
        """Test translating from canonical to source-specific names."""
        mapper = FieldMapper()

        canonical_data = {
            "livable_sqft": 2241,  # Use livable_sqft which county_api knows about
            "lot_sqft": 8069,
            "price": 475000,
        }

        # Translate to county API format
        county = mapper.translate_dict(canonical_data, "county_api", to_canonical=False)

        assert county["livable_sqft"] == 2241
        assert county["lot_sqft"] == 8069
        # price passes through since county_api doesn't have reverse mapping for it
        assert county["price"] == 475000

    def test_get_source_fields(self):
        """Test getting all fields for a source."""
        mapper = FieldMapper()

        listing_fields = mapper.get_source_fields("listing")

        assert "price" in listing_fields
        assert "price_num" in listing_fields
        assert "beds" in listing_fields
        assert "baths" in listing_fields

    def test_get_canonical_fields(self):
        """Test getting all canonical field names."""
        mapper = FieldMapper()

        canonical_fields = mapper.get_canonical_fields()

        # Check some expected canonical fields
        assert "beds" in canonical_fields
        assert "baths" in canonical_fields
        assert "lot_sqft" in canonical_fields
        assert "year_built" in canonical_fields
        assert "price" in canonical_fields
        assert "full_address" in canonical_fields

    def test_is_valid_source(self):
        """Test source validation."""
        mapper = FieldMapper()

        assert mapper.is_valid_source("listing")
        assert mapper.is_valid_source("county_api")
        assert mapper.is_valid_source("enrichment")
        assert mapper.is_valid_source("csv")
        assert not mapper.is_valid_source("unknown_source")

    def test_custom_mappings(self):
        """Test adding custom mappings."""
        custom = {
            "test_source": {
                "custom_field": "canonical_field",
            }
        }

        mapper = FieldMapper(custom_mappings=custom)

        assert mapper.to_canonical("custom_field", "test_source") == "canonical_field"
        assert mapper.is_valid_source("test_source")

    def test_bidirectional_consistency(self):
        """Test that to_canonical and from_canonical are consistent."""
        mapper = FieldMapper()

        # For each source, test round-trip consistency
        for source in ["listing", "county_api", "enrichment", "csv"]:
            source_fields = mapper.get_source_fields(source)

            for field in source_fields:
                # Translate to canonical and back
                canonical = mapper.to_canonical(field, source)
                back_to_source = mapper.from_canonical(canonical, source)

                # Should get back to original field (or a valid alias)
                assert back_to_source in source_fields or back_to_source == field
