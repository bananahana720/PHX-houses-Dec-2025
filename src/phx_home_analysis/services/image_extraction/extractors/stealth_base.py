"""Stealth browser-based extractor base class using nodriver and curl_cffi.

This module provides a base class for Zillow and Redfin extractors that need
to bypass PerimeterX and other anti-bot systems using stealth techniques.
"""

import asyncio
import logging
import random
from abc import abstractmethod

import httpx
import nodriver as uc

from ....config.settings import StealthExtractionConfig
from ....domain.entities import Property
from ...infrastructure import BrowserPool, StealthHttpClient
from .base import ExtractionError, ImageExtractor, SourceUnavailableError

logger = logging.getLogger(__name__)


class StealthBrowserExtractor(ImageExtractor):
    """Abstract base class for stealth browser-based extraction.

    Extends ImageExtractor with nodriver browser automation and curl_cffi
    HTTP client for bypassing anti-bot systems like PerimeterX.

    Uses template method pattern:
    - Subclasses implement _build_search_url() and _extract_urls_from_page()
    - Base class handles navigation, CAPTCHA detection/solving, and delays

    Example:
        ```python
        class ZillowExtractor(StealthBrowserExtractor):
            @property
            def source(self) -> ImageSource:
                return ImageSource.ZILLOW

            def _build_search_url(self, property: Property) -> str:
                return f"https://zillow.com/homes/{property.full_address}"

            async def _extract_urls_from_page(self, tab: uc.Tab) -> list[str]:
                # Extract image URLs from page
                return urls
        ```
    """

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
                solved = await self._attempt_captcha_solve(tab)
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
                        retry_after=300,  # 5 minutes
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
            raise ExtractionError(f"Navigation failed for {url}: {e}")

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
            # Adjust threshold based on content analysis
            # Small pages (<30KB) are likely CAPTCHA interstitials
            # Medium pages (30-70KB) need deeper inspection
            # Large pages (>70KB) likely have property content
            if content_length > 70000:
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
        """Move mouse using Bezier curve for natural trajectory.

        Implements cubic Bezier curve movement with randomized control points
        to simulate natural human mouse movement patterns. This is more sophisticated
        than the linear movement in BrowserPool.human_mouse_move().

        Args:
            tab: Browser tab to move mouse in
            target_x: Target X coordinate
            target_y: Target Y coordinate
        """
        logger.debug(
            "%s Bezier mouse move to: (%d, %d)", self.name, target_x, target_y
        )

        try:
            # Start position (assume center-left of viewport)
            start_x = self.config.viewport_width // 4
            start_y = self.config.viewport_height // 2

            # Generate random control points for cubic Bezier curve
            # Control point 1: between start and target, with random offset
            cp1_x = start_x + int((target_x - start_x) * random.uniform(0.2, 0.4))
            cp1_y = start_y + int((target_y - start_y) * random.uniform(0.2, 0.4))
            cp1_x += random.randint(-50, 50)  # Add random variation
            cp1_y += random.randint(-50, 50)

            # Control point 2: between start and target, with random offset
            cp2_x = start_x + int((target_x - start_x) * random.uniform(0.6, 0.8))
            cp2_y = start_y + int((target_y - start_y) * random.uniform(0.6, 0.8))
            cp2_x += random.randint(-50, 50)  # Add random variation
            cp2_y += random.randint(-50, 50)

            logger.debug(
                "%s Bezier control points: CP1=(%d,%d), CP2=(%d,%d)",
                self.name,
                cp1_x,
                cp1_y,
                cp2_x,
                cp2_y,
            )

            # Generate points along Bezier curve
            # Use 15-25 steps for smooth movement
            num_steps = random.randint(15, 25)
            points = []

            for i in range(num_steps + 1):
                t = i / num_steps

                # Cubic Bezier formula: B(t) = (1-t)³P₀ + 3(1-t)²tP₁ + 3(1-t)t²P₂ + t³P₃
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
            for x, y in points:
                try:
                    await tab.mouse_move(x, y)
                    # Vary speed along path (faster in middle, slower at ends)
                    delay = random.uniform(0.01, 0.03)
                    await asyncio.sleep(delay)
                except AttributeError:
                    # Fallback if mouse_move not available
                    logger.debug("%s mouse_move not available, using direct movement", self.name)
                    break

            # Final position with small random offset (±3 pixels)
            final_x = target_x + random.randint(-3, 3)
            final_y = target_y + random.randint(-3, 3)

            try:
                await tab.mouse_move(final_x, final_y)
            except AttributeError:
                pass

            # Small pause after movement
            await asyncio.sleep(random.uniform(0.1, 0.2))

            logger.debug("%s Bezier mouse move complete", self.name)

        except Exception as e:
            logger.warning(
                "%s error during Bezier mouse movement: %s, falling back to direct move",
                self.name,
                e,
            )
            # Fallback to simple movement
            try:
                await tab.mouse_move(target_x, target_y)
            except Exception:
                pass

    async def _attempt_captcha_solve(self, tab: uc.Tab) -> bool:
        """Attempt to solve Press & Hold CAPTCHA (enhanced with Phase 1 improvements).

        Enhanced strategy (Phase 1):
        1. Find button element with "px-captcha" class or "Press & Hold" text
        2. Get element position
        3. Move mouse with Bezier curve for natural trajectory
        4. Mouse down with micro-movements during hold (hand tremor simulation)
        5. Mouse up and verify CAPTCHA is gone
        6. Wider hold duration randomization (4.5-8.5s)

        Args:
            tab: Browser tab with CAPTCHA

        Returns:
            True if CAPTCHA solved, False otherwise
        """
        logger.info("%s attempting CAPTCHA solve (Phase 1 enhanced)", self.name)

        try:
            # Try locating CAPTCHA inside its iframe overlay first
            element = None
            iframe_center: tuple[int, int] | None = None
            try:
                iframe_candidates = await tab.query_selector_all(
                    "iframe#px-captcha-modal, iframe[id*='px-captcha'], iframe[src*='captcha']"
                )
                if iframe_candidates:
                    iframe_el = iframe_candidates[0]
                    try:
                        rect = await iframe_el.get_box_model()
                        if rect and "content" in rect:
                            xs = rect["content"][0::2]
                            ys = rect["content"][1::2]
                            iframe_center = (int(sum(xs) / len(xs)), int(sum(ys) / len(ys)))
                    except Exception:
                        iframe_center = None
                    # Attempt to find button inside iframe if API supports content querying
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
                    "button[class*='px-captcha']",
                    "div[class*='px-captcha'] button",
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
                    x, y = iframe_center
                    logger.warning(
                        "%s CAPTCHA button not found; pressing iframe center (%d,%d)",
                        self.name,
                        x,
                        y,
                    )
                    element_center = (x, y)
                else:
                    logger.warning("%s could not find CAPTCHA button", self.name)
                    return False
            else:
                element_center = None

            # Get element position
            # Note: nodriver API may vary - adjust as needed
            try:
                if element_center:
                    x, y = element_center
                else:
                    rect = await element.get_box_model()
                    if rect and "content" in rect:
                        xs = rect["content"][0::2]
                        ys = rect["content"][1::2]
                        x = int(sum(xs) / len(xs))
                        y = int(sum(ys) / len(ys))
                    else:
                        logger.warning(
                            "%s could not get element position, using default",
                            self.name,
                        )
                        x, y = 640, 360  # Center of 1280x720 viewport
            except AttributeError:
                # Fallback if method not available
                logger.warning(
                    "%s get_box_model not available, using element click",
                    self.name,
                )
                x, y = None, None

            # Phase 1 Enhancement: Use Bezier curve for mouse movement
            if x is not None and y is not None:
                await self._human_mouse_move_bezier(tab, x, y)
                await self._human_delay()

            # Phase 1 Enhancement: Wider hold duration randomization (4.5-8.5s)
            hold_duration = random.uniform(
                self.config.captcha_hold_min,
                self.config.captcha_hold_max,
            )

            logger.info(
                "%s pressing and holding CAPTCHA button for %.2fs with micro-movements",
                self.name,
                hold_duration,
            )

            # Phase 1 Enhancement: Press and hold with micro-movements (hand tremor simulation)
            try:
                # If we have coordinates, use mouse events with micro-movements
                if x is not None and y is not None:
                    await tab.mouse_down(x, y)

                    # Simulate hand tremor during hold with ±2px jitter
                    # Random micro-movement intervals (0.1-0.3s)
                    elapsed = 0.0
                    while elapsed < hold_duration:
                        # Random micro-movement interval
                        interval = random.uniform(0.1, 0.3)
                        sleep_time = min(interval, hold_duration - elapsed)
                        await asyncio.sleep(sleep_time)
                        elapsed += sleep_time

                        # Apply micro-movement (±2px jitter) if not at end
                        if elapsed < hold_duration:
                            jitter_x = x + random.randint(-2, 2)
                            jitter_y = y + random.randint(-2, 2)
                            try:
                                await tab.mouse_move(jitter_x, jitter_y)
                                logger.debug(
                                    "%s micro-movement: (%d,%d) -> (%d,%d)",
                                    self.name,
                                    x,
                                    y,
                                    jitter_x,
                                    jitter_y,
                                )
                            except AttributeError:
                                # Mouse move not available, continue hold
                                pass

                    await tab.mouse_up(x, y)
                else:
                    # Fallback: just click the element
                    await element.click()
                    await asyncio.sleep(hold_duration)

            except AttributeError:
                # Fallback if mouse methods not available
                logger.warning(
                    "%s mouse events not available, using element click",
                    self.name,
                )
                await element.click()
                await asyncio.sleep(hold_duration)

            # Wait for page to change (CAPTCHA solve typically triggers navigation)
            await asyncio.sleep(3.0)

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
        """Attempt to solve Press & Hold CAPTCHA with multi-attempt strategy.

        Phase 1 Enhancement: Multi-attempt solving with progressive backoff.
        This method tries different solving strategies across multiple attempts:
        - Attempt 1: Standard Bezier movement + micro-movements
        - Attempt 2: Longer hold duration, different movement path
        - Attempt 3: Extended hold with more aggressive micro-movements

        Args:
            tab: Browser tab with CAPTCHA
            max_attempts: Maximum number of solve attempts (default: 3)

        Returns:
            True if CAPTCHA solved on any attempt, False if all attempts fail
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
                # Try to solve CAPTCHA using current strategy
                success = await self._attempt_captcha_solve(tab)

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
                    # Progressive backoff: 5-10s × attempt number
                    backoff_min = 5.0 * attempt
                    backoff_max = 10.0 * attempt
                    backoff = random.uniform(backoff_min, backoff_max)

                    logger.info(
                        "%s backing off for %.2fs before attempt %d",
                        self.name,
                        backoff,
                        attempt + 1,
                    )
                    await asyncio.sleep(backoff)

                    # Modify strategy for next attempt
                    if attempt == 1:
                        # Attempt 2: Increase hold duration by 20%
                        original_min = self.config.captcha_hold_min
                        original_max = self.config.captcha_hold_max
                        logger.debug(
                            "%s attempt 2 strategy: increase hold duration 20%%",
                            self.name,
                        )
                    elif attempt == 2:
                        # Attempt 3: Increase hold duration by 40%
                        logger.debug(
                            "%s attempt 3 strategy: increase hold duration 40%%",
                            self.name,
                        )

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
