"""Configuration loader with YAML parsing, validation, and environment overrides.

This module provides the ConfigLoader class for loading and validating configuration
from YAML files with support for environment variable overrides and hot-reload.

Configuration Precedence (highest to lowest):
    1. Environment variables (PHX__SECTION__FIELD format)
    2. YAML configuration files
    3. Schema defaults

Example:
    >>> loader = ConfigLoader()
    >>> config = loader.load()
    >>> config.scoring.section_weights.location.points
    250
    >>> config.buyer_criteria.hard_criteria.min_beds
    4

Environment Override Example:
    # Set in .env or shell
    PHX__BUYER_CRITERIA__HARD_CRITERIA__MIN_BEDS=5

    >>> config = ConfigLoader().load()
    >>> config.buyer_criteria.hard_criteria.min_beds
    5

Hot-Reload Example:
    >>> def on_change(config):
    ...     print(f"Config reloaded: {config.scoring.tier_thresholds.unicorn.min_score}")
    >>> loader = ConfigLoader()
    >>> loader.watch(on_change)  # Blocks, reloads on file change
"""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from ..validation.config_schemas import (
    AppConfigSchema,
    BuyerCriteriaConfigSchema,
    ConfigurationError,
    ScoringWeightsConfigSchema,
)

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load and validate configuration from YAML files with environment overrides.

    Configuration precedence (highest to lowest):
        1. Environment variables (.env file or system env)
        2. YAML configuration files
        3. Schema defaults

    The environment variable format is: PHX__{SECTION}__{FIELD}
    where SECTION and FIELD use double underscores as separators.

    Example:
        >>> loader = ConfigLoader()
        >>> config = loader.load()
        >>> config.scoring.section_weights.location.points
        250

    Attributes:
        base_dir: Project base directory
        scoring_weights_path: Path to scoring_weights.yaml
        buyer_criteria_path: Path to buyer_criteria.yaml
    """

    ENV_PREFIX = "PHX__"

    def __init__(
        self,
        base_dir: Path | str | None = None,
        scoring_weights_path: Path | str | None = None,
        buyer_criteria_path: Path | str | None = None,
    ) -> None:
        """Initialize ConfigLoader with file paths.

        Args:
            base_dir: Project base directory (default: PHX_BASE_DIR env or cwd)
            scoring_weights_path: Path to scoring_weights.yaml
            buyer_criteria_path: Path to buyer_criteria.yaml
        """
        base_dir_resolved = base_dir or os.getenv("PHX_BASE_DIR") or os.getcwd()
        self.base_dir = Path(base_dir_resolved)

        if scoring_weights_path is not None:
            self.scoring_weights_path = Path(scoring_weights_path)
        else:
            self.scoring_weights_path = self.base_dir / "config" / "scoring_weights.yaml"

        if buyer_criteria_path is not None:
            self.buyer_criteria_path = Path(buyer_criteria_path)
        else:
            self.buyer_criteria_path = self.base_dir / "config" / "buyer_criteria.yaml"

    def load(self) -> AppConfigSchema:
        """Load and validate complete configuration.

        Returns:
            Validated AppConfigSchema instance

        Raises:
            ConfigurationError: If validation fails with detailed error message
            FileNotFoundError: If config files don't exist
            yaml.YAMLError: If YAML parsing fails
        """
        logger.info("Loading configuration files...")

        # Load and validate individual configs
        scoring_data = self._load_yaml_file(self.scoring_weights_path)
        buyer_data = self._load_yaml_file(self.buyer_criteria_path)

        # Apply environment overrides
        scoring_data = self._apply_env_overrides(scoring_data, "SCORING")
        buyer_data = self._apply_env_overrides(buyer_data, "BUYER_CRITERIA")

        # Validate scoring config
        try:
            scoring_config = ScoringWeightsConfigSchema(**scoring_data)
        except ValidationError as e:
            raise self._format_validation_error(
                e, str(self.scoring_weights_path), scoring_data
            ) from None

        # Validate buyer criteria config
        try:
            buyer_config = BuyerCriteriaConfigSchema(**buyer_data)
        except ValidationError as e:
            raise self._format_validation_error(
                e, str(self.buyer_criteria_path), buyer_data
            ) from None

        # Combine into complete config
        try:
            app_config = AppConfigSchema(
                scoring=scoring_config,
                buyer_criteria=buyer_config,
            )
        except ValidationError as e:
            raise self._format_validation_error(e, "combined configuration", {}) from None

        logger.info(
            "Configuration loaded successfully: "
            f"scoring={self.scoring_weights_path.name}, "
            f"buyer_criteria={self.buyer_criteria_path.name}"
        )

        return app_config

    def load_scoring_weights(self) -> ScoringWeightsConfigSchema:
        """Load and validate only scoring weights configuration.

        Returns:
            Validated ScoringWeightsConfigSchema

        Raises:
            ConfigurationError: If validation fails
            FileNotFoundError: If file doesn't exist
        """
        data = self._load_yaml_file(self.scoring_weights_path)
        data = self._apply_env_overrides(data, "SCORING")

        try:
            return ScoringWeightsConfigSchema(**data)
        except ValidationError as e:
            raise self._format_validation_error(e, str(self.scoring_weights_path), data) from None

    def load_buyer_criteria(self) -> BuyerCriteriaConfigSchema:
        """Load and validate only buyer criteria configuration.

        Returns:
            Validated BuyerCriteriaConfigSchema

        Raises:
            ConfigurationError: If validation fails
            FileNotFoundError: If file doesn't exist
        """
        data = self._load_yaml_file(self.buyer_criteria_path)
        data = self._apply_env_overrides(data, "BUYER_CRITERIA")

        try:
            return BuyerCriteriaConfigSchema(**data)
        except ValidationError as e:
            raise self._format_validation_error(e, str(self.buyer_criteria_path), data) from None

    def _load_yaml_file(self, path: Path) -> dict[str, Any]:
        """Load YAML file with helpful error messages.

        Args:
            path: Path to YAML file

        Returns:
            Parsed YAML data as dictionary

        Raises:
            FileNotFoundError: With helpful message if file missing
            ConfigurationError: If YAML parsing fails
        """
        if not path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {path}\n"
                f"  Expected location: {path.absolute()}\n"
                f"  Create from template: config/templates/{path.name}.template"
            )

        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if data is None:
                raise ConfigurationError(
                    f"Configuration file is empty: {path}\n"
                    f"  The file exists but contains no valid YAML data."
                )

            if not isinstance(data, dict):
                raise ConfigurationError(
                    f"Configuration file must contain a YAML mapping: {path}\n"
                    f"  Got: {type(data).__name__}"
                )

            return data

        except yaml.YAMLError as e:
            # Extract line number from YAML error if available
            line_info = ""
            if hasattr(e, "problem_mark") and e.problem_mark is not None:
                mark = e.problem_mark
                line_info = f" (line {mark.line + 1}, column {mark.column + 1})"

            raise ConfigurationError(
                f"Failed to parse YAML file: {path}{line_info}\n"
                f"  Error: {e}\n"
                f"  Check YAML syntax: indentation, colons, quotes"
            ) from e

    def _apply_env_overrides(self, data: dict[str, Any], section_prefix: str) -> dict[str, Any]:
        """Apply environment variable overrides to configuration.

        Environment variables should use format: PHX__{SECTION}__{FIELD}
        where nested fields use double underscores.

        Example:
            PHX__BUYER_CRITERIA__HARD_CRITERIA__MIN_BEDS=5

        Args:
            data: Configuration dictionary to update
            section_prefix: Prefix for this section (e.g., "SCORING", "BUYER_CRITERIA")

        Returns:
            Updated configuration dictionary
        """
        prefix = f"{self.ENV_PREFIX}{section_prefix}__"

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Extract path after prefix
                path_str = key[len(prefix) :]
                path = path_str.lower().split("__")

                # Apply override
                try:
                    self._set_nested_value(data, path, value)
                    logger.debug(f"Applied env override: {key}={value}")
                except (KeyError, TypeError) as e:
                    logger.warning(f"Failed to apply env override {key}: {e}")

        return data

    def _set_nested_value(self, data: dict[str, Any], path: list[str], value: str) -> None:
        """Set nested dictionary value from path.

        Performs type coercion based on existing value type.

        Args:
            data: Dictionary to update
            path: List of keys forming the path
            value: String value to set (will be coerced)
        """
        # Navigate to parent
        current = data
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Set value with type coercion
        final_key = path[-1]
        existing = current.get(final_key)

        if isinstance(existing, bool):
            current[final_key] = value.lower() in ("true", "1", "yes", "on")
        elif isinstance(existing, int):
            current[final_key] = int(value)
        elif isinstance(existing, float):
            current[final_key] = float(value)
        else:
            # Default to string or try to infer type
            if value.isdigit():
                current[final_key] = int(value)
            elif re.match(r"^-?\d+\.?\d*$", value):
                current[final_key] = float(value)
            elif value.lower() in ("true", "false"):
                current[final_key] = value.lower() == "true"
            else:
                current[final_key] = value

    def _format_validation_error(
        self,
        error: ValidationError,
        source: str,
        data: dict[str, Any],
    ) -> ConfigurationError:
        """Format validation error with helpful context.

        Creates enhanced error messages with:
        - File path
        - Field path
        - Invalid value
        - Valid range or example
        - Human-readable explanation

        Args:
            error: Original Pydantic ValidationError
            source: Source file path or description
            data: Original data dictionary (for value lookup)

        Returns:
            ConfigurationError with enhanced message
        """
        messages = []

        for err in error.errors():
            # Build field path
            field_path = " -> ".join(str(loc) for loc in err["loc"])
            error_type = err["type"]
            msg = err["msg"]

            # Try to get the actual invalid value
            actual_value = self._get_nested_value(data, list(err["loc"]))
            value_str = f"{actual_value!r}" if actual_value is not None else "missing"

            # Build enhanced error message
            error_msg = [
                "=" * 80,
                "Configuration Validation Error",
                "=" * 80,
                f"Source: {source}",
                f"Field: {field_path}",
                f"Value: {value_str}",
                f"Error: {msg}",
            ]

            # Add context based on error type
            ctx = err.get("ctx", {})
            if "ge" in ctx:
                error_msg.append(f"Minimum allowed: {ctx['ge']}")
            if "le" in ctx:
                error_msg.append(f"Maximum allowed: {ctx['le']}")
            if "gt" in ctx:
                error_msg.append(f"Must be greater than: {ctx['gt']}")
            if "lt" in ctx:
                error_msg.append(f"Must be less than: {ctx['lt']}")

            # Add type-specific hints
            if "missing" in error_type:
                error_msg.append(f"Example: {field_path.replace(' -> ', '.')}: <value>")
            elif "int" in error_type or "float" in error_type:
                error_msg.append("Value must be a number")
            elif "literal" in error_type:
                if "expected" in ctx:
                    error_msg.append(f"Valid values: {ctx['expected']}")

            error_msg.append("=" * 80)
            messages.append("\n".join(error_msg))

        full_message = "\n\n".join(messages)
        return ConfigurationError(full_message)

    def _get_nested_value(self, data: dict[str, Any], path: list[str | int]) -> Any | None:
        """Get nested value from dictionary.

        Args:
            data: Dictionary to search
            path: List of keys/indices

        Returns:
            Value at path or None if not found
        """
        current: Any = data
        for key in path:
            try:
                if isinstance(current, dict):
                    current = current[str(key)]
                elif isinstance(current, (list, tuple)) and isinstance(key, int):
                    current = current[key]
                else:
                    return None
            except (KeyError, IndexError, TypeError):
                return None
        return current

    def watch(self, callback: Callable[[AppConfigSchema], None]) -> None:
        """Watch configuration files for changes and reload on modification.

        This method blocks and continuously watches for file changes.
        On each change, it reloads and validates the configuration,
        then calls the callback with the new config.

        If validation fails, the callback is NOT called and an error is logged.

        Args:
            callback: Function to call with new config on change
                     Signature: callback(config: AppConfigSchema) -> None

        Example:
            >>> def on_config_change(config):
            ...     print(f"Unicorn threshold: {config.scoring.tier_thresholds.unicorn.min_score}")
            >>> loader = ConfigLoader()
            >>> loader.watch(on_config_change)  # Blocks until Ctrl+C
        """
        # Import watchfiles here to make it optional
        try:
            from watchfiles import watch as watchfiles_watch
        except ImportError as e:
            raise ImportError(
                "watchfiles is required for hot-reload functionality.\n"
                "Install with: pip install watchfiles"
            ) from e

        watch_paths = [
            str(self.scoring_weights_path),
            str(self.buyer_criteria_path),
        ]

        logger.info("Starting config file watcher...")
        logger.info("Watching configuration files for changes:")
        for path in watch_paths:
            logger.info(f"  - {path}")
        logger.info("Press Ctrl+C to stop.\n")

        for changes in watchfiles_watch(*watch_paths):
            changed_files = [str(change[1]) for change in changes]
            logger.info(f"Config file(s) changed: {changed_files}")
            logger.info(f"\nConfig file changed: {changed_files}")

            try:
                config = self.load()
                callback(config)
                logger.info("[OK] Configuration reloaded successfully")
            except (ConfigurationError, FileNotFoundError, yaml.YAMLError) as e:
                logger.error(f"[ERROR] Configuration reload failed:\n{e}")


# =============================================================================
# GLOBAL CONFIG SINGLETON
# =============================================================================

_global_config: AppConfigSchema | None = None
_global_loader: ConfigLoader | None = None


def get_config(reload: bool = False) -> AppConfigSchema:
    """Get global configuration singleton.

    This function provides convenient access to the application configuration
    without needing to manage a ConfigLoader instance.

    Args:
        reload: If True, force reload from files

    Returns:
        Global AppConfigSchema instance

    Raises:
        ConfigurationError: If configuration is invalid
        FileNotFoundError: If config files don't exist

    Example:
        >>> config = get_config()
        >>> config.scoring.section_weights.location.points
        250
    """
    global _global_config, _global_loader

    if _global_config is None or reload:
        if _global_loader is None:
            _global_loader = ConfigLoader()
        _global_config = _global_loader.load()

    return _global_config


def reset_config() -> None:
    """Reset global configuration singleton.

    Useful for testing to ensure fresh configuration loads.

    Example:
        >>> reset_config()
        >>> config = get_config()  # Will reload from files
    """
    global _global_config, _global_loader
    _global_config = None
    _global_loader = None


def init_config(
    base_dir: Path | str | None = None,
    scoring_weights_path: Path | str | None = None,
    buyer_criteria_path: Path | str | None = None,
) -> AppConfigSchema:
    """Initialize global configuration with custom paths.

    Call this at application startup to configure custom file paths.
    Subsequent calls to get_config() will use these paths.

    Args:
        base_dir: Project base directory
        scoring_weights_path: Path to scoring_weights.yaml
        buyer_criteria_path: Path to buyer_criteria.yaml

    Returns:
        Validated AppConfigSchema instance

    Example:
        >>> config = init_config(base_dir="/custom/path")
        >>> get_config()  # Returns same config
    """
    global _global_config, _global_loader

    _global_loader = ConfigLoader(
        base_dir=base_dir,
        scoring_weights_path=scoring_weights_path,
        buyer_criteria_path=buyer_criteria_path,
    )
    _global_config = _global_loader.load()

    return _global_config


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ConfigLoader",
    "get_config",
    "reset_config",
    "init_config",
]
