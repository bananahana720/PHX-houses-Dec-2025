"""Infrastructure services for HTTP clients and networking."""

from .browser_pool import BrowserPool
from .proxy_extension_builder import ProxyExtensionBuilder
from .proxy_manager import ProxyConfig, ProxyManager, ProxyProvider
from .stealth_http_client import StealthDownloadError, StealthHttpClient

__all__ = [
    "BrowserPool",
    "ProxyConfig",
    "ProxyExtensionBuilder",
    "ProxyManager",
    "ProxyProvider",
    "StealthDownloadError",
    "StealthHttpClient",
]
