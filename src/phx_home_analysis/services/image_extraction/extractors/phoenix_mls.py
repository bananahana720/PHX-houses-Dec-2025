"""Phoenix MLS image extractor implementation.

Extracts property images from phoenixmlssearch.com using stealth browser
(nodriver) to bypass WAF protection. Handles search by address and gallery
image extraction.

Enhanced (E2.R1): Now also extracts metadata including MLS fields, kill-switch
criteria, property details, and school information.

WAF Protection: PhoenixMLS uses RunCloud 7G WAF that blocks standard HTTP
requests with 403 Forbidden. Stealth browser automation is required.
"""

import asyncio
import logging
import re
from typing import Any
from urllib.parse import quote_plus, urljoin

import httpx
import nodriver as uc
from bs4 import BeautifulSoup

from ....config.settings import StealthExtractionConfig
from ....domain.entities import Property
from ....domain.enums import ImageSource
from .stealth_base import StealthBrowserExtractor

logger = logging.getLogger(__name__)


# Phoenix metro area cities that Phoenix MLS covers
PHOENIX_METRO_CITIES = {
    "anthem",
    "apache junction",
    "avondale",
    "buckeye",
    "carefree",
    "casa grande",
    "cave creek",
    "chandler",
    "el mirage",
    "fountain hills",
    "gilbert",
    "glendale",
    "gold canyon",
    "goodyear",
    "laveen",
    "litchfield park",
    "maricopa",
    "mesa",
    "new river",
    "paradise valley",
    "peoria",
    "phoenix",
    "queen creek",
    "rio verde",
    "san tan valley",
    "scottsdale",
    "sun city",
    "sun city west",
    "sun lakes",
    "surprise",
    "tempe",
    "tolleson",
    "wickenburg",
}


# Pre-compiled regex patterns for HTML parsing (performance optimization)
# URL patterns
RE_MLS_LISTING_URL = re.compile(r"/mls/listing/")
RE_PROPERTY_TITLE_LINK = re.compile(r"(property|listing)-(title|link)")

# Gallery patterns
RE_GALLERY_CONTAINER = re.compile(r"(gallery|photos|images|slideshow)", re.IGNORECASE)

# MLS identifier patterns
RE_MLS_NUMBER = re.compile(r"MLS #")
RE_MLS_NUMBER_EXTRACT = re.compile(r"MLS #:\s*(\w+)")
RE_PRICE_EXTRACT = re.compile(r"\$([0-9,]+)")

# Property details patterns
RE_PRICE_ELEMENT = re.compile(r"price|listing-price")
RE_DETAILS_TABLE = re.compile(r"details|facts|features")
RE_STATUS_BADGE = re.compile(r"status|badge|tag", re.IGNORECASE)
RE_PRICE_HISTORY = re.compile(r"price-history|original|reduced")
RE_PRICE_REDUCED = re.compile(r"price\s*reduced", re.IGNORECASE)
RE_UPDATED = re.compile(r"(?:last\s*)?updated|modified", re.IGNORECASE)
RE_ORIGINAL_PRICE = re.compile(r"(?:original(?:\s+price)?|was)[:\s]*\$([0-9,]+)", re.IGNORECASE)

# Date patterns
RE_ISO_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")
RE_US_DATE = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")

# Section patterns
RE_SCHOOL_SECTION = re.compile(r"school|education")
RE_FEATURES_SECTION = re.compile(r"features|amenities")
RE_ELEMENTARY = re.compile(r"Elementary:?\s*(.+)", re.IGNORECASE)
RE_MIDDLE = re.compile(r"Middle:?\s*(.+)", re.IGNORECASE)
RE_HIGH = re.compile(r"High:?\s*(.+)", re.IGNORECASE)
RE_KITCHEN = re.compile(r"Kitchen", re.IGNORECASE)
RE_MASTER_BATH = re.compile(r"Master Bath", re.IGNORECASE)
RE_INTERIOR = re.compile(r"Interior", re.IGNORECASE)
RE_EXTERIOR = re.compile(r"Exterior", re.IGNORECASE)
RE_CROSS_STREETS = re.compile(r"Cross Streets", re.IGNORECASE)
RE_CROSS_STREETS_EXTRACT = re.compile(r"Cross Streets:?\s*(.+)", re.IGNORECASE)

# === E2-R3: NEW EXTRACTION PATTERNS ===

# Geo coordinate patterns
RE_GEO_LAT = re.compile(r"Geo\s*Lat[:\s]*(-?\d+\.?\d*)", re.IGNORECASE)
RE_GEO_LON = re.compile(r"Geo\s*Lon[:\s]*(-?\d+\.?\d*)", re.IGNORECASE)

# Legal/Parcel patterns
RE_TOWNSHIP = re.compile(r"Township[:\s]*([^<\n,]+)", re.IGNORECASE)
RE_RANGE = re.compile(r"Range[:\s]*([^<\n,]+)", re.IGNORECASE)
RE_SECTION = re.compile(r"Section[:\s]*(\d+)", re.IGNORECASE)
RE_LOT_NUMBER = re.compile(r"Lot\s*(?:Number)?[:\s]*([^<\n,]+)", re.IGNORECASE)
RE_SUBDIVISION = re.compile(r"Subdivision[:\s]*([^<\n]+)", re.IGNORECASE)
RE_APN = re.compile(
    r"(?:Assessor\s*(?:Number|Parcel)|APN|Parcel\s*(?:Number|ID))[:\s]*([^<\n,]+)",
    re.IGNORECASE,
)

