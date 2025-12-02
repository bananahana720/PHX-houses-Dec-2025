"""Hash-based duplicate detection for properties.

This module provides functionality to detect duplicate properties based on
address normalization and hashing. Uses the same hash pattern documented
in CLAUDE.md: MD5 hash of lowercase normalized address, first 8 chars.
"""

import hashlib
from typing import Dict, List, Tuple

from .normalizer import normalize_address


def compute_property_hash(address: str) -> str:
    """Compute hash for property based on normalized address.

    Uses MD5 hash of lowercase normalized address, returning first 8 chars.
    Matches the pattern used in CLAUDE.md.

    Args:
        address: Raw address string

    Returns:
        8-character hex hash string

    Examples:
        >>> compute_property_hash("4732 W Davis Rd, Glendale, AZ 85306")
        'ef7cd95f'
        >>> compute_property_hash("4732 West Davis Road, Glendale, AZ 85306")
        'ef7cd95f'  # Same hash due to normalization
    """
    normalized = normalize_address(address)
    return hashlib.md5(normalized.encode()).hexdigest()[:8]


class DuplicateDetector:
    """Detect duplicate properties based on address hashing.

    This class provides stateful duplicate detection, tracking seen addresses
    and their hashes to identify duplicates as they are processed.

    Example:
        >>> detector = DuplicateDetector()
        >>> detector.check("123 W Main St")
        (False, None)
        >>> detector.check("123 West Main Street")  # Same address, different format
        (True, '123 W Main St')
    """

    def __init__(self) -> None:
        """Initialize the duplicate detector with empty state."""
        self._seen_hashes: Dict[str, str] = {}  # hash -> original address

    def check(self, address: str) -> Tuple[bool, str | None]:
        """Check if address is a duplicate.

        If the address has been seen before (based on normalized hash),
        returns True along with the original address that matched.

        Args:
            address: Address to check

        Returns:
            Tuple of (is_duplicate, original_address_if_duplicate)
        """
        prop_hash = compute_property_hash(address)
        if prop_hash in self._seen_hashes:
            return True, self._seen_hashes[prop_hash]
        self._seen_hashes[prop_hash] = address
        return False, None

    def find_duplicates(self, addresses: List[str]) -> Dict[str, List[str]]:
        """Find all duplicate groups in a list of addresses.

        Groups addresses by their normalized hash and returns only groups
        containing more than one address (i.e., duplicates).

        Args:
            addresses: List of addresses to check

        Returns:
            Dict mapping hash -> list of duplicate addresses

        Example:
            >>> detector = DuplicateDetector()
            >>> detector.find_duplicates([
            ...     "123 W Main St",
            ...     "456 Oak Ave",
            ...     "123 West Main Street",  # Duplicate of first
            ... ])
            {'abc12345': ['123 W Main St', '123 West Main Street']}
        """
        hash_groups: Dict[str, List[str]] = {}
        for addr in addresses:
            prop_hash = compute_property_hash(addr)
            if prop_hash not in hash_groups:
                hash_groups[prop_hash] = []
            hash_groups[prop_hash].append(addr)

        # Return only groups with duplicates
        return {h: addrs for h, addrs in hash_groups.items() if len(addrs) > 1}

    def reset(self) -> None:
        """Clear seen hashes to start fresh."""
        self._seen_hashes.clear()

    @property
    def seen_count(self) -> int:
        """Return the number of unique addresses seen."""
        return len(self._seen_hashes)

    def get_hash(self, address: str) -> str:
        """Get the hash for an address without adding it to seen set.

        Args:
            address: Address to hash

        Returns:
            8-character hex hash string
        """
        return compute_property_hash(address)
