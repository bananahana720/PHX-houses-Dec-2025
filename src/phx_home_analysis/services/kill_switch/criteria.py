"""Concrete kill switch implementations for PHX Home Analysis buyer criteria.

This module implements all kill switches based on the buyer requirements
documented in CLAUDE.md:

Kill Switches (Must Pass All):
- NO HOA (hoa_fee must be 0 or None)
- City sewer (no septic systems)
- Minimum 2-car garage
- Minimum 4 bedrooms
- Minimum 2 bathrooms
- Lot size: 7,000-15,000 sqft
- No new builds (year_built < current year)

Each kill switch handles missing/None data gracefully and provides detailed
failure messages explaining why a property was rejected.
"""

from typing import TYPE_CHECKING

from ...domain.enums import SewerType
from .base import KillSwitch

if TYPE_CHECKING:
    from ...domain.entities import Property


class NoHoaKillSwitch(KillSwitch):
    """Kill switch: Property must have NO HOA fees.

    Buyer requirement is zero monthly HOA fees. Properties with HOA are
    automatically rejected regardless of fee amount.
    """

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "no_hoa"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return "NO HOA fees allowed (hoa_fee must be 0 or None)"

    def check(self, property: "Property") -> bool:
        """Test if property has no HOA.

        Args:
            property: Property to evaluate

        Returns:
            True if hoa_fee is 0 or None, False otherwise
        """
        # None means no HOA data, assume no HOA (pass)
        # 0 explicitly means no HOA (pass)
        # Any positive number means HOA exists (fail)
        if property.hoa_fee is None:
            return True
        return property.hoa_fee == 0

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with HOA fee amount.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including monthly HOA fee
        """
        if property.hoa_fee is not None and property.hoa_fee > 0:
            return f"HOA fee: ${property.hoa_fee}/month (buyer requires NO HOA)"
        return f"Failed kill switch: {self.description}"


class CitySewerKillSwitch(KillSwitch):
    """Kill switch: Property must have city sewer (no septic).

    Buyer requirement is municipal sewer connection. Properties with septic
    systems are automatically rejected.
    """

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "city_sewer"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return "City sewer required (no septic systems)"

    def check(self, property: "Property") -> bool:
        """Test if property has city sewer.

        Args:
            property: Property to evaluate

        Returns:
            True if sewer_type is CITY, False otherwise
        """
        # None/Unknown sewer type fails (cannot verify requirement)
        if property.sewer_type is None or property.sewer_type == SewerType.UNKNOWN:
            return False
        return property.sewer_type == SewerType.CITY

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with sewer type.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual sewer type
        """
        if property.sewer_type == SewerType.SEPTIC:
            return "Septic system (buyer requires city sewer)"
        elif property.sewer_type == SewerType.UNKNOWN or property.sewer_type is None:
            return "Sewer type unknown (buyer requires verified city sewer)"
        return f"Failed kill switch: {self.description}"


class MinGarageKillSwitch(KillSwitch):
    """Kill switch: Property must have minimum 2-car garage.

    Buyer requirement is at least 2 garage spaces. Properties with less than
    2 garage spaces are automatically rejected.
    """

    def __init__(self, min_spaces: int = 2):
        """Initialize garage kill switch with minimum space requirement.

        Args:
            min_spaces: Minimum number of garage spaces required (default: 2)
        """
        self._min_spaces = min_spaces

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "min_garage"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return f"Minimum {self._min_spaces}-car garage required"

    def check(self, property: "Property") -> bool:
        """Test if property has minimum garage spaces.

        Args:
            property: Property to evaluate

        Returns:
            True if garage_spaces >= min_spaces, False otherwise
        """
        # None or missing garage data fails (cannot verify requirement)
        if property.garage_spaces is None:
            return False
        return property.garage_spaces >= self._min_spaces

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with garage count.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual garage spaces
        """
        if property.garage_spaces is None:
            return f"Garage spaces unknown (buyer requires {self._min_spaces}+ car garage)"
        return f"Only {property.garage_spaces}-car garage (buyer requires {self._min_spaces}+)"


class MinBedroomsKillSwitch(KillSwitch):
    """Kill switch: Property must have minimum 4 bedrooms.

    Buyer requirement is at least 4 bedrooms. Properties with fewer bedrooms
    are automatically rejected.
    """

    def __init__(self, min_beds: int = 4):
        """Initialize bedrooms kill switch with minimum requirement.

        Args:
            min_beds: Minimum number of bedrooms required (default: 4)
        """
        self._min_beds = min_beds

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "min_bedrooms"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return f"Minimum {self._min_beds} bedrooms required"

    def check(self, property: "Property") -> bool:
        """Test if property has minimum bedrooms.

        Args:
            property: Property to evaluate

        Returns:
            True if beds >= min_beds, False otherwise
        """
        # beds is required field in Property, should never be None
        # But handle defensively
        if property.beds is None:
            return False
        return property.beds >= self._min_beds

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with bedroom count.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual bedroom count
        """
        if property.beds is None:
            return f"Bedroom count unknown (buyer requires {self._min_beds}+)"
        return f"Only {property.beds} bedrooms (buyer requires {self._min_beds}+)"


