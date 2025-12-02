"""Browser pool infrastructure for managing nodriver browser instances.

Provides stealth-configured browser instances with human-like behavior patterns
for web scraping operations that require anti-detection measures.

Supports browser window isolation for non-headless mode to prevent interference
with user input during stealth automation.
"""

import asyncio
import logging
import random

import nodriver as uc

from .proxy_extension_builder import ProxyExtensionBuilder

logger = logging.getLogger(__name__)


class BrowserPool:
    """Manages nodriver browser instances with stealth configurations.

    Provides lazy initialization, user agent rotation, and human-like
    interaction patterns to avoid detection by anti-bot systems.

    Supports browser window isolation for non-headless mode to prevent
    interference with user input during stealth automation.

    Attributes:
        proxy_url: Optional proxy server URL
        headless: Whether to run browser in headless mode
        viewport_width: Browser viewport width in pixels
        viewport_height: Browser viewport height in pixels
        isolation_mode: Browser isolation mode for non-headless operation
        fallback_to_minimize: Fall back to minimize if preferred isolation fails
    """

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    ]

    def __init__(
        self,
        proxy_url: str | None = None,
        headless: bool = True,
        viewport_width: int = 1280,
        viewport_height: int = 720,
        isolation_mode: str = "virtual_display",
        fallback_to_minimize: bool = True,
    ) -> None:
        """Initialize browser pool configuration.

        Note: Browser is not started until first get_browser() call.

        Args:
            proxy_url: Optional proxy server URL (e.g., "http://user:pass@proxy:port")
            headless: Whether to run browser in headless mode
            viewport_width: Browser viewport width in pixels
            viewport_height: Browser viewport height in pixels
            isolation_mode: Browser isolation mode for non-headless operation.
                Options: "virtual_display", "secondary_display", "off_screen",
                "minimize", "none"
            fallback_to_minimize: If preferred isolation fails, use minimize mode
        """
        # Import here to avoid circular imports
        from phx_home_analysis.config.settings import BrowserIsolationMode

        self.proxy_url = proxy_url
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.fallback_to_minimize = fallback_to_minimize

        # Parse isolation mode
        if isinstance(isolation_mode, str):
            try:
                self.isolation_mode = BrowserIsolationMode(isolation_mode)
            except ValueError:
                logger.warning(
                    "Unknown isolation mode '%s', defaulting to VIRTUAL_DISPLAY",
                    isolation_mode,
                )
                self.isolation_mode = BrowserIsolationMode.VIRTUAL_DISPLAY
        else:
            self.isolation_mode = isolation_mode

        self._browser: uc.Browser | None = None
        self._browser_lock = asyncio.Lock()
        self._proxy_extension: ProxyExtensionBuilder | None = None

        # Check if proxy URL contains credentials
        self._proxy_has_auth = bool(
            proxy_url and "@" in proxy_url and "://" in proxy_url
        )

        logger.info(
            "BrowserPool configured: headless=%s, viewport=%dx%d, proxy=%s (auth=%s), isolation=%s",
            headless,
            viewport_width,
            viewport_height,
            "enabled" if proxy_url else "disabled",
            "yes" if self._proxy_has_auth else "no",
            self.isolation_mode.value if not headless else "n/a",
        )

    async def get_browser(self) -> uc.Browser:
        """Get or create browser instance with thread-safe lazy initialization.

        Uses asyncio.Lock to ensure only one browser is created even when
        called concurrently from multiple coroutines.

        If proxy URL contains credentials, creates a Chrome extension for
        authentication instead of using --proxy-server with inline credentials
        (which Chrome doesn't support).

        For non-headless mode, applies window isolation based on isolation_mode
        to prevent interference with user input.

        Returns:
            Browser instance configured with stealth settings

        Raises:
            ValueError: If proxy URL format is invalid
        """
        if self._browser is not None:
            return self._browser

        async with self._browser_lock:
            # Double-check pattern: another coroutine may have created it
            if self._browser is not None:
                return self._browser

            logger.info("Initializing new browser instance with stealth configuration")

            # Create browser with nodriver
            # Note: nodriver 0.48+ uses add_argument() instead of browser_args property
            browser_config = uc.Config()
            browser_config.headless = self.headless

            # Add stealth arguments (nodriver has restrictions on certain flags)
            # --no-sandbox and some flags are controlled via Config attributes
            browser_config.add_argument("--disable-blink-features=AutomationControlled")
            browser_config.add_argument(
                f"--window-size={self.viewport_width},{self.viewport_height}"
            )

            # Configure window isolation for non-headless mode
            if not self.headless:
                self._configure_window_isolation(browser_config)

            # Handle proxy configuration
            if self.proxy_url:
                if self._proxy_has_auth:
                    # Create proxy extension for authenticated proxy
                    logger.info(
                        "Creating proxy authentication extension for: %s",
                        self.proxy_url.split("@")[1] if "@" in self.proxy_url else self.proxy_url,
                    )

                    try:
                        self._proxy_extension = ProxyExtensionBuilder.from_url(
                            self.proxy_url
                        )
                        extension_path = self._proxy_extension.create_extension()

                        # Load extension (works in both headless and headed mode)
                        browser_config.add_argument(
                            f"--load-extension={extension_path}"
                        )
                        # For headless mode, also need this to ensure extension loads
                        browser_config.add_argument(
                            f"--disable-extensions-except={extension_path}"
                        )

                        logger.info(
                            "Proxy extension loaded from: %s", extension_path
                        )

                    except Exception as e:
                        logger.error("Failed to create proxy extension: %s", e)
                        # Cleanup on error
                        if self._proxy_extension:
                            self._proxy_extension.cleanup()
                            self._proxy_extension = None
                        raise

                else:
                    # No authentication - use standard --proxy-server
                    browser_config.add_argument(f"--proxy-server={self.proxy_url}")
                    logger.info(
                        "Browser configured with proxy (no auth): %s", self.proxy_url
                    )

            self._browser = await uc.start(config=browser_config)

            logger.info("Browser initialized successfully (headless=%s)", self.headless)

            return self._browser

    def _configure_window_isolation(self, browser_config: uc.Config) -> None:
        """Configure browser window isolation for non-headless mode.

        Positions the browser window on a virtual display, secondary monitor,
        or off-screen to prevent interference with user input.

        Args:
            browser_config: nodriver Config object to add arguments to
        """
        from phx_home_analysis.config.settings import BrowserIsolationMode

        from .display_utils import (
            find_virtual_display,
            get_displays,
            get_recommended_position,
        )

        position: tuple[int, int] | None = None
        effective_mode = self.isolation_mode

        if effective_mode == BrowserIsolationMode.VIRTUAL_DISPLAY:
            # Try to find virtual display
            vd = find_virtual_display()
            if vd:
                position = (vd.x, vd.y)
                logger.info(
                    "Using virtual display for isolation at (%d, %d)", vd.x, vd.y
                )
            elif self.fallback_to_minimize:
                logger.warning(
                    "Virtual display not found, falling back to minimize mode"
                )
                effective_mode = BrowserIsolationMode.MINIMIZE
            else:
                # Use recommended position (off-screen or secondary)
                position = get_recommended_position()
                logger.warning(
                    "Virtual display not found, using position (%d, %d)",
                    position[0],
                    position[1],
                )

        elif effective_mode == BrowserIsolationMode.SECONDARY_DISPLAY:
            # Try to find secondary display
            displays = get_displays()
            secondary = next(
                (d for d in displays if not d.is_primary),
                None,
            )
            if secondary:
                position = (secondary.x, secondary.y)
                logger.info(
                    "Using secondary display for isolation at (%d, %d)",
                    secondary.x,
                    secondary.y,
                )
            elif self.fallback_to_minimize:
                logger.warning(
                    "Secondary display not found, falling back to minimize mode"
                )
                effective_mode = BrowserIsolationMode.MINIMIZE
            else:
                position = get_recommended_position()
                logger.warning(
                    "Secondary display not found, using position (%d, %d)",
                    position[0],
                    position[1],
                )

        elif effective_mode == BrowserIsolationMode.OFF_SCREEN:
            # Position off-screen
            position = get_recommended_position()
            logger.info(
                "Using off-screen position for isolation at (%d, %d)",
                position[0],
                position[1],
            )

        elif effective_mode == BrowserIsolationMode.NONE:
            logger.info("Browser isolation disabled, window will be visible")

        # Apply position if determined
        if position:
            browser_config.add_argument(
                f"--window-position={position[0]},{position[1]}"
            )

        # Apply minimize mode if needed
        if effective_mode == BrowserIsolationMode.MINIMIZE:
            browser_config.add_argument("--start-minimized")
            logger.info("Browser will start minimized")

    async def new_tab(self, url: str) -> uc.Tab:
        """Create new tab and navigate to URL.

        Args:
            url: URL to navigate to

        Returns:
            Tab instance ready for interaction

        Raises:
            Exception: If browser initialization or navigation fails
        """
        browser = await self.get_browser()

        logger.info("Creating new tab and navigating to: %s", url)
        tab = await browser.get(url)

        # Add human delay after navigation
        await self.human_delay(0.5, 1.5)

        logger.info("Tab created and navigation complete")
        return tab

    async def close(self) -> None:
        """Stop browser and cleanup resources.

        Closes browser and cleans up proxy extension if it was created.
        Safe to call multiple times - will only close if browser exists.
        """
        if self._browser is not None:
            logger.info("Closing browser instance")
            try:
                await self._browser.stop()
                self._browser = None
                logger.info("Browser closed successfully")
            except Exception as e:
                logger.error("Error closing browser: %s", e)
                # Ensure browser reference is cleared even on error
                self._browser = None

        # Cleanup proxy extension if it exists
        if self._proxy_extension is not None:
            logger.info("Cleaning up proxy extension")
            try:
                self._proxy_extension.cleanup()
                self._proxy_extension = None
            except Exception as e:
                logger.error("Error cleaning up proxy extension: %s", e)
                # Ensure reference is cleared even on error
                self._proxy_extension = None

    def get_random_user_agent(self) -> str:
        """Get random user agent from rotation list.

        Returns:
            Randomly selected user agent string
        """
        ua = random.choice(self.USER_AGENTS)
        logger.debug("Selected user agent: %s", ua[:50] + "...")
        return ua

    @staticmethod
    async def human_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """Sleep for random duration to simulate human behavior.

        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
        """
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug("Human delay: %.2fs", delay)
        await asyncio.sleep(delay)

    @staticmethod
    async def human_scroll(tab: uc.Tab, distance: int = 300) -> None:
        """Scroll page with random variation to simulate human behavior.

        Args:
            tab: Browser tab to scroll
            distance: Approximate scroll distance in pixels
        """
        # Add random variation to scroll distance (±20%)
        variation = random.uniform(0.8, 1.2)
        actual_distance = int(distance * variation)

        logger.debug("Human scroll: %dpx (requested: %dpx)", actual_distance, distance)

        await tab.scroll_down(actual_distance)

        # Add small delay after scroll
        await BrowserPool.human_delay(0.2, 0.5)

    @staticmethod
    async def human_mouse_move(tab: uc.Tab, x: int, y: int) -> None:
        """Move mouse with intermediate points to simulate human movement.

        Creates a more natural mouse movement path by adding intermediate
        waypoints rather than instant teleportation to target.

        Args:
            tab: Browser tab to move mouse in
            x: Target X coordinate
            y: Target Y coordinate
        """
        logger.debug("Human mouse move to: (%d, %d)", x, y)

        # Get current mouse position (or start from 0,0)
        # Note: nodriver may not support getting current position,
        # so we'll use direct movement with small delay

        # Add small random offset to target (±5 pixels)
        target_x = x + random.randint(-5, 5)
        target_y = y + random.randint(-5, 5)

        try:
            # Move mouse to target position
            # Note: nodriver's mouse API may vary - adjust if needed
            await tab.mouse_move(target_x, target_y)

            # Small delay after movement
            await BrowserPool.human_delay(0.1, 0.3)

        except AttributeError:
            # Fallback if mouse_move not available in this version
            logger.warning("Mouse move not supported in current nodriver version")

    async def __aenter__(self) -> "BrowserPool":
        """Async context manager entry.

        Returns:
            Self for use in async with statement
        """
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit - cleanup browser.

        Args:
            exc_type: Exception type if error occurred
            exc_val: Exception value if error occurred
            exc_tb: Exception traceback if error occurred
        """
        await self.close()
