"""Example: Using BrowserPool with authenticated proxy.

Demonstrates automatic proxy extension creation and usage.
"""

import asyncio
import logging
import os

from dotenv import load_dotenv

from src.phx_home_analysis.services.infrastructure import BrowserPool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def test_proxy_browsing():
    """Test browsing with authenticated proxy."""

    # Load environment variables
    load_dotenv()

    # Build proxy URL from environment
    proxy_server = os.getenv("PROXY_SERVER")
    proxy_username = os.getenv("PROXY_USERNAME")
    proxy_password = os.getenv("PROXY_PASSWORD")

    if not all([proxy_server, proxy_username, proxy_password]):
        logger.error("Missing proxy credentials in .env file")
        logger.info("Required: PROXY_SERVER, PROXY_USERNAME, PROXY_PASSWORD")
        return

    proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_server}"

    logger.info("Starting browser with authenticated proxy...")

    # BrowserPool automatically detects authentication and creates extension
    async with BrowserPool(proxy_url=proxy_url, headless=True) as pool:
        logger.info("Browser pool created (extension auto-configured)")

        # Get browser instance
        browser = await pool.get_browser()
        logger.info("Browser started")

        # Test 1: Check IP address via proxy
        logger.info("\n=== Test 1: Checking IP via proxy ===")
        tab = await pool.new_tab("https://httpbin.org/ip")

        # Wait for page to load
        await pool.human_delay(2, 3)

        # Get page content (would show proxy IP)
        logger.info("Page loaded successfully via proxy")

        # Test 2: Navigate to another page
        logger.info("\n=== Test 2: Navigate to example.com ===")
        await tab.get("https://example.com")
        await pool.human_delay(1, 2)
        logger.info("Navigation successful")

        # Test 3: Human-like interaction
        logger.info("\n=== Test 3: Human-like behavior ===")
        await pool.human_scroll(tab, distance=500)
        logger.info("Scrolled page")

        await pool.human_delay(0.5, 1.0)
        logger.info("Paused like human")

        logger.info("\n=== All tests completed successfully ===")

    # Extension cleanup happens automatically via context manager
    logger.info("Browser closed, extension cleaned up")


async def example_manual_cleanup():
    """Example with manual cleanup (not recommended)."""

    load_dotenv()

    proxy_url = (
        f"http://{os.getenv('PROXY_USERNAME')}:"
        f"{os.getenv('PROXY_PASSWORD')}@"
        f"{os.getenv('PROXY_SERVER')}"
    )

    pool = None
    try:
        # Create pool
        pool = BrowserPool(proxy_url=proxy_url, headless=True)

        # Get browser
        browser = await pool.get_browser()

        # Do something
        tab = await pool.new_tab("https://example.com")
        await pool.human_delay(2, 3)

        logger.info("Work completed")

    finally:
        # IMPORTANT: Always cleanup
        if pool:
            await pool.close()
            logger.info("Cleanup completed")


async def example_without_auth():
    """Example with proxy that doesn't require authentication."""

    # No authentication in URL
    proxy_url = "http://proxy.example.com:8080"

    async with BrowserPool(proxy_url=proxy_url, headless=True) as pool:
        # BrowserPool detects no auth and uses standard --proxy-server flag
        # No extension created
        browser = await pool.get_browser()

        tab = await pool.new_tab("https://example.com")
        await pool.human_delay(1, 2)

        logger.info("No-auth proxy test completed")


def main():
    """Run example."""
    logger.info("=" * 60)
    logger.info("Proxy Browser Example")
    logger.info("=" * 60)

    # Run main test
    asyncio.run(test_proxy_browsing())

    # Uncomment to test other examples:
    # asyncio.run(example_manual_cleanup())
    # asyncio.run(example_without_auth())


if __name__ == "__main__":
    main()