class MinBathroomsKillSwitch(KillSwitch):
    """Kill switch: Property must have minimum 2 bathrooms.

    Buyer requirement is at least 2 bathrooms. Properties with fewer bathrooms
    are automatically rejected.
    """

    def __init__(self, min_baths: float = 2.0):
        """Initialize bathrooms kill switch with minimum requirement.

        Args:
            min_baths: Minimum number of bathrooms required (default: 2.0)
        """
        self._min_baths = min_baths

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "min_bathrooms"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return f"Minimum {self._min_baths} bathrooms required"

    def check(self, property: "Property") -> bool:
        """Test if property has minimum bathrooms.

        Args:
            property: Property to evaluate

        Returns:
            True if baths >= min_baths, False otherwise
        """
        # baths is required field in Property, should never be None
        # But handle defensively
        if property.baths is None:
            return False
        return property.baths >= self._min_baths

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with bathroom count.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual bathroom count
        """
        if property.baths is None:
            return f"Bathroom count unknown (buyer requires {self._min_baths}+)"
        return f"Only {property.baths} bathrooms (buyer requires {self._min_baths}+)"


class LotSizeKillSwitch(KillSwitch):
    """Kill switch: Property lot must be within 7,000-15,000 sqft range.

    Buyer requirement is lot size between 7,000 and 15,000 square feet.
    Properties outside this range (too small or too large) are automatically
    rejected.
    """

    def __init__(self, min_sqft: int = 7000, max_sqft: int = 15000):
        """Initialize lot size kill switch with range.

        Args:
            min_sqft: Minimum lot size in square feet (default: 7000)
            max_sqft: Maximum lot size in square feet (default: 15000)
        """
        self._min_sqft = min_sqft
        self._max_sqft = max_sqft

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "lot_size"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return f"Lot size must be {self._min_sqft:,}-{self._max_sqft:,} sqft"

    def check(self, property: "Property") -> bool:
        """Test if property lot size is within acceptable range.

        Args:
            property: Property to evaluate

        Returns:
            True if min_sqft <= lot_sqft <= max_sqft, False otherwise
        """
        # None or missing lot size fails (cannot verify requirement)
        if property.lot_sqft is None:
            return False
        return self._min_sqft <= property.lot_sqft <= self._max_sqft

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with lot size.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual lot size
        """
        if property.lot_sqft is None:
            return (
                f"Lot size unknown (buyer requires "
                f"{self._min_sqft:,}-{self._max_sqft:,} sqft)"
            )
        elif property.lot_sqft < self._min_sqft:
            return (
                f"Lot too small: {property.lot_sqft:,} sqft "
                f"(buyer requires {self._min_sqft:,}+ sqft)"
            )
        else:  # lot_sqft > max_sqft
            return (
                f"Lot too large: {property.lot_sqft:,} sqft "
                f"(buyer requires max {self._max_sqft:,} sqft)"
            )


class NoNewBuildKillSwitch(KillSwitch):
    """Kill switch: Property must not be a new build (pre-current year).

    Buyer requirement is no new construction. Properties built in the current year
    or later are automatically rejected.
    """

    def __init__(self, max_year: int | None = None):
        """Initialize new build kill switch with maximum year.

        Args:
            max_year: Maximum year_built allowed (default: current year - 1)
        """
        from datetime import datetime
        self._max_year = max_year if max_year is not None else datetime.now().year - 1

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "no_new_build"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return f"No new builds (year_built must be {self._max_year} or earlier)"

    def check(self, property: "Property") -> bool:
        """Test if property is not a new build.

        Args:
            property: Property to evaluate

        Returns:
            True if year_built <= max_year, False otherwise
        """
        # None or missing year_built fails (cannot verify requirement)
        if property.year_built is None:
            return False
        return property.year_built <= self._max_year

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with year built.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual year built
        """
        if property.year_built is None:
            return (
                f"Year built unknown (buyer requires pre-{self._max_year + 1} construction)"
            )
        return (
            f"New build: {property.year_built} "
            f"(buyer requires {self._max_year} or earlier)"
        )
