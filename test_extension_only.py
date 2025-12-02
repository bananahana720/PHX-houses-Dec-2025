"""Test proxy extension builder without browser dependencies.

Verifies ProxyExtensionBuilder creates valid extension directory and files.
"""

import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import directly to avoid browser_pool dependencies
from phx_home_analysis.services.infrastructure.proxy_extension_builder import (
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
    logger.info("TEST: ProxyExtensionBuilder")
    logger.info("=" * 60)

    # Test with explicit credentials
    builder = ProxyExtensionBuilder(
        host="p.webshare.io",
        port=80,
        username="svcvoqpm-US-rotate",
        password="g2j2p2cv602u",
    )

    try:
        # Create extension
        ext_path = builder.create_extension()
        logger.info("Extension created at: %s", ext_path)

        # Verify files exist
        assert ext_path.exists(), "Extension directory not created"
        assert (ext_path / "manifest.json").exists(), "manifest.json missing"
        assert (ext_path / "background.js").exists(), "background.js missing"

        # Read and display manifest
        logger.info("\n--- manifest.json ---")
        manifest_content = (ext_path / "manifest.json").read_text()
        logger.info(manifest_content)

        # Read and display background.js
        logger.info("\n--- background.js ---")
        background_content = (ext_path / "background.js").read_text()
        logger.info(background_content)

        # Verify background.js has credentials
        assert '"p.webshare.io"' in background_content, "Host not substituted"
        assert "80" in background_content, "Port not substituted"
        assert '"svcvoqpm-US-rotate"' in background_content, "Username not substituted"
        assert '"g2j2p2cv602u"' in background_content, "Password not substituted"

        # Verify no placeholders remain
        assert "PROXY_HOST" not in background_content, "Host placeholder not replaced"
        assert "PROXY_PORT" not in background_content or "80" in background_content, "Port placeholder issue"
        assert "PROXY_USERNAME" not in background_content, "Username placeholder not replaced"
        assert "PROXY_PASSWORD" not in background_content, "Password placeholder not replaced"

        logger.info("\n✓ Extension files verified")

        # Cleanup
        builder.cleanup()
        assert not ext_path.exists(), "Extension directory not cleaned up"
        logger.info("✓ Cleanup verified")

        logger.info("\n✓ TEST PASSED")
        return True

    except Exception as e:
        logger.error("\n✗ TEST FAILED: %s", e, exc_info=True)
        builder.cleanup()
        return False


def test_from_url():
    """Test ProxyExtensionBuilder.from_url() parsing."""
    logger.info("\n" + "=" * 60)
    logger.info("TEST: from_url() parsing")
    logger.info("=" * 60)

    proxy_url = "http://svcvoqpm-US-rotate:g2j2p2cv602u@p.webshare.io:80"

    try:
        builder = ProxyExtensionBuilder.from_url(proxy_url)

        logger.info("Parsed config:")
        logger.info("  Host: %s", builder.config.host)
        logger.info("  Port: %d", builder.config.port)
        logger.info("  Username: %s", builder.config.username)
        logger.info("  Password: %s", "*" * len(builder.config.password))

        assert builder.config.host == "p.webshare.io", "Host not parsed correctly"
        assert builder.config.port == 80, "Port not parsed correctly"
        assert builder.config.username == "svcvoqpm-US-rotate", "Username not parsed correctly"
        assert builder.config.password == "g2j2p2cv602u", "Password not parsed correctly"

        logger.info("✓ URL parsing verified")

        # Test extension creation
        ext_path = builder.create_extension()
        assert ext_path.exists(), "Extension not created"
        logger.info("✓ Extension created at: %s", ext_path)

        background_content = (ext_path / "background.js").read_text()
        assert '"p.webshare.io"' in background_content, "Host not in background.js"
        assert "80" in background_content, "Port not in background.js"

        builder.cleanup()
        logger.info("✓ Cleanup completed")

        logger.info("\n✓ TEST PASSED")
        return True

    except Exception as e:
        logger.error("\n✗ TEST FAILED: %s", e, exc_info=True)
        return False


def main():
    """Run all tests."""
    logger.info("\n" + "=" * 60)
    logger.info("PROXY EXTENSION BUILDER TEST SUITE")
    logger.info("=" * 60 + "\n")

    results = []

    # Test 1: Basic builder
    results.append(test_extension_builder())

    # Test 2: URL parsing
    results.append(test_from_url())

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info("Passed: %d/%d", sum(results), len(results))
    logger.info("Failed: %d/%d", len(results) - sum(results), len(results))

    if all(results):
        logger.info("\n✓ ALL TESTS PASSED")
    else:
        logger.error("\n✗ SOME TESTS FAILED")

    return all(results)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
