"""Proxy management for residential IP rotation and stealth browsing.

Supports multiple proxy providers with configurable rotation strategies.
"""

import logging
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProxyProvider(Enum):
    """Supported proxy providers for residential IP rotation."""

    WEBSHARE = "webshare"
    BRIGHTDATA = "brightdata"
    OXYLABS = "oxylabs"
    DIRECT = "direct"  # No proxy - direct connection


@dataclass
class ProxyConfig:
    """Configuration for a proxy server.

    Attributes:
        server: Proxy server address in host:port format
        username: Proxy authentication username
        password: Proxy authentication password
        protocol: Proxy protocol (http, https, socks5)
    """

    server: str
    username: str
    password: str
    protocol: str = "http"

    def to_url(self) -> str:
        """Convert proxy config to URL format.

        Returns:
            Proxy URL in format: protocol://username:password@host:port
        """
        return f"{self.protocol}://{self.username}:{self.password}@{self.server}"


class ProxyManager:
    """Manages proxy configuration and rotation for HTTP requests.

    Supports multiple proxy providers with environment variable configuration.
    Tracks request count for monitoring and rotation strategies.

    Environment Variables:
        PROXY_SERVER: Proxy server address (host:port)
        PROXY_USERNAME: Proxy authentication username
        PROXY_PASSWORD: Proxy authentication password
        PROXY_PROTOCOL: Proxy protocol (default: http)

    Example:
        ```python
        # Auto-configure from environment
        manager = ProxyManager(provider=ProxyProvider.WEBSHARE)

        # Manual configuration
        config = ProxyConfig(
            server="proxy.example.com:8000",
            username="user",
            password="pass"
        )
        manager = ProxyManager(config=config)

        # Use with httpx
        import httpx
        if manager.is_configured:
            client = httpx.Client(proxies=manager.get_proxy_url())
        ```
    """

    def __init__(
        self,
        provider: ProxyProvider = ProxyProvider.WEBSHARE,
        config: ProxyConfig | None = None,
    ):
        """Initialize proxy manager.

        Args:
            provider: Proxy provider to use (ignored if config provided)
            config: Manual proxy configuration (overrides env vars)
        """
        self._provider = provider
        self._config = config or self._load_from_env()
        self._request_count = 0

        if self._provider == ProxyProvider.DIRECT:
            logger.info("Proxy manager initialized in DIRECT mode (no proxy)")
        elif self.is_configured:
            server = self._config.server if self._config else "unknown"
            logger.info(
                f"Proxy manager initialized with {self._provider.value} "
                f"(server: {server})"
            )
        else:
            logger.warning(
                f"Proxy manager initialized but no configuration found "
                f"(provider: {self._provider.value}). Set PROXY_* env vars or pass config."
            )

    def _load_from_env(self) -> ProxyConfig | None:
        """Load proxy configuration from environment variables.

        Returns:
            ProxyConfig if all required env vars are set, None otherwise
        """
        server = os.getenv("PROXY_SERVER")
        username = os.getenv("PROXY_USERNAME")
        password = os.getenv("PROXY_PASSWORD")
        protocol = os.getenv("PROXY_PROTOCOL", "http")

        if not all([server, username, password]):
            return None

        # At this point, we know all required values are non-None due to the check above
        assert server is not None and username is not None and password is not None
        return ProxyConfig(
            server=server,
            username=username,
            password=password,
            protocol=protocol,
        )

    def get_proxy(self) -> ProxyConfig | None:
        """Get current proxy configuration.

        Returns:
            ProxyConfig if configured, None for DIRECT mode or unconfigured
        """
        if self._provider == ProxyProvider.DIRECT:
            return None
        return self._config

    def get_proxy_url(self) -> str | None:
        """Get proxy URL for HTTP client configuration.

        Returns:
            Proxy URL in format: protocol://username:password@host:port
            None if DIRECT mode or unconfigured
        """
        config = self.get_proxy()
        if config is None:
            return None
        return config.to_url()

    @property
    def is_configured(self) -> bool:
        """Check if proxy is configured and ready to use.

        Returns:
            True if proxy config is available (or DIRECT mode), False otherwise
        """
        if self._provider == ProxyProvider.DIRECT:
            return True
        return self._config is not None

    @property
    def request_count(self) -> int:
        """Get total number of requests tracked by this manager.

        Returns:
            Total request count since initialization
        """
        return self._request_count

    def increment_request_count(self) -> None:
        """Increment the request counter.

        Used for monitoring and implementing rotation strategies.
        """
        self._request_count += 1
        logger.debug(f"Proxy request count: {self._request_count}")

    @property
    def provider(self) -> ProxyProvider:
        """Get the current proxy provider.

        Returns:
            ProxyProvider enum value
        """
        return self._provider

    def get_httpx_proxies(self) -> dict | None:
        """Get proxy configuration for httpx.AsyncClient.

        Returns:
            Dict suitable for httpx.AsyncClient(proxies=...) parameter
            None if DIRECT mode or unconfigured
        """
        proxy_url = self.get_proxy_url()
        if proxy_url is None:
            return None

        # httpx expects dict mapping protocols to proxy URLs
        return {
            "http://": proxy_url,
            "https://": proxy_url,
        }

    def __repr__(self) -> str:
        """String representation for debugging."""
        if self._provider == ProxyProvider.DIRECT:
            return "ProxyManager(provider=DIRECT, configured=True)"

        config_status = "configured" if self.is_configured else "unconfigured"
        server = self._config.server if self._config else "None"
        return (
            f"ProxyManager(provider={self._provider.value}, "
            f"server={server}, {config_status}, requests={self._request_count})"
        )
