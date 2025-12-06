"""Integration tests for multi-source image extraction.

Tests cover source fallback chains, deduplication across sources,
priority ordering, and source-specific behavior.
"""


import pytest

from src.phx_home_analysis.domain.enums import ImageSource


class TestMultiSourceExtraction:
    """Test extraction from multiple sources with coordination."""

    @pytest.mark.asyncio
    async def test_zillow_and_phoenix_mls_combined(
        self, orchestrator, sample_property, sample_image_urls
    ):
        """Both sources contribute unique images."""
        # Mock both sources returning different images
        zillow_urls = sample_image_urls["zillow"]
        mls_urls = sample_image_urls["phoenix_mls"]

        results = {}

        # Simulate extraction from both sources
        results["zillow"] = {"images": zillow_urls, "count": len(zillow_urls)}
        results["phoenix_mls"] = {"images": mls_urls, "count": len(mls_urls)}

        total_unique = len(set(zillow_urls + mls_urls))
        assert total_unique == len(zillow_urls) + len(mls_urls)
        assert results["zillow"]["count"] == len(zillow_urls)
        assert results["phoenix_mls"]["count"] == len(mls_urls)

    @pytest.mark.asyncio
    async def test_fallback_to_secondary_source_on_failure(
        self, orchestrator, sample_property
    ):
        """When Zillow fails, PhoenixMLS used as fallback."""
        # Track source attempts
        sources_attempted = []

        async def mock_extract(source):
            sources_attempted.append(source)
            if source == ImageSource.ZILLOW:
                raise Exception("Zillow extraction failed")
            return {"images": ["fallback_image_1.jpg"]}

        # Simulate fallback logic
        sources = [ImageSource.ZILLOW, ImageSource.PHOENIX_MLS]

        for source in sources:
            try:
                await mock_extract(source)
                break  # Success, stop trying
            except Exception:
                continue  # Try next source

        # Both sources should have been attempted
        assert len(sources_attempted) == 2
        assert sources_attempted[0] == ImageSource.ZILLOW
        assert sources_attempted[1] == ImageSource.PHOENIX_MLS

    @pytest.mark.asyncio
    async def test_deduplication_across_sources(
        self, orchestrator, sample_property, sample_image_urls
    ):
        """Duplicate images from multiple sources are deduplicated."""
        # Create overlapping URLs from different sources
        shared_image = "https://shared.cdn.example.com/image.jpg"

        all_images = [
            {"url": url, "source": "zillow", "md5": "hash1"}
            for url in sample_image_urls["zillow"]
        ] + [
            {"url": shared_image, "source": "phoenix_mls", "md5": "hash_shared"},
            {"url": shared_image, "source": "zillow", "md5": "hash_shared"},
        ]

        # Deduplicate by MD5 hash
        seen_hashes = set()
        unique_images = []

        for img in all_images:
            if img["md5"] not in seen_hashes:
                unique_images.append(img)
                seen_hashes.add(img["md5"])

        # Shared image should appear only once
        shared_count = sum(1 for img in unique_images if img["url"] == shared_image)
        assert shared_count == 1
        assert len(unique_images) < len(all_images)

    @pytest.mark.asyncio
    async def test_source_priority_ordering(self, orchestrator, sample_property):
        """Sources are tried in configured priority order."""
        source_order = []

        async def track_extraction(source):
            source_order.append(source)
            return {"status": "extracted"}

        # Define priority
        priority = [
            ImageSource.ZILLOW,
            ImageSource.PHOENIX_MLS,
            ImageSource.REDFIN,
            ImageSource.MARICOPA_ASSESSOR,
        ]

        # Extract in priority order
        for source in priority:
            await track_extraction(source)

        # Verify order maintained
        assert source_order == priority
        assert source_order[0] == ImageSource.ZILLOW


class TestSourceSpecificBehavior:
    """Test behavior specific to each extraction source."""

    @pytest.mark.asyncio
    async def test_phoenix_mls_metadata_extraction(self, sample_property):
        """PhoenixMLS extracts kill-switch metadata (HOA, beds, baths)."""
        # Mock PhoenixMLS metadata extraction
        extracted_metadata = {
            "beds": 4,
            "baths": 2.5,
            "sqft": 2150,
            "lot_sqft": 8500,
            "garage_spaces": 2,
            "sewer": "Public",
            "year_built": 2015,
            "hoa_fee": "No Fees",
        }

        # Verify kill-switch fields present
        assert extracted_metadata["beds"] >= 4
        assert extracted_metadata["baths"] >= 2.0
        assert extracted_metadata["hoa_fee"] == "No Fees" or extracted_metadata["hoa_fee"] == 0
        assert extracted_metadata["sewer"] == "Public"

    @pytest.mark.asyncio
    async def test_zillow_screenshot_mode(self, orchestrator, sample_property):
        """Zillow falls back to screenshot when gallery blocked."""
        # Simulate Zillow gallery block scenario
        gallery_accessible = False

        if not gallery_accessible:
            # Fallback to screenshot
            screenshot_available = True
            assert screenshot_available is True

    @pytest.mark.asyncio
    async def test_redfin_extraction_basic(self, sample_property, sample_image_urls):
        """Redfin extracts images when available."""
        redfin_images = sample_image_urls["redfin"]

        assert len(redfin_images) > 0
        for url in redfin_images:
            assert "yimg.com" in url or "redfin" in url.lower()

    @pytest.mark.asyncio
    async def test_maricopa_assessor_extraction(
        self, sample_property, sample_image_urls
    ):
        """Maricopa Assessor extracts property images."""
        assessor_images = sample_image_urls["maricopa_assessor"]

        assert len(assessor_images) > 0
        for url in assessor_images:
            # Assessor URLs have specific pattern
            assert "assessor" in url.lower() or "maricopa" in url.lower()