# Property structure patterns
RE_EXTERIOR_STORIES = re.compile(r"(?:Exterior\s*)?Stories[:\s]*(\d+)", re.IGNORECASE)
RE_INTERIOR_LEVELS = re.compile(r"(?:Interior\s*)?Levels[:\s]*([^<\n,]+)", re.IGNORECASE)
RE_BUILDER = re.compile(r"Builder(?:\s*Name)?[:\s]*([^<\n,]+)", re.IGNORECASE)
RE_DWELLING_STYLES = re.compile(r"Dwelling\s*(?:Styles?|Type)[:\s]*([^<\n]+)", re.IGNORECASE)

# School district patterns (separate from school names)
RE_ELEMENTARY_DISTRICT = re.compile(
    r"Elementary\s*(?:School\s*)?District[:\s]*([^<\n]+)", re.IGNORECASE
)
RE_MIDDLE_DISTRICT = re.compile(
    r"(?:Jr\.?\s*High|Middle)\s*(?:School\s*)?District[:\s]*([^<\n]+)", re.IGNORECASE
)
RE_HIGH_DISTRICT = re.compile(r"High\s*(?:School\s*)?District[:\s]*([^<\n]+)", re.IGNORECASE)

# Contract/Listing patterns
RE_LIST_DATE = re.compile(
    r"List\s*Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4}|\d{4}-\d{2}-\d{2})", re.IGNORECASE
)
RE_OWNERSHIP = re.compile(r"Ownership(?:\s*Type)?[:\s]*([^<\n,]+)", re.IGNORECASE)
RE_POSSESSION = re.compile(r"Possession(?:\s*Terms)?[:\s]*([^<\n]+)", re.IGNORECASE)
RE_NEW_FINANCING = re.compile(r"New\s*Financing[:\s]*([^<\n]+)", re.IGNORECASE)

# Pool details patterns
RE_PRIVATE_POOL_FEATURES = re.compile(
    r"Private\s*Pool(?:\s*Features)?[:\s]*([^<\n]+)", re.IGNORECASE
)
RE_SPA = re.compile(r"(?<!<)(?<!n )Spa[:\s]+([^<\n,]+)", re.IGNORECASE)
RE_COMMUNITY_POOL = re.compile(r"Community\s*Pool[:\s]*(Yes|No|Y|N|True|False)", re.IGNORECASE)

# Updates/Renovations patterns
RE_KITCHEN_YEAR_UPDATED = re.compile(r"Kitchen\s*(?:Yr|Year)\s*Updated[:\s]*(\d{4})", re.IGNORECASE)
RE_KITCHEN_UPDATE_SCOPE = re.compile(r"Kitchen\s*(?:Partial|Full)[:\s]*([^<\n,]+)", re.IGNORECASE)

# Basement pattern
RE_BASEMENT = re.compile(r"Basement[:\s]*(Yes|No|Y|N|Full|Partial|Finished|None)", re.IGNORECASE)

# Fireplaces total pattern
RE_FIREPLACES_TOTAL = re.compile(r"Fireplaces?\s*Total[:\s]*(\d+)", re.IGNORECASE)

# Covered spaces pattern
RE_TOTAL_COVERED_SPACES = re.compile(r"Total\s*Covered\s*Spaces[:\s]*(\d+)", re.IGNORECASE)

# Feature list patterns (for comma/semicolon separated lists)
RE_VIEW = re.compile(r"View[:\s]*([^<\n]+)", re.IGNORECASE)
RE_COMMUNITY_FEATURES = re.compile(r"Community\s*Features[:\s]*([^<\n]+)", re.IGNORECASE)
RE_PROPERTY_DESCRIPTION = re.compile(r"Property\s*Description[:\s]*([^<\n]+)", re.IGNORECASE)
RE_DINING_AREA = re.compile(r"Dining\s*(?:Area|Room)[:\s]*([^<\n]+)", re.IGNORECASE)
RE_TECHNOLOGY = re.compile(r"Technology[:\s]*([^<\n]+)", re.IGNORECASE)
RE_WINDOW = re.compile(r"Window(?:\s*Features)?[:\s]*([^<\n]+)", re.IGNORECASE)
RE_OTHER_ROOMS = re.compile(r"Other\s*Rooms[:\s]*([^<\n]+)", re.IGNORECASE)
RE_CONSTRUCTION = re.compile(r"Construction[:\s]*([^<\n]+)", re.IGNORECASE)
RE_CONSTRUCTION_FINISH = re.compile(
    r"Const(?:ruction)?\s*-?\s*Finish[:\s]*([^<\n]+)", re.IGNORECASE
)
RE_PARKING = re.compile(r"Parking(?:\s*Features)?[:\s]*([^<\n]+)", re.IGNORECASE)
RE_FENCING = re.compile(r"Fencing[:\s]*([^<\n]+)", re.IGNORECASE)
RE_UTILITIES = re.compile(r"Utilities[:\s]*([^<\n]+)", re.IGNORECASE)
RE_SERVICES = re.compile(r"Services(?:\s*Available)?[:\s]*([^<\n]+)", re.IGNORECASE)

