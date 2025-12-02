"""Data preprocessing and normalization utilities.

This module provides functions for normalizing property data including
address standardization, type inference, and data cleaning.
"""

import re
from typing import Any


def normalize_address(address: str) -> str:
    """Normalize address for deduplication and matching.

    Performs the following transformations:
    - Converts to lowercase
    - Expands common abbreviations (St -> Street, W -> West, etc.)
    - Removes extra whitespace
    - Strips leading/trailing whitespace

    Args:
        address: Raw address string

    Returns:
        Normalized address string

    Examples:
        >>> normalize_address("123 W Main St")
        '123 west main street'
        >>> normalize_address("456 N Oak Ave, Phoenix, AZ 85001")
        '456 north oak avenue, phoenix, az 85001'
    """
    if not address:
        return ""

    address = address.lower().strip()

    # Direction abbreviations (must use word boundaries)
    direction_replacements = {
        r"\bn\b": "north",
        r"\bs\b": "south",
        r"\be\b": "east",
        r"\bw\b": "west",
        r"\bne\b": "northeast",
        r"\bnw\b": "northwest",
        r"\bse\b": "southeast",
        r"\bsw\b": "southwest",
    }

    # Street type abbreviations
    street_replacements = {
        r"\bst\b": "street",
        r"\brd\b": "road",
        r"\bdr\b": "drive",
        r"\bave\b": "avenue",
        r"\bblvd\b": "boulevard",
        r"\bln\b": "lane",
        r"\bct\b": "court",
        r"\bpl\b": "place",
        r"\bpkwy\b": "parkway",
        r"\bcir\b": "circle",
        r"\bter\b": "terrace",
        r"\btrl\b": "trail",
        r"\bway\b": "way",  # Usually not abbreviated, but include for consistency
        r"\bhwy\b": "highway",
    }

    # Apply direction replacements
    for pattern, replacement in direction_replacements.items():
        address = re.sub(pattern, replacement, address)

    # Apply street type replacements
    for pattern, replacement in street_replacements.items():
        address = re.sub(pattern, replacement, address)

    # Remove extra whitespace
    address = " ".join(address.split())

    return address


def infer_type(value: str) -> Any:
    """Infer Python type from string value.

    Attempts to convert string values to their appropriate Python types
    in the following order: int, float, bool, then keeps as string.

    Args:
        value: String value to parse

    Returns:
        Parsed value as int, float, bool, None, or original string

    Examples:
        >>> infer_type("42")
        42
        >>> infer_type("3.14")
        3.14
        >>> infer_type("true")
        True
        >>> infer_type("hello")
        'hello'
        >>> infer_type("")
        None
    """
    if not isinstance(value, str):
        return value

    value = value.strip()

    # Handle empty/null values
    if not value or value.lower() in ("null", "none", "n/a", "na", ""):
        return None

    # Try boolean
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    if value.lower() in ("false", "no", "0", "off"):
        return False

    # Try integer
    try:
        # Handle negative numbers and numbers with commas
        clean_value = value.replace(",", "")
        if clean_value.lstrip("-").isdigit():
            return int(clean_value)
    except ValueError:
        pass

    # Try float
    try:
        clean_value = value.replace(",", "")
        float_val = float(clean_value)
        # Return as int if it's a whole number
        if float_val.is_integer() and "." not in value:
            return int(float_val)
        return float_val
    except ValueError:
        pass

    # Keep as string
    return value


def normalize_sewer_type(value: str | None) -> str | None:
    """Normalize sewer type values to standard enum values.

    Args:
        value: Raw sewer type string

    Returns:
        Normalized sewer type ('city', 'septic', or 'unknown')
    """
    if not value:
        return None

    value = value.lower().strip()

    # City sewer variants
    city_variants = {
        "city",
        "municipal",
        "public",
        "sewer",
        "city sewer",
        "public sewer",
        "municipal sewer",
        "connected",
    }
    if value in city_variants or "city" in value or "municipal" in value:
        return "city"

    # Septic variants
    septic_variants = {
        "septic",
        "septic tank",
        "septic system",
        "private",
        "onsite",
        "on-site",
    }
    if value in septic_variants or "septic" in value:
        return "septic"

    return "unknown"


def normalize_orientation(value: str | None) -> str | None:
    """Normalize orientation values to standard enum values.

    Args:
        value: Raw orientation string

    Returns:
        Normalized orientation (north, south, east, west, or compound directions)
    """
    if not value:
        return None

    value = value.lower().strip()

    # Mapping of variants to canonical values
    mappings = {
        # Cardinal directions
        "n": "north",
        "north": "north",
        "s": "south",
        "south": "south",
        "e": "east",
        "east": "east",
        "w": "west",
        "west": "west",
        # Compound directions
        "ne": "northeast",
        "northeast": "northeast",
        "north-east": "northeast",
        "nw": "northwest",
        "northwest": "northwest",
        "north-west": "northwest",
        "se": "southeast",
        "southeast": "southeast",
        "south-east": "southeast",
        "sw": "southwest",
        "southwest": "southwest",
        "south-west": "southwest",
    }

    return mappings.get(value, "unknown")


def normalize_solar_status(value: str | None) -> str | None:
    """Normalize solar status values to standard enum values.

    Args:
        value: Raw solar status string

    Returns:
        Normalized solar status ('owned', 'leased', 'none', or 'unknown')
    """
    if not value:
        return None

    value = value.lower().strip()

    # Owned variants
    owned_variants = {"owned", "purchased", "bought", "own"}
    if value in owned_variants or "owned" in value:
        return "owned"

    # Leased variants
    leased_variants = {"leased", "lease", "rented", "ppa", "power purchase"}
    if value in leased_variants or "lease" in value or "ppa" in value:
        return "leased"

    # None variants
    none_variants = {"none", "no", "no solar", "n/a", "na", ""}
    if value in none_variants:
        return "none"

    return "unknown"


def clean_price(value: str | int | float) -> int | None:
    """Clean and normalize price values.

    Handles various price formats including:
    - $475,000
    - 475000
    - 475k
    - $475K

    Args:
        value: Raw price value

    Returns:
        Integer price in dollars, or None if invalid
    """
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value)

    if not isinstance(value, str):
        return None

    value = value.strip().upper()

    # Remove currency symbols and commas
    value = value.replace("$", "").replace(",", "").strip()

    # Handle K/M suffixes
    multiplier = 1
    if value.endswith("K"):
        multiplier = 1000
        value = value[:-1]
    elif value.endswith("M"):
        multiplier = 1000000
        value = value[:-1]

    try:
        return int(float(value) * multiplier)
    except (ValueError, TypeError):
        return None


def normalize_boolean(value: Any) -> bool | None:
    """Normalize various boolean representations.

    Args:
        value: Value to normalize to boolean

    Returns:
        Boolean value or None if cannot be determined
    """
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(value)

    if isinstance(value, str):
        value = value.lower().strip()
        if value in ("true", "yes", "1", "on", "y", "t"):
            return True
        if value in ("false", "no", "0", "off", "n", "f"):
            return False

    return None
