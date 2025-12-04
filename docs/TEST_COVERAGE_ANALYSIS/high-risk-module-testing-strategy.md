# High-Risk Module Testing Strategy

### County Assessor Client (16% coverage, 200 LOC)

**Why Untested:**
- External API dependency (Maricopa County)
- Requires authentication token
- Network calls difficult to test
- Rate limiting considerations

**Testing Strategy:**
```python
# tests/services/county_data/test_assessor_client.py
class TestAssessorClientWithMocks:
    """Test county assessor client with mocked HTTP."""

    @pytest.fixture
    def mock_http_client(self):
        """Mock HTTP client for assessor API."""
        return respx.mock(assert_all_called=False)

    @respx.mock
    def test_get_property_data_success(self, respx_mock):
        """Test successful property data retrieval."""
        respx_mock.get(
            "https://api.maricopa.gov/property/12345"
        ).mock(return_value=httpx.Response(
            200,
            json={
                "lot_sqft": 12000,
                "year_built": 2015,
                "garage_spaces": 2,
                "roof_type": "composition"
            }
        ))

        client = AssessorClient(token="test_token")
        result = client.get_property_data("12345")

        assert result.lot_sqft == 12000
        assert result.year_built == 2015

    @respx.mock
    def test_get_property_data_not_found(self, respx_mock):
        """Test handling of not-found property."""
        respx_mock.get(
            "https://api.maricopa.gov/property/99999"
        ).mock(return_value=httpx.Response(404))

        client = AssessorClient(token="test_token")
        result = client.get_property_data("99999")

        assert result is None

    @respx.mock
    def test_get_property_data_rate_limited(self, respx_mock):
        """Test handling of rate limiting (429)."""
        respx_mock.get(
            "https://api.maricopa.gov/property/12345"
        ).mock(return_value=httpx.Response(429))

        client = AssessorClient(token="test_token")

        with pytest.raises(RateLimitError):
            client.get_property_data("12345")

    @respx.mock
    def test_get_property_data_malformed_response(self, respx_mock):
        """Test handling of malformed API response."""
        respx_mock.get(
            "https://api.maricopa.gov/property/12345"
        ).mock(return_value=httpx.Response(
            200,
            json={"invalid": "response"}  # Missing required fields
        ))

        client = AssessorClient(token="test_token")

        with pytest.raises(ValueError):
            client.get_property_data("12345")

    @respx.mock
    def test_batch_property_lookup(self, respx_mock):
        """Test batch lookups with multiple properties."""
        client = AssessorClient(token="test_token")

        # Setup multiple responses
        respx_mock.get("https://api.maricopa.gov/property/1").mock(
            return_value=httpx.Response(200, json={"lot_sqft": 10000})
        )
        respx_mock.get("https://api.maricopa.gov/property/2").mock(
            return_value=httpx.Response(200, json={"lot_sqft": 8000})
        )

        results = client.batch_get_property_data(["1", "2"])

        assert len(results) == 2
        assert results[0].lot_sqft == 10000
        assert results[1].lot_sqft == 8000
```

### Image Extraction Services (10-28% coverage)

**Challenge:** Complex browser automation with multiple extractors
**Strategy:** Use recorded responses + fixture factories

```python
# tests/services/image_extraction/test_extractors.py
class TestZillowExtractor:
    """Test Zillow listing extraction."""

    @pytest.fixture
    def mock_browser_page(self):
        """Fixture for mocked browser page."""
        page = AsyncMock()
        page.goto = AsyncMock()
        page.wait_for_selector = AsyncMock()
        page.query_selector_all = AsyncMock(return_value=[])
        return page

    @pytest.mark.asyncio
    async def test_extract_images_from_listing(self, mock_browser_page):
        """Test extracting images from Zillow listing."""
        extractor = ZillowExtractor()

        # Mock image elements
        mock_images = [
            MagicMock(get_attribute=AsyncMock(
                return_value="https://zillow.com/image1.jpg"
            )),
            MagicMock(get_attribute=AsyncMock(
                return_value="https://zillow.com/image2.jpg"
            )),
        ]
        mock_browser_page.query_selector_all.return_value = mock_images

        result = await extractor.extract_images(
            mock_browser_page,
            "https://zillow.com/listing/123"
        )

        assert len(result) == 2
        assert all(url.startswith("https://zillow.com") for url in result)

    @pytest.mark.asyncio
    async def test_extract_images_no_images_found(self, mock_browser_page):
        """Test handling when no images found."""
        extractor = ZillowExtractor()
        mock_browser_page.query_selector_all.return_value = []

        result = await extractor.extract_images(
            mock_browser_page,
            "https://zillow.com/listing/no-images"
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_extract_images_page_timeout(self, mock_browser_page):
        """Test handling page load timeout."""
        extractor = ZillowExtractor()
        mock_browser_page.goto.side_effect = TimeoutError("Page load timeout")

        with pytest.raises(ExtractionError):
            await extractor.extract_images(
                mock_browser_page,
                "https://zillow.com/listing/timeout"
            )
```

---