# Remarks patterns
RE_PUBLIC_REMARKS = re.compile(r"(?:Public\s*)?Remarks:\s*([^<]+)", re.IGNORECASE)
RE_DIRECTIONS = re.compile(r"Directions:\s*([^<]+)", re.IGNORECASE)

# Days on market patterns (list of patterns)
DOM_PATTERNS = [
    re.compile(r"(?:listed|on market)\s+(\d+)\s*days?\s*ago", re.IGNORECASE),
    re.compile(r"(?:dom|days on market)[:\s]+(\d+)", re.IGNORECASE),
    re.compile(r"(\d+)\s*days?\s*on\s*market", re.IGNORECASE),
]


class PhoenixMLSExtractor(StealthBrowserExtractor):
    """Extract property images from Phoenix MLS Search website.

    Uses nodriver stealth browser to bypass WAF protection. Searches by
    address to find property pages, then extracts gallery images and metadata.

    WAF Protection: PhoenixMLS uses RunCloud 7G WAF that blocks standard HTTP
    requests. Stealth browser automation is required to access the site.

    Architecture:
    - Extends StealthBrowserExtractor for WAF bypass
    - Implements _build_search_url() and _extract_urls_from_page()
    - Preserves existing metadata parsing logic
    """

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        config: StealthExtractionConfig | None = None,
    ):
        """Initialize PhoenixMLS extractor with stealth configuration.

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
            ImageSource.PHOENIX_MLS
        """
        return ImageSource.PHOENIX_MLS

    def can_handle(self, property: Property) -> bool:
        """Check if this extractor can handle the given property.

        Phoenix MLS only covers Phoenix metropolitan area cities.

        Args:
            property: Property to check

        Returns:
            True if property is in Phoenix metro area
        """
        # Validate base_url is configured
        if not hasattr(self.source, "base_url") or not self.source.base_url:
            logger.warning(f"{self.source.name} has no base_url configured")
            return False

        # Check if city is in Phoenix metro area
        city_normalized = property.city.lower().strip()
        return city_normalized in PHOENIX_METRO_CITIES

    def _build_search_url(self, property: Property) -> str:
        """Build PhoenixMLS search URL from property address.

        PhoenixMLS search URL format:
            /mls/search/?OrderBy=-ListPrice&StandardStatus[]=Active&StreetAddress={address}

        Args:
            property: Property entity with address components

        Returns:
            Full PhoenixMLS search URL for the property

        Example:
            Input: "4732 W Davis Rd", "Glendale", "AZ"
            Output: "https://phoenixmlssearch.com/mls/search/?...&StreetAddress=4732+W+Davis+Rd+Glendale+AZ"
        """
        # Build address query
        address_query = f"{property.street} {property.city} {property.state}"
        encoded_address = quote_plus(address_query)

        # Build full URL
        url = (
            f"{self.source.base_url}/mls/search/"
            f"?OrderBy=-ListPrice&StandardStatus[]=Active&StreetAddress={encoded_address}"
        )

        logger.debug("%s built search URL: %s", self.name, url)
        return url

    async def _extract_urls_from_page(self, tab: uc.Tab) -> list[str]:
        """Extract image URLs from PhoenixMLS listing detail page.

        Strategy:
        1. Get search results page HTML from browser tab
        2. Find listing link matching the property address
        3. Navigate to the listing detail page
        4. Extract image URLs from gallery on detail page
        5. Extract metadata and cache on property

        Args:
            tab: Browser tab with loaded PhoenixMLS search results page

        Returns:
            List of image URLs found
        """
        try:
            # Step 1: Get search results page HTML
            search_html = await tab.get_content()
            search_url = tab.target.url if hasattr(tab, "target") else str(tab.url)

            # Step 2: Find listing detail page URL
            listing_url = self._find_listing_url(search_html, search_url)

            if not listing_url:
                logger.warning(
                    "%s could not find listing detail page link in search results",
                    self.name,
                )
                return []

            # Step 3: Navigate to listing detail page
            logger.debug("%s navigating to listing detail: %s", self.name, listing_url)
            await tab.get(listing_url)

            # Wait for page to load
            await asyncio.sleep(2)

            # Step 4: Get listing detail page HTML
            detail_html = await tab.get_content()
            detail_url = tab.target.url if hasattr(tab, "target") else str(tab.url)

            # Step 5a: Parse image gallery
            image_urls = self._parse_image_gallery(detail_html, detail_url)

            # Step 5b: Parse metadata
            metadata = self._parse_listing_metadata(detail_html)
            self.last_metadata = metadata

            logger.info(
                "%s extracted %d image URLs + metadata from listing detail page",
                self.name,
                len(image_urls),
            )

            return image_urls

        except Exception as e:
            logger.error("%s failed to extract URLs from page: %s", self.name, e)
            return []

    def _find_listing_url(self, search_html: str, base_url: str) -> str | None:
        """Find the listing detail page URL from search results.

        Searches for listing cards/links in the search results page and extracts
        the first listing detail page URL.

        Common PhoenixMLS search result patterns:
        - <a> tags with href to /mls/listing/{id}
        - Listing cards with data attributes
        - Property titles with links

        Args:
            search_html: HTML content of search results page
            base_url: Base URL for resolving relative URLs

        Returns:
            Absolute URL to listing detail page, or None if not found
        """
        soup = BeautifulSoup(search_html, "html.parser")

        # Pattern 1: Look for links to /mls/listing/ pages
        listing_links = soup.find_all("a", href=RE_MLS_LISTING_URL)
        if listing_links:
            first_link = listing_links[0]
            href = first_link.get("href")
            if href:
                listing_url = urljoin(base_url, str(href))
                logger.debug("Found listing URL via /mls/listing/ pattern: %s", listing_url)
                return listing_url

        # Pattern 2: Look for property cards with data-listing-id
        property_cards = soup.find_all(["div", "article"], attrs={"data-listing-id": True})
        for card in property_cards:
            # Find link within card
            link = card.find("a", href=True)
            if link:
                href = link.get("href")
                if href and ("/listing/" in str(href) or "/property/" in str(href)):
                    listing_url = urljoin(base_url, str(href))
                    logger.debug("Found listing URL via property card: %s", listing_url)
                    return listing_url

        # Pattern 3: Look for property title links
        title_links = soup.find_all("a", class_=RE_PROPERTY_TITLE_LINK)
        if title_links:
            first_link = title_links[0]
            href = first_link.get("href")
            if href:
                listing_url = urljoin(base_url, str(href))
                logger.debug("Found listing URL via title link: %s", listing_url)
                return listing_url

        # Pattern 4: Generic fallback - find any link containing "listing" or "property"
        all_links = soup.find_all("a", href=True)
        for link in all_links:
            href = str(link.get("href", ""))
            if "/listing/" in href or "/property/" in href:
                # Exclude search/filter/sort links
                if "search" not in href and "filter" not in href and "sort" not in href:
                    listing_url = urljoin(base_url, href)
                    logger.debug("Found listing URL via generic pattern: %s", listing_url)
                    return listing_url

        logger.warning("No listing URL found in search results")
        return None

    def _parse_image_gallery(self, html: str, base_url: str) -> list[str]:
        """Parse image gallery from listing page HTML.

        Prioritizes SparkPlatform CDN URLs (cdn.photos.sparkplatform.com) which
        are the actual property photos. Filters out site assets like logos, icons.

        Common MLS image gallery patterns:
        - <img> tags in gallery containers (class/id with "gallery", "photos", etc.)
        - Data attributes with image URLs (data-src, data-image-url)
        - JavaScript arrays with image URLs in <script> tags
        - Thumbnail links (<a> tags pointing to full-size images)

        Args:
            html: HTML content of listing page
            base_url: Base URL for resolving relative URLs

        Returns:
            List of absolute image URLs (prioritized: SparkPlatform first, then others)
        """
        soup = BeautifulSoup(html, "html.parser")
        sparkplatform_urls: list[str] = []
        other_urls: list[str] = []
        seen_urls: set[str] = set()

        # Pattern 1: Look for common gallery containers
        gallery_containers = soup.find_all(
            ["div", "section"],
            class_=RE_GALLERY_CONTAINER,
        )

        for container in gallery_containers:
            # Find all images in container
            for img in container.find_all("img"):
                url = self._extract_image_url(img, base_url)
                if url and url not in seen_urls and self._is_property_image(url):
                    if "cdn.photos.sparkplatform.com" in url:
                        sparkplatform_urls.append(url)
                    else:
                        other_urls.append(url)
                    seen_urls.add(url)

        # Pattern 2: Look for image links (thumbnail -> full size)
        for link in soup.find_all("a", href=True):
            href_attr = link.get("href")
            # href can be None or a list in BeautifulSoup
            if not href_attr:
                continue
            if isinstance(href_attr, list):
                href = href_attr[0] if href_attr else ""
            else:
                href = str(href_attr)
            if not href:
                continue
            # Check if href points to an image file
            if self._is_image_url(href):
                absolute_url = urljoin(base_url, href)
                if absolute_url not in seen_urls and self._is_property_image(absolute_url):
                    if "cdn.photos.sparkplatform.com" in absolute_url:
                        sparkplatform_urls.append(absolute_url)
                    else:
                        other_urls.append(absolute_url)
                    seen_urls.add(absolute_url)

        # Pattern 3: Look for script tags with image arrays
        # Many MLS sites embed image URLs in JavaScript
        for script in soup.find_all("script"):
            script_text = script.string
            if script_text:
                js_image_urls = self._extract_urls_from_script(script_text)
                for url in js_image_urls:
                    absolute_url = urljoin(base_url, url)
                    if absolute_url not in seen_urls and self._is_property_image(absolute_url):
                        if "cdn.photos.sparkplatform.com" in absolute_url:
                            sparkplatform_urls.append(absolute_url)
                        else:
                            other_urls.append(absolute_url)
                        seen_urls.add(absolute_url)

        # Prioritize SparkPlatform CDN URLs (actual property photos)
        image_urls = sparkplatform_urls + other_urls

        logger.debug(
            f"Parsed {len(image_urls)} image URLs from gallery "
            f"({len(sparkplatform_urls)} SparkPlatform, {len(other_urls)} other)"
        )
        return image_urls

    def _extract_image_url(self, img_tag: object, base_url: str) -> str | None:
        """Extract image URL from <img> tag.

        Checks multiple attributes: src, data-src, data-original, data-lazy-src.

        Args:
            img_tag: BeautifulSoup <img> tag
            base_url: Base URL for resolving relative URLs

        Returns:
            Absolute image URL or None
        """
        # img_tag is a BeautifulSoup Tag object - type as Any for attribute access
        tag: Any = img_tag

        # Try common image URL attributes
        for attr in ["src", "data-src", "data-original", "data-lazy-src", "data-url"]:
            url = tag.get(attr)
            if url:
                # Skip placeholder/loading images
                if "placeholder" in str(url).lower() or "loading" in str(url).lower():
                    continue
                # Skip data URIs
                if str(url).startswith("data:"):
                    continue
                # Convert to absolute URL
                return str(urljoin(base_url, str(url)))
        return None

    def _is_image_url(self, url: str) -> bool:
        """Check if URL points to an image file.

        Args:
            url: URL to check

        Returns:
            True if URL has image file extension
        """
        image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
        url_lower = url.lower()
        return any(url_lower.endswith(ext) for ext in image_extensions)

    def _is_property_image(self, url: str) -> bool:
        """Check if URL is a property image (not site asset).

        Filters out:
        - Site logos (logo.gif, logo.png, etc.)
        - Icons and UI elements (icon-, sprite-, ui-)
        - Thumbnails smaller than property photos
        - Placeholder images

        Args:
            url: Image URL to check

        Returns:
            True if URL appears to be a property photo
        """
        url_lower = url.lower()

        # Filter out site assets by filename patterns
        site_asset_patterns = [
            "logo",
            "icon-",
            "sprite",
            "ui-",
            "button",
            "banner",
            "header",
            "footer",
            "placeholder",
            "loading",
            "watermark",
        ]

        for pattern in site_asset_patterns:
            if pattern in url_lower:
                logger.debug(f"Blocked URL: {url} (matched pattern: {pattern})")
                return False

        return True

    def _extract_urls_from_script(self, script_text: str) -> list[str]:
        """Extract image URLs from JavaScript code.

        Looks for common patterns:
        - Array literals: ["url1.jpg", "url2.jpg"]
        - String literals with image extensions

        Args:
            script_text: JavaScript code as string

        Returns:
            List of image URLs found
        """
        urls: list[str] = []

        # Pattern: URLs in quotes with image extensions
        url_pattern = r'["\']([^"\']+\.(?:jpg|jpeg|png|gif|webp)(?:\?[^"\']*)?)["\']'
        matches = re.findall(url_pattern, script_text, re.IGNORECASE)

        for match in matches:
            # Skip very short URLs (likely not real images)
            if len(match) > 10:
                urls.append(match)

        return urls

    def _parse_listing_metadata(self, html: str) -> dict[str, Any]:
        """Parse listing metadata from PhoenixMLS page HTML.

        Extracts all MLS fields from listing detail page using BeautifulSoup
        and structured selectors.

        Args:
            html: HTML content of listing page

        Returns:
            Dict of metadata fields (property_type, beds, baths, etc.)
        """
        soup = BeautifulSoup(html, "html.parser")
        metadata: dict[str, Any] = {}

        # MLS Number (e.g., "MLS #: 6789012")
        mls_elem = soup.find(string=RE_MLS_NUMBER)
        if mls_elem:
            mls_match = RE_MLS_NUMBER_EXTRACT.search(str(mls_elem))
            if mls_match:
                metadata["mls_number"] = mls_match.group(1)

        # Price
        price_elem = soup.find("span", class_=RE_PRICE_ELEMENT)
        if price_elem:
            price_text = price_elem.get_text(strip=True)
            price_match = RE_PRICE_EXTRACT.search(price_text)
            if price_match:
                metadata["price"] = int(price_match.group(1).replace(",", ""))

        # Property Details Table (common pattern on MLS sites)
        details_table = soup.find("table", class_=RE_DETAILS_TABLE)
        if details_table:
            for row in details_table.find_all("tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    # Map common labels to fields
                    if "bed" in label:
                        metadata["beds"] = self._parse_int_safe(value)
                    elif "bath" in label:
                        metadata["baths"] = self._parse_float_safe(value)
                    elif "sqft" in label or "square feet" in label:
                        metadata["sqft"] = self._parse_int_safe(value.replace(",", ""))
                    elif "lot size" in label:
                        # Handle "8,500 sqft" or "0.19 acres"
                        if "acre" in value.lower():
                            acres = self._parse_float_safe(value.split()[0])
                            if acres:
                                metadata["lot_sqft"] = int(acres * 43560)
                        else:
                            metadata["lot_sqft"] = self._parse_int_safe(value.replace(",", ""))
                    elif "year built" in label:
                        metadata["year_built"] = self._parse_int_safe(value)
                    elif "garage" in label:
                        metadata["garage_spaces"] = self._parse_int_safe(value)
                    elif "hoa" in label or "association fee" in label:
                        # Handle "No Fees" or "$150/month"
                        if "no fee" in value.lower():
                            metadata["hoa_fee"] = 0.0
                        else:
                            hoa_match = RE_PRICE_EXTRACT.search(value)
                            if hoa_match:
                                metadata["hoa_fee"] = float(hoa_match.group(1).replace(",", ""))
                    elif "pool" in label:
                        metadata["has_pool"] = "yes" in value.lower() or "private" in value.lower()
                    elif "sewer" in label:
                        if "public" in value.lower() or "city" in value.lower():
                            metadata["sewer_type"] = "city"
                        elif "septic" in value.lower():
                            metadata["sewer_type"] = "septic"
                    elif "property type" in label:
                        metadata["property_type"] = value
                    elif "style" in label or "architecture" in label:
                        metadata["architecture_style"] = value
                    elif "cooling" in label:
                        metadata["cooling_type"] = value
                    elif "heating" in label:
                        metadata["heating_type"] = value
                    elif "water" in label:
                        metadata["water_source"] = value
                    elif "roof" in label:
                        metadata["roof_material"] = value
                    # === NEW EXTRACTION PATTERNS (E2-R2) ===
                    elif "fireplace" in label:
                        metadata["fireplace_yn"] = (
                            "yes" in value.lower()
                            or "true" in value.lower()
                            or (value.isdigit() and int(value) > 0)
                        )
                    elif "flooring" in label or "floor" in label:
                        # Parse flooring types as list
                        metadata["flooring_types"] = [
                            f.strip() for f in value.split(",") if f.strip()
                        ]
                    elif "laundry" in label:
                        # Parse laundry features as list
                        metadata["laundry_features"] = [
                            f.strip() for f in value.split(",") if f.strip()
                        ]
                    elif "status" in label and "listing" in label:
                        metadata["listing_status"] = value
                    elif "office" in label or "brokerage" in label or "broker" in label:
                        metadata["listing_office"] = value

        # Listing Status (badge/tag pattern - e.g., "Active", "Pending", "Sold")
        if "listing_status" not in metadata:
            status_elem = soup.find(
                ["span", "div", "badge"],
                class_=RE_STATUS_BADGE,
            )
            if status_elem:
                status_text = status_elem.get_text(strip=True)
                if status_text.lower() in ("active", "pending", "sold", "contingent"):
                    metadata["listing_status"] = status_text.capitalize()

        # Days on Market (patterns: "Listed X days ago", "DOM: X", "Days on Market: X")
        for pattern in DOM_PATTERNS:
            dom_match = soup.find(string=pattern)
            if dom_match:
                match = pattern.search(str(dom_match))
                if match:
                    metadata["days_on_market"] = int(match.group(1))
                    break

        # Original List Price and Price Reduced
        # Pattern: "Original Price: $X" or "Was $X, Now $Y" or "Price Reduced"
        price_history = soup.find(["div", "span", "p"], class_=RE_PRICE_HISTORY)
        if price_history:
            history_text = price_history.get_text(strip=True)
            # Match "Original Price: $X" or "Original: $X" or "Was $X"
            original_match = RE_ORIGINAL_PRICE.search(history_text)
            if original_match:
                metadata["original_list_price"] = int(original_match.group(1).replace(",", ""))
                # If we have both original and current price, determine if reduced
                if "price" in metadata and metadata["original_list_price"] > metadata["price"]:
                    metadata["price_reduced"] = True
                elif "price" in metadata:
                    metadata["price_reduced"] = False
        # Also check for "Price Reduced" badge/tag
        reduced_elem = soup.find(string=RE_PRICE_REDUCED)
        if reduced_elem:
            metadata["price_reduced"] = True

        # MLS Last Updated (timestamp pattern)
        updated_elem = soup.find(string=RE_UPDATED)
        if updated_elem:
            updated_text = str(updated_elem)
            # Try ISO date pattern
            date_match = RE_ISO_DATE.search(updated_text)
            if date_match:
                metadata["mls_last_updated"] = date_match.group(1)
            else:
                # Try "MM/DD/YYYY" pattern
                date_match = RE_US_DATE.search(updated_text)
                if date_match:
                    metadata["mls_last_updated"] = date_match.group(1)

        # Schools (usually in separate section)
        schools_section = soup.find("div", class_=RE_SCHOOL_SECTION)
        if schools_section:
            for school_elem in schools_section.find_all(["div", "span", "p"]):
                text = school_elem.get_text(strip=True)
                if "elementary" in text.lower():
                    # Extract school name after "Elementary:"
                    school_match = RE_ELEMENTARY.search(text)
                    if school_match:
                        metadata["elementary_school_name"] = school_match.group(1).strip()
                elif "middle" in text.lower():
                    school_match = RE_MIDDLE.search(text)
                    if school_match:
                        metadata["middle_school_name"] = school_match.group(1).strip()
                elif "high" in text.lower():
                    school_match = RE_HIGH.search(text)
                    if school_match:
                        metadata["high_school_name"] = school_match.group(1).strip()

        # Features (comma-separated lists)
        features_section = soup.find("div", class_=RE_FEATURES_SECTION)
        if features_section:
            # Kitchen features
            kitchen_elem = features_section.find(string=RE_KITCHEN)
            if kitchen_elem:
                kitchen_parent = kitchen_elem.find_parent(["div", "section"])
                if kitchen_parent:
                    features_text = kitchen_parent.get_text(strip=True)
                    metadata["kitchen_features"] = [
                        f.strip() for f in features_text.split(",") if f.strip()
                    ]

            # Master bath features
            master_elem = features_section.find(string=RE_MASTER_BATH)
            if master_elem:
                master_parent = master_elem.find_parent(["div", "section"])
                if master_parent:
                    features_text = master_parent.get_text(strip=True)
                    metadata["master_bath_features"] = [
                        f.strip() for f in features_text.split(",") if f.strip()
                    ]

            # Interior features
            interior_elem = features_section.find(string=RE_INTERIOR)
            if interior_elem:
                interior_parent = interior_elem.find_parent(["div", "section"])
                if interior_parent:
                    features_text = interior_parent.get_text(strip=True)
                    metadata["interior_features_list"] = [
                        f.strip() for f in features_text.split(",") if f.strip()
                    ]

            # Exterior features
            exterior_elem = features_section.find(string=RE_EXTERIOR)
            if exterior_elem:
                exterior_parent = exterior_elem.find_parent(["div", "section"])
                if exterior_parent:
                    features_text = exterior_parent.get_text(strip=True)
                    metadata["exterior_features_list"] = [
                        f.strip() for f in features_text.split(",") if f.strip()
                    ]

        # Cross streets
        cross_elem = soup.find(string=RE_CROSS_STREETS)
        if cross_elem:
            cross_parent = cross_elem.find_parent(["div", "span", "p"])
            if cross_parent:
                cross_text = cross_parent.get_text(strip=True)
                cross_match = RE_CROSS_STREETS_EXTRACT.search(cross_text)
                if cross_match:
                    metadata["cross_streets"] = cross_match.group(1).strip()

        # === E2-R3: EXTENDED FIELD EXTRACTION ===

        # Helper for parsing comma/semicolon-separated feature lists
        def parse_feature_list(text: str) -> list[str]:
            """Parse comma or semicolon separated feature list."""
            # Split by comma or semicolon, strip whitespace, filter empty
            items = re.split(r"[,;]", text)
            return [item.strip() for item in items if item.strip()]

        # Geo Coordinates
        geo_lat_match = RE_GEO_LAT.search(html)
        if geo_lat_match:
            try:
                metadata["geo_lat"] = float(geo_lat_match.group(1))
            except ValueError:
                pass

        geo_lon_match = RE_GEO_LON.search(html)
        if geo_lon_match:
            try:
                metadata["geo_lon"] = float(geo_lon_match.group(1))
            except ValueError:
                pass

        # Legal/Parcel Data
        township_match = RE_TOWNSHIP.search(html)
        if township_match:
            metadata["township"] = township_match.group(1).strip()

        range_match = RE_RANGE.search(html)
        if range_match:
            metadata["range_section"] = range_match.group(1).strip()

        section_match = RE_SECTION.search(html)
        if section_match:
            metadata["section"] = section_match.group(1).strip()

        lot_number_match = RE_LOT_NUMBER.search(html)
        if lot_number_match:
            metadata["lot_number"] = lot_number_match.group(1).strip()

        subdivision_match = RE_SUBDIVISION.search(html)
        if subdivision_match:
            metadata["subdivision"] = subdivision_match.group(1).strip()

        apn_match = RE_APN.search(html)
        if apn_match:
            metadata["apn"] = apn_match.group(1).strip()

        # Property Structure
        stories_match = RE_EXTERIOR_STORIES.search(html)
        if stories_match:
            metadata["exterior_stories"] = self._parse_int_safe(stories_match.group(1))

        levels_match = RE_INTERIOR_LEVELS.search(html)
        if levels_match:
            metadata["interior_levels"] = levels_match.group(1).strip()

        builder_match = RE_BUILDER.search(html)
        if builder_match:
            metadata["builder_name"] = builder_match.group(1).strip()

        dwelling_match = RE_DWELLING_STYLES.search(html)
        if dwelling_match:
            metadata["dwelling_styles"] = dwelling_match.group(1).strip()

        # School Districts (separate from school names)
        elem_district_match = RE_ELEMENTARY_DISTRICT.search(html)
        if elem_district_match:
            metadata["elementary_district"] = elem_district_match.group(1).strip()

        mid_district_match = RE_MIDDLE_DISTRICT.search(html)
        if mid_district_match:
            metadata["middle_district"] = mid_district_match.group(1).strip()

        high_district_match = RE_HIGH_DISTRICT.search(html)
        if high_district_match:
            metadata["high_district"] = high_district_match.group(1).strip()

        # Contract/Listing Info
        list_date_match = RE_LIST_DATE.search(html)
        if list_date_match:
            metadata["list_date"] = list_date_match.group(1).strip()

        ownership_match = RE_OWNERSHIP.search(html)
        if ownership_match:
            metadata["ownership_type"] = ownership_match.group(1).strip()

        possession_match = RE_POSSESSION.search(html)
        if possession_match:
            metadata["possession_terms"] = possession_match.group(1).strip()

        financing_match = RE_NEW_FINANCING.search(html)
        if financing_match:
            metadata["new_financing"] = parse_feature_list(financing_match.group(1))

        # Pool Details
        private_pool_match = RE_PRIVATE_POOL_FEATURES.search(html)
        if private_pool_match:
            metadata["private_pool_features"] = parse_feature_list(private_pool_match.group(1))

        spa_match = RE_SPA.search(html)
        if spa_match:
            metadata["spa_features"] = spa_match.group(1).strip()

        community_pool_match = RE_COMMUNITY_POOL.search(html)
        if community_pool_match:
            value = community_pool_match.group(1).lower()
            metadata["community_pool"] = value in ("yes", "y", "true")

        # Updates/Renovations
        kitchen_year_match = RE_KITCHEN_YEAR_UPDATED.search(html)
        if kitchen_year_match:
            metadata["kitchen_year_updated"] = self._parse_int_safe(kitchen_year_match.group(1))

        kitchen_scope_match = RE_KITCHEN_UPDATE_SCOPE.search(html)
        if kitchen_scope_match:
            metadata["kitchen_update_scope"] = kitchen_scope_match.group(1).strip()

        # Basement
        basement_match = RE_BASEMENT.search(html)
        if basement_match:
            value = basement_match.group(1).lower()
            metadata["has_basement"] = value not in ("no", "n", "none")

        # Fireplaces Total
        fireplaces_match = RE_FIREPLACES_TOTAL.search(html)
        if fireplaces_match:
            metadata["fireplaces_total"] = self._parse_int_safe(fireplaces_match.group(1))

        # Total Covered Spaces
        covered_match = RE_TOTAL_COVERED_SPACES.search(html)
        if covered_match:
            metadata["total_covered_spaces"] = self._parse_int_safe(covered_match.group(1))

        # Feature Lists (comma/semicolon separated)
        view_match = RE_VIEW.search(html)
        if view_match:
            metadata["view_features"] = parse_feature_list(view_match.group(1))

        community_match = RE_COMMUNITY_FEATURES.search(html)
        if community_match:
            metadata["community_features"] = parse_feature_list(community_match.group(1))

        prop_desc_match = RE_PROPERTY_DESCRIPTION.search(html)
        if prop_desc_match:
            metadata["property_description"] = parse_feature_list(prop_desc_match.group(1))

        dining_match = RE_DINING_AREA.search(html)
        if dining_match:
            metadata["dining_area_features"] = parse_feature_list(dining_match.group(1))

        tech_match = RE_TECHNOLOGY.search(html)
        if tech_match:
            metadata["technology_features"] = parse_feature_list(tech_match.group(1))

        window_match = RE_WINDOW.search(html)
        if window_match:
            metadata["window_features"] = parse_feature_list(window_match.group(1))

        other_rooms_match = RE_OTHER_ROOMS.search(html)
        if other_rooms_match:
            metadata["other_rooms"] = parse_feature_list(other_rooms_match.group(1))

        construction_match = RE_CONSTRUCTION.search(html)
        if construction_match:
            metadata["construction_materials"] = parse_feature_list(construction_match.group(1))

        const_finish_match = RE_CONSTRUCTION_FINISH.search(html)
        if const_finish_match:
            metadata["construction_finish"] = parse_feature_list(const_finish_match.group(1))

        parking_match = RE_PARKING.search(html)
        if parking_match:
            metadata["parking_features"] = parse_feature_list(parking_match.group(1))

        fencing_match = RE_FENCING.search(html)
        if fencing_match:
            metadata["fencing_types"] = parse_feature_list(fencing_match.group(1))

        utilities_match = RE_UTILITIES.search(html)
        if utilities_match:
            metadata["utilities_provider"] = parse_feature_list(utilities_match.group(1))

        services_match = RE_SERVICES.search(html)
        if services_match:
            metadata["services_available"] = parse_feature_list(services_match.group(1))

        # Remarks
        remarks_match = RE_PUBLIC_REMARKS.search(html)
        if remarks_match:
            metadata["public_remarks"] = remarks_match.group(1).strip()

        directions_match = RE_DIRECTIONS.search(html)
        if directions_match:
            metadata["directions"] = directions_match.group(1).strip()

        return metadata

    def _parse_int_safe(self, value: str) -> int | None:
        """Safely parse integer from string, returning None on failure."""
        try:
            return int(re.sub(r"[^\d]", "", value))
        except (ValueError, AttributeError):
            return None

    def _parse_float_safe(self, value: str) -> float | None:
        """Safely parse float from string, returning None on failure."""
        try:
            cleaned = re.sub(r"[^\d.]", "", value)
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def get_cached_metadata(self, property: Property) -> dict[str, Any] | None:
        """Retrieve cached metadata from property object.

        After extract_image_urls() is called, metadata is cached on the
        property object for later enrichment merge.

        Args:
            property: Property object with cached metadata

        Returns:
            Dict of metadata fields or None if not cached
        """
        return getattr(property, "_mls_metadata_cache", None)
