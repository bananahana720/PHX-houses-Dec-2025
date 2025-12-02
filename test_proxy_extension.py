"""Test script for proxy extension functionality.

Verifies that:
1. ProxyExtensionBuilder creates valid extension directory
2. Extension files are properly configured with credentials
3. BrowserPool integrates extension correctly
4. Cleanup works properly
"""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.phx_home_analysis.services.infrastructure import (
    BrowserPool,
    ProxyExtensionBuilder,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def test_extension_builder():
    """Test ProxyExtensionBuilder creates extension correctly."""
    logger.info("=" * 60)
    logger.info("TEST 1: ProxyExtensionBuilder")
    logger.info("=" * 60)

    # Test with explicit credentials
    builder = ProxyExtensionBuilder(
        host="p.webshare.io",
        port=80,
        username="test_user",
        password="test_pass",
    )

    try:
        # Create extension
        ext_path = builder.create_extension()
        logger.info("Extension created at: %s", ext_path)

        # Verify files exist
        assert ext_path.exists(), "Extension directory not created"
        assert (ext_path / "manifest.json").exists(), "manifest.json missing"
        assert (ext_path / "background.js").exists(), "background.js missing"

        # Verify background.js has credentials
        background_content = (ext_path / "background.js").read_text()
        assert '"p.webshare.io"' in background_content, "Host not substituted"
        assert "80" in background_content, "Port not substituted"
        assert '"test_user"' in background_content, "Username not substituted"
        assert '"test_pass"' in background_content, "Password not substituted"

        # Verify no placeholders remain
        assert "PROXY_HOST" not in background_content, "Host placeholder not replaced"
        assert "PROXY_USERNAME" not in background_content, "Username placeholder not replaced"

        logger.info("✓ Extension files verified")

        # Cleanup
        builder.cleanup()
        assert not ext_path.exists(), "Extension directory not cleaned up"
        logger.info("✓ Cleanup verified")

        logger.info("✓ TEST 1 PASSED\n")
        return True

    except Exception as e:
        logger.error("✗ TEST 1 FAILED: %s", e)
        builder.cleanup()
        return False


def test_extension_builder_from_url():
    """Test ProxyExtensionBuilder.from_url() parsing."""
    logger.info("=" * 60)
    logger.info("TEST 2: ProxyExtensionBuilder.from_url()")
    logger.info("=" * 60)

    proxy_url = "http://user123:pass456@proxy.example.com:8080"

    try:
        builder = ProxyExtensionBuilder.from_url(proxy_url)

        assert builder.config.host == "proxy.example.com", "Host not parsed correctly"
        assert builder.config.port == 8080, "Port not parsed correctly"
        assert builder.config.username == "user123", "Username not parsed correctly"
        assert builder.config.password == "pass456", "Password not parsed correctly"

        logger.info("✓ URL parsing verified")

        # Test extension creation
        ext_path = builder.create_extension()
        assert ext_path.exists(), "Extension not created"

        background_content = (ext_path / "background.js").read_text()
        assert '"proxy.example.com"' in background_content
        assert "8080" in background_content

        builder.cleanup()
        logger.info("✓ Extension creation verified")

        logger.info("✓ TEST 2 PASSED\n")
        return True

    except Exception as e:
        logger.error("✗ TEST 2 FAILED: %s", e)
        return False


async def test_browser_pool_integration():
    """Test BrowserPool integrates proxy extension correctly."""
    logger.info("=" * 60)
    logger.info("TEST 3: BrowserPool Integration")
    logger.info("=" * 60)

    # Load environment variables
    load_dotenv()

    proxy_server = os.getenv("PROXY_SERVER")
    proxy_username = os.getenv("PROXY_USERNAME")
    proxy_password = os.getenv("PROXY_PASSWORD")

    if not all([proxy_server, proxy_username, proxy_password]):
        logger.warning("✗ TEST 3 SKIPPED: Proxy credentials not found in .env")
        return False

    proxy_url = f"http://{proxy_username}:{proxy_password}@{proxy_server}"

    try:
        # Create browser pool with authenticated proxy
        pool = BrowserPool(proxy_url=proxy_url, headless=True)

        # Verify proxy extension will be created
        assert pool._proxy_has_auth, "Proxy auth not detected"
        logger.info("✓ Proxy authentication detected")

        # Get browser (this should create extension)
        browser = await pool.get_browser()
        logger.info("✓ Browser created")

        # Verify extension was created
        assert pool._proxy_extension is not None, "Proxy extension not created"
        assert pool._proxy_extension.extension_dir is not None, "Extension dir not set"
        assert pool._proxy_extension.extension_dir.exists(), "Extension dir doesn't exist"
        logger.info("✓ Proxy extension created at: %s", pool._proxy_extension.extension_dir)

        # Close browser and cleanup
        await pool.close()

        # Verify cleanup
        assert pool._browser is None, "Browser not cleared"
        assert pool._proxy_extension is None, "Extension builder not cleared"
        logger.info("✓ Cleanup completed")

        logger.info("✓ TEST 3 PASSED\n")
        return True

    except Exception as e:
        logger.error("✗ TEST 3 FAILED: %s", e)
        if 'pool' in locals():
            await pool.close()
        return False


async def test_browser_pool_no_auth():
    """Test BrowserPool with non-authenticated proxy."""
    logger.info("=" * 60)
    logger.info("TEST 4: BrowserPool without Authentication")
    logger.info("=" * 60)

    proxy_url = "http://proxy.example.com:8080"

    try:
        pool = BrowserPool(proxy_url=proxy_url, headless=True)

        # Verify no auth detected
        assert not pool._proxy_has_auth, "Proxy auth incorrectly detected"
        logger.info("✓ No authentication detected (as expected)")

        # Get browser (should NOT create extension)
        browser = await pool.get_browser()
        logger.info("✓ Browser created")

        # Verify no extension created
        assert pool._proxy_extension is None, "Extension incorrectly created"
        logger.info("✓ No proxy extension created (as expected)")

        await pool.close()
        logger.info("✓ Cleanup completed")

        logger.info("✓ TEST 4 PASSED\n")
        return True

    except Exception as e:
        logger.error("✗ TEST 4 FAILED: %s", e)
        if 'pool' in locals():
            await pool.close()
        return False


async def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("PROXY EXTENSION TEST SUITE")
    logger.info("=" * 60 + "\n")

    results = []

    # Test 1: Extension builder
    results.append(test_extension_builder())

    # Test 2: URL parsing
    results.append(test_extension_builder_from_url())

    # Test 3: BrowserPool integration (requires .env)
    results.append(await test_browser_pool_integration())

    # Test 4: BrowserPool without auth
    results.append(await test_browser_pool_no_auth())

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info("Passed: %d/%d", sum(results), len(results))
    logger.info("Failed: %d/%d", len(results) - sum(results), len(results))

    if all(results):
        logger.info("✓ ALL TESTS PASSED")
    else:
        logger.error("✗ SOME TESTS FAILED")

    return all(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
