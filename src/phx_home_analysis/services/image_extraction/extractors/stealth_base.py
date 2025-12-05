"""Stealth browser-based extractor base class using nodriver and curl_cffi.

This module provides a base class for Zillow and Redfin extractors that need
to bypass PerimeterX and other anti-bot systems using stealth techniques.

Key Features:
    - Bezier curve mouse movement for natural human-like trajectories
    - 2-layer CAPTCHA solving with page refresh detection
    - Shadow DOM traversal via CDP for PerimeterX iframe detection
    - Micro-movement hand tremor simulation during button holds

Example:
    class ZillowExtractor(StealthBrowserExtractor):
        @property
        def source(self) -> ImageSource:
            return ImageSource.ZILLOW

        def _build_search_url(self, property: Property) -> str:
            return f"https://zillow.com/homes/{property.full_address}"

        async def _extract_urls_from_page(self, tab: uc.Tab) -> list[str]:
            return await self._extract_zillow_image_urls(tab)
"""

import asyncio
import logging
import random
import time
from abc import abstractmethod

import httpx
import nodriver as uc

from ....config.settings import StealthExtractionConfig
from ....domain.entities import Property
from ...infrastructure import BrowserPool, StealthHttpClient
from ..metrics import log_captcha_event
from .base import ExtractionError, ImageExtractor, SourceUnavailableError

logger = logging.getLogger(__name__)


