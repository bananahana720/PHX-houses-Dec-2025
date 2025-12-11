"""Kill-switch configuration loader for CSV-driven criteria management.

This module provides configuration loading for both HARD and SOFT kill-switch
criteria from CSV files, enabling configuration-driven criteria without code changes.

The loader extends the existing SoftCriterionConfig pattern to support both
criterion types with appropriate validation.

CSV Schema:
    name,type,operator,threshold,severity,description

Example CSV:
    name,type,operator,threshold,severity,description
    no_hoa,HARD,==,0,0.0,NO HOA fees allowed
    city_sewer,SOFT,==,CITY,2.5,City sewer required

Usage:
    from pathlib import Path
    from phx_home_analysis.services.kill_switch.config_loader import (
        KillSwitchConfig,
        load_kill_switch_config,
    )

    configs = load_kill_switch_config(Path("config/kill_switch.csv"))
    for cfg in configs:
        print(f"{cfg.name} ({cfg.type}): severity={cfg.severity}")
"""

import csv
import logging
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# Maximum threshold length to prevent injection/DoS
MAX_THRESHOLD_LENGTH = 100


class KillSwitchConfig(BaseModel):
    """Configuration for a single kill-switch criterion (HARD or SOFT).

    This model validates CSV rows for both HARD and SOFT criteria,
    enforcing type-specific constraints:
    - HARD criteria must have severity 0.0
    - SOFT criteria must have severity >= 0.1 and <= 10.0

    Attributes:
        name: Unique identifier for the criterion (e.g., "no_hoa", "city_sewer")
        type: Criterion type - "HARD" (instant fail) or "SOFT" (severity accumulation)
        operator: Comparison operator (==, !=, >, <, >=, <=, range, in, not_in)
        threshold: Value to compare against (string, max 100 chars)
        severity: Severity weight when criterion fails (0.0 for HARD, 0.1-10.0 for SOFT)
        description: Human-readable description of the criterion

    Example:
        # HARD criterion
        hard_cfg = KillSwitchConfig(
            name="no_hoa",
            type="HARD",
            operator="==",
            threshold="0",
            severity=0.0,
            description="NO HOA fees allowed",
        )

        # SOFT criterion
        soft_cfg = KillSwitchConfig(
            name="city_sewer",
            type="SOFT",
            operator="==",
            threshold="CITY",
            severity=2.5,
            description="City sewer required",
        )
    """

    name: str = Field(..., min_length=1, description="Unique criterion identifier")
    type: Literal["HARD", "SOFT"] = Field(..., description="Criterion type")
    operator: Literal["==", "!=", ">", "<", ">=", "<=", "range", "in", "not_in"] = Field(
        ..., description="Comparison operator"
    )
    threshold: str = Field(..., description="Comparison value(s)")
    severity: float = Field(
        ...,
        ge=0.0,
        le=10.0,
        description="Severity weight when failed (0.0 for HARD)",
    )
    description: str = Field(..., description="Human-readable description")

    model_config = {"strict": True, "extra": "forbid"}

    @field_validator("threshold")
    @classmethod
    def validate_threshold(cls, v: str) -> str:
        """Validate threshold for length and invalid characters.

        Raises:
            ValueError: If threshold is too long or contains control characters
        """
        if len(v) > MAX_THRESHOLD_LENGTH:
            raise ValueError(f"Threshold too long (max {MAX_THRESHOLD_LENGTH} chars, got {len(v)})")
        # Check for control characters (except tab and newline which may be valid)
        if any(ord(c) < 32 and c not in "\t\n" for c in v):
            raise ValueError("Threshold contains invalid control characters")
        return v.strip()

    @field_validator("severity")
    @classmethod
    def validate_severity_precision(cls, v: float) -> float:
        """Ensure severity has reasonable precision (max 2 decimal places)."""
        return round(v, 2)

    @model_validator(mode="after")
    def validate_type_severity_consistency(self) -> "KillSwitchConfig":
        """Validate that HARD criteria have severity 0.0 and SOFT have severity >= 0.1.

        Raises:
            ValueError: If HARD criterion has non-zero severity
            ValueError: If SOFT criterion has severity < 0.1
        """
        if self.type == "HARD" and self.severity != 0.0:
            raise ValueError(
                f"HARD criterion '{self.name}' must have severity 0.0, got {self.severity}"
            )
        if self.type == "SOFT" and self.severity < 0.1:
            raise ValueError(
                f"SOFT criterion '{self.name}' must have severity >= 0.1, got {self.severity}"
            )
        return self

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary with all configuration fields
        """
        return {
            "name": self.name,
            "type": self.type,
            "operator": self.operator,
            "threshold": self.threshold,
            "severity": self.severity,
            "description": self.description,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        if self.type == "HARD":
            return f"{self.name} [HARD]: {self.operator} {self.threshold}"
        return f"{self.name} [SOFT severity={self.severity}]: {self.operator} {self.threshold}"


def load_kill_switch_config(path: Path) -> list[KillSwitchConfig]:
    """Load kill-switch configuration from CSV file.

    Reads a CSV file with kill-switch criteria definitions and returns
    validated KillSwitchConfig objects for both HARD and SOFT criteria.

    CSV Schema (header row required):
        name,type,operator,threshold,severity,description

    Comment lines (starting with #) are skipped.

    Args:
        path: Path to CSV file containing criteria configuration

    Returns:
        List of validated KillSwitchConfig objects

    Raises:
        FileNotFoundError: If CSV file does not exist
        ValueError: If CSV format is invalid, validation fails, or duplicate names found

    Example:
        >>> from pathlib import Path
        >>> configs = load_kill_switch_config(Path("config/kill_switch.csv"))
        >>> for cfg in configs:
        ...     print(f"{cfg.name}: {cfg.type}, severity={cfg.severity}")
        no_hoa: HARD, severity=0.0
        city_sewer: SOFT, severity=2.5
    """
    if not path.exists():
        logger.error("Kill-switch config file not found: %s", path)
        raise FileNotFoundError(f"Kill-switch config file not found: {path}")

    configs: list[KillSwitchConfig] = []
    seen_names: set[str] = set()

    # Use utf-8-sig to handle BOM (byte order mark) in CSV files
    with open(path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)

        # Validate header
        expected_fields = {"name", "type", "operator", "threshold", "severity", "description"}
        if reader.fieldnames is None:
            logger.error("CSV file has no header row: %s", path)
            raise ValueError(f"CSV file has no header row: {path}")

        missing_fields = expected_fields - set(reader.fieldnames)
        if missing_fields:
            logger.error(
                "CSV missing required fields: %s. Expected: %s",
                missing_fields,
                expected_fields,
            )
            raise ValueError(
                f"CSV missing required fields: {missing_fields}. Expected: {expected_fields}"
            )

        for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            # Skip comment lines (rows where name starts with #)
            name_value = row.get("name", "").strip()
            if not name_value or name_value.startswith("#"):
                continue

            # Check for duplicate names
            if name_value in seen_names:
                logger.error("Duplicate criterion name '%s' at row %d", name_value, row_num)
                raise ValueError(f"Duplicate criterion name '{name_value}' at row {row_num}")
            seen_names.add(name_value)

            # Validate type is HARD or SOFT
            row_type = row.get("type", "").upper().strip()
            if row_type not in ("HARD", "SOFT"):
                logger.warning(
                    "Skipping row %d with invalid type '%s' (expected HARD/SOFT)",
                    row_num,
                    row_type,
                )
                continue

            try:
                # Convert severity to float
                severity_str = row.get("severity", "0").strip()
                severity = float(severity_str)

                config = KillSwitchConfig(
                    name=name_value,
                    type=row_type,  # type: ignore[arg-type]
                    operator=row["operator"].strip(),  # type: ignore[arg-type]
                    threshold=row["threshold"].strip(),
                    severity=severity,
                    description=row["description"].strip(),
                )
                configs.append(config)
            except (ValueError, KeyError) as e:
                logger.error("Invalid data in CSV row %d: %s. Row: %s", row_num, e, row)
                raise ValueError(f"Invalid data in CSV row {row_num}: {e}. Row: {row}") from e

    logger.info(
        "Loaded %d kill-switch configs from %s (HARD: %d, SOFT: %d)",
        len(configs),
        path,
        sum(1 for c in configs if c.type == "HARD"),
        sum(1 for c in configs if c.type == "SOFT"),
    )

    return configs


def get_hard_configs(configs: list[KillSwitchConfig]) -> list[KillSwitchConfig]:
    """Filter to only HARD criteria configurations.

    Args:
        configs: List of KillSwitchConfig objects

    Returns:
        List containing only HARD type configurations
    """
    return [c for c in configs if c.type == "HARD"]


def get_soft_configs(configs: list[KillSwitchConfig]) -> list[KillSwitchConfig]:
    """Filter to only SOFT criteria configurations.

    Args:
        configs: List of KillSwitchConfig objects

    Returns:
        List containing only SOFT type configurations
    """
    return [c for c in configs if c.type == "SOFT"]
