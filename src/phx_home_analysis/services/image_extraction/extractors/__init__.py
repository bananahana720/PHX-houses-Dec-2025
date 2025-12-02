"""Image extractor implementations for various property listing sources.

Each extractor handles a specific image source with its authentication,
rate limiting, and URL discovery logic.

The Zillow and Redfin extractors can use either:
- nodriver + curl_cffi (default): Stealth browser automation to bypass PerimeterX
- Playwright (fallback): Traditional browser automation

Set USE_PLAYWRIGHT_EXTRACTORS=1 environment variable to use Playwright fallback.
"""

import os

from .base import (
    ExtractionError,
    ImageDownloadError,
    ImageExtractor,
    RateLimitError,
    SourceUnavailableError,
)
from .maricopa_assessor import MaricopaAssessorExtractor
from .phoenix_mls import PhoenixMLSExtractor
from .stealth_base import StealthBrowserExtractor

# Conditional import: nodriver (default) or Playwright (fallback)
USE_PLAYWRIGHT = os.getenv("USE_PLAYWRIGHT_EXTRACTORS", "0") == "1"

if USE_PLAYWRIGHT:
    # Fallback: Use Playwright-based extractors
    from .redfin_playwright import RedfinExtractor
    from .zillow_playwright import ZillowExtractor
else:
    # Default: Use nodriver + curl_cffi stealth extractors
    from .redfin import RedfinExtractor
    from .zillow import ZillowExtractor

# Also export Playwright versions directly for explicit usage
from .redfin_playwright import RedfinExtractor as RedfinPlaywrightExtractor
from .zillow_playwright import ZillowExtractor as ZillowPlaywrightExtractor

__all__ = [
    # Base classes
    "ImageExtractor",
    "StealthBrowserExtractor",
    # Exception classes
    "ExtractionError",
    "SourceUnavailableError",
    "RateLimitError",
    "ImageDownloadError",
    # HTTP-based extractors
    "MaricopaAssessorExtractor",
    "PhoenixMLSExtractor",
    # Browser-based extractors (nodriver or Playwright based on env)
    "ZillowExtractor",
    "RedfinExtractor",
    # Explicit Playwright fallback extractors
    "ZillowPlaywrightExtractor",
    "RedfinPlaywrightExtractor",
]
