"""Live integration tests for E2-R3 PhoenixMLS extended field extraction.

Tests the complete data flow:
PhoenixMLS HTML -> _parse_listing_metadata() -> MetadataPersister -> enrichment_data.json

This module validates:
1. MLS_FIELD_MAPPING covers all E2-R3 fields
2. EnrichmentData schema has all E2-R3 target fields
3. MetadataPersister correctly persists E2-R3 fields
4. End-to-end data flow from extraction to storage
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest

from phx_home_analysis.domain.entities import EnrichmentData, Property
from phx_home_analysis.repositories.json_repository import JsonEnrichmentRepository
from phx_home_analysis.services.image_extraction.extractors.phoenix_mls import (
    PhoenixMLSExtractor,
)
from phx_home_analysis.services.image_extraction.metadata_persister import (
    MLS_FIELD_MAPPING,
    MetadataPersister,
)


# =============================================================================
# E2-R3 Field Definitions
# =============================================================================

# E2-R3 source fields (extracted from PhoenixMLS HTML)
E2R3_SOURCE_FIELDS = [
    # Geo
    "geo_lat",
    "geo_lon",
    # Legal
    "township",
    "range_section",
    "section",
    "lot_number",
    "subdivision",
    "apn",
    # Structure
    "exterior_stories",
    "interior_levels",
    "builder_name",
    "dwelling_styles",
    # Districts
    "elementary_district",
    "middle_district",
    "high_district",
    # Contract
    "list_date",
    "ownership_type",
    "possession_terms",
    "new_financing",
    # Pool
    "private_pool_features",
    "spa_features",
    "community_pool",
    # Updates
    "kitchen_year_updated",
    "kitchen_update_scope",
    # Additional
    "has_basement",
    "fireplaces_total",
    "total_covered_spaces",
    "utilities_provider",
    "services_available",
    # Remarks
    "public_remarks",
    "directions",
    # Feature lists
    "view_features",
    "community_features",
    "property_description",
    "dining_area_features",
    "technology_features",
    "window_features",
    "other_rooms",
    "construction_materials",
    "construction_finish",
    "parking_features",
    "fencing_types",
]

# E2-R3 target fields (in EnrichmentData schema)
E2R3_TARGET_FIELDS = [
    # Geo
    "latitude",
    "longitude",
    # Legal
    "township",
    "range_section",
    "section",
    "lot_number",
    "subdivision",
    "apn",
    # Structure
    "exterior_stories",
    "interior_levels",
    "builder_name",
    "dwelling_styles",
    # Districts
    "elementary_district",
    "middle_district",
    "high_district",
    # Contract
    "list_date",
    "ownership_type",
    "possession_terms",
    "new_financing",
    # Pool
    "private_pool_features",
    "spa_features",
    "community_pool",
    # Updates
    "kitchen_year_updated",
    "kitchen_update_scope",
    # Additional
    "has_basement",
    "fireplaces_total",
    "total_covered_spaces",
    "utilities_provider",
    "services_available",
    # Remarks
    "public_remarks",
    "directions",
    # Feature lists
    "view_features",
    "community_features",
    "property_description",
    "dining_area_features",
    "technology_features",
    "window_features",
    "other_rooms",
    "construction_materials",
    "construction_finish",
    "parking_features",
    "fencing_types",
]


# =============================================================================
# Test Class: E2-R3 Field Mapping Validation
# =============================================================================


class TestE2R3FieldMappingValidation:
    """Validate E2-R3 fields exist in MLS_FIELD_MAPPING and EnrichmentData."""

    def test_mls_field_mapping_covers_all_e2r3_source_fields(self) -> None:
        """Verify all E2-R3 source fields are in MLS_FIELD_MAPPING."""
        missing_fields: list[str] = []

        for field in E2R3_SOURCE_FIELDS:
            if field not in MLS_FIELD_MAPPING:
                missing_fields.append(field)

        if missing_fields:
            pytest.fail(
                f"E2-R3 source fields missing from MLS_FIELD_MAPPING: {missing_fields}"
            )

    def test_enrichment_data_has_all_e2r3_target_fields(self) -> None:
        """Verify EnrichmentData has all E2-R3 target fields."""
        enrichment = EnrichmentData(full_address="Test Address")
        missing_fields: list[str] = []

        for field in E2R3_TARGET_FIELDS:
            if not hasattr(enrichment, field):
                missing_fields.append(field)

        if missing_fields:
            pytest.fail(
                f"EnrichmentData missing E2-R3 target fields: {missing_fields}"
            )

    def test_property_entity_has_all_e2r3_target_fields(self) -> None:
        """Verify Property entity has all E2-R3 target fields for merge support."""
        # Create minimal Property for testing
        prop = Property(
            street="123 Test St",
            city="Phoenix",
            state="AZ",
            zip_code="85001",
            full_address="123 Test St, Phoenix, AZ 85001",
            price="$500,000",
            price_num=500000,
            beds=4,
            baths=2.0,
            sqft=2000,
            price_per_sqft_raw=250.0,
        )
        missing_fields: list[str] = []

        for field in E2R3_TARGET_FIELDS:
            if not hasattr(prop, field):
                missing_fields.append(field)

        if missing_fields:
            pytest.fail(f"Property entity missing E2-R3 target fields: {missing_fields}")

    def test_field_mapping_source_to_target_consistency(self) -> None:
        """Verify MLS_FIELD_MAPPING maps all E2-R3 source fields to valid targets."""
        mapping_errors: list[str] = []

        for source_field in E2R3_SOURCE_FIELDS:
            if source_field in MLS_FIELD_MAPPING:
                target_field = MLS_FIELD_MAPPING[source_field]
                # Check target exists in EnrichmentData
                enrichment = EnrichmentData(full_address="Test")
                if not hasattr(enrichment, target_field):
                    mapping_errors.append(
                        f"{source_field} -> {target_field} "
                        f"(target not in EnrichmentData)"
                    )

        if mapping_errors:
            pytest.fail(f"Invalid MLS_FIELD_MAPPING entries: {mapping_errors}")

    def test_mls_field_mapping_entry_count(self) -> None:
        """Verify MLS_FIELD_MAPPING has expected number of entries."""
        # E2-R2 had ~35 fields, E2-R3 added ~40 more
        expected_min_fields = 60

        actual_count = len(MLS_FIELD_MAPPING)
        assert actual_count >= expected_min_fields, (
            f"MLS_FIELD_MAPPING has {actual_count} entries, "
            f"expected at least {expected_min_fields}"
        )


# =============================================================================
# Test Class: Metadata Persister Integration
# =============================================================================


class TestMetadataPersisterIntegration:
    """Test MetadataPersister correctly persists E2-R3 fields."""

    @pytest.fixture
    def sample_e2r3_metadata(self) -> dict[str, Any]:
        """Sample metadata dict as produced by _parse_listing_metadata()."""
        return {
            # E2-R2 fields (existing)
            "mls_number": "6835123",
            "beds": 4,
            "baths": 3.0,
            "sqft": 2698,
            "year_built": 1998,
            "hoa_fee": 0.0,
            "has_pool": True,
            # E2-R3 fields (new)
            "geo_lat": 33.673711,
            "geo_lon": -112.062768,
            "township": "4N",
            "range_section": "3E",
            "section": "21",
            "lot_number": "236",
            "subdivision": "ARROYO ROJO",
            "apn": "213-05-716",
            "exterior_stories": 2,
            "interior_levels": "Two Levels",
            "builder_name": "Trend Homes",
            "dwelling_styles": "Detached",
            "elementary_district": "Deer Valley Unified District",
            "middle_district": "Deer Valley Unified District",
            "high_district": "Deer Valley Unified District",
            "list_date": "2024-11-15",
            "ownership_type": "Fee Simple",
            "possession_terms": "Close Of Escrow",
            "new_financing": ["Cash", "Conventional", "FHA", "VA Loan"],
            "private_pool_features": ["Heated", "Diving Pool", "Play Pool"],
            "spa_features": "In Ground",
            "community_pool": False,
            "kitchen_year_updated": 2024,
            "kitchen_update_scope": "Partial",
            "has_basement": False,
            "fireplaces_total": 1,
            "total_covered_spaces": 4,
            "utilities_provider": ["APS", "SW Gas", "City Water"],
            "services_available": ["Cable TV", "High Speed Internet"],
            "public_remarks": "Priced to sell! Present your buyers today...",
            "directions": "North on 32nd St, East on Irma Lane",
            "view_features": ["Mountain(s)", "City Lights"],
            "community_features": ["Biking/Walking Path", "Children's Playgrnd"],
            "property_description": ["N/S Exposure", "Corner Lot"],
            "dining_area_features": ["Eat-in Kitchen", "Formal"],
            "technology_features": ["Pre-Wired for Cable", "Pre-Wired for Internet"],
            "window_features": ["Dual Pane", "Low-E Windows"],
            "other_rooms": ["Den", "Family Room", "Game Room"],
            "construction_materials": ["Frame - Wood", "Stucco"],
            "construction_finish": ["Painted"],
            "parking_features": ["Garage Door Opener", "Extended"],
            "fencing_types": ["Block", "Wrought Iron"],
        }

    @pytest.fixture
    def temp_data_dir(self, tmp_path: Path) -> Path:
        """Create temporary data directory for test files."""
        data_dir = tmp_path / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    def test_metadata_persister_handles_e2r3_fields(
        self,
        sample_e2r3_metadata: dict[str, Any],
        temp_data_dir: Path,
    ) -> None:
        """Verify MetadataPersister correctly persists E2-R3 fields.

        This test validates the full data flow from MetadataPersister -> JSON file -> reload.
        JsonEnrichmentRepository._enrichment_to_dict() now serializes all E2-R3 fields.
        """
        enrichment_path = temp_data_dir / "test_enrichment.json"
        lineage_path = temp_data_dir / "test_lineage.json"

        # Initialize empty enrichment file
        enrichment_path.write_text("[]", encoding="utf-8")
        lineage_path.write_text("{}", encoding="utf-8")

        persister = MetadataPersister(
            enrichment_path=enrichment_path,
            lineage_path=lineage_path,
        )

        results = persister.persist_metadata(
            full_address="764 E Irma Lane, Phoenix, AZ 85024",
            property_hash="abc12345",
            metadata=sample_e2r3_metadata,
        )

        # Check that E2-R3 fields were updated
        assert results.get("latitude") == "updated", "latitude should be updated"
        assert results.get("longitude") == "updated", "longitude should be updated"
        assert results.get("township") == "updated", "township should be updated"
        assert results.get("subdivision") == "updated", "subdivision should be updated"
        assert results.get("view_features") == "updated", "view_features should be updated"
        assert results.get("elementary_district") == "updated"
        assert results.get("fireplaces_total") == "updated"

        # Verify data persisted to file
        repo = JsonEnrichmentRepository(enrichment_path)
        all_data = repo.load_all()

        assert "764 E Irma Lane, Phoenix, AZ 85024" in all_data
        entry = all_data["764 E Irma Lane, Phoenix, AZ 85024"]

        # Verify E2-R3 field values
        assert entry.latitude == 33.673711
        assert entry.longitude == -112.062768
        assert entry.township == "4N"
        assert entry.subdivision == "ARROYO ROJO"
        assert entry.apn == "213-05-716"
        assert entry.exterior_stories == 2
        assert entry.interior_levels == "Two Levels"
        assert entry.builder_name == "Trend Homes"
        assert entry.elementary_district == "Deer Valley Unified District"
        assert entry.list_date == "2024-11-15"
        assert entry.ownership_type == "Fee Simple"
        assert entry.kitchen_year_updated == 2024
        assert entry.fireplaces_total == 1
        assert entry.has_basement is False
        assert entry.community_pool is False
        assert entry.view_features == ["Mountain(s)", "City Lights"]
        assert entry.community_features == ["Biking/Walking Path", "Children's Playgrnd"]
        assert entry.new_financing == ["Cash", "Conventional", "FHA", "VA Loan"]
        assert entry.fencing_types == ["Block", "Wrought Iron"]

    def test_metadata_persister_preserves_existing_fields(
        self,
        temp_data_dir: Path,
    ) -> None:
        """Verify persister does not overwrite existing fields with None.

        This test validates field preservation during updates.
        """
        enrichment_path = temp_data_dir / "test_enrichment.json"
        lineage_path = temp_data_dir / "test_lineage.json"

        # Initialize enrichment file with existing data
        existing_data = [
            {
                "full_address": "123 Main St, Phoenix, AZ 85001",
                "beds": 4,
                "baths": 2.0,
                "school_rating": 7.5,  # Existing field not in metadata
            }
        ]
        enrichment_path.write_text(json.dumps(existing_data), encoding="utf-8")
        lineage_path.write_text("{}", encoding="utf-8")

        persister = MetadataPersister(
            enrichment_path=enrichment_path,
            lineage_path=lineage_path,
        )

        # Persist only E2-R3 fields (no beds/baths/school_rating)
        new_metadata = {
            "geo_lat": 33.5,
            "geo_lon": -112.0,
            "township": "5N",
        }

        persister.persist_metadata(
            full_address="123 Main St, Phoenix, AZ 85001",
            property_hash="xyz67890",
            metadata=new_metadata,
        )

        # Verify existing fields preserved
        repo = JsonEnrichmentRepository(enrichment_path)
        all_data = repo.load_all()
        entry = all_data["123 Main St, Phoenix, AZ 85001"]

        assert entry.beds == 4, "beds should be preserved"
        assert entry.baths == 2.0, "baths should be preserved"
        assert entry.school_rating == 7.5, "school_rating should be preserved"
        assert entry.latitude == 33.5, "latitude should be updated"
        assert entry.longitude == -112.0, "longitude should be updated"
        assert entry.township == "5N", "township should be updated"

    def test_metadata_persister_handles_list_fields(
        self,
        temp_data_dir: Path,
    ) -> None:
        """Verify persister correctly handles list-type E2-R3 fields.

        This test validates list field serialization/deserialization.
        """
        enrichment_path = temp_data_dir / "test_enrichment.json"
        lineage_path = temp_data_dir / "test_lineage.json"

        enrichment_path.write_text("[]", encoding="utf-8")
        lineage_path.write_text("{}", encoding="utf-8")

        persister = MetadataPersister(
            enrichment_path=enrichment_path,
            lineage_path=lineage_path,
        )

        list_metadata = {
            "view_features": ["Mountain(s)", "City Lights", "Sunrise"],
            "community_features": ["Biking/Walking Path", "Pool"],
            "new_financing": ["Cash", "VA"],
            "construction_materials": ["Frame - Wood", "Block", "Stucco"],
            "other_rooms": ["Den", "Office", "Bonus Room"],
        }

        persister.persist_metadata(
            full_address="456 List Test Ave, Phoenix, AZ 85001",
            property_hash="list1234",
            metadata=list_metadata,
        )

        repo = JsonEnrichmentRepository(enrichment_path)
        all_data = repo.load_all()
        entry = all_data["456 List Test Ave, Phoenix, AZ 85001"]

        assert isinstance(entry.view_features, list)
        assert len(entry.view_features) == 3
        assert "Mountain(s)" in entry.view_features
        assert isinstance(entry.community_features, list)
        assert isinstance(entry.new_financing, list)
        assert len(entry.new_financing) == 2
        assert isinstance(entry.construction_materials, list)
        assert isinstance(entry.other_rooms, list)


# =============================================================================
# Test Class: PhoenixMLS Extractor Pattern Validation
# =============================================================================


class TestPhoenixMLSExtractionPatterns:
    """Validate PhoenixMLS extraction regex patterns for E2-R3 fields."""

    @pytest.fixture
    def extractor(self) -> PhoenixMLSExtractor:
        """Create PhoenixMLSExtractor instance for testing."""
        return PhoenixMLSExtractor(timeout=30.0)

    def test_extractor_has_e2r3_regex_patterns(self, extractor: PhoenixMLSExtractor) -> None:
        """Verify PhoenixMLSExtractor has regex patterns for E2-R3 fields."""
        import re

        from phx_home_analysis.services.image_extraction.extractors import phoenix_mls

        # E2-R3 regex patterns that should exist
        expected_patterns = [
            "RE_GEO_LAT",
            "RE_GEO_LON",
            "RE_TOWNSHIP",
            "RE_RANGE",
            "RE_SECTION",
            "RE_LOT_NUMBER",
            "RE_SUBDIVISION",
            "RE_APN",
            "RE_EXTERIOR_STORIES",
            "RE_INTERIOR_LEVELS",
            "RE_BUILDER",
            "RE_DWELLING_STYLES",
            "RE_ELEMENTARY_DISTRICT",
            "RE_MIDDLE_DISTRICT",
            "RE_HIGH_DISTRICT",
            "RE_LIST_DATE",
            "RE_OWNERSHIP",
            "RE_POSSESSION",
            "RE_NEW_FINANCING",
            "RE_PRIVATE_POOL_FEATURES",
            "RE_SPA",
            "RE_COMMUNITY_POOL",
            "RE_KITCHEN_YEAR_UPDATED",
            "RE_KITCHEN_UPDATE_SCOPE",
            "RE_BASEMENT",
            "RE_FIREPLACES_TOTAL",
            "RE_TOTAL_COVERED_SPACES",
            "RE_VIEW",
            "RE_COMMUNITY_FEATURES",
            "RE_PROPERTY_DESCRIPTION",
            "RE_DINING_AREA",
            "RE_TECHNOLOGY",
            "RE_WINDOW",
            "RE_OTHER_ROOMS",
            "RE_CONSTRUCTION",
            "RE_CONSTRUCTION_FINISH",
            "RE_PARKING",
            "RE_FENCING",
            "RE_UTILITIES",
            "RE_SERVICES",
            "RE_PUBLIC_REMARKS",
            "RE_DIRECTIONS",
        ]

        missing_patterns: list[str] = []
        for pattern_name in expected_patterns:
            if not hasattr(phoenix_mls, pattern_name):
                missing_patterns.append(pattern_name)
            else:
                # Verify it's actually a regex pattern
                pattern = getattr(phoenix_mls, pattern_name)
                if not isinstance(pattern, re.Pattern):
                    missing_patterns.append(f"{pattern_name} (not a regex)")

        if missing_patterns:
            pytest.fail(f"Missing or invalid E2-R3 regex patterns: {missing_patterns}")

    def test_parse_listing_metadata_extracts_e2r3_fields(
        self,
        extractor: PhoenixMLSExtractor,
    ) -> None:
        """Test _parse_listing_metadata extracts E2-R3 fields from sample HTML.

        NOTE: HTML format should match real PhoenixMLS pages.
        The APN regex expects formats like "APN: xxx" or "Assessor Number: xxx".
        """
        # Sample HTML snippet with E2-R3 fields
        # NOTE: Uses "APN:" format which matches RE_APN pattern reliably
        sample_html = """
        <html>
        <body>
            <div>Geo Lat: 33.673711</div>
            <div>Geo Lon: -112.062768</div>
            <div>Township: 4N</div>
            <div>Range: 3E</div>
            <div>Section: 21</div>
            <div>Lot Number: 236</div>
            <div>Subdivision: ARROYO ROJO</div>
            <div>APN: 213-05-716</div>
            <div>Exterior Stories: 2</div>
            <div>Interior Levels: Two Levels</div>
            <div>Builder Name: Trend Homes</div>
            <div>Dwelling Styles: Detached</div>
            <div>Elementary School District: Deer Valley Unified District</div>
            <div>High School District: Deer Valley Union High</div>
            <div>List Date: 11/15/2024</div>
            <div>Ownership Type: Fee Simple</div>
            <div>Possession Terms: Close Of Escrow</div>
            <div>New Financing: Cash, Conventional, FHA</div>
            <div>Private Pool Features: Heated, Diving Pool</div>
            <div>Spa: In Ground</div>
            <div>Community Pool: No</div>
            <div>Kitchen Yr Updated: 2024</div>
            <div>Basement: No</div>
            <div>Fireplaces Total: 1</div>
            <div>Total Covered Spaces: 4</div>
            <div>View: Mountain(s), City Lights</div>
            <div>Community Features: Biking/Walking Path, Children's Playgrnd</div>
            <div>Construction: Frame - Wood, Stucco</div>
            <div>Fencing: Block, Wrought Iron</div>
            <div>Utilities: APS, SW Gas</div>
            <div>Remarks: Beautiful property with amazing views.</div>
            <div>Directions: North on 32nd St, East on Irma</div>
        </body>
        </html>
        """

        metadata = extractor._parse_listing_metadata(sample_html)

        # Verify E2-R3 fields extracted
        assert metadata.get("geo_lat") == 33.673711
        assert metadata.get("geo_lon") == -112.062768
        assert metadata.get("township") == "4N"
        assert metadata.get("range_section") == "3E"
        assert metadata.get("section") == "21"
        assert metadata.get("lot_number") == "236"
        assert metadata.get("subdivision") == "ARROYO ROJO"
        assert metadata.get("apn") == "213-05-716"
        assert metadata.get("exterior_stories") == 2
        assert metadata.get("interior_levels") == "Two Levels"
        assert metadata.get("builder_name") == "Trend Homes"
        assert metadata.get("dwelling_styles") == "Detached"
        assert metadata.get("elementary_district") == "Deer Valley Unified District"
        assert metadata.get("high_district") == "Deer Valley Union High"
        assert metadata.get("ownership_type") == "Fee Simple"
        assert metadata.get("possession_terms") == "Close Of Escrow"
        assert metadata.get("has_basement") is False
        assert metadata.get("fireplaces_total") == 1
        assert metadata.get("total_covered_spaces") == 4
        assert metadata.get("community_pool") is False
        # List fields
        assert "Mountain(s)" in str(metadata.get("view_features", []))
        assert "Frame - Wood" in str(metadata.get("construction_materials", []))


# =============================================================================
# Test Class: End-to-End Data Flow Statistics
# =============================================================================


class TestE2R3DataFlowStatistics:
    """Generate statistics about E2-R3 data flow coverage."""

    def test_count_e2r3_fields_in_mapping(self) -> None:
        """Count and report E2-R3 field coverage in MLS_FIELD_MAPPING."""
        e2r3_in_mapping = 0
        e2r3_missing = []

        for field in E2R3_SOURCE_FIELDS:
            if field in MLS_FIELD_MAPPING:
                e2r3_in_mapping += 1
            else:
                e2r3_missing.append(field)

        total_e2r3 = len(E2R3_SOURCE_FIELDS)
        coverage_pct = (e2r3_in_mapping / total_e2r3) * 100

        print(f"\nE2-R3 Field Mapping Coverage:")
        print(f"  Total E2-R3 source fields: {total_e2r3}")
        print(f"  Fields in MLS_FIELD_MAPPING: {e2r3_in_mapping}")
        print(f"  Coverage: {coverage_pct:.1f}%")

        if e2r3_missing:
            print(f"  Missing fields: {e2r3_missing}")

        # Assert 100% coverage
        assert coverage_pct == 100.0, (
            f"E2-R3 field coverage is {coverage_pct:.1f}%, expected 100%. "
            f"Missing: {e2r3_missing}"
        )

    def test_count_total_mls_field_mappings(self) -> None:
        """Report total MLS_FIELD_MAPPING statistics."""
        total_mappings = len(MLS_FIELD_MAPPING)

        # Categorize by type
        kill_switch_fields = [
            "hoa_fee",
            "beds",
            "baths",
            "sqft",
            "lot_sqft",
            "garage_spaces",
            "sewer_type",
            "year_built",
        ]
        e2r2_fields = [
            "mls_number",
            "listing_url",
            "listing_status",
            "listing_office",
            "mls_last_updated",
            "price",
            "days_on_market",
            "original_list_price",
            "price_reduced",
            "property_type",
            "architecture_style",
            "cooling_type",
            "heating_type",
            "water_source",
            "roof_material",
            "has_pool",
            "kitchen_features",
            "master_bath_features",
            "interior_features_list",
            "flooring_types",
            "laundry_features",
            "fireplace_yn",
            "exterior_features_list",
            "elementary_school_name",
            "middle_school_name",
            "high_school_name",
            "cross_streets",
        ]

        ks_count = sum(1 for f in kill_switch_fields if f in MLS_FIELD_MAPPING)
        e2r2_count = sum(1 for f in e2r2_fields if f in MLS_FIELD_MAPPING)
        e2r3_count = sum(1 for f in E2R3_SOURCE_FIELDS if f in MLS_FIELD_MAPPING)

        print(f"\nMLS_FIELD_MAPPING Statistics:")
        print(f"  Total mappings: {total_mappings}")
        print(f"  Kill-switch fields: {ks_count}/{len(kill_switch_fields)}")
        print(f"  E2-R2 fields: {e2r2_count}/{len(e2r2_fields)}")
        print(f"  E2-R3 fields: {e2r3_count}/{len(E2R3_SOURCE_FIELDS)}")

        assert total_mappings >= 60, f"Expected at least 60 mappings, got {total_mappings}"
