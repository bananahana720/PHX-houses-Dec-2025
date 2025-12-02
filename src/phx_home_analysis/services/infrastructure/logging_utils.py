"""Logging utilities for secure credential handling.

This module provides utility functions for sanitizing sensitive information
before logging to prevent credential exposure in log files.
"""

import urllib.parse


def sanitize_url_for_logging(url: str | None) -> str:
    """Remove credentials from URL before logging.

    Replaces username:password in URLs with ***:*** to prevent
    credential exposure in log files.

    Args:
        url: URL that may contain embedded credentials

    Returns:
        Sanitized URL safe for logging

    Example:
        >>> sanitize_url_for_logging("http://user:pass@proxy.com:8080")
        "http://***:***@proxy.com:8080"
        >>> sanitize_url_for_logging("http://proxy.com:8080")
        "http://proxy.com:8080"
        >>> sanitize_url_for_logging(None)
        "<none>"
    """
    if not url:
        return "<none>"

    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.username or parsed.password:
            # Reconstruct with masked credentials
            netloc = f"***:***@{parsed.hostname}"
            if parsed.port:
                netloc += f":{parsed.port}"
            sanitized = parsed._replace(netloc=netloc)
            return sanitized.geturl()
        return url
    except Exception:
        return "<invalid-url>"


def sanitize_proxy_config_for_logging(proxy_url: str | None) -> dict[str, str]:
    """Get safe proxy configuration details for logging.

    Returns a dictionary with sanitized proxy information suitable for
    structured logging without exposing credentials.

    Args:
        proxy_url: Proxy URL that may contain credentials

    Returns:
        Dictionary with keys:
        - status: "enabled" or "disabled"
        - url: Sanitized URL (only if enabled)
        - auth: "yes" or "no" (only if enabled)

    Example:
        >>> sanitize_proxy_config_for_logging("http://user:pass@proxy:8080")
        {"status": "enabled", "url": "http://***:***@proxy:8080", "auth": "yes"}
        >>> sanitize_proxy_config_for_logging(None)
        {"status": "disabled"}
    """
    if not proxy_url:
        return {"status": "disabled"}

    has_auth = bool("@" in proxy_url and "://" in proxy_url)
    return {
        "status": "enabled",
        "url": sanitize_url_for_logging(proxy_url),
        "auth": "yes" if has_auth else "no",
    }
