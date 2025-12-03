"""Base reporter interface for PHX Home Analysis.

Defines the abstract Reporter interface that all report generators must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from ..domain.entities import Property


class Reporter(ABC):
    """Abstract base class for report generators.

    All reporters must implement the generate method to produce output
    in their respective format (HTML, CSV, console, etc.).
    """

    @abstractmethod
    def generate(self, properties: list[Property], output_path: Path) -> None:
        """Generate report from property data.

        Args:
            properties: List of Property entities with analysis results
            output_path: Path where report should be written

        Raises:
            ValueError: If properties list is empty
            IOError: If output_path cannot be written
        """
        pass
