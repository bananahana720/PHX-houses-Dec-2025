"""Infrastructure services for HTTP clients and networking."""

from .browser_pool import BrowserPool
from .display_utils import (
    DisplayInfo,
    check_virtual_display_driver,
    find_virtual_display,
    get_display_summary,
    get_displays,
    get_recommended_position,
)
from .proxy_extension_builder import ProxyExtensionBuilder
from .proxy_manager import ProxyConfig, ProxyManager, ProxyProvider
from .stealth_http_client import StealthDownloadError, StealthHttpClient
from .url_validator import URLValidationError, URLValidator, ValidationResult

__all__ = [
    "BrowserPool",
    "DisplayInfo",
    "ProxyConfig",
    "ProxyExtensionBuilder",
    "ProxyManager",
    "ProxyProvider",
    "StealthDownloadError",
    "StealthHttpClient",
    "URLValidationError",
    "URLValidator",
    "ValidationResult",
    "check_virtual_display_driver",
    "find_virtual_display",
    "get_display_summary",
    "get_displays",
    "get_recommended_position",
]
