"""Protocols for dependency injection in enrichment service.

This module defines Protocol classes that enable loose coupling between
the enrichment service and its dependencies. Using protocols allows for:
- Easy mocking in unit tests
- Swapping implementations without code changes
- Clear interface contracts
"""

from typing import Protocol, runtime_checkable

from ..county_data.models import ParcelData


@runtime_checkable
class AssessorClientProtocol(Protocol):
    """Protocol for assessor client implementations.

    Defines the interface that any county assessor client must implement
    to be used with the enrichment merge service.

    This is a runtime checkable protocol, meaning isinstance() checks
    will work against it.

    Example:
        def process_with_client(client: AssessorClientProtocol) -> None:
            # Works with any implementation that has these methods
            if isinstance(client, AssessorClientProtocol):
                parcel = await client.extract_for_address("123 Main St")
    """

    async def extract_for_address(self, street: str) -> ParcelData | None:
        """Extract parcel data for a street address.

        Args:
            street: Street address to look up (e.g., "4732 W Davis Rd").

        Returns:
            ParcelData if found, None if address not found or error occurred.
        """
        ...

    async def __aenter__(self) -> "AssessorClientProtocol":
        """Async context manager entry.

        Returns:
            Self for use in async with statements.
        """
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit.

        Performs cleanup such as closing HTTP sessions.

        Args:
            exc_type: Exception type if an exception was raised.
            exc_val: Exception instance if an exception was raised.
            exc_tb: Traceback if an exception was raised.
        """
        ...


@runtime_checkable
class LineageTrackerProtocol(Protocol):
    """Protocol for lineage tracker implementations.

    Defines the interface for recording field-level data lineage
    during merge operations.
    """

    def record_field(
        self,
        property_hash: str,
        field_name: str,
        source: object,  # DataSource enum, but using object for Protocol
        confidence: float,
        original_value: object | None = None,
        notes: str | None = None,
    ) -> object:
        """Record lineage for a field update.

        Args:
            property_hash: MD5 hash of property address (first 8 chars).
            field_name: Name of the field being recorded.
            source: Data source that provided the value.
            confidence: Confidence score (0.0-1.0).
            original_value: The raw value before transformation.
            notes: Optional notes about the data origin.

        Returns:
            The created lineage record object.
        """
        ...

    def property_count(self) -> int:
        """Get number of properties with lineage records.

        Returns:
            Count of tracked properties.
        """
        ...

    def save(self) -> None:
        """Persist lineage data to storage."""
        ...
