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
from .playwright_mcp import PlaywrightMcpClient, extract_images_from_url
from .proxy_extension_builder import ProxyExtensionBuilder
from .proxy_manager import ProxyConfig, ProxyManager, ProxyProvider
from .stealth_http_client import StealthDownloadError, StealthHttpClient
from .url_validator import URLValidationError, URLValidator, ValidationResult
from .user_agent_pool import (
    UserAgentRotator,
    get_random_user_agent,
    get_rotator,
)

__all__ = [
    "BrowserPool",
    "DisplayInfo",
    "PlaywrightMcpClient",
    "ProxyConfig",
    "ProxyExtensionBuilder",
    "ProxyManager",
    "ProxyProvider",
    "StealthDownloadError",
    "StealthHttpClient",
    "URLValidationError",
    "URLValidator",
    "UserAgentRotator",
    "ValidationResult",
    "check_virtual_display_driver",
    "extract_images_from_url",
    "find_virtual_display",
    "get_display_summary",
    "get_displays",
    "get_random_user_agent",
    "get_recommended_position",
    "get_rotator",
]
