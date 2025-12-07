"""Playwright MCP client wrapper for fallback extraction.

Provides a wrapper around Playwright MCP tools for browser automation
when nodriver and curl_cffi fail. Uses MCP browser tools for navigation,
snapshot extraction, and element interaction.

This is the tertiary fallback in the extraction chain:
1. nodriver (primary - best stealth)
2. curl-cffi (secondary - HTTP with TLS fingerprinting)
3. Playwright MCP (tertiary - fallback for minimal anti-bot sites)
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


class PlaywrightMcpClient:
    """Wrapper for Playwright MCP browser automation tools.

    Provides a simplified interface to MCP browser tools for
    property listing extraction when stealth methods fail.

    Note: This fallback works best for sites with minimal anti-bot
    protection. Zillow/Redfin will likely block Playwright.

    Example:
        ```python
        client = PlaywrightMcpClient()
        await client.navigate("https://www.realtor.com/...")
        snapshot = await client.get_snapshot()
        images = client.extract_images_from_snapshot(snapshot)
        ```
    """

    def __init__(self):
        """Initialize Playwright MCP client."""
        self._initialized = False
        logger.info("PlaywrightMcpClient initialized (fallback mode)")

    async def navigate(self, url: str) -> dict[str, Any]:
        """Navigate to URL using MCP browser.

        Args:
            url: URL to navigate to

        Returns:
            Navigation result with status

        Raises:
            RuntimeError: If MCP tools are not available
        """
        logger.info("Playwright MCP: Navigating to %s", url)

        try:
            # Import MCP tools dynamically to avoid hard dependency
            from mcp__playwright__browser_navigate import browser_navigate

            result = await browser_navigate(url=url)
            self._initialized = True
            return result

        except ImportError as e:
            raise RuntimeError(
                "Playwright MCP tools not available. Ensure Claude Code MCP server is configured."
            ) from e

    async def get_snapshot(self) -> dict[str, Any]:
        """Get accessibility snapshot of current page.

        Returns:
            Snapshot data with accessibility tree

        Raises:
            RuntimeError: If MCP tools are not available
        """
        logger.info("Playwright MCP: Getting page snapshot")

        try:
            from mcp__playwright__browser_snapshot import browser_snapshot

            snapshot = await browser_snapshot()
            return snapshot

        except ImportError as e:
            raise RuntimeError(
                "Playwright MCP tools not available. Ensure Claude Code MCP server is configured."
            ) from e

    async def take_screenshot(
        self, filename: str | None = None, fullPage: bool = False
    ) -> dict[str, Any]:
        """Take screenshot of current page.

        Args:
            filename: Optional filename for screenshot
            fullPage: Whether to capture full scrollable page

        Returns:
            Screenshot result with file path

        Raises:
            RuntimeError: If MCP tools are not available
        """
        logger.info("Playwright MCP: Taking screenshot (fullPage=%s)", fullPage)

        try:
            from mcp__playwright__browser_take_screenshot import browser_take_screenshot

            result = await browser_take_screenshot(filename=filename, fullPage=fullPage)
            return result

        except ImportError as e:
            raise RuntimeError(
                "Playwright MCP tools not available. Ensure Claude Code MCP server is configured."
            ) from e

    async def click(self, element: str, ref: str) -> dict[str, Any]:
        """Click element on page.

        Args:
            element: Human-readable element description
            ref: Exact element reference from snapshot

        Returns:
            Click result

        Raises:
            RuntimeError: If MCP tools are not available
        """
        logger.info("Playwright MCP: Clicking element: %s", element)

        try:
            from mcp__playwright__browser_click import browser_click

            result = await browser_click(element=element, ref=ref)
            return result

        except ImportError as e:
            raise RuntimeError(
                "Playwright MCP tools not available. Ensure Claude Code MCP server is configured."
            ) from e

    async def close(self) -> None:
        """Close browser and clean up resources."""
        if not self._initialized:
            return

        logger.info("Playwright MCP: Closing browser")

        try:
            from mcp__playwright__browser_close import browser_close

            await browser_close()
            self._initialized = False

        except ImportError:
            logger.warning("Could not import MCP browser_close")

    def extract_images_from_snapshot(
        self, snapshot: dict[str, Any], filter_pattern: str | None = None
    ) -> list[str]:
        r"""Extract image URLs from accessibility snapshot.

        Searches snapshot accessibility tree for image elements
        and extracts their URLs.

        Args:
            snapshot: Accessibility snapshot from get_snapshot()
            filter_pattern: Optional regex pattern to filter URLs

        Returns:
            List of image URLs found in snapshot

        Example:
            ```python
            snapshot = await client.get_snapshot()
            images = client.extract_images_from_snapshot(
                snapshot,
                filter_pattern=r"photos\.(zillow|redfin)"
            )
            ```
        """
        logger.info("Extracting images from snapshot")
        image_urls: set[str] = set()

        # Snapshot structure varies, but typically has accessibility tree
        # Walk the tree looking for image-related nodes
        def walk_tree(node: dict) -> None:
            """Recursively walk accessibility tree."""
            if not isinstance(node, dict):
                return

            # Check for image URL in various fields
            for key in ("url", "src", "value", "name"):
                value = node.get(key)
                if (
                    isinstance(value, str)
                    and value.startswith("http")
                    and self._is_likely_image_url(value)
                ):
                    image_urls.add(value)

            # Recurse into children
            for child_key in ("children", "nodes", "elements"):
                children = node.get(child_key)
                if isinstance(children, list):
                    for child in children:
                        walk_tree(child)

        # Start walk from snapshot root
        walk_tree(snapshot)

        # Filter by pattern if provided
        if filter_pattern:
            pattern = re.compile(filter_pattern)
            filtered_urls = [url for url in image_urls if pattern.search(url)]
            logger.info(
                "Filtered %d URLs to %d matching pattern: %s",
                len(image_urls),
                len(filtered_urls),
                filter_pattern,
            )
            return filtered_urls

        return list(image_urls)

    def _is_likely_image_url(self, url: str) -> bool:
        """Check if URL is likely an image.

        Args:
            url: URL to check

        Returns:
            True if URL appears to be an image
        """
        url_lower = url.lower()

        # Check for image extensions
        image_extensions = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")
        if any(ext in url_lower for ext in image_extensions):
            return True

        # Check for CDN patterns
        cdn_patterns = (
            "photos.zillowstatic.com",
            "ssl.cdn-redfin.com",
            "photos",
            "images",
            "img",
        )
        if any(pattern in url_lower for pattern in cdn_patterns):
            return True

        return False


# Convenience function for simple extraction
async def extract_images_from_url(url: str, filter_pattern: str | None = None) -> list[str]:
    """Extract images from URL using Playwright MCP.

    Convenience function for simple extraction workflow:
    1. Navigate to URL
    2. Get snapshot
    3. Extract image URLs
    4. Close browser

    Args:
        url: URL to extract images from
        filter_pattern: Optional regex pattern to filter URLs

    Returns:
        List of image URLs

    Example:
        ```python
        images = await extract_images_from_url(
            "https://www.realtor.com/realestateandhomes-detail/...",
            filter_pattern=r"photos"
        )
        ```
    """
    client = PlaywrightMcpClient()

    try:
        await client.navigate(url)
        snapshot = await client.get_snapshot()
        images = client.extract_images_from_snapshot(snapshot, filter_pattern)
        return images

    finally:
        await client.close()
