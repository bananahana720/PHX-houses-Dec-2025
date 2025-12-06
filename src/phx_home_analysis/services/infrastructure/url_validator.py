"""URL Validator for SSRF Protection.

This module provides URL validation to prevent Server-Side Request Forgery (SSRF)
attacks when downloading images from untrusted sources like real estate listing
websites.

SSRF Risk: Attackers could manipulate listing data to include URLs pointing to
internal services, cloud metadata endpoints, or private networks, allowing them
to access sensitive data or internal APIs.
"""

import ipaddress
import logging
import socket
from dataclasses import dataclass
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class URLValidationError(Exception):
    """URL failed SSRF validation checks."""

    def __init__(self, url: str, reason: str):
        self.url = url
        self.reason = reason
        super().__init__(f"URL validation failed for {url}: {reason}")


@dataclass(frozen=True)
class ValidationResult:
    """Result of URL validation check."""

    is_valid: bool
    error_message: str = ""

    def __bool__(self) -> bool:
        """Allow using result directly in conditionals."""
        return self.is_valid


class URLValidator:
    """Validates URLs before fetching to prevent SSRF attacks.

    Security Model:
    - Fail-closed: Unknown hosts are rejected by default
    - Allowlist-based: Only approved CDN domains are permitted
    - IP blocking: Private, loopback, and link-local IPs are blocked
    - Scheme validation: Only HTTP/HTTPS allowed

    Example:
        ```python
        validator = URLValidator()
        result = validator.validate_url("https://photos.zillowstatic.com/img.jpg")
        if not result.is_valid:
            logger.warning(f"Rejected URL: {result.error_message}")
        ```
    """

    # Trusted CDN hosts for real estate images
    ALLOWED_CDN_HOSTS: frozenset[str] = frozenset({
        # Zillow
        "photos.zillowstatic.com",
        "zillowstatic.com",
        "photos.zillow.com",
        # Redfin
        "ssl.cdn-redfin.com",
        "cdn-redfin.com",
        "redfin.com",
        # Realtor.com
        "ap.rdcpix.com",
        "rdcpix.com",
        "staticrdc.com",
        # Homes.com
        "images.homes.com",
        "homes.com",
        # Maricopa County Assessor
        "mcassessor.maricopa.gov",
        "gis.maricopa.gov",
        # Phoenix MLS
        "phoenixmlssearch.com",
        "cdn.photos.sparkplatform.com",  # SparkPlatform CDN for MLS property images
        # Cloudfront (CDN for multiple services)
        "d1w0jwjwlq0zii.cloudfront.net",  # Common real estate CDN
        # Additional Zillow CDN subdomains
        "maps.googleapis.com",  # For map tiles only
        "streetviewpixels-pa.googleapis.com",  # Street view images
    })

    # IP ranges that should never be accessed (CIDR notation)
    BLOCKED_IP_RANGES: tuple[str, ...] = (
        "127.0.0.0/8",       # Loopback (localhost)
        "10.0.0.0/8",        # Private (Class A)
        "172.16.0.0/12",     # Private (Class B)
        "192.168.0.0/16",    # Private (Class C)
        "169.254.0.0/16",    # Link-local (APIPA)
        "0.0.0.0/8",         # Current network
        "100.64.0.0/10",     # Carrier-grade NAT
        "192.0.0.0/24",      # IETF Protocol Assignments
        "192.0.2.0/24",      # TEST-NET-1 Documentation
        "198.51.100.0/24",   # TEST-NET-2 Documentation
        "203.0.113.0/24",    # TEST-NET-3 Documentation
        "224.0.0.0/4",       # Multicast
        "240.0.0.0/4",       # Reserved for future use
        "255.255.255.255/32",  # Broadcast
        # IPv6 blocked ranges
        "::1/128",           # IPv6 loopback
        "fc00::/7",          # IPv6 unique local addresses
        "fe80::/10",         # IPv6 link-local
        "::ffff:0:0/96",     # IPv4-mapped IPv6
    )

    # Allowed URL schemes
    ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})

    def __init__(
        self,
        additional_allowed_hosts: set[str] | None = None,
        strict_mode: bool = True,
        resolve_dns: bool = True,
    ):
        """Initialize URL validator.

        Args:
            additional_allowed_hosts: Extra hosts to allow beyond defaults
            strict_mode: If True, only allowlisted hosts are permitted.
                        If False, any non-blocked host is allowed (less secure).
            resolve_dns: If True, resolve hostnames to IPs and check against
                        blocked ranges. Prevents DNS rebinding attacks.
        """
        self.allowed_hosts = set(self.ALLOWED_CDN_HOSTS)
        if additional_allowed_hosts:
            self.allowed_hosts.update(additional_allowed_hosts)

        self.strict_mode = strict_mode
        self.resolve_dns = resolve_dns

        # Pre-compile blocked IP networks for efficient lookup
        self._blocked_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        for cidr in self.BLOCKED_IP_RANGES:
            try:
                self._blocked_networks.append(ipaddress.ip_network(cidr, strict=False))
            except ValueError as e:
                logger.warning(f"Invalid CIDR in blocked ranges: {cidr} - {e}")

        logger.debug(
            "URLValidator initialized: %d allowed hosts, %d blocked ranges, "
            "strict_mode=%s, resolve_dns=%s",
            len(self.allowed_hosts),
            len(self._blocked_networks),
            strict_mode,
            resolve_dns,
        )

    def validate_url(self, url: str) -> ValidationResult:
        """Validate URL is safe to fetch.

        Performs the following checks:
        1. URL is well-formed with scheme and host
        2. Scheme is HTTP or HTTPS
        3. Host is in allowlist (if strict mode)
        4. Host does not resolve to blocked IP range (if DNS resolution enabled)

        Args:
            url: URL to validate

        Returns:
            ValidationResult with is_valid flag and error message if invalid
        """
        if not url:
            return ValidationResult(False, "Empty URL")

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            logger.warning("URL parsing failed for %s: %s", url[:100], e)
            return ValidationResult(False, f"URL parsing failed: {e}")

        # Check scheme
        scheme = parsed.scheme.lower()
        if scheme not in self.ALLOWED_SCHEMES:
            logger.warning(
                "Blocked URL with disallowed scheme: %s (scheme: %s)",
                url[:100],
                scheme,
            )
            return ValidationResult(
                False,
                f"Disallowed scheme: {scheme}. Only {', '.join(self.ALLOWED_SCHEMES)} allowed.",
            )

        # Check host exists
        host = parsed.hostname
        if not host:
            logger.warning("URL missing hostname: %s", url[:100])
            return ValidationResult(False, "URL missing hostname")

        host_lower = host.lower()

        # Check if host is an IP address directly
        ip_check_result = self._check_ip_address(host_lower)
        if ip_check_result is not None:
            if not ip_check_result.is_valid:
                logger.warning(
                    "Blocked URL with forbidden IP: %s (reason: %s)",
                    url[:100],
                    ip_check_result.error_message,
                )
                return ip_check_result

        # Check allowlist (strict mode) or blocklist (permissive mode)
        if self.strict_mode:
            if not self._is_host_allowed(host_lower):
                logger.warning(
                    "Blocked URL: host not in allowlist: %s (host: %s)",
                    url[:100],
                    host_lower,
                )
                return ValidationResult(
                    False,
                    f"Host not in allowlist: {host_lower}",
                )
        else:
            # Permissive mode: just check blocklist
            # This is less secure but may be needed for some use cases
            pass

        # DNS resolution check (prevents DNS rebinding attacks)
        if self.resolve_dns:
            dns_result = self._check_dns_resolution(host_lower)
            if not dns_result.is_valid:
                logger.warning(
                    "Blocked URL after DNS resolution: %s (reason: %s)",
                    url[:100],
                    dns_result.error_message,
                )
                return dns_result

        # URL passed all checks
        logger.debug("URL validated successfully: %s", url[:100])
        return ValidationResult(True)

    def _is_host_allowed(self, host: str) -> bool:
        """Check if host is in the allowlist.

        Checks both exact matches and parent domain matches.

        Args:
            host: Hostname to check (already lowercase)

        Returns:
            True if host is allowed
        """
        # Exact match
        if host in self.allowed_hosts:
            return True

        # Check parent domains (e.g., "img.zillowstatic.com" matches "zillowstatic.com")
        parts = host.split(".")
        for i in range(len(parts) - 1):
            parent = ".".join(parts[i + 1:])
            if parent in self.allowed_hosts:
                return True

        return False

    def _check_ip_address(self, host: str) -> ValidationResult | None:
        """Check if host is a raw IP address and validate it.

        Args:
            host: Hostname or IP address to check

        Returns:
            ValidationResult if host is an IP (valid or invalid),
            None if host is not an IP address
        """
        try:
            ip = ipaddress.ip_address(host)

            # Check against blocked ranges
            for network in self._blocked_networks:
                if ip in network:
                    return ValidationResult(
                        False,
                        f"IP address {host} is in blocked range {network}",
                    )

            # IP is not in any blocked range
            # In strict mode, raw IPs are not allowed unless explicitly listed
            if self.strict_mode:
                return ValidationResult(
                    False,
                    f"Raw IP addresses not allowed in strict mode: {host}",
                )

            return ValidationResult(True)

        except ValueError:
            # Not an IP address, return None to continue with hostname checks
            return None

    def _check_dns_resolution(self, host: str) -> ValidationResult:
        """Resolve hostname and check if resolved IPs are in blocked ranges.

        This prevents DNS rebinding attacks where an attacker controls a domain
        that initially resolves to a safe IP but later resolves to internal IPs.

        Args:
            host: Hostname to resolve

        Returns:
            ValidationResult indicating if resolved IPs are safe
        """
        try:
            # Get all IP addresses for the host
            addr_info = socket.getaddrinfo(
                host,
                None,
                socket.AF_UNSPEC,  # IPv4 and IPv6
                socket.SOCK_STREAM,
            )

            for _family, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]

                try:
                    ip = ipaddress.ip_address(ip_str)

                    # Check against blocked ranges
                    for network in self._blocked_networks:
                        if ip in network:
                            return ValidationResult(
                                False,
                                f"Host {host} resolves to blocked IP: {ip_str} (range: {network})",
                            )

                except ValueError:
                    # Skip invalid IP addresses
                    continue

            return ValidationResult(True)

        except socket.gaierror as e:
            # DNS resolution failed - fail closed
            return ValidationResult(
                False,
                f"DNS resolution failed for {host}: {e}",
            )

        except Exception as e:
            # Unexpected error - fail closed
            logger.error("Unexpected error during DNS resolution for %s: %s", host, e)
            return ValidationResult(
                False,
                f"DNS resolution error: {e}",
            )

    def is_safe_url(self, url: str) -> bool:
        """Convenience method to check if URL is safe.

        Args:
            url: URL to validate

        Returns:
            True if URL passes all validation checks
        """
        return self.validate_url(url).is_valid

    def add_allowed_host(self, host: str) -> None:
        """Add a host to the allowlist at runtime.

        Args:
            host: Hostname to allow
        """
        self.allowed_hosts.add(host.lower())
        logger.info("Added host to allowlist: %s", host)

    def remove_allowed_host(self, host: str) -> None:
        """Remove a host from the allowlist at runtime.

        Args:
            host: Hostname to remove
        """
        self.allowed_hosts.discard(host.lower())
        logger.info("Removed host from allowlist: %s", host)
