"""Abstract base class for kill switch criteria.

This module defines the KillSwitch interface that all concrete kill switch
implementations must follow. Each kill switch represents a single non-negotiable
requirement that properties must satisfy.

Kill Switch System (Weighted Severity Threshold):
- HARD criteria (instant fail): beds < 4, baths < 2, HOA > $0
- SOFT criteria (severity weighted): sewer, garage, lot_size, year_built

Verdict Logic:
- Any HARD failure -> FAIL (instant, severity N/A)
- severity >= 3.0 -> FAIL (threshold exceeded)
- 1.5 <= severity < 3.0 -> WARNING (approaching limit)
- severity < 1.5 -> PASS
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...domain.entities import Property


class KillSwitchVerdict(Enum):
    """Kill switch verdict outcome."""
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


# Severity weights for SOFT criteria
SOFT_SEVERITY_WEIGHTS: dict[str, float] = {
    "city_sewer": 2.5,      # Septic risk - infrastructure concern
    "min_garage": 1.5,      # Convenience factor
    "lot_size": 1.0,        # Minor preference
    "no_new_build": 2.0,    # New build avoidance
}

# HARD criteria names - instant fail, no severity calculation
HARD_CRITERIA_NAMES: set[str] = {"no_hoa", "min_bedrooms", "min_bathrooms"}

# Threshold constants
SEVERITY_FAIL_THRESHOLD: float = 3.0
SEVERITY_WARNING_THRESHOLD: float = 1.5


class KillSwitch(ABC):
    """Abstract base class for property kill switch criteria.

    A kill switch can be either HARD (instant fail) or SOFT (contributes to
    severity score). Properties failing any HARD criterion are automatically
    excluded. SOFT criteria accumulate severity scores that determine verdict.

    Subclasses must implement:
    - name: Unique identifier for the kill switch
    - description: Human-readable explanation of the requirement
    - check: Boolean test method that returns True if property passes
    - is_hard: Whether this is a HARD criterion (instant fail)
    - failure_message: Custom message explaining why property failed (optional)
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name identifier for this kill switch.

        Returns:
            Short, unique name (e.g., "no_hoa", "min_bedrooms")
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of this requirement.

        Returns:
            Full description explaining what this kill switch tests
        """
        pass

    @property
    def is_hard(self) -> bool:
        """Whether this is a HARD criterion (instant fail).

        Override in subclasses to mark as HARD (True) or SOFT (False).
        Default implementation checks if name is in HARD_CRITERIA_NAMES.

        Returns:
            True if HARD criterion, False if SOFT criterion
        """
        return self.name in HARD_CRITERIA_NAMES

    @property
    def severity_weight(self) -> float:
        """Severity weight for SOFT criteria.

        Returns:
            Weight value for SOFT criteria, 0.0 for HARD criteria
        """
        if self.is_hard:
            return 0.0
        return SOFT_SEVERITY_WEIGHTS.get(self.name, 0.0)

    @abstractmethod
    def check(self, property: "Property") -> bool:
        """Test whether property passes this kill switch.

        Args:
            property: Property entity to evaluate

        Returns:
            True if property passes (meets requirement), False if it fails
        """
        pass

    def failure_message(self, property: "Property") -> str:
        """Generate custom failure message for this property.

        Override this method to provide specific details about why a property
        failed this kill switch. Default implementation returns generic message.

        Args:
            property: Property that failed this kill switch

        Returns:
            Human-readable failure message
        """
        suffix = " [HARD FAIL]" if self.is_hard else f" [severity +{self.severity_weight}]"
        return f"Failed kill switch: {self.description}{suffix}"

    def __str__(self) -> str:
        """String representation shows name, type, and description."""
        type_str = "HARD" if self.is_hard else f"SOFT (weight={self.severity_weight})"
        return f"{self.name} [{type_str}]: {self.description}"

    def __repr__(self) -> str:
        """Developer representation shows class name."""
        return f"{self.__class__.__name__}()"
