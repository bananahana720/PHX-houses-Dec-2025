"""Factory functions for creating KillSwitch instances from configuration.

This module provides factory functions to create KillSwitch instances from
KillSwitchConfig objects loaded from CSV files.

Usage:
    from phx_home_analysis.services.kill_switch.config_factory import (
        create_kill_switch_from_config,
        create_kill_switches_from_config,
        load_kill_switches_from_config,
    )

    # Load all kill switches from CSV
    kill_switches = load_kill_switches_from_config(Path("config/kill_switch.csv"))

    # Or create from pre-loaded configs (useful for hot-reload)
    configs = load_kill_switch_config(Path("config/kill_switch.csv"))
    kill_switches = create_kill_switches_from_config(configs)

    # Or create individual kill switch from config
    config = KillSwitchConfig(name="min_bedrooms", type="HARD", ...)
    kill_switch = create_kill_switch_from_config(config)
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .base import KillSwitch
from .criteria import (
    CitySewerKillSwitch,
    LotSizeKillSwitch,
    MinBathroomsKillSwitch,
    MinBedroomsKillSwitch,
    MinGarageKillSwitch,
    MinSqftKillSwitch,
    NoHoaKillSwitch,
    NoNewBuildKillSwitch,
    NoSolarLeaseKillSwitch,
)

if TYPE_CHECKING:
    from .config_loader import KillSwitchConfig

logger = logging.getLogger(__name__)


def create_kill_switch_from_config(config: "KillSwitchConfig") -> KillSwitch | None:
    """Factory to create KillSwitch instance from config.

    Maps config name to corresponding KillSwitch class and instantiates
    with appropriate parameters from config threshold.

    Args:
        config: KillSwitchConfig instance from CSV

    Returns:
        KillSwitch instance or None if name not recognized

    Example:
        >>> config = KillSwitchConfig(
        ...     name="min_bedrooms",
        ...     type="HARD",
        ...     operator=">=",
        ...     threshold="4",
        ...     severity=0.0,
        ...     description="Minimum 4 bedrooms",
        ... )
        >>> kill_switch = create_kill_switch_from_config(config)
        >>> kill_switch.name
        'min_bedrooms'
    """
    name = config.name.lower()

    try:
        if name == "no_hoa":
            return NoHoaKillSwitch()

        elif name == "no_solar_lease":
            return NoSolarLeaseKillSwitch()

        elif name == "min_bedrooms":
            threshold = int(config.threshold)
            return MinBedroomsKillSwitch(min_beds=threshold)

        elif name == "min_bathrooms":
            min_baths = float(config.threshold)
            return MinBathroomsKillSwitch(min_baths=min_baths)

        elif name == "min_sqft":
            threshold = int(config.threshold)
            return MinSqftKillSwitch(min_sqft=threshold)

        elif name == "city_sewer":
            return CitySewerKillSwitch()

        elif name == "no_new_build":
            threshold = int(config.threshold)
            return NoNewBuildKillSwitch(max_year=threshold)

        elif name == "min_garage":
            threshold = int(config.threshold)
            return MinGarageKillSwitch(min_spaces=threshold, indoor_required=True)

        elif name == "lot_size":
            # Parse range threshold "7000-15000"
            if "-" in config.threshold:
                parts = config.threshold.split("-")
                lot_min = int(parts[0])
                lot_max = int(parts[1])
                return LotSizeKillSwitch(min_sqft=lot_min, max_sqft=lot_max)
            else:
                # Single value means min only, use default max
                lot_min = int(config.threshold)
                return LotSizeKillSwitch(min_sqft=lot_min)

        else:
            logger.warning(
                "Unknown kill switch criterion '%s' in config - skipped",
                config.name,
            )
            return None

    except (ValueError, TypeError) as e:
        logger.error("Failed to create kill switch '%s': %s", config.name, e)
        return None


def create_kill_switches_from_config(
    configs: list["KillSwitchConfig"],
    *,
    strict: bool = True,
) -> list[KillSwitch]:
    """Create KillSwitch instances from a list of configurations.

    This is useful for hot-reload scenarios where configs are already loaded.

    Args:
        configs: List of KillSwitchConfig objects
        strict: If True (default), raise ValueError on unknown criteria.
            If False, log warning and skip unknown criteria.

    Returns:
        List of KillSwitch instances created from configs

    Raises:
        ValueError: If strict=True and an unknown criterion is encountered

    Example:
        >>> from phx_home_analysis.services.kill_switch.config_loader import (
        ...     load_kill_switch_config
        ... )
        >>> configs = load_kill_switch_config(Path("config/kill_switch.csv"))
        >>> kill_switches = create_kill_switches_from_config(configs)
        >>> len(kill_switches)
        9
    """
    kill_switches = []

    for config in configs:
        kill_switch = create_kill_switch_from_config(config)
        if kill_switch is not None:
            kill_switches.append(kill_switch)
        elif strict:
            raise ValueError(
                f"Unknown kill switch criterion '{config.name}' in config. "
                "Add implementation or use strict=False to skip."
            )
        else:
            logger.warning(
                "Skipping unknown kill switch criterion '%s' (strict=False)",
                config.name,
            )

    logger.debug("Created %d kill switches from %d configs", len(kill_switches), len(configs))
    return kill_switches


def load_kill_switches_from_config(
    config_path: Path,
    *,
    strict: bool = True,
) -> list[KillSwitch]:
    """Load kill switches from CSV configuration file.

    Args:
        config_path: Path to CSV configuration file
        strict: If True (default), raise ValueError on unknown criteria.
            If False, log warning and skip unknown criteria.

    Returns:
        List of KillSwitch instances created from config

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid or strict=True with unknown criteria

    Example:
        >>> from pathlib import Path
        >>> kill_switches = load_kill_switches_from_config(
        ...     Path("config/kill_switch.csv")
        ... )
        >>> len(kill_switches)
        9
    """
    from .config_loader import load_kill_switch_config

    configs = load_kill_switch_config(config_path)
    kill_switches = create_kill_switches_from_config(configs, strict=strict)

    logger.info(
        "Loaded %d kill switches from config: %s",
        len(kill_switches),
        config_path,
    )
    return kill_switches
