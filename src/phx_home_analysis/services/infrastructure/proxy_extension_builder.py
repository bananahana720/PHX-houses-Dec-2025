"""Chrome extension builder for proxy authentication.

Creates temporary Chrome extension that handles proxy authentication
automatically, enabling use of authenticated proxies with nodriver/Chrome.
"""

import logging
import shutil
import tempfile
from pathlib import Path
from typing import NamedTuple

logger = logging.getLogger(__name__)


class ProxyConfig(NamedTuple):
    """Proxy configuration components."""

    host: str
    port: int
    username: str
    password: str


class ProxyExtensionBuilder:
    """Builds temporary Chrome extension for proxy authentication.

    Chrome's --proxy-server flag doesn't support inline authentication
    (user:pass@host:port). This builder creates a temporary Chrome extension
    that configures the proxy and handles authentication requests automatically.

    The extension is created in a temporary directory and should be cleaned up
    after browser use.

    Attributes:
        config: Proxy configuration (host, port, username, password)
        extension_dir: Path to temporary extension directory (None until created)

    Example:
        >>> builder = ProxyExtensionBuilder("proxy.example.com", 8080, "user", "pass")
        >>> extension_path = builder.create_extension()
        >>> # Use extension_path with Chrome's --load-extension argument
        >>> builder.cleanup()
    """

    # Template directory containing manifest.json and background.js
    TEMPLATE_DIR = Path(__file__).parent / "proxy_extension"

    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        """Initialize proxy extension builder.

        Args:
            host: Proxy server hostname (e.g., "p.webshare.io")
            port: Proxy server port (e.g., 80)
            username: Proxy authentication username
            password: Proxy authentication password
        """
        self.config = ProxyConfig(
            host=host,
            port=port,
            username=username,
            password=password,
        )
        self.extension_dir: Path | None = None

        logger.info(
            "ProxyExtensionBuilder initialized: %s:%d (user: ***)",
            host,
            port,
        )

    @classmethod
    def from_url(cls, proxy_url: str) -> "ProxyExtensionBuilder":
        """Create builder from proxy URL.

        Args:
            proxy_url: Proxy URL in format "http://user:pass@host:port"

        Returns:
            ProxyExtensionBuilder instance

        Raises:
            ValueError: If URL format is invalid or missing credentials

        Example:
            >>> builder = ProxyExtensionBuilder.from_url(
            ...     "http://user:pass@proxy.example.com:8080"
            ... )
        """
        # Parse proxy URL
        if "://" not in proxy_url:
            raise ValueError(f"Invalid proxy URL format (missing scheme): {proxy_url}")

        scheme, rest = proxy_url.split("://", 1)

        if "@" not in rest:
            raise ValueError(
                f"Proxy URL must include credentials (user:pass@host:port): {proxy_url}"
            )

        credentials, host_port = rest.split("@", 1)

        if ":" not in credentials:
            raise ValueError(
                f"Invalid credentials format (expected user:pass): {credentials}"
            )

        username, password = credentials.split(":", 1)

        if ":" not in host_port:
            raise ValueError(f"Invalid host:port format: {host_port}")

        host, port_str = host_port.split(":", 1)

        try:
            port = int(port_str)
        except ValueError as e:
            raise ValueError(f"Invalid port number: {port_str}") from e

        logger.info("Parsed proxy URL: %s (scheme: %s)", host_port, scheme)

        return cls(host=host, port=port, username=username, password=password)

    def create_extension(self) -> Path:
        """Create temporary extension directory with configured credentials.

        Creates a temporary directory and populates it with:
        - manifest.json (copied from template)
        - background.js (template with credentials substituted)

        Returns:
            Path to extension directory for use with --load-extension

        Raises:
            FileNotFoundError: If template files don't exist
            RuntimeError: If extension already created (call cleanup() first)

        Example:
            >>> builder = ProxyExtensionBuilder("proxy.example.com", 8080, "user", "pass")
            >>> ext_path = builder.create_extension()
            >>> print(ext_path)
            /tmp/proxy_ext_abc123
        """
        if self.extension_dir is not None:
            raise RuntimeError(
                "Extension already created. Call cleanup() before creating again."
            )

        # Verify template directory exists
        if not self.TEMPLATE_DIR.exists():
            raise FileNotFoundError(
                f"Template directory not found: {self.TEMPLATE_DIR}"
            )

        manifest_path = self.TEMPLATE_DIR / "manifest.json"
        background_template_path = self.TEMPLATE_DIR / "background.js"

        if not manifest_path.exists():
            raise FileNotFoundError(f"Template manifest not found: {manifest_path}")

        if not background_template_path.exists():
            raise FileNotFoundError(
                f"Template background.js not found: {background_template_path}"
            )

        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="proxy_ext_"))
        logger.info("Created temporary extension directory: %s", temp_dir)

        try:
            # Copy manifest.json as-is
            shutil.copy2(manifest_path, temp_dir / "manifest.json")
            logger.debug("Copied manifest.json to extension directory")

            # Read background.js template and substitute credentials
            background_template = background_template_path.read_text(encoding="utf-8")

            # Replace placeholders (including the quotes in the template)
            background_content = background_template.replace(
                '"PROXY_HOST"', f'"{self.config.host}"'
            )
            background_content = background_content.replace(
                "PROXY_PORT", str(self.config.port)
            )
            background_content = background_content.replace(
                '"PROXY_USERNAME"', f'"{self.config.username}"'
            )
            background_content = background_content.replace(
                '"PROXY_PASSWORD"', f'"{self.config.password}"'
            )

            # Write configured background.js
            background_path = temp_dir / "background.js"
            background_path.write_text(background_content, encoding="utf-8")
            logger.debug("Created background.js with proxy configuration")

            self.extension_dir = temp_dir

            logger.info(
                "Proxy extension created successfully at: %s (proxy: %s:%d)",
                temp_dir,
                self.config.host,
                self.config.port,
            )

            return temp_dir

        except Exception as e:
            # Cleanup on error
            logger.error("Error creating extension, cleaning up: %s", e)
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise

    def cleanup(self) -> None:
        """Remove temporary extension directory.

        Safe to call multiple times - will only cleanup if directory exists.
        After cleanup, create_extension() can be called again.
        """
        if self.extension_dir is None:
            logger.debug("No extension directory to cleanup")
            return

        if not self.extension_dir.exists():
            logger.warning("Extension directory already removed: %s", self.extension_dir)
            self.extension_dir = None
            return

        try:
            logger.info("Cleaning up extension directory: %s", self.extension_dir)
            shutil.rmtree(self.extension_dir, ignore_errors=True)
            logger.debug("Extension directory removed successfully")

        except Exception as e:
            logger.error("Error cleaning up extension directory: %s", e)

        finally:
            # Clear reference regardless of cleanup success
            self.extension_dir = None
