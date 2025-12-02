"""Abstract base classes for repositories."""

from abc import ABC, abstractmethod
from typing import Optional

from ..domain.entities import Property, EnrichmentData


class DataLoadError(Exception):
    """Raised when data cannot be loaded from a source."""
    pass


class DataSaveError(Exception):
    """Raised when data cannot be saved to a destination."""
    pass


class PropertyRepository(ABC):
    """Abstract base class for property data repositories."""

    @abstractmethod
    def load_all(self) -> list[Property]:
        """Load all properties from the data source.

        Returns:
            List of Property objects.

        Raises:
            DataLoadError: If data cannot be loaded.
        """
        pass

    @abstractmethod
    def load_by_address(self, full_address: str) -> Optional[Property]:
        """Load a single property by its full address.

        Args:
            full_address: The complete formatted address.

        Returns:
            Property object if found, None otherwise.

        Raises:
            DataLoadError: If data cannot be loaded.
        """
        pass

    @abstractmethod
    def save_all(self, properties: list[Property]) -> None:
        """Save all properties to the data destination.

        Args:
            properties: List of Property objects to save.

        Raises:
            DataSaveError: If data cannot be saved.
        """
        pass

    @abstractmethod
    def save_one(self, property: Property) -> None:
        """Save a single property to the data destination.

        Args:
            property: Property object to save.

        Raises:
            DataSaveError: If data cannot be saved.
        """
        pass


class EnrichmentRepository(ABC):
    """Abstract base class for enrichment data repositories."""

    @abstractmethod
    def load_all(self) -> dict[str, EnrichmentData]:
        """Load all enrichment data from the data source.

        Returns:
            Dictionary mapping full_address to EnrichmentData objects.

        Raises:
            DataLoadError: If data cannot be loaded.
        """
        pass

    @abstractmethod
    def load_for_property(self, full_address: str) -> Optional[EnrichmentData]:
        """Load enrichment data for a specific property.

        Args:
            full_address: The complete formatted address.

        Returns:
            EnrichmentData object if found, None otherwise.

        Raises:
            DataLoadError: If data cannot be loaded.
        """
        pass

    @abstractmethod
    def save_all(self, enrichment_data: dict[str, EnrichmentData]) -> None:
        """Save all enrichment data to the data destination.

        Args:
            enrichment_data: Dictionary mapping full_address to EnrichmentData.

        Raises:
            DataSaveError: If data cannot be saved.
        """
        pass