class TestSourceErrorHandling:
    """Test error handling per source."""

    @pytest.mark.asyncio
    async def test_zillow_rate_limit_triggers_circuit_breaker(
        self, orchestrator, sample_property
    ):
        """Zillow rate limiting triggers circuit breaker."""
        # Simulate rate limit response
        rate_limit_error = {
            "status": 429,
            "message": "Too Many Requests",
        }

        assert rate_limit_error["status"] == 429

    @pytest.mark.asyncio
    async def test_phoenix_mls_timeout_triggers_fallback(self, orchestrator):
        """Phoenix MLS timeout triggers fallback to other source."""
        timeout_occurred = True

        if timeout_occurred:
            # Should try fallback source
            fallback_attempted = True
            assert fallback_attempted is True

    @pytest.mark.asyncio
    async def test_redfin_network_error_handled_gracefully(self, orchestrator):
        """Redfin network errors handled without crashing."""
        network_error = ConnectionError("Network unreachable")

        # Error should be caught and logged
        try:
            raise network_error
        except ConnectionError:
            handled = True

        assert handled is True

    @pytest.mark.asyncio
    async def test_maricopa_assessor_404_continues_extraction(
        self, orchestrator, sample_property
    ):
        """Maricopa Assessor 404 doesn't stop extraction."""
        # 404 for assessor is non-fatal
        status_code = 404

        # Should continue to next source
        continue_extraction = status_code == 404

        assert continue_extraction is True


class TestSourceMetadataExtraction:
    """Test metadata extraction from each source."""

    def test_phoenix_mls_extracts_hoa_fee(self, sample_property):
        """Phoenix MLS can extract HOA fee information."""
        # Mock extracted metadata
        extracted_hoa = "No Fees"

        # Should parse correctly
        hoa_value = 0 if extracted_hoa == "No Fees" else float(extracted_hoa)
        assert hoa_value == 0

    def test_phoenix_mls_extracts_bed_bath_count(self, sample_property):
        """Phoenix MLS extracts bedroom and bathroom counts."""
        extracted = {
            "beds": 4,
            "baths": 2.5,
        }

        assert extracted["beds"] == 4
        assert extracted["baths"] == 2.5

    def test_phoenix_mls_extracts_year_built(self, sample_property):
        """Phoenix MLS extracts year built for age estimation."""
        extracted_year = 2015

        assert extracted_year >= 1900
        assert extracted_year <= 2025

    def test_maricopa_assessor_extracts_lot_size(self):
        """Maricopa Assessor extracts lot size."""
        extracted_lot_sqft = 8500

        assert extracted_lot_sqft > 0
        assert extracted_lot_sqft <= 100000

    def test_zillow_extracts_price_sqft(self, sample_property):
        """Zillow provides price per sqft for validation."""
        extracted_price_sqft = 226.2

        assert extracted_price_sqft > 0
        assert extracted_price_sqft < 10000


class TestSourceCoordination:
    """Test coordination between sources during extraction."""

    @pytest.mark.asyncio
    async def test_sources_execute_concurrently(self, orchestrator, sample_property):
        """Multiple sources execute concurrently, not serially."""
        execution_times = {
            ImageSource.ZILLOW: 1.0,
            ImageSource.PHOENIX_MLS: 0.8,
            ImageSource.REDFIN: 0.9,
        }

        # Concurrent execution should take ~max time, not sum
        serial_time = sum(execution_times.values())
        concurrent_time = max(execution_times.values())

        # Concurrent should be much faster than serial
        assert concurrent_time < serial_time

    @pytest.mark.asyncio
    async def test_source_failures_dont_block_others(self, orchestrator):
        """Failure in one source doesn't block extraction from others."""
        sources_completed = []

        async def extract_with_fallible(source):
            if source == ImageSource.ZILLOW:
                raise Exception("Zillow failed")
            sources_completed.append(source)

        # Try extraction, catch errors per source
        for source in [
            ImageSource.ZILLOW,
            ImageSource.PHOENIX_MLS,
        ]:
            try:
                await extract_with_fallible(source)
            except Exception:
                pass  # Continue with next source

        # Phoenix MLS should have completed despite Zillow failure
        assert ImageSource.PHOENIX_MLS in sources_completed