class StealthBrowserExtractor(ImageExtractor):
    """Abstract base class for stealth browser-based extraction.

    Extends ImageExtractor with nodriver browser automation and curl_cffi
    HTTP client for bypassing anti-bot systems like PerimeterX.

    Uses template method pattern:
    - Subclasses implement _build_search_url() and _extract_urls_from_page()
    - Base class handles navigation, CAPTCHA detection/solving, and delays

    Class Constants:
        CAPTCHA_SOLVE_WAIT_SECONDS: Seconds to wait after solve attempt for page change
        CAPTCHA_RETRY_AFTER_SECONDS: Seconds to suggest waiting before retry
        PAGE_CONTENT_CHANGE_THRESHOLD: Ratio of content change indicating refresh
        LARGE_PAGE_CONTENT_THRESHOLD: Bytes indicating page has real content
        DEFAULT_VIEWPORT_CENTER: Default center coordinates for 1280x720 viewport
        BEZIER_CURVE_STEPS_RANGE: Min/max steps for mouse curve movement
        BEZIER_CONTROL_POINT_VARIANCE: Pixel variance for curve control points
        MOUSE_JITTER_PIXELS: Maximum pixels for hand tremor simulation
        MOUSE_MOVE_DELAY_RANGE: Min/max seconds between curve points
        REFRESH_CHECK_INTERVAL_SECONDS: Interval for checking page refresh during hold
    """

    # CAPTCHA solving timing constants
    CAPTCHA_SOLVE_WAIT_SECONDS: float = 3.0
    CAPTCHA_RETRY_AFTER_SECONDS: int = 300  # 5 minutes

    # Page content analysis thresholds
    PAGE_CONTENT_CHANGE_THRESHOLD: float = 0.5  # 50% change = refresh
    LARGE_PAGE_CONTENT_THRESHOLD: int = 70000  # bytes

    # Default viewport center (for 1280x720)
    DEFAULT_VIEWPORT_CENTER: tuple[int, int] = (640, 360)

    # Bezier curve mouse movement parameters
    BEZIER_CURVE_STEPS_RANGE: tuple[int, int] = (15, 25)
    BEZIER_CONTROL_POINT_VARIANCE: int = 50  # pixels
    BEZIER_CONTROL_POINT_1_RANGE: tuple[float, float] = (0.2, 0.4)
    BEZIER_CONTROL_POINT_2_RANGE: tuple[float, float] = (0.6, 0.8)

    # Mouse movement timing
    MOUSE_MOVE_DELAY_RANGE: tuple[float, float] = (0.01, 0.03)
    MOUSE_POST_MOVE_DELAY_RANGE: tuple[float, float] = (0.1, 0.2)
    MOUSE_FINAL_OFFSET_PIXELS: int = 3  # Final position variance

    # Hand tremor simulation
    MOUSE_JITTER_PIXELS: int = 2
    MICRO_MOVEMENT_INTERVAL_RANGE: tuple[float, float] = (0.1, 0.3)

    # Page refresh detection
    REFRESH_CHECK_INTERVAL_SECONDS: float = 0.25

    # Progressive backoff multipliers for retry attempts
    BACKOFF_MULTIPLIER_MIN: float = 5.0
    BACKOFF_MULTIPLIER_MAX: float = 10.0

    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 30.0,
        config: StealthExtractionConfig | None = None,
    ):
        """Initialize stealth extractor with browser and HTTP client.

        Args:
            http_client: Shared httpx client (not used - maintained for compatibility)
            timeout: Request timeout in seconds
            config: Stealth extraction configuration (loaded from env if not provided)
        """
        # Call parent constructor (maintains compatibility but we don't use http_client)
        super().__init__(http_client=http_client, timeout=timeout)

        # Load config from environment if not provided
        self.config = config or StealthExtractionConfig.from_env()

        # Initialize browser pool with isolation settings
        self._browser_pool = BrowserPool(
            proxy_url=self.config.proxy_url,
            headless=self.config.browser_headless,
            viewport_width=self.config.viewport_width,
            viewport_height=self.config.viewport_height,
            isolation_mode=self.config.isolation_mode.value,
            fallback_to_minimize=self.config.fallback_to_minimize,
        )

        # Initialize stealth HTTP client
        self._stealth_client = StealthHttpClient(
            proxy_url=self.config.proxy_url,
            timeout=self.config.request_timeout,
            max_retries=self.config.max_retries,
        )

        logger.info(
            "%s initialized with stealth config: headless=%s, proxy=%s",
            self.name,
            self.config.browser_headless,
            "enabled" if self.config.is_configured else "disabled",
        )

    async def download_image(self, url: str) -> tuple[bytes, str]:
        """Download image using stealth HTTP client.

        Args:
            url: Image URL to download

        Returns:
            Tuple of (image_bytes, content_type)

        Raises:
            ImageDownloadError: If download fails after retries
        """
        logger.debug("%s downloading image: %s", self.name, url)
        return await self._stealth_client.download_image(url=url)

    async def close(self) -> None:
        """Close browser pool and HTTP client resources."""
        logger.info("%s closing resources", self.name)

        # Close browser pool
        await self._browser_pool.close()

        # Close stealth HTTP client
        await self._stealth_client.close()

        # Close parent's HTTP client if we own it
        await super().close()

        logger.info("%s resources closed", self.name)

    async def extract_image_urls(self, property: Property) -> list[str]:
        """Extract image URLs using stealth browser navigation.

        Template method that:
        1. Builds search URL (subclass implements)
        2. Navigates with stealth techniques
        3. Detects and attempts to solve CAPTCHAs
        4. Extracts URLs from page (subclass implements)

        Args:
            property: Property to find images for

        Returns:
            List of image URLs discovered

        Raises:
            SourceUnavailableError: If CAPTCHA solving fails
            ExtractionError: For other extraction failures
        """
        url = self._build_search_url(property)
        logger.info("%s extracting images for: %s", self.name, property.full_address)

        tab = await self._navigate_with_stealth(url)

        try:
            # Check for CAPTCHA
            if await self._check_for_captcha(tab):
                logger.warning("%s CAPTCHA detected for %s", self.name, url)

                # Log CAPTCHA detection event
                log_captcha_event(
                    event_type="captcha_detected",
                    property_address=property.full_address,
                    details={"url": url},
                    source=self.source.value,
                )

                # Attempt to solve CAPTCHA
                solve_start = time.time()
                solved = await self._attempt_captcha_solve_v2(tab)
                solve_time = time.time() - solve_start

                if not solved:
                    logger.error(
                        "%s CAPTCHA solving failed for %s (%.2fs)",
                        self.name, url, solve_time
                    )

                    # Log CAPTCHA failure event
                    log_captcha_event(
                        event_type="captcha_failed",
                        property_address=property.full_address,
                        details={
                            "url": url,
                            "solve_time_seconds": round(solve_time, 2),
                        },
                        source=self.source.value,
                    )

                    raise SourceUnavailableError(
                        self.source,
                        "CAPTCHA detected and solving failed",
                        retry_after=self.CAPTCHA_RETRY_AFTER_SECONDS,
                    )

                logger.info(
                    "%s CAPTCHA solved for %s (%.2fs)",
                    self.name, url, solve_time
                )

                # Log CAPTCHA success event
                log_captcha_event(
                    event_type="captcha_solved",
                    property_address=property.full_address,
                    details={
                        "url": url,
                        "solve_time_seconds": round(solve_time, 2),
                    },
                    source=self.source.value,
                )

            # Add human delay before extraction
            await self._human_delay()

            # Extract URLs from page (subclass implements)
            urls = await self._extract_urls_from_page(tab)

            logger.info(
                "%s extracted %d image URLs for %s",
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

    @abstractmethod
    def _build_search_url(self, property: Property) -> str:
        """Build search URL for property listing.

        Args:
            property: Property to build URL for

        Returns:
            Full URL to navigate to
        """
        pass

    @abstractmethod
    async def _extract_urls_from_page(self, tab: uc.Tab) -> list[str]:
        """Extract image URLs from the current page.

        Args:
            tab: Browser tab with loaded page

        Returns:
            List of image URLs found
        """
        pass

    async def _navigate_with_stealth(self, url: str) -> uc.Tab:
        """Navigate to URL with stealth techniques and human delays.

        Args:
            url: URL to navigate to

        Returns:
            Browser tab ready for interaction

        Raises:
            ExtractionError: If navigation fails
        """
        logger.info("%s navigating to: %s", self.name, url)

        try:
            # Add initial delay to appear more human-like
            await self._human_delay()

            # Get browser and create new tab
            browser = await self._browser_pool.get_browser()
            tab = await browser.get(url)

            # Wait for page to stabilize
            await self._human_delay()

            logger.info("%s navigation complete", self.name)
            return tab

        except Exception as e:
            logger.error("%s navigation failed: %s", self.name, e)
            raise ExtractionError(f"Navigation failed for {url}: {e}") from e

    async def _check_for_captcha(self, tab: uc.Tab) -> bool:
        """Check if CAPTCHA is blocking the page (enhanced detection).

        Enhanced detection strategy (Phase 1 improvements):
        1. Network request analysis - check for PerimeterX API calls
        2. DOM text analysis - check for CAPTCHA indicators in page content
        3. Page size heuristic - validate content threshold
        4. Property content verification - confirm successful page load

        Args:
            tab: Browser tab to check

        Returns:
            True if CAPTCHA is blocking content, False otherwise
        """
        try:
            # Strategy 1: Network request analysis (primary detection)
            # Check for PerimeterX API calls indicating CAPTCHA challenge
            try:
                # Get network requests from tab (if available)
                # Note: This may require enabling network monitoring in browser
                # For now, we'll use DOM-based detection as primary method
                logger.debug("%s checking network requests for PerimeterX calls", self.name)
                # TODO: Implement network request inspection when nodriver API supports it
            except Exception as e:
                logger.debug("%s network analysis not available: %s", self.name, e)

            # Strategy 2: DOM text analysis (fallback/primary for now)
            page_text = await tab.get_content()
            page_text_lower = page_text.lower()
            content_length = len(page_text)

            logger.debug(
                "%s page content length: %d bytes",
                self.name,
                content_length,
            )

            # Strategy 3: Enhanced page size heuristic
            # Small pages (<30KB) are likely CAPTCHA interstitials
            # Medium pages (30-70KB) need deeper inspection
            # Large pages (>70KB) likely have real property content
            if content_length > self.LARGE_PAGE_CONTENT_THRESHOLD:
                # Large page - check for property indicators
                property_indicators = [
                    "zillowstatic.com",
                    "photos.zillow",
                    "property details",
                    "home details",
                    "beds",
                    "baths",
                    "sqft",
                    "redfin.com",
                    "listing",
                    "hdpPhotos",  # Zillow photo data
                    "propertyDetails",  # Redfin property details
                ]
                for indicator in property_indicators:
                    if indicator in page_text_lower:
                        logger.debug(
                            "%s page has property content (%d chars), "
                            "indicator: %s - no CAPTCHA",
                            self.name,
                            content_length,
                            indicator,
                        )
                        return False

                # Large page without property indicators - suspicious
                logger.info(
                    "%s large page (%d chars) but no property indicators - may be CAPTCHA",
                    self.name,
                    content_length,
                )

            # Check for CAPTCHA indicators
            captcha_indicators = [
                "press and hold",
                "px-captcha",
                "perimeterx",
                "challenge-running",  # Additional PerimeterX indicator
                "px-block",  # PerimeterX block page
            ]

            for indicator in captcha_indicators:
                if indicator in page_text_lower:
                    logger.warning(
                        "%s CAPTCHA indicator found: '%s' (page: %d chars)",
                        self.name,
                        indicator,
                        content_length,
                    )
                    return True

            # No CAPTCHA indicators found
            logger.debug(
                "%s no CAPTCHA detected (page: %d chars)",
                self.name,
                content_length,
            )
            return False

        except Exception as e:
            logger.warning("%s error checking for CAPTCHA: %s", self.name, e)
            # Assume no CAPTCHA if we can't check
            return False

    async def _human_mouse_move_bezier(
        self, tab: uc.Tab, target_x: int, target_y: int
    ) -> None:
        """Move mouse using cubic Bezier curve for natural human-like trajectory.

        Implements parametric cubic Bezier curve movement with randomized control
        points to simulate natural human mouse movement patterns. More sophisticated
        than linear interpolation, this approach:

        - Varies speed along the path (slower at endpoints, faster in middle)
        - Adds random curvature via control point variance
        - Includes small final position jitter to avoid exact pixel targeting
        - Uses timing delays between points for realistic movement speed

        The cubic Bezier formula used:
            B(t) = (1-t)^3 * P0 + 3(1-t)^2 * t * P1 + 3(1-t) * t^2 * P2 + t^3 * P3

        Where P0=start, P3=target, and P1/P2 are randomized control points.

        Args:
            tab: Browser tab to execute mouse movement in.
            target_x: Target X coordinate in viewport pixels.
            target_y: Target Y coordinate in viewport pixels.

        Note:
            Falls back to direct mouse_move on any error to ensure the mouse
            reaches the target even if smooth movement fails.
        """
        logger.debug(
            "%s Bezier mouse move to: (%d, %d)", self.name, target_x, target_y
        )

        try:
            # Start position (assume center-left of viewport)
            start_x = self.config.viewport_width // 4
            start_y = self.config.viewport_height // 2

            # Generate random control points for cubic Bezier curve
            variance = self.BEZIER_CONTROL_POINT_VARIANCE
            cp1_range = self.BEZIER_CONTROL_POINT_1_RANGE
            cp2_range = self.BEZIER_CONTROL_POINT_2_RANGE

            # Control point 1: early in path with random offset
            cp1_x = start_x + int(
                (target_x - start_x) * random.uniform(*cp1_range)
            )
            cp1_y = start_y + int(
                (target_y - start_y) * random.uniform(*cp1_range)
            )
            cp1_x += random.randint(-variance, variance)
            cp1_y += random.randint(-variance, variance)

            # Control point 2: later in path with random offset
            cp2_x = start_x + int(
                (target_x - start_x) * random.uniform(*cp2_range)
            )
            cp2_y = start_y + int(
                (target_y - start_y) * random.uniform(*cp2_range)
            )
            cp2_x += random.randint(-variance, variance)
            cp2_y += random.randint(-variance, variance)

            logger.debug(
                "%s Bezier control points: CP1=(%d,%d), CP2=(%d,%d)",
                self.name,
                cp1_x,
                cp1_y,
                cp2_x,
                cp2_y,
            )

            # Generate points along Bezier curve
            steps_range = self.BEZIER_CURVE_STEPS_RANGE
            num_steps = random.randint(*steps_range)
            points: list[tuple[int, int]] = []

            for i in range(num_steps + 1):
                t = i / num_steps

                # Cubic Bezier formula
                x = int(
                    (1 - t) ** 3 * start_x
                    + 3 * (1 - t) ** 2 * t * cp1_x
                    + 3 * (1 - t) * t**2 * cp2_x
                    + t**3 * target_x
                )
                y = int(
                    (1 - t) ** 3 * start_y
                    + 3 * (1 - t) ** 2 * t * cp1_y
                    + 3 * (1 - t) * t**2 * cp2_y
                    + t**3 * target_y
                )

                points.append((x, y))

            # Move mouse along curve with small delays
            delay_range = self.MOUSE_MOVE_DELAY_RANGE
            for x, y in points:
                try:
                    await tab.mouse_move(x, y)
                    delay = random.uniform(*delay_range)
                    await asyncio.sleep(delay)
                except AttributeError:
                    logger.debug(
                        "%s mouse_move not available, using direct movement",
                        self.name,
                    )
                    break

            # Final position with small random offset to avoid exact targeting
            offset = self.MOUSE_FINAL_OFFSET_PIXELS
            final_x = target_x + random.randint(-offset, offset)
            final_y = target_y + random.randint(-offset, offset)

            try:
                await tab.mouse_move(final_x, final_y)
            except AttributeError:
                pass

            # Small pause after movement completes
            post_delay_range = self.MOUSE_POST_MOVE_DELAY_RANGE
            await asyncio.sleep(random.uniform(*post_delay_range))

            logger.debug("%s Bezier mouse move complete", self.name)

        except Exception as e:
            logger.warning(
                "%s error during Bezier mouse movement: %s, falling back to direct",
                self.name,
                e,
            )
            # Fallback to simple direct movement
            try:
                await tab.mouse_move(target_x, target_y)
            except Exception:
                pass

    async def _detect_page_refresh(
        self,
        tab: uc.Tab,
        initial_url: str,
        initial_content_length: int,
    ) -> bool:
        """Detect if page has refreshed during CAPTCHA hold.

        PerimeterX uses a 2-layer CAPTCHA system where the first press-and-hold
        is interrupted by a page refresh after approximately 1-2 seconds. The
        second attempt after refresh succeeds with a longer 4-5 second hold.

        This method is called periodically during the button hold to detect
        when the first layer's refresh occurs, allowing the solver to abort
        and retry with the correct (longer) hold duration.

        Detection Signals:
            1. URL changed - Navigation event occurred during hold
            2. Content length changed >50% - Page DOM was replaced
            3. Content unavailable - Tab is mid-navigation

        Args:
            tab: Browser tab being monitored for refresh signals.
            initial_url: URL captured before hold started, used for comparison.
            initial_content_length: Page content length in bytes before hold.

        Returns:
            True if page refresh was detected (abort hold and retry).
            False if page appears stable (continue holding).

        Note:
            On any exception, returns True (assumes refresh) as the safer option
            to avoid holding on a refreshed page with reset CAPTCHA state.
        """
        try:
            # Signal 1: URL navigation occurred
            current_url = tab.target.url if hasattr(tab, "target") else str(tab.url)
            if current_url != initial_url:
                logger.debug("%s page refresh detected: URL changed", self.name)
                return True

            # Signal 2: Content length drastically changed
            try:
                content = await tab.get_content()
                current_length = len(content) if content else 0

                if initial_content_length > 0:
                    change_ratio = (
                        abs(current_length - initial_content_length)
                        / initial_content_length
                    )
                    if change_ratio > self.PAGE_CONTENT_CHANGE_THRESHOLD:
                        logger.debug(
                            "%s page refresh detected: content length changed %.0f%%",
                            self.name,
                            change_ratio * 100,
                        )
                        return True
            except Exception:
                # Signal 3: Content unavailable during navigation
                logger.debug("%s page refresh detected: content unavailable", self.name)
                return True

            return False

        except Exception as e:
            logger.warning("%s error checking for page refresh: %s", self.name, e)
            return True  # Assume refresh on error (safer default)

    async def _find_captcha_button_via_cdp(self, tab: uc.Tab) -> tuple[int, int] | None:
        """Find CAPTCHA button center coordinates using CDP JavaScript evaluation.

        PerimeterX embeds its CAPTCHA button inside a shadow DOM within an iframe,
        which prevents standard CSS selectors from accessing it. This method uses
        Chrome DevTools Protocol (CDP) to execute JavaScript that traverses the
        shadow DOM and calculates the button's viewport coordinates.

        The JavaScript IIFE:
            1. Finds the #px-captcha container element
            2. Accesses its shadowRoot (or falls back to direct iframe)
            3. Locates the verification iframe within
            4. Returns bounding rect center coordinates

        Args:
            tab: Browser tab containing the CAPTCHA page.

        Returns:
            Tuple of (x, y) center coordinates for mouse click target.
            None if CAPTCHA button could not be located.

        Note:
            This is the primary detection method. Falls back to CSS selector
            scanning in _attempt_captcha_solve() if CDP detection fails.
        """
        try:
            # JavaScript to find the CAPTCHA iframe and return its center coordinates
            js_code = '''
            (function() {
                // Find the px-captcha container
                var container = document.querySelector('#px-captcha');
                if (!container) {
                    console.log('No #px-captcha container found');
                    return null;
                }

                // Access shadow root
                var shadowRoot = container.shadowRoot;
                if (!shadowRoot) {
                    // Fallback: maybe there's a direct iframe child (non-shadow)
                    var directIframe = container.querySelector('iframe[title*="verification"], iframe[title*="Human"]');
                    if (directIframe) {
                        var rect = directIframe.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            return {
                                x: Math.round(rect.left + rect.width / 2),
                                y: Math.round(rect.top + rect.height / 2),
                                width: rect.width,
                                height: rect.height,
                                source: 'direct-iframe'
                            };
                        }
                    }
                    console.log('No shadow root on #px-captcha');
                    return null;
                }

                // Find iframe inside shadow root
                var iframe = shadowRoot.querySelector('iframe[title*="verification"], iframe[title*="Human"], iframe');
                if (!iframe) {
                    console.log('No iframe found in shadow root');
                    return null;
                }

                // Get bounding rect from main document perspective
                var rect = iframe.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) {
                    console.log('Iframe has zero dimensions');
                    return null;
                }

                return {
                    x: Math.round(rect.left + rect.width / 2),
                    y: Math.round(rect.top + rect.height / 2),
                    width: rect.width,
                    height: rect.height,
                    source: 'shadow-iframe'
                };
            })();
            '''

            # Execute JavaScript and get result
            result = await tab.evaluate(js_code)

            if result and isinstance(result, dict) and 'x' in result and 'y' in result:
                x, y = result['x'], result['y']
                source = result.get('source', 'unknown')
                logger.info(
                    "%s found CAPTCHA button via CDP at (%d, %d), size: %dx%d, source: %s",
                    self.name, x, y, result.get('width', 0), result.get('height', 0), source
                )
                return (x, y)

            logger.debug("%s CDP evaluate returned no valid coordinates: %s", self.name, result)
            return None

        except Exception as e:
            logger.warning("%s CDP evaluate failed: %s", self.name, e)
            return None

    async def _attempt_captcha_solve(self, tab: uc.Tab, attempt_number: int = 1) -> bool:
        """Solve PerimeterX Press & Hold CAPTCHA with 2-layer timing and refresh detection.

        This method implements the complete CAPTCHA solving strategy for PerimeterX's
        "Press & Hold" challenge. PerimeterX uses a 2-layer system where:
        - First attempt is interrupted by page refresh after ~1-2 seconds
        - Second attempt after refresh succeeds with longer ~4-5 second hold

        Solving Strategy:
            1. Locate button via CDP shadow DOM traversal (primary) or CSS selectors (fallback)
            2. Move mouse to button using Bezier curve for natural trajectory
            3. Press and hold with micro-movements simulating hand tremor
            4. Monitor for page refresh during hold (abort if detected)
            5. Release and verify CAPTCHA challenge is resolved

        Hold Duration Logic:
            - attempt_number=1: Short hold (config.captcha_initial_hold_min/max)
              Expected to be interrupted by page refresh
            - attempt_number>=2: Long hold (config.captcha_retry_hold_min/max)
              Full solve duration after refresh has occurred

        Args:
            tab: Browser tab containing the CAPTCHA challenge page.
            attempt_number: Which attempt this is (1=first/short, 2+=retry/long).

        Returns:
            True if CAPTCHA was solved and page content is now accessible.
            False if refresh was detected mid-hold or CAPTCHA still present after attempt.

        Note:
            This method is called by _attempt_captcha_solve_v2() which handles
            the retry loop and progressive backoff between attempts.
        """
        logger.info(
            "%s attempting CAPTCHA solve (attempt %d, Phase 1 enhanced + refresh detection)",
            self.name,
            attempt_number,
        )

        try:
            # Step 0: Try CDP evaluate first (most reliable for shadow DOM/iframe)
            cdp_coords = await self._find_captcha_button_via_cdp(tab)
            element_center = None
            element = None
            iframe_center: tuple[int, int] | None = None

            if cdp_coords:
                element_center = cdp_coords
                logger.info("%s using CDP coordinates: %s", self.name, element_center)
            else:
                # Fall back to existing iframe/selector logic
                logger.debug("%s CDP detection failed, falling back to iframe/selector logic", self.name)
                try:
                    # Updated selectors to match actual PerimeterX CAPTCHA iframe structure
                    iframe_selectors = [
                        "#px-captcha iframe",  # Primary: iframe inside px-captcha container
                        "iframe[title*='verification']",  # Title-based match
                        "iframe[title*='Human verification']",  # Exact title match
                        ".px-captcha-container iframe",  # Class-based container
                        "div#px-captcha iframe",  # Explicit div container
                        "iframe#px-captcha-modal",  # Legacy modal ID
                        "iframe[id*='px-captcha']",  # ID wildcard
                        "iframe[src*='captcha']",  # Source URL match
                    ]

                    iframe_el = None
                    for selector in iframe_selectors:
                        try:
                            iframe_candidates = await tab.query_selector_all(selector)
                            if iframe_candidates:
                                iframe_el = iframe_candidates[0]
                                logger.debug(
                                    "%s found CAPTCHA iframe with selector: %s",
                                    self.name,
                                    selector,
                                )
                                break
                        except Exception as e:
                            logger.debug(
                                "%s selector %s failed: %s",
                                self.name,
                                selector,
                                e,
                            )
                            continue

                    if iframe_el:
                        try:
                            box = await iframe_el.get_box_model()
                            if box:
                                # Extract coordinates from box model
                                # Box model has content/border/padding/margin as arrays of [x,y,x,y,x,y,x,y]
                                quads = box.get("content", box.get("border", []))
                                if quads and len(quads) >= 8:
                                    # Extract x and y coordinates (every other value)
                                    xs = [quads[i] for i in range(0, len(quads), 2)]
                                    ys = [quads[i] for i in range(1, len(quads), 2)]
                                    iframe_x = int(sum(xs) / len(xs))
                                    iframe_y = int(sum(ys) / len(ys))
                                    iframe_center = (iframe_x, iframe_y)
                                    logger.debug(
                                        "%s calculated iframe center at (%d, %d)",
                                        self.name,
                                        iframe_x,
                                        iframe_y,
                                    )
                        except Exception as e:
                            logger.debug(
                                "%s failed to get iframe box model: %s",
                                self.name,
                                e,
                            )
                            iframe_center = None

                        # Attempt to find button inside iframe if API supports content querying
                        # Note: This rarely works with cross-origin iframes, but we try anyway
                        try:
                            frame_buttons = await iframe_el.query_selector_all("button")
                            for btn in frame_buttons:
                                text = (
                                    (getattr(btn, "text", "") or "").lower()
                                    or btn.attrs.get("aria-label", "").lower()
                                )
                                if "press" in text and "hold" in text:
                                    element = btn
                                    logger.debug("%s found CAPTCHA button inside iframe", self.name)
                                    break
                        except Exception:
                            pass
                except Exception:
                    pass

                # If not found in iframe, try regular DOM selectors
                if not element:
                    selectors = [
                        # Primary: wrapper-based selectors (modern CAPTCHA DOM structure)
                        "#px-captcha-wrapper [role='button']",
                        "#px-captcha-wrapper div[tabindex='0']",
                        ".px-captcha-container [role='button']",
                        # Secondary: class-based (legacy support)
                        "button[class*='px-captcha']",
                        "div[class*='px-captcha'] button",
                        # Fallback: role-based without class constraints
                        "[role='button'][tabindex='0']",
                        "div[aria-describedby][role='button']",
                    ]

                    for selector in selectors:
                        try:
                            found = await tab.select(selector)
                            if found:
                                element = found
                                logger.debug(
                                    "%s found CAPTCHA button with selector: %s",
                                    self.name,
                                    selector,
                                )
                                break
                        except Exception:
                            continue

                if not element:
                    # Fallback: scan buttons for matching text
                    try:
                        buttons = await tab.query_selector_all("button")
                        for btn in buttons:
                            text = (
                                (getattr(btn, "text", "") or "").lower()
                                or btn.attrs.get("aria-label", "").lower()
                            )
                            if "press" in text and "hold" in text:
                                element = btn
                                logger.debug("%s found CAPTCHA button by text scan", self.name)
                                break
                    except Exception:
                        pass

                if not element:
                    # If we located the iframe bounds, press/hold at its center as a last resort
                    if iframe_center:
                        logger.warning(
                            "%s CAPTCHA button not found; pressing iframe center (%d,%d)",
                            self.name,
                            iframe_center[0],
                            iframe_center[1],
                        )
                        element_center = iframe_center
                    else:
                        logger.warning("%s could not find CAPTCHA button", self.name)
                        return False
                else:
                    element_center = None

            # Get element position for mouse targeting
            # Note: nodriver API may vary - adjust as needed
            x: int | None = None
            y: int | None = None

            try:
                if element_center:
                    x, y = element_center
                elif element is not None:
                    rect = await element.get_box_model()
                    if rect and "content" in rect:
                        xs = rect["content"][0::2]
                        ys = rect["content"][1::2]
                        x = int(sum(xs) / len(xs))
                        y = int(sum(ys) / len(ys))
                    else:
                        logger.warning(
                            "%s could not get element position, using default viewport center",
                            self.name,
                        )
                        x, y = self.DEFAULT_VIEWPORT_CENTER
                else:
                    logger.warning(
                        "%s no element or coordinates available",
                        self.name,
                    )
                    return False
            except AttributeError:
                # Fallback if method not available
                logger.warning(
                    "%s get_box_model not available, using element click",
                    self.name,
                )

            # Phase 1 Enhancement: Use Bezier curve for mouse movement
            if x is not None and y is not None:
                await self._human_mouse_move_bezier(tab, x, y)
                await self._human_delay()

            # Step 3: Capture initial state for refresh detection
            initial_url = tab.target.url if hasattr(tab, "target") else str(tab.url)
            try:
                initial_content = await tab.get_content()
                initial_content_length = len(initial_content) if initial_content else 0
            except Exception:
                initial_content_length = 0

            # Step 3: 2-layer hold duration based on attempt number
            # First attempt: shorter hold (1.5-2.5s) - will likely be interrupted by refresh
            # Retry attempts: longer hold (4.5-6.5s) - full CAPTCHA solve after refresh
            if attempt_number == 1:
                hold_duration = random.uniform(
                    self.config.captcha_initial_hold_min,
                    self.config.captcha_initial_hold_max,
                )
            else:
                hold_duration = random.uniform(
                    self.config.captcha_retry_hold_min,
                    self.config.captcha_retry_hold_max,
                )

            logger.info(
                "%s pressing/holding CAPTCHA for %.2fs w/ micro-movements (attempt %d)",
                self.name,
                hold_duration,
                attempt_number,
            )

            # Phase 1 Enhancement: Press and hold with micro-movements (hand tremor simulation)
            try:
                # If we have coordinates, use mouse events with micro-movements
                if x is not None and y is not None:
                    await tab.mouse_down(x, y)

                    # Simulate hand tremor during hold with pixel jitter
                    # Check for page refresh at configured interval during hold
                    elapsed = 0.0
                    last_refresh_check = 0.0
                    jitter = self.MOUSE_JITTER_PIXELS
                    interval_range = self.MICRO_MOVEMENT_INTERVAL_RANGE
                    refresh_interval = self.REFRESH_CHECK_INTERVAL_SECONDS

                    while elapsed < hold_duration:
                        # Sleep for random micro-movement interval
                        interval = random.uniform(*interval_range)
                        sleep_time = min(interval, hold_duration - elapsed)
                        await asyncio.sleep(sleep_time)
                        elapsed += sleep_time

                        # Periodically check for page refresh (2-layer detection)
                        if elapsed - last_refresh_check >= refresh_interval:
                            refresh_detected = await self._detect_page_refresh(
                                tab, initial_url, initial_content_length
                            )
                            if refresh_detected:
                                logger.info(
                                    "%s page refresh detected mid-hold at %.2fs, aborting",
                                    self.name,
                                    elapsed,
                                )
                                await tab.mouse_up(x, y)
                                return False  # Signal retry with longer hold
                            last_refresh_check = elapsed

                        # Apply micro-movement (hand tremor) if not at end of hold
                        if elapsed < hold_duration:
                            jitter_x = x + random.randint(-jitter, jitter)
                            jitter_y = y + random.randint(-jitter, jitter)
                            try:
                                await tab.mouse_move(jitter_x, jitter_y)
                            except AttributeError:
                                # Mouse move not available, continue hold
                                pass

                    await tab.mouse_up(x, y)
                elif element is not None:
                    # Fallback: just click the element without micro-movements
                    await element.click()
                    await asyncio.sleep(hold_duration)

            except AttributeError:
                # Fallback if mouse methods not available
                if element is not None:
                    logger.warning(
                        "%s mouse events not available, using element click",
                        self.name,
                    )
                    await element.click()
                    await asyncio.sleep(hold_duration)

            # Wait for page to change (CAPTCHA solve typically triggers navigation)
            await asyncio.sleep(self.CAPTCHA_SOLVE_WAIT_SECONDS)

            # Check if CAPTCHA is gone
            captcha_still_present = await self._check_for_captcha(tab)

            if captcha_still_present:
                logger.warning("%s CAPTCHA still present after solve attempt", self.name)
                return False

            logger.info("%s CAPTCHA solved successfully", self.name)
            return True

        except Exception as e:
            logger.error("%s error solving CAPTCHA: %s", self.name, e)
            return False

    async def _attempt_captcha_solve_v2(
        self, tab: uc.Tab, max_attempts: int = 3
    ) -> bool:
        """Orchestrate multi-attempt CAPTCHA solving with progressive backoff.

        This method coordinates the 2-layer CAPTCHA solving strategy by:
        1. Calling _attempt_captcha_solve() with attempt_number to control hold duration
        2. Applying progressive backoff between failed attempts
        3. Returning success on first successful solve

        The 2-layer timing is handled by _attempt_captcha_solve() based on attempt_number:
        - Attempt 1: Short hold (1.5-2.5s) - expected to be interrupted by refresh
        - Attempt 2+: Long hold (4.5-6.5s) - full solve after refresh occurred

        Progressive backoff between attempts:
        - Backoff duration = (5-10 seconds) * attempt_number
        - Helps avoid rate limiting and allows page state to stabilize

        Args:
            tab: Browser tab containing the CAPTCHA challenge.
            max_attempts: Maximum solve attempts before giving up (default: 3).

        Returns:
            True if CAPTCHA was solved on any attempt.
            False if all attempts were exhausted without success.
        """
        logger.info(
            "%s attempting CAPTCHA solve with up to %d attempts",
            self.name,
            max_attempts,
        )

        for attempt in range(1, max_attempts + 1):
            logger.info(
                "%s CAPTCHA solve attempt %d/%d",
                self.name,
                attempt,
                max_attempts,
            )

            try:
                # Try to solve CAPTCHA (hold duration varies by attempt_number)
                success = await self._attempt_captcha_solve(tab, attempt_number=attempt)

                if success:
                    logger.info(
                        "%s CAPTCHA solved on attempt %d/%d",
                        self.name,
                        attempt,
                        max_attempts,
                    )
                    return True

                # Failed this attempt
                logger.warning(
                    "%s CAPTCHA solve attempt %d/%d failed",
                    self.name,
                    attempt,
                    max_attempts,
                )

                # If not the last attempt, apply progressive backoff
                if attempt < max_attempts:
                    backoff_min = self.BACKOFF_MULTIPLIER_MIN * attempt
                    backoff_max = self.BACKOFF_MULTIPLIER_MAX * attempt
                    backoff = random.uniform(backoff_min, backoff_max)

                    logger.info(
                        "%s backing off for %.2fs before attempt %d",
                        self.name,
                        backoff,
                        attempt + 1,
                    )
                    await asyncio.sleep(backoff)

            except Exception as e:
                logger.error(
                    "%s error during CAPTCHA solve attempt %d: %s",
                    self.name,
                    attempt,
                    e,
                )
                # Continue to next attempt unless it's the last one
                if attempt >= max_attempts:
                    break

        # All attempts exhausted
        logger.error(
            "%s CAPTCHA solving failed after %d attempts",
            self.name,
            max_attempts,
        )
        return False

    async def _human_delay(self) -> None:
        """Sleep for random duration to simulate human behavior.

        Uses configured min/max delay values from StealthExtractionConfig.
        """
        delay = random.uniform(
            self.config.human_delay_min,
            self.config.human_delay_max,
        )
        logger.debug("%s human delay: %.2fs", self.name, delay)
        await asyncio.sleep(delay)
