"""Concrete kill switch implementations for PHX Home Analysis buyer criteria.

This module implements all kill switches based on the buyer requirements.
All 8 default criteria are HARD (instant fail):

Kill Switches (Must Pass All - HARD):
1. NO HOA (hoa_fee must be 0 or None)
2. NO Solar Lease (no leased solar panels)
3. Minimum 4 bedrooms
4. Minimum 2 bathrooms
5. Minimum 1800 sqft living space
6. Lot size > 8000 sqft (no maximum)
7. City sewer (no septic systems)
8. Minimum 1 indoor garage space (attached/direct access)

Optional criterion (not in defaults):
- No new builds (year_built < current year) - NoNewBuildKillSwitch

Each kill switch handles missing/None data gracefully and provides detailed
failure messages explaining why a property was rejected.
"""

from typing import TYPE_CHECKING

from ...domain.enums import SewerType, SolarStatus
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

    @property
    def is_hard(self) -> bool:
        """This is a HARD criterion (instant fail)."""
        return True

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
    """Kill switch: Property must have minimum 1 indoor garage space.

    Buyer requirement is at least 1 indoor garage space (attached/direct access).
    Properties without indoor garage are automatically rejected. Detached garages
    and carports do not count toward indoor garage requirement.
    """

    def __init__(self, min_spaces: int = 1, indoor_required: bool = True):
        """Initialize garage kill switch with minimum space requirement.

        Args:
            min_spaces: Minimum number of garage spaces required (default: 1)
            indoor_required: Whether garage must be indoor/attached (default: True)
        """
        self._min_spaces = min_spaces
        self._indoor_required = indoor_required

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "min_garage"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        if self._indoor_required:
            return f"Minimum {self._min_spaces} indoor garage space(s) required"
        return f"Minimum {self._min_spaces} garage space(s) required"

    @property
    def is_hard(self) -> bool:
        """This is a HARD criterion (instant fail)."""
        return True

    def check(self, property: "Property") -> bool:
        """Test if property has minimum garage spaces.

        Args:
            property: Property to evaluate

        Returns:
            True if garage_spaces >= min_spaces (and indoor if required), False otherwise
        """
        # None or missing garage data fails (cannot verify requirement)
        if property.garage_spaces is None:
            return False

        # Check minimum spaces
        if property.garage_spaces < self._min_spaces:
            return False

        # If indoor required, check indoor_garage field (if available)
        if self._indoor_required:
            # Check if property has indoor_garage field
            indoor_garage = getattr(property, "indoor_garage", None)
            if indoor_garage is None:
                # Field not available - assume garage is indoor if garage_spaces >= 1
                # This is a reasonable default for listings (most 1+ car garages are attached)
                return property.garage_spaces >= self._min_spaces
            # Field available - check it
            return indoor_garage is True

        return True

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with garage count.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual garage spaces
        """
        if property.garage_spaces is None:
            if self._indoor_required:
                return f"Garage spaces unknown (buyer requires {self._min_spaces}+ indoor garage)"
            return f"Garage spaces unknown (buyer requires {self._min_spaces}+ garage spaces)"

        # Check if failure is due to indoor requirement
        indoor_garage = getattr(property, "indoor_garage", None)
        if self._indoor_required and indoor_garage is False:
            return (
                f"No indoor garage (has {property.garage_spaces} spaces but detached/carport only, "
                f"buyer requires {self._min_spaces}+ indoor garage)"
            )

        # Failure due to insufficient spaces
        if self._indoor_required:
            return (
                f"Only {property.garage_spaces} garage space(s) "
                f"(buyer requires {self._min_spaces}+ indoor garage)"
            )
        return f"Only {property.garage_spaces} garage space(s) (buyer requires {self._min_spaces}+)"


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


class MinSqftKillSwitch(KillSwitch):
    """Kill switch: Property must have minimum square footage.

    Buyer requirement is at least 1800 sqft of living space. Properties
    with less square footage are automatically rejected.
    """

    def __init__(self, min_sqft: int = 1800):
        """Initialize sqft kill switch with minimum requirement.

        Args:
            min_sqft: Minimum square feet required (default: 1800)
        """
        self._min_sqft = min_sqft

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "min_sqft"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return f"Minimum {self._min_sqft:,} sqft required"

    @property
    def is_hard(self) -> bool:
        """This is a HARD criterion (instant fail)."""
        return True

    def check(self, property: "Property") -> bool:
        """Test if property has minimum square footage.

        Args:
            property: Property to evaluate

        Returns:
            True if sqft > min_sqft, False otherwise
        """
        # sqft is required field in Property, should never be None
        # But handle defensively
        if property.sqft is None:
            return False
        return property.sqft > self._min_sqft

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with sqft.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual sqft
        """
        if property.sqft is None:
            return f"Square footage unknown (buyer requires {self._min_sqft:,}+ sqft)"
        return f"Only {property.sqft:,} sqft (buyer requires >{self._min_sqft:,} sqft)"


