"""Zillow image extractor using nodriver for stealth browser automation.

Zillow is a JavaScript-heavy site with anti-bot protection requiring stealth
browser automation to properly load images from dynamic galleries and carousels.
"""

import asyncio
import json
import logging
import os
import re
import time
from urllib.parse import quote_plus

import httpx
import nodriver as uc

from ....config.settings import StealthExtractionConfig
from ....domain.entities import Property
from ....domain.enums import ImageSource
from .stealth_base import StealthBrowserExtractor

logger = logging.getLogger(__name__)


class ZillowExtractor(StealthBrowserExtractor):
    """Zillow image extractor using nodriver stealth browser automation.

    Zillow requires stealth browser automation because:
    - Heavy JavaScript rendering for image galleries
    - Lazy-loaded images in carousels
    - Dynamic content based on viewport/interactions
    - PerimeterX anti-bot protection blocking simple HTTP requests
    - Press & Hold CAPTCHA challenges for detected automation

    Extracts high-resolution images from property detail pages using
    nodriver for undetectable Chrome automation and curl_cffi for
    bot-resistant HTTP downloads.

    SECURITY: This extractor includes multiple safeguards against search result
    contamination (extracting images from wrong properties):
    - Strict zpid validation in JSON extraction
    - URL-based zpid filtering for all extracted images
    - Page type validation before and after extraction
    - High URL count threshold triggering re-validation

    Example:
        ```python
        async with ZillowExtractor() as extractor:
            urls = await extractor.extract_image_urls(property)
            for url in urls:
                image_bytes, content_type = await extractor.download_image(url)
        ```
    """

    # Maximum number of images expected from a single property listing
    # Exceeding this suggests search result contamination
    MAX_EXPECTED_IMAGES_PER_PROPERTY = 50

    # Patterns that indicate search result or carousel URLs (to be rejected)
    SEARCH_RESULT_URL_PATTERNS = [
        "/search/",
        "/homes-for-sale/",
        "searchResultsMap",
        "carousel",
        "similar-homes",
        "nearby",
        "recommendation",
    ]

    # Placeholder URL patterns indicating "No Photo Available" images
    PLACEHOLDER_URL_PATTERNS = [
        "no-photo",
        "no-image",
        "placeholder",
        "unavailable",
        "default-image",
        "missing-photo",
        "no_photo",
    ]

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        config: StealthExtractionConfig | None = None,
    ):
        """Initialize Zillow extractor with stealth configuration.

        Args:
            http_client: Shared httpx client (maintained for compatibility)
            timeout: Request timeout in seconds
            config: Stealth extraction configuration (loaded from env if not provided)
        """
        super().__init__(http_client=http_client, timeout=timeout, config=config)

        # Store metadata from last extraction for orchestrator retrieval
        self.last_metadata: dict = {}

        logger.info(
            "%s initialized for stealth extraction",
            self.name,
        )

    @property
    def source(self) -> ImageSource:
        """Image source identifier.

        Returns:
            ImageSource.ZILLOW
        """
        return ImageSource.ZILLOW

    def _build_search_url(self, property: Property) -> str:
        """Build Zillow search URL from property address.

        Zillow search URL format:
            /homes/{street}-{city}-{state}-{zip}_rb/

        Each component is URL-encoded and spaces replaced with dashes.

        Args:
            property: Property entity with address components

        Returns:
            Full Zillow search URL for the property

        Example:
            Input: "4732 W Davis Rd", "Glendale", "AZ", "85306"
            Output: "https://www.zillow.com/homes/4732-W-Davis-Rd-Glendale-AZ-85306_rb/"
        """
        # URL-encode address components and replace spaces with dashes
        street = quote_plus(property.street.replace(" ", "-"))
        city = quote_plus(property.city.replace(" ", "-"))
        state = property.state
        zip_code = property.zip_code

        # Construct search path
        search_path = f"{street}-{city}-{state}-{zip_code}_rb"

        # Build full URL
        url = f"{self.source.base_url}/homes/{search_path}/"

        logger.debug("%s built search URL: %s", self.name, url)
        return url

    def _build_detail_url(self, property: Property) -> str:
        """Build Zillow detail URL when zpid-based slug is available.

        Tries to format: /homedetails/{street-city-state-zip}/{zpid}_zpid/
        Falls back to search URL if zpid not supplied.
        """
        street = property.street.replace(" ", "-")
        city = property.city.replace(" ", "-")
        slug = f"{street}-{city}-{property.state}-{property.zip_code}"

        # If property has a zpid attribute in extra metadata, use it
        zpid = getattr(property, "zpid", None)
        if zpid:
            return f"{self.source.base_url}/homedetails/{slug}/{zpid}_zpid/"

        # Fallback: use search URL
        return self._build_search_url(property)

    async def _extract_urls_from_page(
        self, tab: uc.Tab, expected_zpid: str | None = None
    ) -> list[str]:
        """Extract high-resolution image URLs from loaded Zillow page.

        Uses nodriver's native element selection methods to extract all image URLs from:
        - srcset attributes (highest resolution)
        - img src attributes
        - background-image CSS properties

        Filters results through _is_high_quality_url() to exclude thumbnails,
        icons, placeholders, and other low-quality images.

        Args:
            tab: Browser tab with loaded Zillow property page

        Returns:
            List of high-resolution image URLs

        Raises:
            ExtractionError: If element selection or URL extraction fails
        """
        logger.info("%s extracting image URLs from page", self.name)
        image_urls: set[str] = set()

        try:
            # Wait for content to load
            await asyncio.sleep(2)

            # Strategy 1: Get all img elements using native selector
            imgs = await tab.query_selector_all("img")
            logger.debug("%s found %d img elements", self.name, len(imgs))

            for img in imgs:
                # Check srcset first (contains high-res URLs)
                srcset = img.attrs.get("srcset", "")
                if srcset:
                    # Parse srcset: "url1 1x, url2 2x"
                    urls_in_srcset = re.findall(r"(https://[^\s,]+)", srcset)
                    for url in urls_in_srcset:
                        image_urls.add(url)

                # Fallback to src
                src = img.attrs.get("src", "") or getattr(img, "src", "")
                if src and src.startswith("http"):
                    image_urls.add(src)

            # Strategy 2: Check for background images in divs
            divs = await tab.query_selector_all('[style*="background-image"]')
            logger.debug("%s found %d elements with background-image", self.name, len(divs))

            for div in divs:
                style = div.attrs.get("style", "")
                match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                if match:
                    url = match.group(1)
                    if url.startswith("http"):
                        image_urls.add(url)

            logger.debug(
                "%s found %d raw URLs from page",
                self.name,
                len(image_urls),
            )

            # Parse __NEXT_DATA__ for responsivePhotos (full gallery)
            try:
                content = await tab.get_content()
                logger.info(
                    "%s responsivePhotos marker present: %s",
                    self.name,
                    "responsivePhotos" in content,
                )
                json_photos = await self._extract_photos_from_next_data(
                    tab, content, expected_zpid=expected_zpid
                )
                if json_photos:
                    logger.info(
                        "%s found %d responsivePhotos URLs in __NEXT_DATA__",
                        self.name,
                        len(json_photos),
                    )
                    image_urls.update(json_photos)

                # Additional regex-based capture as a fallback
                json_urls = set(
                    re.findall(
                        r"https://photos\\.zillowstatic\\.com/[\\w\\-/\\.]+",
                        content,
                    )
                )
                escaped_urls = set(
                    url.replace("\\/", "/")
                    for url in re.findall(
                        r"https:\\/\\/photos\\.zillowstatic\\.com[\\w\\-/\\.]+",
                        content,
                    )
                )
                json_urls.update(escaped_urls)
                if json_urls:
                    logger.debug(
                        "%s found %d photo URLs via regex in JSON",
                        self.name,
                        len(json_urls),
                    )
                    image_urls.update(json_urls)
            except Exception as e:
                logger.debug("%s failed JSON photo extraction: %s", self.name, e)

            # Filter through quality check
            if not image_urls:
                logger.warning("%s no image URLs found on page", self.name)
                return []

            # Filter for high-quality URLs only
            filtered_urls = [url for url in image_urls if self._is_high_quality_url(url)]

            logger.info(
                "%s filtered to %d high-quality URLs from %d total",
                self.name,
                len(filtered_urls),
                len(image_urls),
            )

            return filtered_urls

        except Exception as e:
            logger.error("%s failed to extract URLs: %s", self.name, e)
            # Return empty list rather than raising - some extractions may find nothing
            return []

    def _is_search_result_url(self, url: str) -> bool:
        """Check if URL indicates search results or carousel content.

        SECURITY: Detects URLs that suggest images from search results page,
        "similar homes" carousels, or recommendation sections rather than
        the target property's gallery.

        Args:
            url: Image URL to check

        Returns:
            True if URL appears to be from search/carousel content, False otherwise
        """
        url_lower = url.lower()
        for pattern in self.SEARCH_RESULT_URL_PATTERNS:
            if pattern in url_lower:
                logger.debug(
                    "%s rejecting search result URL (pattern '%s'): %s",
                    self.name,
                    pattern,
                    url[:80],
                )
                return True
        return False

    def _is_placeholder_url(self, url: str) -> bool:
        """Check if URL is a "No Photo Available" placeholder image.

        Placeholder images are generic "no photo available" images that
        aren't actual property photos. They have characteristic URL patterns
        and are typically very small files.

        Args:
            url: Image URL to check

        Returns:
            True if URL appears to be a placeholder image, False otherwise
        """
        url_lower = url.lower()
        for pattern in self.PLACEHOLDER_URL_PATTERNS:
            if pattern in url_lower:
                logger.debug(
                    "%s rejecting placeholder URL (pattern '%s'): %s",
                    self.name,
                    pattern,
                    url[:80],
                )
                return True
        return False

    def _validate_zpid_in_url(self, url: str, expected_zpid: str | None) -> bool:
        """Validate that image URL is associated with the expected property zpid.

        SECURITY: Zillow image URLs often contain zpid identifiers. This method
        validates that extracted URLs belong to the target property, not
        to other properties shown in search results or carousels.

        URL patterns containing zpid:
        - photos.zillowstatic.com/fp/...zpid_123456789...
        - Encoded zpid in path segments

        Args:
            url: Image URL to validate
            expected_zpid: The zpid of the target property (None if unknown)

        Returns:
            True if URL is valid for this property (or zpid unknown), False if
            URL contains a DIFFERENT zpid indicating wrong property
        """
        if not expected_zpid:
            # Cannot validate without expected zpid - allow through
            return True

        # Look for zpid patterns in URL
        # Zillow embeds zpid in various formats in image URLs
        zpid_patterns = [
            rf"zpid[_\-]?{expected_zpid}",
            rf"{expected_zpid}_zpid",
            rf"/{expected_zpid}/",
            rf"p_e/{expected_zpid}",  # Common Zillow photo path pattern
        ]

        url_lower = url.lower()

        # Check if URL contains expected zpid
        for pattern in zpid_patterns:
            if re.search(pattern, url_lower):
                logger.debug(
                    "%s URL validated for zpid %s: %s",
                    self.name,
                    expected_zpid,
                    url[:80],
                )
                return True

        # Check if URL contains a DIFFERENT zpid (contamination indicator)
        # Pattern: any 9-10 digit number that could be zpid
        other_zpid_match = re.search(r"/(\d{9,10})[/_\-]", url_lower)
        if other_zpid_match:
            found_zpid = other_zpid_match.group(1)
            if found_zpid != expected_zpid:
                logger.warning(
                    "%s URL contains different zpid %s (expected %s) - REJECTED: %s",
                    self.name,
                    found_zpid,
                    expected_zpid,
                    url[:80],
                )
                return False

        # No zpid found in URL - allow through (some valid URLs don't have zpid)
        return True

    def _filter_urls_for_property(
        self, urls: list[str], expected_zpid: str | None
    ) -> list[str]:
        """Filter extracted URLs to only include those from target property.

        SECURITY: Post-extraction filter to remove contaminated URLs from
        search results, carousels, or other properties.

        Applies multiple filters:
        1. Search result URL pattern rejection
        2. Placeholder image detection (no photo available)
        3. Zpid validation (if expected_zpid available)
        4. High-quality URL check

        Args:
            urls: Raw list of extracted URLs
            expected_zpid: The zpid of the target property

        Returns:
            Filtered list containing only valid property images
        """
        filtered = []
        rejected_search = 0
        rejected_placeholder = 0
        rejected_zpid = 0
        rejected_quality = 0

        for url in urls:
            # Filter 1: Reject search result patterns
            if self._is_search_result_url(url):
                rejected_search += 1
                continue

            # Filter 2: Reject placeholder images
            if self._is_placeholder_url(url):
                rejected_placeholder += 1
                continue

            # Filter 3: Validate zpid if available
            if not self._validate_zpid_in_url(url, expected_zpid):
                rejected_zpid += 1
                continue

            # Filter 4: Quality check
            if not self._is_high_quality_url(url):
                rejected_quality += 1
                continue

            filtered.append(url)

        if rejected_search > 0 or rejected_zpid > 0 or rejected_placeholder > 0:
            logger.warning(
                "%s URL filtering: accepted=%d, rejected_search=%d, rejected_placeholder=%d, rejected_zpid=%d, rejected_quality=%d",
                self.name,
                len(filtered),
                rejected_search,
                rejected_placeholder,
                rejected_zpid,
                rejected_quality,
            )
        else:
            logger.debug(
                "%s URL filtering: accepted=%d, rejected_placeholder=%d, rejected_quality=%d",
                self.name,
                len(filtered),
                rejected_placeholder,
                rejected_quality,
            )

        return filtered

    def _is_high_quality_url(self, url: str) -> bool:
        """Check if URL points to high-quality property image.

        Filters out low-quality images by:
        1. Excluding URLs with quality-indicating keywords (thumbnails, icons, etc.)
        2. Including URLs from known high-quality CDN domains
        3. Accepting URLs with standard image extensions

        Args:
            url: Image URL to validate

        Returns:
            True if URL appears to be high-quality property photo, False otherwise

        Example exclusions:
            - "thumb_320.jpg" -> False (thumbnail)
            - "map_tile.png" -> False (map image)
            - "loading.gif" -> False (placeholder)

        Example inclusions:
            - "photos.zillowstatic.com/...uncrate.jpg" -> True (Zillow CDN)
            - "ssl.cdn-redfin.com/photo/123.jpg" -> True (Redfin CDN)
        """
        url_lower = url.lower()

        # Exclude low-quality patterns
        exclude_patterns = [
            "thumb",  # Thumbnails
            "small",  # Small-sized images
            "icon",  # Icon images
            "logo",  # Logos
            "map",  # Map tiles
            "placeholder",  # Placeholder images
            "loading",  # Loading spinners
            "avatar",  # User avatars
            "agent",  # Agent photos
            "partner",  # Partner branding
            "showcase",  # Showcase/promotional images
            "bedrock/app",  # Zillow CMS/app images
        ]

        for pattern in exclude_patterns:
            if pattern in url_lower:
                logger.debug(
                    "%s excluding URL (contains '%s'): %s",
                    self.name,
                    pattern,
                    url[:80],
                )
                return False

        # Include high-quality CDN patterns
        include_patterns = [
            "photos.zillowstatic.com",  # Zillow CDN
            "ssl.cdn-redfin.com",  # Redfin CDN (cross-listed properties)
            "uncrate",  # Zillow high-res indicator
        ]

        for pattern in include_patterns:
            if pattern in url_lower:
                logger.debug(
                    "%s including URL (matches '%s'): %s",
                    self.name,
                    pattern,
                    url[:80],
                )
                return True

        # Default: accept if it has a standard image extension
        has_image_ext = any(
            ext in url_lower for ext in [".jpg", ".jpeg", ".png", ".webp"]
        )

        if has_image_ext:
            logger.debug("%s including URL (has image extension): %s", self.name, url[:80])
        else:
            logger.debug("%s excluding URL (no image extension): %s", self.name, url[:80])

        return has_image_ext

    async def _extract_photos_from_next_data(
        self, tab: uc.Tab, content: str, expected_zpid: str | None = None
    ) -> set[str]:
        """Parse __NEXT_DATA__ JSON for responsivePhotos to capture full gallery.

        SECURITY: This method now includes zpid-aware filtering to prevent
        extracting photos from search results or "similar homes" carousels.
        Only photos associated with the expected_zpid are extracted.
        """
        urls: set[str] = set()
        skipped_sections = 0

        data: dict | None = None
        script_json = ""

        # Preferred: read __NEXT_DATA__ text directly from DOM
        try:
            script_json = await tab.evaluate(
                "() => document.getElementById('__NEXT_DATA__')?.textContent || ''"
            )
        except Exception as e:
            logger.info("%s could not read __NEXT_DATA__ via DOM: %s", self.name, e)

        # Try accessing the window object directly to avoid HTML parsing
        if not script_json:
            try:
                window_data = await tab.evaluate("() => window.__NEXT_DATA__ || null")
                if window_data:
                    data = window_data
                    logger.info("%s obtained __NEXT_DATA__ from window object", self.name)
            except Exception as e:
                logger.info("%s could not access window.__NEXT_DATA__: %s", self.name, e)

        # Fallback: regex from full HTML content
        if not script_json:
            match = re.search(
                r'id="__NEXT_DATA__"[^>]*>(\{.*?\})</script>',
                content,
                re.DOTALL,
            )
            if match:
                script_json = match.group(1)

        if script_json and data is None:
            logger.info("%s __NEXT_DATA__ payload length: %d", self.name, len(script_json))
            try:
                data = json.loads(script_json)
            except json.JSONDecodeError:
                logger.info("%s failed to parse __NEXT_DATA__ JSON", self.name)

        # Optional debug dump
        if data is not None and os.getenv("ZILLOW_DEBUG_DUMP"):
            dump_path = f"/tmp/zillow_next_data_{expected_zpid or 'unknown'}.json"
            try:
                with open(dump_path, "w", encoding="utf-8") as f:
                    json.dump(data, f)
                logger.info("%s wrote __NEXT_DATA__ dump to %s", self.name, dump_path)
            except Exception as e:
                logger.info("%s failed to dump __NEXT_DATA__: %s", self.name, e)

        # FIX: Zpid-aware traversal - only extract from sections matching our zpid
        # Traverse parsed JSON when available
        if data is not None:
            def walk(node: dict | list | str | int | float | bool | None, parent_zpid: str | None = None) -> None:
                """Walk JSON tree, tracking zpid context to filter by property.

                Args:
                    node: Current JSON node
                    parent_zpid: The zpid of the parent context (if any)
                """
                nonlocal skipped_sections

                if isinstance(node, dict):
                    # Check if this dict has a zpid - use it as context
                    current_zpid = parent_zpid
                    node_zpid = str(node.get("zpid") or node.get("id") or "")

                    if node_zpid and node_zpid.isdigit() and len(node_zpid) >= 8:
                        current_zpid = node_zpid

                    # FIX: Skip responsivePhotos from non-matching zpid contexts
                    for key, value in node.items():
                        if key == "responsivePhotos" and isinstance(value, list):
                            # Only extract if zpid matches or is unknown
                            if expected_zpid and current_zpid and current_zpid != str(expected_zpid):
                                skipped_sections += 1
                                logger.debug(
                                    "%s SKIPPING responsivePhotos from zpid %s (expected %s)",
                                    self.name,
                                    current_zpid,
                                    expected_zpid,
                                )
                                continue
                            urls.update(self._extract_from_responsive_list(value))

                        # FIX: Skip known carousel/search result sections
                        if key in ("searchResults", "similarHomes", "nearbyHomes",
                                   "recommendedHomes", "otherListings", "carousel"):
                            skipped_sections += 1
                            logger.debug(
                                "%s SKIPPING section '%s' (likely search/carousel)",
                                self.name,
                                key,
                            )
                            continue

                        walk(value, current_zpid)
                elif isinstance(node, list):
                    for item in node:
                        walk(item, parent_zpid)

            walk(data)

            if skipped_sections > 0:
                logger.info(
                    "%s Skipped %d non-target sections during JSON traversal",
                    self.name,
                    skipped_sections,
                )

        # Inspect gdpClientCache for zpid-specific responsivePhotos/homePhotos
        try:
            gdp_cache_raw = (
                data.get("props", {})
                .get("pageProps", {})
                .get("componentProps", {})
                .get("gdpClientCache")
                if data
                else None
            )
            gdp_cache = (
                json.loads(gdp_cache_raw) if isinstance(gdp_cache_raw, str) else None
            )
            if gdp_cache and os.getenv("ZILLOW_DEBUG_DUMP"):
                dump_path = f"/tmp/zillow_gdp_cache_{expected_zpid or 'unknown'}.json"
                try:
                    with open(dump_path, "w", encoding="utf-8") as f:
                        json.dump(gdp_cache, f)
                    logger.info("%s wrote gdpClientCache dump to %s", self.name, dump_path)
                except Exception as e:
                    logger.info("%s failed to dump gdpClientCache: %s", self.name, e)
            if isinstance(gdp_cache, dict):
                for key, value in gdp_cache.items():
                    # FIX: STRICT zpid filtering - skip entries not matching our zpid
                    if expected_zpid and expected_zpid not in key:
                        # Check if payload has matching zpid before processing
                        if isinstance(value, dict):
                            value_zpid = str(value.get("zpid") or value.get("id") or "")
                            if value_zpid and value_zpid != str(expected_zpid):
                                logger.debug(
                                    "%s SKIPPING gdpClientCache entry with zpid %s (expected %s)",
                                    self.name,
                                    value_zpid,
                                    expected_zpid,
                                )
                                skipped_sections += 1
                                continue

                    if isinstance(value, dict):
                        value_zpid = str(value.get("zpid") or value.get("id") or "")
                        if expected_zpid and value_zpid and value_zpid != str(expected_zpid):
                            continue

                        # responsivePhotos directly on this object
                        if isinstance(value.get("responsivePhotos"), list):
                            urls.update(
                                self._extract_from_responsive_list(
                                    value["responsivePhotos"]
                                )
                            )

                        # Some responses use homePhotos/media collections
                        if isinstance(value.get("homePhotos"), list):
                            urls.update(
                                self._extract_from_responsive_list(
                                    value["homePhotos"]
                                )
                            )
                        if isinstance(value.get("photos"), list):
                            urls.update(
                                self._extract_from_responsive_list(value["photos"])
                            )
                        if isinstance(value.get("media"), dict):
                            media = value["media"]
                            if isinstance(media.get("photos"), list):
                                urls.update(
                                    self._extract_from_responsive_list(media["photos"])
                                )

        except Exception as e:
            logger.debug("%s gdpClientCache parsing failed: %s", self.name, e)

        # Fallback: directly parse responsivePhotos array from HTML if traversal found nothing
        if not urls:
            responsive_list = self._extract_responsive_photos_array(content)
            if responsive_list:
                urls.update(self._extract_from_responsive_list(responsive_list))
            else:
                logger.info("%s responsivePhotos not found in JSON/HTML", self.name)

        return urls

    def _extract_from_responsive_list(self, photos: list) -> set[str]:
        """Extract URLs from a responsivePhotos/homePhotos-like array."""
        results: set[str] = set()
        for photo in photos:
            url = self._choose_best_photo_url(photo)
            if url:
                results.add(url)
        return results

    def _extract_responsive_photos_array(self, content: str) -> list | None:
        """Best-effort extraction of responsivePhotos array when JSON parsing fails."""
        marker = '"responsivePhotos"'
        start = content.find(marker)
        if start == -1:
            return None

        array_start = content.find("[", start)
        if array_start == -1:
            return None

        depth = 0
        end = None
        for i, ch in enumerate(content[array_start:], start=array_start):
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    end = i
                    break

        if end is None:
            return None

        array_str = content[array_start : end + 1]
        try:
            return json.loads(array_str)
        except json.JSONDecodeError:
            try:
                return json.loads(array_str.replace("\\/", "/"))
            except json.JSONDecodeError:
                return None

    def _choose_best_photo_url(self, photo: dict) -> str | None:
        """Pick the highest resolution URL from a responsivePhotos entry."""
        if not isinstance(photo, dict):
            return None

        candidates: list[tuple[int, str]] = []

        # mixedSources is typically a list of dicts with width/height/url
        mixed_sources = photo.get("mixedSources")
        candidates.extend(self._collect_candidates(mixed_sources))

        # rawMixedSources may be a dict keyed by format -> list of sources
        raw_sources = photo.get("rawMixedSources")
        if isinstance(raw_sources, dict):
            for value in raw_sources.values():
                candidates.extend(self._collect_candidates(value))
        else:
            candidates.extend(self._collect_candidates(raw_sources))

        # Fall back to direct url/src fields
        for key in ("url", "src"):
            direct_url = photo.get(key)
            if isinstance(direct_url, str):
                candidates.append((0, direct_url))

        if not candidates:
            return None

        # Choose candidate with max width (default 0) to prefer highest resolution
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]

    def _collect_candidates(self, source) -> list[tuple[int, str]]:
        """Collect (width, url) tuples from mixedSources variants."""
        results: list[tuple[int, str]] = []

        if isinstance(source, list):
            iterable = source
        elif isinstance(source, dict):
            iterable = source.values()
        else:
            return results

        for entry in iterable:
            if not isinstance(entry, dict):
                continue
            url = entry.get("url")
            width = entry.get("width") or entry.get("w") or 0
            if url and isinstance(url, str):
                try:
                    width_val = int(width)
                except (TypeError, ValueError):
                    width_val = 0
                results.append((width_val, url))

        return results

    async def _extract_zpid_from_url(self, tab: uc.Tab) -> str | None:
        """Extract zpid from current URL if present."""
        try:
            href = await tab.evaluate("() => window.location.href")
            match = re.search(r"/(\d+)_zpid", href)
            if match:
                return match.group(1)
        except Exception as e:
            logger.debug("%s could not parse zpid from URL: %s", self.name, e)
        return None

    async def _open_gallery_and_cycle(self, tab: uc.Tab, cycles: int = 60) -> None:
        """Open the photo gallery and cycle through images to force loading."""
        try:
            hero = await tab.query_selector("img[src*='photos.zillowstatic.com']")
            if hero:
                await hero.click()
                await asyncio.sleep(1.0)
                for _ in range(cycles):
                    await tab.press("ArrowRight")
                    await asyncio.sleep(0.25)
            else:
                # Fallback: scroll the hero area to trigger lazy load
                for _ in range(8):
                    await tab.scroll_down(600)
                    await asyncio.sleep(0.3)
        except Exception as e:
            logger.debug("%s _open_gallery_and_cycle failed: %s", self.name, e)

    async def extract_listing_metadata(self, tab: uc.Tab) -> dict:
        """Extract comprehensive listing metadata from loaded Zillow page.

        Extracts property details, market data, and features including:

        **Property Details**:
        - beds, baths, sqft, lot_sqft, year_built
        - property_type, garage_spaces, parking_spaces, pool, stories

        **Listing Metadata**:
        - list_price, hoa_fee, days_on_market
        - original_list_price, price_reduced, price_reduced_pct

        **Features**:
        - cooling_type, heating_type, flooring_types, appliances_included
        - sewer_type, water_source

        Args:
            tab: Browser tab with loaded Zillow property page

        Returns:
            Dictionary with all extracted fields (empty dict if extraction fails)

        Note:
            Call this after _extract_urls_from_page() while page is still loaded.
            Returns None for unavailable fields (doesn't fail).
        """
        logger.info("%s extracting comprehensive listing metadata", self.name)
        metadata: dict = {}

        try:
            # Get page content for extraction
            content = await tab.get_content()

            # Extract property details (core attributes)
            metadata.update(self._extract_property_details(content))

            # Extract property features (systems and amenities)
            metadata.update(self._extract_property_features(content))

            # Extract market data (pricing and timeline)
            metadata["days_on_market"] = self._extract_days_on_market(content)
            metadata.update(self._extract_price_info(content))

            # Extract HOA if present (backup extraction)
            hoa = self._extract_hoa_fee(content)
            if hoa is not None:
                metadata["hoa_fee"] = hoa

            # Count how many fields were successfully extracted
            non_none_count = sum(1 for v in metadata.values() if v is not None)
            logger.info(
                "%s extracted %d metadata fields (beds=%s, baths=%s, sqft=%s, DOM=%s)",
                self.name,
                non_none_count,
                metadata.get("beds"),
                metadata.get("baths"),
                metadata.get("sqft"),
                metadata.get("days_on_market"),
            )

            return metadata

        except Exception as e:
            logger.error("%s failed to extract metadata: %s", self.name, e)
            return {}

    def _extract_days_on_market(self, content: str) -> int | None:
        """Extract days on market from page content.

        Zillow patterns:
        - "X days on Zillow"
        - "Listed X hours ago"
        - "Just listed"
        """
        content_lower = content.lower()

        # Pattern: "X days on zillow"
        match = re.search(r"(\d+)\s+days?\s+on\s+zillow", content_lower)
        if match:
            return int(match.group(1))

        # Pattern: "Listed X hours ago" = 0 days
        if re.search(r"listed\s+\d+\s+hours?\s+ago", content_lower):
            return 0

        # Pattern: "Just listed"
        if "just listed" in content_lower:
            return 0

        # Try JSON-LD structured data
        match = re.search(r'"daysOnZillow"\s*:\s*(\d+)', content)
        if match:
            return int(match.group(1))

        return None

    def _extract_price_info(self, content: str) -> dict:
        """Extract price history and reduction info.

        Returns:
            Dict with original_list_price, price_reduced, price_reduced_pct
        """
        result: dict = {
            "original_list_price": None,
            "price_reduced": None,
            "price_reduced_pct": None,
        }

        # Look for price cut indicator
        content_lower = content.lower()

        # Pattern: "Price cut: -$X,XXX" or "Reduced $X,XXX"
        if "price cut" in content_lower or "price drop" in content_lower:
            result["price_reduced"] = True

            # Try to extract amount
            cut_match = re.search(
                r"(?:price\s+cut|reduced)[:\s]*-?\$?([\d,]+)",
                content_lower,
            )
            if cut_match:
                try:
                    cut_amount = int(cut_match.group(1).replace(",", ""))
                    result["price_reduced_amount"] = cut_amount
                except ValueError:
                    pass
        elif "price increased" in content_lower:
            result["price_reduced"] = False

        # Try to extract price history from JSON-LD
        # Pattern: "priceHistory":[{"date":"2025-01-15","price":450000}...]
        history_match = re.search(
            r'"priceHistory"\s*:\s*\[(.*?)\]',
            content,
            re.DOTALL,
        )
        if history_match:
            try:
                # Extract all prices from history
                prices = re.findall(r'"price"\s*:\s*(\d+)', history_match.group(1))
                if len(prices) >= 2:
                    prices_int = [int(p) for p in prices]
                    result["original_list_price"] = max(prices_int)
                    current_price = prices_int[-1]
                    if result["original_list_price"] > current_price:
                        result["price_reduced"] = True
                        result["price_reduced_pct"] = round(
                            (1 - current_price / result["original_list_price"]) * 100, 1
                        )
            except (ValueError, IndexError):
                pass

        return result

    def _extract_hoa_fee(self, content: str) -> int | None:
        """Extract HOA fee from page content.

        Patterns:
        - "HOA: $X/mo"
        - "HOA fee: $X monthly"
        - "No HOA" = 0
        """
        content_lower = content.lower()

        # No HOA
        if "no hoa" in content_lower:
            return 0

        # Pattern: "HOA: $XXX/mo"
        match = re.search(r"hoa[:\s]*\$?([\d,]+)\s*/?\s*mo", content_lower)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                pass

        # Pattern from JSON-LD: "monthlyHoaFee":XXX
        match = re.search(r'"monthlyHoaFee"\s*:\s*(\d+)', content)
        if match:
            return int(match.group(1))

        return None

    def _extract_property_details(self, content: str) -> dict:
        """Extract core property details from page content.

        Extracts:
        - beds (bedrooms count)
        - baths (bathrooms count)
        - sqft (interior square footage)
        - lot_sqft (lot size)
        - year_built
        - property_type (Single Family, Townhouse, etc.)
        - garage_spaces
        - parking_spaces
        - pool (boolean)
        - stories (number of floors)
        - list_price

        Returns:
            Dictionary with extracted property details (None for missing fields)
        """
        result: dict = {
            "beds": None,
            "baths": None,
            "sqft": None,
            "lot_sqft": None,
            "year_built": None,
            "property_type": None,
            "garage_spaces": None,
            "parking_spaces": None,
            "pool": None,
            "stories": None,
            "list_price": None,
        }

        # Try JSON-LD structured data first (most reliable)
        # Zillow embeds property data in script tags with application/ld+json
        json_ld_match = re.search(
            r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
            content,
            re.DOTALL | re.IGNORECASE,
        )

        if json_ld_match:
            try:
                import json

                json_data = json.loads(json_ld_match.group(1))

                # Beds (numberOfRooms, numberOfBedrooms)
                if "numberOfRooms" in json_data:
                    result["beds"] = int(json_data["numberOfRooms"])
                elif "numberOfBedrooms" in json_data:
                    result["beds"] = int(json_data["numberOfBedrooms"])

                # Baths (numberOfBathroomsTotal)
                if "numberOfBathroomsTotal" in json_data:
                    result["baths"] = float(json_data["numberOfBathroomsTotal"])

                # Sqft (floorSize value)
                if "floorSize" in json_data:
                    floor_size = json_data["floorSize"]
                    if isinstance(floor_size, dict) and "value" in floor_size:
                        result["sqft"] = int(floor_size["value"])
                    elif isinstance(floor_size, (int, float)):
                        result["sqft"] = int(floor_size)

                # List price (price)
                if "price" in json_data:
                    result["list_price"] = int(json_data["price"])

            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.debug("%s JSON-LD parsing partial failure: %s", self.name, e)

        # Fallback to regex patterns for fields not found in JSON-LD
        content_lower = content.lower()

        # Beds - patterns: "4 bd", "4 beds", "Bedrooms: 4"
        if result["beds"] is None:
            match = re.search(r"(\d+)\s*(?:bd|beds?|bedrooms?)[:\s]", content_lower)
            if match:
                result["beds"] = int(match.group(1))

        # Baths - patterns: "2 ba", "2.5 baths", "Bathrooms: 2"
        if result["baths"] is None:
            match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ba|baths?|bathrooms?)[:\s]", content_lower)
            if match:
                result["baths"] = float(match.group(1))

        # Sqft - patterns: "2,400 sqft", "2400 square feet"
        if result["sqft"] is None:
            match = re.search(r"([\d,]+)\s*(?:sqft|square\s*(?:feet|ft))", content_lower)
            if match:
                try:
                    result["sqft"] = int(match.group(1).replace(",", ""))
                except ValueError:
                    pass

        # Lot size - patterns: "7,500 sqft lot", "0.17 acres"
        match = re.search(r"([\d,]+)\s*sqft\s*lot", content_lower)
        if match:
            try:
                result["lot_sqft"] = int(match.group(1).replace(",", ""))
            except ValueError:
                pass
        else:
            # Convert acres to sqft (1 acre = 43,560 sqft)
            match = re.search(r"([\d.]+)\s*acres?", content_lower)
            if match:
                try:
                    acres = float(match.group(1))
                    result["lot_sqft"] = int(acres * 43560)
                except ValueError:
                    pass

        # Year built - patterns: "Built in 2020", "Year built: 2020"
        match = re.search(r"(?:built\s*in|year\s*built)[:\s]*(\d{4})", content_lower)
        if match:
            result["year_built"] = int(match.group(1))

        # Property type - patterns: "Single Family", "Townhouse", "Condo"
        type_patterns = [
            (r"single[\s-]family", "Single Family"),
            (r"townhouse", "Townhouse"),
            (r"condo(?:minium)?", "Condo"),
            (r"multi[\s-]family", "Multi Family"),
            (r"manufactured", "Manufactured"),
            (r"apartment", "Apartment"),
        ]
        for pattern, prop_type in type_patterns:
            if re.search(pattern, content_lower):
                result["property_type"] = prop_type
                break

        # Garage spaces - patterns: "2 car garage", "Garage spaces: 2"
        match = re.search(r"(\d+)[\s-]?car\s*garage", content_lower)
        if match:
            result["garage_spaces"] = int(match.group(1))
        else:
            match = re.search(r"garage[:\s]*(\d+)", content_lower)
            if match:
                result["garage_spaces"] = int(match.group(1))

        # Parking spaces - patterns: "Parking: 3 spaces"
        match = re.search(r"parking[:\s]*(\d+)", content_lower)
        if match:
            result["parking_spaces"] = int(match.group(1))

        # Pool - detect presence
        if "pool" in content_lower or "swimming pool" in content_lower:
            result["pool"] = True
        elif "no pool" in content_lower:
            result["pool"] = False

        # Stories - patterns: "2 stories", "Single story"
        if "single story" in content_lower or "one story" in content_lower:
            result["stories"] = 1
        else:
            match = re.search(r"(\d+)\s*stor(?:y|ies)", content_lower)
            if match:
                result["stories"] = int(match.group(1))

        # List price - patterns: "$450,000", "Price: $450000"
        if result["list_price"] is None:
            match = re.search(r"\$\s*([\d,]+)(?:\s*(?:usd)?)?", content_lower)
            if match:
                try:
                    price_str = match.group(1).replace(",", "")
                    price = int(price_str)
                    # Sanity check: price should be reasonable (50k-10M)
                    if 50000 <= price <= 10000000:
                        result["list_price"] = price
                except ValueError:
                    pass

        return result

    def _extract_property_features(self, content: str) -> dict:
        """Extract property features and systems from page content.

        Extracts:
        - cooling_type (Central, Evaporative, None)
        - heating_type (Gas, Electric, etc.)
        - flooring_types (Tile, Carpet, Hardwood, etc.)
        - appliances_included (list)
        - sewer_type (City, Septic)
        - water_source (City, Well)

        Returns:
            Dictionary with extracted features (None for missing fields)
        """
        result: dict = {
            "cooling_type": None,
            "heating_type": None,
            "flooring_types": None,
            "appliances_included": None,
            "sewer_type": None,
            "water_source": None,
        }

        content_lower = content.lower()

        # Cooling type
        if "central air" in content_lower or "central cooling" in content_lower:
            result["cooling_type"] = "Central"
        elif "evaporative cooling" in content_lower or "swamp cooler" in content_lower:
            result["cooling_type"] = "Evaporative"
        elif "no cooling" in content_lower or "none" in content_lower:
            result["cooling_type"] = "None"

        # Heating type
        if "gas heat" in content_lower or "natural gas" in content_lower:
            result["heating_type"] = "Gas"
        elif "electric heat" in content_lower:
            result["heating_type"] = "Electric"
        elif "heat pump" in content_lower:
            result["heating_type"] = "Heat Pump"
        elif "forced air" in content_lower:
            result["heating_type"] = "Forced Air"

        # Flooring types - collect all mentioned
        flooring_types = []
        if "tile" in content_lower:
            flooring_types.append("Tile")
        if "carpet" in content_lower:
            flooring_types.append("Carpet")
        if "hardwood" in content_lower or "wood floor" in content_lower:
            flooring_types.append("Hardwood")
        if "laminate" in content_lower:
            flooring_types.append("Laminate")
        if "vinyl" in content_lower:
            flooring_types.append("Vinyl")
        if "concrete" in content_lower:
            flooring_types.append("Concrete")
        if flooring_types:
            result["flooring_types"] = flooring_types

        # Appliances included
        appliances = []
        if "refrigerator" in content_lower or "fridge" in content_lower:
            appliances.append("Refrigerator")
        if "dishwasher" in content_lower:
            appliances.append("Dishwasher")
        if "microwave" in content_lower:
            appliances.append("Microwave")
        if "washer" in content_lower:
            appliances.append("Washer")
        if "dryer" in content_lower:
            appliances.append("Dryer")
        if "stove" in content_lower or "range" in content_lower or "oven" in content_lower:
            appliances.append("Stove/Oven")
        if appliances:
            result["appliances_included"] = appliances

        # Sewer type
        if "city sewer" in content_lower or "public sewer" in content_lower:
            result["sewer_type"] = "City"
        elif "septic" in content_lower:
            result["sewer_type"] = "Septic"

        # Water source
        if "city water" in content_lower or "public water" in content_lower:
            result["water_source"] = "City"
        elif "well" in content_lower and "water" in content_lower:
            result["water_source"] = "Well"

        return result

    async def _click_first_search_result(self, tab: uc.Tab) -> bool:
        """Click the first property result when on Zillow search results page.

        Handles the case where address search results in a search results page
        instead of a direct property detail page. Attempts to click the first
        property card/link to navigate to its detail page.

        Detection strategy:
        1. Try multiple selector patterns for search result links
        2. Priority order: most specific to most general
        3. Click first found element
        4. Log all attempts for debugging

        Args:
            tab: Browser tab with search results page

        Returns:
            True if successfully clicked a result link, False otherwise

        Security: Only used after validation confirms search results page
        """
        try:
            logger.info("%s Attempting to click first search result", self.name)

            # Priority selectors from most specific to most general
            search_result_selectors = [
                'article a[href*="homedetails"]',  # Article with homedetails link
                'a[data-test="property-card-link"]',  # Zillow property card link
                'div[data-test="property-card"] a',  # Link within property card
                'a[href*="/homedetails/"]',  # Any homedetails link
                'div[class*="property-card"] a',  # Property card with class
                'li[class*="result"] a',  # Result list item link
                'a[class*="result-link"]',  # Result link by class
                'div[role="link"] a',  # Link in role=link container
            ]

            for selector in search_result_selectors:
                try:
                    elements = await tab.query_selector_all(selector)
                    if elements:
                        link = elements[0]
                        logger.info(
                            "%s Found %d search results with selector: %s",
                            self.name,
                            len(elements),
                            selector,
                        )

                        # Get link URL for logging
                        href = link.attrs.get("href", "unknown")
                        absolute_href = (
                            f"{self.source.base_url}{href}"
                            if href.startswith("/")
                            else href
                        )
                        logger.debug(
                            "%s Clicking first result: %s",
                            self.name,
                            href[:100],
                        )

                        try:
                            await link.scroll_into_view()
                        except Exception:
                            pass

                        await link.click()

                        # Wait for SPA navigation to finish
                        if await self._wait_for_property_detail_page(tab, timeout=12):
                            if await self._check_for_captcha(tab):
                                logger.warning(
                                    "%s CAPTCHA detected after clicking search result, attempting solve",
                                    self.name,
                                )
                                if not await self._attempt_captcha_solve_v2(tab):
                                    logger.error(
                                        "%s CAPTCHA solving failed after search result click",
                                        self.name,
                                    )
                                    return False
                                await self._human_delay()
                                if await self._wait_for_property_detail_page(tab, timeout=8):
                                    return True
                            logger.info(
                                "%s Clicked first search result successfully",
                                self.name,
                            )
                            return True

                        logger.warning(
                            "%s Clicked first result but page did not transition, attempting direct navigation to href",
                            self.name,
                        )

                        if absolute_href and absolute_href != "unknown":
                            try:
                                await tab.get(absolute_href)
                                if await self._wait_for_property_detail_page(
                                    tab, timeout=10
                                ):
                                    logger.info(
                                        "%s Direct navigation to first result href succeeded",
                                        self.name,
                                    )
                                    return True
                            except Exception as nav_err:
                                logger.debug(
                                    "%s Direct navigation to href failed: %s",
                                    self.name,
                                    nav_err,
                                )
                        return False

                except Exception as e:
                    logger.debug(
                        "%s Failed to find/click with selector '%s': %s",
                        self.name,
                        selector,
                        e,
                    )
                    continue

            logger.warning(
                "%s Could not find any search result links with any selector",
                self.name,
            )
            return False

        except Exception as e:
            logger.error(
                "%s Error clicking first search result: %s",
                self.name,
                e,
            )
            return False

    async def _wait_for_property_detail_page(
        self, tab: uc.Tab, timeout: float = 12.0, interval: float = 1.0
    ) -> bool:
        """Poll for property detail signals after a navigation attempt."""
        start = time.monotonic()
        start_url = tab.url or ""
        checks = 0

        while time.monotonic() - start < timeout:
            checks += 1
            if await self._is_property_detail_page(tab):
                logger.info(
                    "%s Property detail page detected after %.1fs (checks=%d, url=%s)",
                    self.name,
                    time.monotonic() - start,
                    checks,
                    (tab.url or "")[:120],
                )
                return True

            await asyncio.sleep(interval)

        logger.warning(
            "%s Timed out waiting for property detail page (start_url=%s, final_url=%s)",
            self.name,
            start_url[:120],
            (tab.url or "")[:120],
        )
        return False

    async def _is_property_detail_page(self, tab: uc.Tab) -> bool:
        """Validate that we're on a property detail page, not search results.

        Detection strategy:
        1. Check for property detail indicators (photos carousel, listing data)
        2. Check for search results indicators (multiple property cards)
        3. Validate URL structure (should contain zpid or specific property path)
        4. NEW: Count zpid occurrences - detail pages have 1-5, search results have 10+
        5. NEW: Count property card patterns - more than 3 suggests search results
        6. NEW: Strict URL validation - must have /homedetails/ AND _zpid, reject _rb

        Args:
            tab: Browser tab to check

        Returns:
            True if on property detail page, False if on search results or other page

        Security: Prevents extracting images from multiple properties on search pages
        """
        try:
            content = await tab.get_content()
            content_lower = content.lower()
            current_url = tab.url or ""

            # FIX #1C: Strict URL validation - must have /homedetails/ AND _zpid, reject _rb
            url_lower = current_url.lower()
            if "_rb/" in url_lower or "_rb?" in url_lower:
                logger.warning(
                    "%s URL contains _rb suffix (search results URL): %s",
                    self.name,
                    current_url[:120],
                )
                return False

            # Fast path: URL or canonical link already points to a property detail page
            detail_url = "homedetails" in current_url or re.search(r"/\d+_zpid", current_url)
            canonical_detail = bool(
                re.search(r'rel=["\']canonical["\'][^>]+homedetails', content_lower)
            )
            if detail_url or canonical_detail:
                # Additional validation: must contain /homedetails/ path
                if "/homedetails/" not in url_lower:
                    logger.warning(
                        "%s URL missing /homedetails/ path despite other signals: %s",
                        self.name,
                        current_url[:120],
                    )
                    return False
                logger.info(
                    "%s Property detail page confirmed by URL (url=%s)",
                    self.name,
                    current_url[:120],
                )
                return True

            # Positive indicators for property detail page
            detail_indicators = [
                "photos.zillowstatic.com",  # Property photos CDN
                "propertydetails",  # Property details section
                "home-details",  # Home details container
                "zpid",  # Zillow Property ID (in URL or content)
                "photo-carousel",  # Photo gallery
                "hdp-listing",  # Home Details Page listing class
            ]

            # Negative indicators for search results page
            search_indicators = [
                "search-results",  # Search results container
                "list-result",  # Result list items
                "search-page-list",  # Search page listing
                "result-list-container",  # Results container
                "data-test=\"search-result\"",  # Search result test ID
            ]

            # Check for search result indicators
            search_hits = [indicator for indicator in search_indicators if indicator in content_lower]
            if search_hits:
                logger.warning(
                    "%s Search result indicators found: %s",
                    self.name,
                    ", ".join(search_hits[:3]),
                )
                return False

            # FIX #1A: zpid counting - detail pages have 1-5 zpid refs, search results have 10+
            zpid_count = content_lower.count("zpid")
            if zpid_count > 15:
                logger.warning(
                    "%s High zpid count (%d) suggests search results page",
                    self.name,
                    zpid_count,
                )
                return False

            # FIX #1B: Property card counting - more than 3 property cards = search results
            card_patterns = ["property-card", "list-card", "search-card", "styledpropertycard"]
            card_count = sum(content_lower.count(p) for p in card_patterns)
            if card_count > 3:
                logger.warning(
                    "%s Multiple property cards (%d) suggests search results page",
                    self.name,
                    card_count,
                )
                return False

            # Check for detail page indicators
            detail_count = sum(1 for ind in detail_indicators if ind in content_lower)
            if detail_count >= 2:  # At least 2 positive indicators
                logger.info(
                    "%s Validated property detail page (%d indicators)",
                    self.name,
                    detail_count,
                )
                return True

            # Check for very high zpid density as a fallback search-results signal
            if detail_count == 0 and zpid_count > 40:
                logger.warning(
                    "%s High zpid density without detail indicators (%d) - likely search results",
                    self.name,
                    zpid_count,
                )
                return False

            # If we got here, couldn't confirm it's a detail page
            logger.warning(
                "%s Could not confirm property detail page (indicators: %d, zpid_count: %d, card_count: %d, URL: %s)",
                self.name,
                detail_count,
                zpid_count,
                card_count,
                current_url[:80],
            )
            return False

        except Exception as e:
            logger.error("%s Error validating page type: %s", self.name, e)
            return False

    def _score_address_match(self, target: str, result_text: str) -> float:
        """FIX #5: Score how well autocomplete result matches target address (0.0-1.0).

        Evaluates address components:
        - Street number MUST match (0.5 points)
        - Street name words weighted by relevance (0.3 points)
        - City matching (0.2 points)

        Args:
            target: Target address string (e.g., "4732 W Davis Rd, Glendale, AZ 85306")
            result_text: Autocomplete result text from DOM

        Returns:
            Score from 0.0 to 1.0, where >= 0.5 indicates a strong match
        """
        target_lower = target.lower().replace(",", " ")
        result_lower = result_text.lower()

        # Extract components
        parts = target_lower.split()
        street_num = parts[0] if parts and parts[0].isdigit() else None

        score = 0.0

        # Street number MUST match
        if street_num and street_num in result_lower:
            score += 0.5
        else:
            return 0.0

        # Street name words (skip direction abbreviations and street types)
        street_words = [
            w
            for w in parts[1:4]
            if len(w) > 2 and w not in ("dr", "rd", "st", "ave", "ln", "ct", "blvd", "w", "e", "n", "s")
        ]
        if street_words:
            matched = sum(1 for w in street_words if w in result_lower)
            score += 0.3 * (matched / len(street_words))

        # City matching
        if len(parts) > 4:
            city = parts[-4] if parts[-4] not in ("az", "arizona") else parts[-5] if len(parts) > 5 else None
            if city and len(city) > 2 and city in result_lower:
                score += 0.2

        return score

    async def _navigate_to_property_via_search(
        self, property: Property, tab: uc.Tab
    ) -> bool:
        """Navigate to property using direct detail URL first, else interactive search.

        Mimics Redfin extractor's successful search pattern:
        1. Navigate to Zillow homepage
        2. Find search input field
        3. Type property address
        4. Wait for autocomplete suggestions
        5. Click matching suggestion
        6. Validate we landed on property detail page

        Args:
            property: Property to search for
            tab: Browser tab to use for navigation

        Returns:
            True if successfully navigated to property detail page, False otherwise

        Security: Prevents extracting wrong images from search results pages
        """
        try:
            # Step 0: Attempt direct detail URL (faster and more reliable when zpid known)
            direct_url = self._build_detail_url(property)
            try:
                logger.info("%s Trying direct detail URL: %s", self.name, direct_url)
                await tab.get(direct_url)
                await self._human_delay()
                if await self._is_property_detail_page(tab):
                    logger.info("%s Landed on detail page via direct URL", self.name)
                    return True
            except Exception as e:
                logger.debug("%s direct detail URL navigation failed: %s", self.name, e)

            # Step 1: Navigate to Zillow homepage for search
            logger.info(
                "%s Navigating to Zillow homepage for search",
                self.name,
            )
            await tab.get("https://www.zillow.com")
            await self._human_delay()

            # Dismiss cookie/consent overlays that can obscure the search bar
            try:
                consent_selectors = [
                    "button#onetrust-accept-btn-handler",
                    "button[aria-label*='accept']",
                    "button:contains('Accept')",
                    "button:contains('Agree')",
                ]
                for selector in consent_selectors:
                    try:
                        buttons = await tab.query_selector_all(selector)
                        if buttons:
                            await buttons[0].click()
                            logger.debug("%s dismissed consent with selector: %s", self.name, selector)
                            await self._human_delay(0.3, 0.8)
                            break
                    except Exception:
                        continue
            except Exception:
                pass

            # Early CAPTCHA check (homepage frequently triggers PerimeterX)
            if await self._check_for_captcha(tab):
                logger.warning("%s CAPTCHA detected on homepage, attempting solve", self.name)
                if not await self._attempt_captcha_solve_v2(tab):
                    logger.error("%s CAPTCHA solving failed on homepage", self.name)
                    return False
                await self._human_delay()

            # Step 2: Find search input field
            # FIX #2: Enhanced search input selectors (2025-compatible list)
            search_selectors = [
                # Primary: data-testid (most stable)
                'input[data-testid="search-bar-input"]',
                'input[id="search-box-input"]',
                # Secondary: ARIA attributes
                'input[aria-label*="search"]',
                'input[aria-label*="Search"]',
                # Tertiary: placeholder text
                'input[placeholder*="Enter an address"]',
                'input[placeholder*="Address"]',
                'input[placeholder*="Search"]',
                # Fallback: class-based
                'input[class*="SearchBox"]',
                'input[class*="search-input"]',
                'header input[type="text"]',
                'nav input[type="text"]',
            ]

            search_input = None
            # Retry a few times to allow hydration/overlays to settle
            for _ in range(3):
                for selector in search_selectors:
                    try:
                        elements = await tab.query_selector_all(selector)
                        if elements:
                            search_input = elements[0]
                            logger.debug(
                                "%s Found search input with selector: %s",
                                self.name,
                                selector,
                            )
                            break
                    except Exception:
                        continue
                if search_input:
                    break
                await asyncio.sleep(0.8)

            if not search_input:
                # If a CAPTCHA is blocking the page, try to solve and retry once
                if await self._check_for_captcha(tab):
                    logger.warning(
                        "%s CAPTCHA blocking search input, attempting solve",
                        self.name,
                    )
                    if await self._attempt_captcha_solve_v2(tab):
                        await self._human_delay()
                        for selector in search_selectors:
                            try:
                                elements = await tab.query_selector_all(selector)
                                if elements:
                                    search_input = elements[0]
                                    logger.debug(
                                        "%s Found search input after CAPTCHA solve with selector: %s",
                                        self.name,
                                        selector,
                                    )
                                    break
                            except Exception:
                                continue

            if not search_input:
                logger.error("%s Could not find search input field", self.name)
                # Fallback: direct search URL + click first result
                logger.warning(
                    "%s Falling back to direct search URL navigation",
                    self.name,
                )
                try:
                    search_url = self._build_search_url(property)
                    await tab.get(search_url)
                    await self._human_delay()
                    # Try to extract zpid from search page JSON and navigate directly
                    try:
                        content = await tab.get_content()
                        zpid_match = re.search(r'"zpid"\s*:\s*(\d+)', content)
                        if zpid_match:
                            zpid = zpid_match.group(1)
                            slug = (
                                f"{property.street.replace(' ', '-')}-"
                                f"{property.city.replace(' ', '-')}-"
                                f"{property.state}-{property.zip_code}"
                            )
                            detail_url = (
                                f"{self.source.base_url}/homedetails/{slug}/{zpid}_zpid/"
                            )
                            logger.info("%s Navigating directly to detail URL: %s", self.name, detail_url)
                            await tab.get(detail_url)
                            await self._human_delay()
                    except Exception:
                        pass
                    if await self._click_first_search_result(tab) and await self._wait_for_property_detail_page(
                        tab, timeout=12
                    ):
                        logger.info(
                            "%s Navigated to property via direct search fallback",
                            self.name,
                        )
                        return True
                except Exception as e:
                    logger.error("%s Fallback navigation failed: %s", self.name, e)
                return False

            # Step 3: Type property address
            full_address = property.full_address
            logger.info("%s Typing address: %s", self.name, full_address)

            # Click to focus
            await search_input.click()
            await asyncio.sleep(0.5)

            # Type address character by character (human-like)
            await search_input.send_keys(full_address)
            await asyncio.sleep(1.5)  # Wait for autocomplete

            # Step 4: Wait for and click autocomplete suggestion
            # FIX #3: Enhanced autocomplete selectors (address-specific patterns)
            autocomplete_selectors = [
                # Primary: data-testid (most stable)
                '[data-testid="search-result-list"] [data-testid="search-result"]',
                '[data-testid="address-suggestion"]',
                # Secondary: role-based
                '[role="listbox"] [role="option"]',
                '[role="option"][data-address]',
                'li[role="option"]',
                # Tertiary: class-based
                '.search-suggestions-list li',
                'ul[data-testid="search-results"] li',
                'li[data-type="address"]',
                # Fallback
                '.autocomplete-item',
                '.suggestion-item a',
            ]

            suggestion = None
            for selector in autocomplete_selectors:
                try:
                    elements = await tab.query_selector_all(selector)
                    if elements:
                        # FIX #5: Score address matches and click best match with score >= 0.5
                        best_suggestion = None
                        best_score = 0.0

                        for element in elements:
                            try:
                                result_text = await element.text_content()
                                if result_text:
                                    score = self._score_address_match(full_address, result_text)
                                    if score > best_score:
                                        best_score = score
                                        best_suggestion = element
                                        if score >= 0.8:  # Excellent match, can stop early
                                            break
                            except Exception:
                                continue

                        if best_suggestion and best_score >= 0.5:
                            suggestion = best_suggestion
                            logger.info(
                                "%s Found %d autocomplete suggestions, best match score: %.2f",
                                self.name,
                                len(elements),
                                best_score,
                            )
                        elif elements:
                            # Fallback: use first element if no good scoring match
                            suggestion = elements[0]
                            logger.info(
                                "%s Found %d autocomplete suggestions (no strong match, using first)",
                                self.name,
                                len(elements),
                            )
                        break
                except Exception:
                    continue

            if suggestion:
                logger.info("%s Clicking autocomplete suggestion", self.name)
                await suggestion.click()
                # Solve any interstitial CAPTCHA triggered by search
                if await self._check_for_captcha(tab):
                    logger.warning("%s CAPTCHA detected after autocomplete click, attempting solve", self.name)
                    if not await self._attempt_captcha_solve_v2(tab):
                        logger.error("%s CAPTCHA solving failed after autocomplete click", self.name)
                        return False
                    await self._human_delay()
            else:
                # Fallback: Press Enter to submit search
                logger.warning(
                    "%s No autocomplete found, pressing Enter",
                    self.name,
                )
                await search_input.send_keys("\n")

            # Give the SPA a moment to start navigation before polling
            await asyncio.sleep(1.5)

            # Step 5: Validate we landed on property detail page
            if await self._wait_for_property_detail_page(tab, timeout=15):
                logger.info(
                    "%s Successfully navigated to property detail page via search",
                    self.name,
                )
                return True

            # Check if we landed on search results instead
            logger.warning(
                "%s Did not land on property detail page, checking for search results",
                self.name,
            )

            # Try clicking the first search result (with its own wait/validation)
            if await self._click_first_search_result(tab):
                logger.info(
                    "%s Successfully navigated to property detail page from search results",
                    self.name,
                )
                return True

            logger.error(
                "%s Could not click first search result",
                self.name,
            )
            return False

        except Exception as e:
            logger.error(
                "%s Error during interactive search navigation: %s",
                self.name,
                e,
            )
            return False

    async def extract_image_urls(self, property: Property) -> list[str]:
        """Extract image URLs and listing metadata from Zillow page.

        Overrides base class to additionally extract listing metadata
        (days_on_market, price_reduced, etc.) on the same tab before closing.

        Metadata is stored in self.last_metadata and can be retrieved by
        orchestrator after extraction.

        Navigation Strategy:
        1. Try interactive search navigation (PRIMARY - prevents wrong page)
        2. Validate we're on property detail page
        3. If on wrong page (search results), abort with empty list

        Args:
            property: Property to extract images for

        Returns:
            List of image URLs discovered

        Raises:
            SourceUnavailableError: If CAPTCHA solving fails
            ExtractionError: For other extraction failures
        """
        logger.info("%s extracting images for: %s", self.name, property.full_address)

        # Get browser and create new tab
        browser = await self._browser_pool.get_browser()
        tab = await browser.get("about:blank")

        try:
            # Phase 1 Safety: Use interactive search to navigate
            # This is more reliable than direct URL navigation and avoids search results
            navigation_success = await self._navigate_to_property_via_search(
                property, tab
            )

            if not navigation_success:
                logger.warning(
                    "%s Could not navigate to property detail page for %s",
                    self.name,
                    property.full_address,
                )
                return []

            # Phase 2 Safety: Validate we're on property detail page
            if not await self._is_property_detail_page(tab):
                logger.error(
                    "%s Landed on wrong page type (not property detail) for %s - aborting",
                    self.name,
                    property.full_address,
                )
                return []

            # Check for CAPTCHA
            if await self._check_for_captcha(tab):
                logger.warning(
                    "%s CAPTCHA detected for %s",
                    self.name,
                    property.full_address,
                )

                # Attempt to solve CAPTCHA
                if not await self._attempt_captcha_solve_v2(tab):
                    logger.error(
                        "%s CAPTCHA solving failed for %s",
                        self.name,
                        property.full_address,
                    )
                    from .base import SourceUnavailableError

                    raise SourceUnavailableError(
                        self.source,
                        "CAPTCHA detected and solving failed",
                        retry_after=300,  # 5 minutes
                    )

                logger.info("%s CAPTCHA solved for %s", self.name, property.full_address)

            # Add human delay before extraction
            await self._human_delay()

            # Try to open gallery and cycle through photos to force load
            try:
                await self._open_gallery_and_cycle(tab)
            except Exception as e:
                logger.debug("%s gallery cycle skipped: %s", self.name, e)

            # Determine zpid from property or URL for JSON filtering
            expected_zpid = getattr(property, "zpid", None)
            if not expected_zpid:
                expected_zpid = await self._extract_zpid_from_url(tab)
                if expected_zpid:
                    property.zpid = expected_zpid

            # Extract URLs from page
            raw_urls = await self._extract_urls_from_page(tab, expected_zpid=expected_zpid)

            # FIX: Apply comprehensive URL filtering to prevent search result contamination
            # This filters by zpid, search result patterns, and quality
            urls = self._filter_urls_for_property(raw_urls, expected_zpid)

            logger.info(
                "%s URL filtering: %d raw -> %d filtered (zpid=%s)",
                self.name,
                len(raw_urls),
                len(urls),
                expected_zpid or "unknown",
            )

            # FIX: Safety check - too many URLs even after filtering suggests contamination
            if len(urls) > self.MAX_EXPECTED_IMAGES_PER_PROPERTY:
                logger.warning(
                    "%s Extracted %d URLs (threshold %d), re-validating page type",
                    self.name,
                    len(urls),
                    self.MAX_EXPECTED_IMAGES_PER_PROPERTY,
                )
                if not await self._is_property_detail_page(tab):
                    logger.error(
                        "%s Page validation failed after high URL count - aborting extraction",
                        self.name,
                    )
                    return []

                # Even if page validates, cap at MAX to prevent contamination
                logger.warning(
                    "%s Capping URL count from %d to %d to prevent contamination",
                    self.name,
                    len(urls),
                    self.MAX_EXPECTED_IMAGES_PER_PROPERTY,
                )
                urls = urls[: self.MAX_EXPECTED_IMAGES_PER_PROPERTY]

            # If we have far fewer than expected, scroll the gallery to force load and retry
            if len(urls) < 20:
                try:
                    for _ in range(5):
                        await tab.scroll_down(800)
                        await asyncio.sleep(0.6)
                    retry_raw = await self._extract_urls_from_page(
                        tab, expected_zpid=expected_zpid
                    )
                    retry_urls = self._filter_urls_for_property(retry_raw, expected_zpid)
                    if len(retry_urls) > len(urls):
                        urls = retry_urls
                        logger.info(
                            "%s Retried extraction after gallery scroll: %d URLs",
                            self.name,
                            len(urls),
                        )
                except Exception as e:
                    logger.debug("%s gallery scroll retry failed: %s", self.name, e)

            # ENHANCEMENT: Extract listing metadata on same tab
            self.last_metadata = await self.extract_listing_metadata(tab)

            logger.info(
                "%s extracted %d image URLs + metadata for %s",
                self.name,
                len(urls),
                property.full_address,
            )

            return urls

        finally:
            # Always close the tab
            try:
                await tab.close()
            except Exception as e:
                logger.warning("%s error closing tab: %s", self.name, e)
