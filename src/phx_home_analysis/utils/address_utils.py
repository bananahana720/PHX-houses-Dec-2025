"""Address normalization utilities for consistent property lookups.

This module provides functions to normalize addresses for matching and comparison,
ensuring that address variations (case, punctuation, spacing) don't prevent matches.
"""

import re


def normalize_address(address: str) -> str:
    """Normalize address for consistent lookups.

    Applies normalization rules from epic spec:
    - Convert to lowercase
    - Remove commas
    - Remove periods
    - Strip leading/trailing whitespace
    - Collapse multiple spaces to single space

    Args:
        address: Raw address string (e.g., "123 Main St., Phoenix, AZ 85001")

    Returns:
        Normalized address (e.g., "123 main st phoenix az 85001")

    Example:
        >>> normalize_address("123 Main St., Phoenix, AZ 85001")
        '123 main st phoenix az 85001'
        >>> normalize_address("  456 ELM AVE,  Mesa,  AZ  ")
        '456 elm ave mesa az'
        >>> normalize_address("")
        ''
    """
    if not address:
        return ""

    # Core normalization per epic spec
    normalized = address.lower()
    normalized = normalized.replace(",", "")
    normalized = normalized.replace(".", "")
    normalized = normalized.strip()

    # Additional cleanup: collapse multiple spaces
    normalized = re.sub(r"\s+", " ", normalized)

    return normalized


def addresses_match(address1: str, address2: str) -> bool:
    """Check if two addresses match after normalization.

    Args:
        address1: First address to compare
        address2: Second address to compare

    Returns:
        True if normalized addresses are equal

    Example:
        >>> addresses_match("123 Main St.", "123 main st")
        True
        >>> addresses_match("456 Elm Ave", "789 Oak Blvd")
        False
    """
    return normalize_address(address1) == normalize_address(address2)