class LotSizeKillSwitch(KillSwitch):
    """Kill switch: Property lot must be at least 8,000 sqft.

    Buyer requirement is lot size greater than 8,000 square feet.
    Properties with smaller lots are automatically rejected.
    No maximum lot size (larger lots are acceptable in Phoenix market).
    """

    def __init__(self, min_sqft: int = 8000, max_sqft: int | None = None):
        """Initialize lot size kill switch with minimum threshold.

        Args:
            min_sqft: Minimum lot size in square feet (default: 8000)
            max_sqft: Maximum lot size (optional, default: None = no max)
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
        if self._max_sqft is not None:
            return f"Lot size must be {self._min_sqft:,}-{self._max_sqft:,} sqft"
        return f"Lot size must be >{self._min_sqft:,} sqft"

    @property
    def is_hard(self) -> bool:
        """This is a HARD criterion (instant fail)."""
        return True

    def check(self, property: "Property") -> bool:
        """Test if property lot size meets minimum requirement.

        Args:
            property: Property to evaluate

        Returns:
            True if lot_sqft > min_sqft (and < max_sqft if max set), False otherwise
        """
        # None or missing lot size fails (cannot verify requirement)
        if property.lot_sqft is None:
            return False
        if self._max_sqft is not None:
            return property.lot_sqft > self._min_sqft and property.lot_sqft <= self._max_sqft
        return property.lot_sqft > self._min_sqft

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message with lot size.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including actual lot size
        """
        if property.lot_sqft is None:
            if self._max_sqft is not None:
                return (
                    f"Lot size unknown (buyer requires {self._min_sqft:,}-{self._max_sqft:,} sqft)"
                )
            return f"Lot size unknown (buyer requires >{self._min_sqft:,} sqft)"
        elif property.lot_sqft <= self._min_sqft:
            return (
                f"Lot too small: {property.lot_sqft:,} sqft "
                f"(buyer requires >{self._min_sqft:,} sqft)"
            )
        elif self._max_sqft is not None and property.lot_sqft > self._max_sqft:
            return (
                f"Lot too large: {property.lot_sqft:,} sqft "
                f"(buyer requires max {self._max_sqft:,} sqft)"
            )
        # Should not reach here if check() returned False
        return f"Failed kill switch: {self.description}"


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
            return f"Year built unknown (buyer requires pre-{self._max_year + 1} construction)"
        return f"New build: {property.year_built} (buyer requires {self._max_year} or earlier)"


class NoSolarLeaseKillSwitch(KillSwitch):
    """Kill switch: Property must not have active solar lease.

    Solar leases are liabilities, not assets:
    - $100-200/mo payment transfers to buyer
    - 3-8% home value reduction
    - Transfer complications (credit check required)
    - Industry instability (100+ bankruptcies since 2023)

    Buyer requirement is no leased solar panels. Properties with solar leases
    are automatically rejected.
    """

    @property
    def name(self) -> str:
        """Kill switch identifier."""
        return "no_solar_lease"

    @property
    def description(self) -> str:
        """Human-readable requirement description."""
        return "No solar lease allowed (liability, not asset)"

    def check(self, property: "Property") -> bool:
        """Test if property does not have leased solar.

        Args:
            property: Property to evaluate

        Returns:
            True if solar_status is not LEASED, False if LEASED
        """
        # Check solar_status field if exists
        solar_status = getattr(property, "solar_status", None)
        if solar_status is None:
            return True  # Unknown = pass (don't fail on missing data)

        # Leased solar is a HARD fail
        if isinstance(solar_status, str):
            return solar_status.lower() != "leased"
        return bool(solar_status != SolarStatus.LEASED)

    def failure_message(self, property: "Property") -> str:
        """Generate specific failure message for solar lease.

        Args:
            property: Property that failed

        Returns:
            Detailed failure message including solar lease implications
        """
        return "Solar lease present - liability transfers to buyer ($100-200/mo)"
