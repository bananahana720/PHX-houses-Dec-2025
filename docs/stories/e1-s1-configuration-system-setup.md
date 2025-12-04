# E1.S1: Configuration System Setup

**Status:** Ready for Development
**Epic:** Epic 1 - Foundation & Data Infrastructure
**Priority:** P0
**Estimated Points:** 8

## User Story

As a system administrator, I want externalized configuration for scoring weights and kill-switch criteria loaded from YAML files with environment-specific overrides, so that I can adjust analysis parameters without code changes while ensuring all configuration validates against schemas with clear error messages.

## Acceptance Criteria

### AC1: Configuration Loading
**Given** scoring weights in `config/scoring_weights.yaml` and buyer criteria in `config/buyer_criteria.yaml`
**When** the system starts
**Then** ConfigLoader successfully loads and validates both files against Pydantic schemas

### AC2: Environment Overrides
**Given** environment variables defined in `.env` (e.g., `MAX_MONTHLY_PAYMENT=4500`)
**When** ConfigLoader initializes
**Then** environment values override corresponding YAML values

### AC3: Validation and Error Reporting
**Given** invalid configuration (e.g., negative score, missing required field)
**When** ConfigLoader attempts to load
**Then** system fails fast with clear error message including:
- File path and line number
- Field name and invalid value
- Valid range or example value
- Human-readable explanation

### AC4: Startup Protection
**Given** invalid configuration exists
**When** application attempts to start
**Then** system prevents startup and logs validation errors before exit

### AC5: Hot-Reload Support
**Given** `--watch` flag passed to application
**When** configuration file is modified
**Then** ConfigLoader detects change, reloads, and re-validates configuration without restart

### AC6: Template Creation
**Given** new project setup
**When** templates are requested
**Then** template files exist in `config/templates/` with inline documentation

## Technical Tasks

### Task 1: Add Dependencies
**File:** `pyproject.toml:27-47`
**Action:** Add required dependencies to `dependencies` list
```python
"pydantic-settings==2.8.1",  # BaseSettings for env override
"watchfiles==1.0.4",         # Hot-reload file watching
```

### Task 2: Create Configuration Schemas
**File:** `src/phx_home_analysis/validation/config_schemas.py` (NEW)
**Lines:** ~250

Create Pydantic schemas matching YAML structure:

```python
from pydantic import BaseModel, Field, field_validator
from typing import Literal

# Value Zones (from scoring_weights.yaml:10-22)
class ValueZoneSchema(BaseModel):
    min_score: int = Field(ge=0, le=600)
    max_price: int | None = Field(default=None, ge=0)
    label: str
    description: str

class ValueZonesSchema(BaseModel):
    sweet_spot: ValueZoneSchema
    premium: ValueZoneSchema

# Scoring Sections (from scoring_weights.yaml:29-61)
class SectionCriteriaSchema(BaseModel):
    school: int | None = Field(default=None, ge=0)
    quietness: int | None = Field(default=None, ge=0)
    safety: int | None = Field(default=None, ge=0)
    # ... all criteria fields

class SectionWeightSchema(BaseModel):
    points: int = Field(ge=0, le=600)
    weight: float = Field(ge=0.0, le=1.0)
    criteria: SectionCriteriaSchema

class SectionWeightsSchema(BaseModel):
    location: SectionWeightSchema
    systems: SectionWeightSchema
    interior: SectionWeightSchema

    @field_validator('*', mode='after')
    def validate_total_points(cls, v, info):
        """Ensure total points across sections = 600"""
        # Validation logic

# Tier Thresholds (from scoring_weights.yaml:68-82)
class TierThresholdSchema(BaseModel):
    min_score: int = Field(ge=0, le=600)
    label: str
    description: str

class TierThresholdsSchema(BaseModel):
    unicorn: TierThresholdSchema
    contender: TierThresholdSchema
    pass_: TierThresholdSchema = Field(alias="pass")

# Complete Scoring Config
class ScoringWeightsConfigSchema(BaseModel):
    value_zones: ValueZonesSchema
    section_weights: SectionWeightsSchema
    tier_thresholds: TierThresholdsSchema
    defaults: dict[str, int | float] | None = None

# Buyer Criteria (from buyer_criteria.yaml)
class HardCriteriaSchema(BaseModel):
    hoa_fee: int = Field(ge=0, description="Maximum HOA fee allowed (0 = none)")
    min_beds: int = Field(ge=1, le=10, description="Minimum bedrooms required")
    min_baths: float = Field(ge=1.0, le=10.0, description="Minimum bathrooms required")

class SewerCriterionSchema(BaseModel):
    required: Literal["city", "city_sewer", "municipal", "public"]
    severity: float = Field(ge=0.0, le=10.0)

class YearBuiltCriterionSchema(BaseModel):
    max: str | int = Field(description="Max year or 'current_year' token")
    severity: float = Field(ge=0.0, le=10.0)

class GarageCriterionSchema(BaseModel):
    min: int = Field(ge=0, le=10)
    severity: float = Field(ge=0.0, le=10.0)

class LotSizeCriterionSchema(BaseModel):
    min: int = Field(ge=0, description="Minimum lot size in sqft")
    max: int = Field(ge=0, description="Maximum lot size in sqft")
    severity: float = Field(ge=0.0, le=10.0)

    @field_validator('max')
    def validate_max_gt_min(cls, v, info):
        if 'min' in info.data and v <= info.data['min']:
            raise ValueError(f"max ({v}) must be greater than min ({info.data['min']})")
        return v

class SoftCriteriaSchema(BaseModel):
    sewer_type: SewerCriterionSchema
    year_built: YearBuiltCriterionSchema
    garage_spaces: GarageCriterionSchema
    lot_sqft: LotSizeCriterionSchema

class ThresholdsSchema(BaseModel):
    severity_fail: float = Field(ge=0.0, le=10.0)
    severity_warning: float = Field(ge=0.0, le=10.0)

    @field_validator('severity_warning')
    def validate_warning_lt_fail(cls, v, info):
        if 'severity_fail' in info.data and v >= info.data['severity_fail']:
            raise ValueError(
                f"severity_warning ({v}) must be less than severity_fail ({info.data['severity_fail']})"
            )
        return v

class BuyerCriteriaConfigSchema(BaseModel):
    hard_criteria: HardCriteriaSchema
    soft_criteria: SoftCriteriaSchema
    thresholds: ThresholdsSchema

# Complete App Config
class AppConfigSchema(BaseModel):
    scoring: ScoringWeightsConfigSchema
    buyer_criteria: BuyerCriteriaConfigSchema
```

**Validation Requirements:**
- All score fields: 0 <= value <= 600
- All severity fields: 0.0 <= value <= 10.0
- Weights sum to 1.0 across sections
- Warning threshold < fail threshold
- Lot max > lot min
- All required fields present

### Task 3: Create ConfigLoader Class
**File:** `src/phx_home_analysis/config/loader.py` (NEW)
**Lines:** ~300

```python
"""Configuration loader with YAML parsing, validation, and env overrides."""

import os
from pathlib import Path
from typing import Any
import yaml
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from watchfiles import watch

from phx_home_analysis.validation.config_schemas import (
    AppConfigSchema,
    ScoringWeightsConfigSchema,
    BuyerCriteriaConfigSchema,
)


class ConfigLoader:
    """Load and validate configuration from YAML files with env overrides.

    Configuration precedence (highest to lowest):
    1. Environment variables (.env file or system env)
    2. YAML configuration files
    3. Schema defaults

    Example:
        >>> loader = ConfigLoader()
        >>> config = loader.load()
        >>> config.scoring.section_weights.location.points
        230
        >>> config.buyer_criteria.hard_criteria.min_beds
        4
    """

    def __init__(
        self,
        base_dir: Path | str | None = None,
        scoring_weights_path: Path | str | None = None,
        buyer_criteria_path: Path | str | None = None,
    ):
        """Initialize ConfigLoader with file paths.

        Args:
            base_dir: Project base directory (default: cwd or PHX_BASE_DIR env)
            scoring_weights_path: Path to scoring_weights.yaml (default: config/scoring_weights.yaml)
            buyer_criteria_path: Path to buyer_criteria.yaml (default: config/buyer_criteria.yaml)
        """
        self.base_dir = Path(base_dir or os.getenv("PHX_BASE_DIR", os.getcwd()))
        self.scoring_weights_path = Path(
            scoring_weights_path or self.base_dir / "config" / "scoring_weights.yaml"
        )
        self.buyer_criteria_path = Path(
            buyer_criteria_path or self.base_dir / "config" / "buyer_criteria.yaml"
        )

    def load(self) -> AppConfigSchema:
        """Load and validate complete configuration.

        Returns:
            Validated AppConfigSchema instance

        Raises:
            FileNotFoundError: If config files don't exist
            ValidationError: If validation fails with detailed error messages
            yaml.YAMLError: If YAML parsing fails
        """
        scoring_config = self._load_scoring_weights()
        buyer_config = self._load_buyer_criteria()

        # Apply environment overrides
        scoring_config = self._apply_env_overrides(scoring_config, prefix="SCORING_")
        buyer_config = self._apply_env_overrides(buyer_config, prefix="BUYER_")

        # Combine and validate
        try:
            app_config = AppConfigSchema(
                scoring=scoring_config,
                buyer_criteria=buyer_config,
            )
        except ValidationError as e:
            raise self._format_validation_error(e, "application config")

        return app_config

    def _load_scoring_weights(self) -> ScoringWeightsConfigSchema:
        """Load and validate scoring weights YAML.

        Returns:
            Validated ScoringWeightsConfigSchema

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If validation fails
        """
        if not self.scoring_weights_path.exists():
            raise FileNotFoundError(
                f"Scoring weights file not found: {self.scoring_weights_path}\n"
                f"Expected location: {self.scoring_weights_path.absolute()}\n"
                f"Use template: config/templates/scoring_weights.yaml.template"
            )

        try:
            with open(self.scoring_weights_path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"Failed to parse YAML file: {self.scoring_weights_path}\n"
                f"Error: {e}\n"
                f"Check YAML syntax (indentation, colons, quotes)"
            )

        try:
            return ScoringWeightsConfigSchema(**data)
        except ValidationError as e:
            raise self._format_validation_error(e, str(self.scoring_weights_path))

    def _load_buyer_criteria(self) -> BuyerCriteriaConfigSchema:
        """Load and validate buyer criteria YAML.

        Returns:
            Validated BuyerCriteriaConfigSchema

        Raises:
            FileNotFoundError: If file doesn't exist
            ValidationError: If validation fails
        """
        if not self.buyer_criteria_path.exists():
            raise FileNotFoundError(
                f"Buyer criteria file not found: {self.buyer_criteria_path}\n"
                f"Expected location: {self.buyer_criteria_path.absolute()}\n"
                f"Use template: config/templates/buyer_criteria.yaml.template"
            )

        try:
            with open(self.buyer_criteria_path) as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"Failed to parse YAML file: {self.buyer_criteria_path}\n"
                f"Error: {e}\n"
                f"Check YAML syntax (indentation, colons, quotes)"
            )

        try:
            return BuyerCriteriaConfigSchema(**data)
        except ValidationError as e:
            raise self._format_validation_error(e, str(self.buyer_criteria_path))

    def _apply_env_overrides(
        self, config: BaseModel, prefix: str = ""
    ) -> BaseModel:
        """Apply environment variable overrides to config object.

        Environment variables should use format: {PREFIX}{SECTION}__{FIELD}
        Example: SCORING_SECTION_WEIGHTS__LOCATION__POINTS=250

        Args:
            config: Pydantic config model instance
            prefix: Environment variable prefix

        Returns:
            Updated config with env overrides applied
        """
        config_dict = config.model_dump()

        # Recursively update config_dict from environment
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and parse path
                path = key[len(prefix):].lower().split("__")
                self._set_nested_value(config_dict, path, value)

        # Re-validate with updated values
        return type(config)(**config_dict)

    def _set_nested_value(self, d: dict, path: list[str], value: Any) -> None:
        """Set nested dictionary value from dot-separated path."""
        for key in path[:-1]:
            d = d.setdefault(key, {})

        # Type coercion for common types
        final_key = path[-1]
        if isinstance(d.get(final_key), int):
            d[final_key] = int(value)
        elif isinstance(d.get(final_key), float):
            d[final_key] = float(value)
        elif isinstance(d.get(final_key), bool):
            d[final_key] = value.lower() in ("true", "1", "yes")
        else:
            d[final_key] = value

    def _format_validation_error(
        self, error: ValidationError, source: str
    ) -> ValidationError:
        """Format validation error with helpful context.

        Enhances Pydantic validation errors with:
        - File path and line number (if available)
        - Field name and invalid value
        - Valid range or example
        - Human-readable explanation

        Args:
            error: Original ValidationError
            source: Source file path or description

        Returns:
            Enhanced ValidationError with better messages
        """
        enhanced_errors = []

        for err in error.errors():
            field_path = " -> ".join(str(loc) for loc in err["loc"])
            error_type = err["type"]
            msg = err["msg"]

            # Build enhanced error message
            enhanced_msg = (
                f"\n{'='*80}\n"
                f"Configuration Validation Error\n"
                f"{'='*80}\n"
                f"Source: {source}\n"
                f"Field: {field_path}\n"
                f"Error: {msg}\n"
            )

            # Add context based on error type
            if "greater_than_equal" in error_type:
                enhanced_msg += f"Value must be >= {err.get('ctx', {}).get('ge', 'N/A')}\n"
            elif "less_than_equal" in error_type:
                enhanced_msg += f"Value must be <= {err.get('ctx', {}).get('le', 'N/A')}\n"
            elif "missing" in error_type:
                enhanced_msg += f"Required field is missing\n"
                enhanced_msg += f"Example: {field_path}: <value>\n"

            enhanced_msg += f"{'='*80}\n"
            enhanced_errors.append(enhanced_msg)

        # Create new error with enhanced messages
        raise ValidationError.from_exception_data(
            title=f"Config Validation Failed: {source}",
            line_errors=[
                {
                    "type": "value_error",
                    "loc": ("config",),
                    "msg": "\n".join(enhanced_errors),
                    "input": {},
                }
            ],
        )

    def watch(self, callback: callable) -> None:
        """Watch config files for changes and reload on modification.

        Args:
            callback: Function to call with new config on change
                     Signature: callback(config: AppConfigSchema) -> None

        Example:
            >>> def on_config_change(config):
            ...     print(f"Config reloaded: {config.scoring.section_weights.location.points}")
            >>> loader = ConfigLoader()
            >>> loader.watch(on_config_change)  # Blocks until Ctrl+C
        """
        watch_paths = [
            str(self.scoring_weights_path),
            str(self.buyer_criteria_path),
        ]

        print(f"Watching config files for changes:")
        for path in watch_paths:
            print(f"  - {path}")

        for changes in watch(*watch_paths):
            print(f"\nConfig file changed: {changes}")
            try:
                config = self.load()
                callback(config)
                print("✓ Configuration reloaded successfully")
            except (ValidationError, FileNotFoundError, yaml.YAMLError) as e:
                print(f"✗ Configuration reload failed:\n{e}")


# Singleton instance for global access
_global_config: AppConfigSchema | None = None


def get_config(reload: bool = False) -> AppConfigSchema:
    """Get global configuration singleton.

    Args:
        reload: Force reload from files

    Returns:
        Global AppConfigSchema instance
    """
    global _global_config

    if _global_config is None or reload:
        loader = ConfigLoader()
        _global_config = loader.load()

    return _global_config


def reset_config() -> None:
    """Reset global configuration (useful for testing)."""
    global _global_config
    _global_config = None
```

### Task 4: Create Configuration Templates
**Files:** Create in `config/templates/`

**4a. scoring_weights.yaml.template**
- Copy from `config/scoring_weights.yaml` with inline docs
- Add comments explaining each section
- Include valid ranges and examples

**4b. buyer_criteria.yaml.template**
- Copy from `config/buyer_criteria.yaml` with inline docs
- Document severity calculation
- Show example scenarios

**4c. .env.template**
```bash
# PHX Home Analysis Configuration Overrides
# Copy to .env and customize as needed

# Project paths
PHX_BASE_DIR=/path/to/project

# Buyer criteria overrides
BUYER_HARD_CRITERIA__MIN_BEDS=5
BUYER_HARD_CRITERIA__MIN_BATHS=3
BUYER_THRESHOLDS__SEVERITY_FAIL=2.5

# Scoring overrides
SCORING_SECTION_WEIGHTS__LOCATION__POINTS=250
SCORING_TIER_THRESHOLDS__UNICORN__MIN_SCORE=500

# Feature flags
ENABLE_HOT_RELOAD=false
DEBUG_CONFIG_LOADING=true
```

### Task 5: Integrate ConfigLoader with Existing Code
**File:** `src/phx_home_analysis/config/__init__.py`
**Action:** Export ConfigLoader and schemas

```python
from phx_home_analysis.config.loader import (
    ConfigLoader,
    get_config,
    reset_config,
)
from phx_home_analysis.config.settings import (
    AppConfig,
    BuyerProfile,
    ProjectPaths,
    # ... existing exports
)

__all__ = [
    "ConfigLoader",
    "get_config",
    "reset_config",
    "AppConfig",
    "BuyerProfile",
    "ProjectPaths",
    # ... existing exports
]
```

### Task 6: Add CLI Flag for Hot-Reload
**File:** `scripts/phx_home_analyzer.py` (or main entry point)
**Action:** Add `--watch` argument

```python
parser.add_argument(
    "--watch",
    action="store_true",
    help="Watch config files for changes and reload automatically"
)

if args.watch:
    def on_config_change(config):
        print("Configuration reloaded - rerunning analysis...")
        # Re-run analysis with new config

    loader = ConfigLoader()
    loader.watch(on_config_change)
```

### Task 7: Update settings.py Migration Path
**File:** `src/phx_home_analysis/config/settings.py`
**Action:** Add deprecation notice and migration helper

```python
# At top of file
import warnings

def get_buyer_profile_from_config() -> BuyerProfile:
    """Load BuyerProfile from ConfigLoader (new way).

    Deprecated: Use ConfigLoader.load().buyer_criteria instead.
    This function provides backward compatibility during migration.
    """
    warnings.warn(
        "BuyerProfile dataclass is deprecated. Use ConfigLoader instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    from phx_home_analysis.config.loader import get_config
    config = get_config()

    # Map new config structure to old BuyerProfile
    return BuyerProfile(
        max_monthly_payment=config.buyer_criteria.hard_criteria.hoa_fee,  # TODO: Add to schema
        min_bedrooms=config.buyer_criteria.hard_criteria.min_beds,
        min_bathrooms=config.buyer_criteria.hard_criteria.min_baths,
        # ... map remaining fields
    )
```

## Test Plan

### Unit Tests

#### Test Suite 1: config_schemas.py validation
**File:** `tests/unit/validation/test_config_schemas.py`

**Test Cases:**
1. `test_scoring_weights_schema_valid()` - Valid YAML loads successfully
2. `test_scoring_weights_invalid_negative_score()` - Rejects negative points
3. `test_scoring_weights_invalid_score_over_600()` - Rejects points > 600
4. `test_scoring_weights_missing_required_field()` - Error on missing field
5. `test_buyer_criteria_schema_valid()` - Valid YAML loads successfully
6. `test_buyer_criteria_invalid_severity()` - Rejects severity > 10.0
7. `test_buyer_criteria_lot_max_lt_min()` - Error when max < min
8. `test_thresholds_warning_gte_fail()` - Error when warning >= fail
9. `test_tier_thresholds_ordering()` - Ensure unicorn > contender > pass
10. `test_section_weights_sum_to_600()` - Validate total points = 600

**Fixtures:**
```python
@pytest.fixture
def valid_scoring_weights():
    return {
        "value_zones": {
            "sweet_spot": {
                "min_score": 365,
                "max_price": 550000,
                "label": "Value Sweet Spot",
                "description": "High-quality properties..."
            },
            "premium": {...}
        },
        "section_weights": {...},
        "tier_thresholds": {...}
    }

@pytest.fixture
def invalid_scoring_weights_negative():
    data = valid_scoring_weights.copy()
    data["section_weights"]["location"]["points"] = -50
    return data
```

#### Test Suite 2: config_loader.py functionality
**File:** `tests/unit/config/test_config_loader.py`

**Test Cases:**
1. `test_load_valid_config()` - Successful load with valid files
2. `test_load_missing_scoring_weights()` - FileNotFoundError with helpful message
3. `test_load_missing_buyer_criteria()` - FileNotFoundError with helpful message
4. `test_load_invalid_yaml_syntax()` - yaml.YAMLError with line number
5. `test_env_override_simple_value()` - Override scoring points via env
6. `test_env_override_nested_value()` - Override nested config via env
7. `test_env_override_type_coercion()` - Convert env string to int/float/bool
8. `test_validation_error_formatting()` - Clear error with field path
9. `test_get_config_singleton()` - Same instance on repeated calls
10. `test_reset_config()` - Singleton reset works
11. `test_watch_reload_on_change()` - Callback fires on file modification
12. `test_watch_validation_error_handling()` - Graceful handling of invalid reload

**Test Helpers:**
```python
@pytest.fixture
def temp_config_files(tmp_path):
    """Create temporary config files for testing."""
    scoring_weights = tmp_path / "scoring_weights.yaml"
    buyer_criteria = tmp_path / "buyer_criteria.yaml"

    # Write valid YAML to files
    scoring_weights.write_text(yaml.dump(VALID_SCORING_WEIGHTS))
    buyer_criteria.write_text(yaml.dump(VALID_BUYER_CRITERIA))

    return {
        "base_dir": tmp_path,
        "scoring_weights": scoring_weights,
        "buyer_criteria": buyer_criteria,
    }

def test_load_valid_config(temp_config_files):
    loader = ConfigLoader(
        base_dir=temp_config_files["base_dir"],
        scoring_weights_path=temp_config_files["scoring_weights"],
        buyer_criteria_path=temp_config_files["buyer_criteria"],
    )

    config = loader.load()

    assert config.scoring.section_weights.location.points == 230
    assert config.buyer_criteria.hard_criteria.min_beds == 4
```

#### Test Suite 3: Error message clarity
**File:** `tests/unit/config/test_error_messages.py`

**Test Cases:**
1. `test_error_includes_file_path()` - Error shows source file
2. `test_error_includes_field_path()` - Error shows nested field path
3. `test_error_includes_valid_range()` - Error shows valid range
4. `test_error_includes_example_value()` - Error shows example
5. `test_error_includes_line_number()` - YAML error shows line number

### Integration Tests

#### Test Suite 4: End-to-end configuration loading
**File:** `tests/integration/test_config_integration.py`

**Test Cases:**
1. `test_load_from_real_config_files()` - Load from actual config/ directory
2. `test_env_override_with_dotenv()` - Load .env and apply overrides
3. `test_config_used_by_scoring_system()` - Scoring uses ConfigLoader
4. `test_config_used_by_kill_switch()` - Kill-switch uses ConfigLoader
5. `test_hot_reload_triggers_re_analysis()` - Watch mode works end-to-end

## Dependencies

### New Dependencies Required
- `pydantic-settings==2.8.1` - BaseSettings for environment overrides
- `watchfiles==1.0.4` - File watching for hot-reload

### Existing Dependencies Used
- `pydantic==2.12.5` - Schema validation
- `pyyaml>=6.0.0` - YAML parsing
- `python-dotenv==1.2.1` - .env file loading

### Internal Dependencies
- `src/phx_home_analysis/validation/schemas.py` - Existing property schemas
- `src/phx_home_analysis/config/settings.py` - Existing config classes (migration target)

## Definition of Done Checklist

- [ ] Dependencies added to `pyproject.toml` and installed via `uv sync`
- [ ] `config_schemas.py` created with all schema classes matching YAML structure
- [ ] `loader.py` created with ConfigLoader class
- [ ] ConfigLoader implements YAML loading with validation
- [ ] ConfigLoader implements environment variable overrides
- [ ] ConfigLoader implements hot-reload with `--watch` flag
- [ ] Configuration templates created in `config/templates/`
- [ ] Error messages include file path, line number, field name, valid range
- [ ] Invalid configuration prevents system startup
- [ ] Unit tests written with 90%+ coverage for schemas and loader
- [ ] Integration tests verify end-to-end config loading
- [ ] All tests pass: `pytest tests/unit/config/ tests/unit/validation/test_config_schemas.py`
- [ ] Type checking passes: `mypy src/phx_home_analysis/config/loader.py src/phx_home_analysis/validation/config_schemas.py`
- [ ] Linting passes: `ruff check src/phx_home_analysis/config/loader.py src/phx_home_analysis/validation/config_schemas.py`
- [ ] Documentation updated in relevant CLAUDE.md files
- [ ] Backward compatibility maintained with existing settings.py (deprecation warnings added)
- [ ] CLI `--watch` flag implemented and tested

## Notes

### Design Decisions (YOLO MODE)

1. **YAML Format for Kill-Switch**: Epic mentions `kill_switch.csv` but project already uses `buyer_criteria.yaml` (74 lines, comprehensive structure). **Decision: Use YAML** - more readable, supports nested structure, already implemented.

2. **pydantic-settings Package**: Required for BaseSettings with env override support. **Decision: Add pydantic-settings==2.8.1** - official Pydantic extension, well-maintained.

3. **watchfiles for Hot-Reload**: Multiple options (watchdog, watchfiles, inotify). **Decision: Use watchfiles==1.0.4** - Fast Rust-based implementation, same library used by uvicorn/FastAPI, simple API.

4. **Schema Organization**: All config schemas in single `config_schemas.py` vs separate files. **Decision: Single file** - schemas are cohesive, easier to maintain cross-field validation, ~250 lines is reasonable.

5. **Environment Override Format**: Chosen `{PREFIX}{SECTION}__{FIELD}` format (double underscore for nesting). **Example:** `BUYER_HARD_CRITERIA__MIN_BEDS=5` - Standard pydantic-settings convention.

6. **Global Config Singleton**: Provide `get_config()` function for easy access. **Decision: Yes** - Reduces boilerplate, but provide `reset_config()` for testing.

7. **Migration Strategy**: Gradual migration from settings.py dataclasses to ConfigLoader. **Decision: Maintain backward compatibility** - Add deprecation warnings, provide migration helpers, update over multiple stories.

### Current State (Discovered)

**Existing Files:**
- ✅ `config/scoring_weights.yaml` (92 lines) - Complete, well-structured
- ✅ `config/buyer_criteria.yaml` (74 lines) - Complete, well-structured
- ✅ `src/phx_home_analysis/config/settings.py` (417 lines) - Hardcoded dataclasses
- ✅ `src/phx_home_analysis/validation/schemas.py` - Property/enrichment schemas

**Missing (To Create):**
- ❌ `src/phx_home_analysis/validation/config_schemas.py` - NEW
- ❌ `src/phx_home_analysis/config/loader.py` - NEW
- ❌ `config/templates/scoring_weights.yaml.template` - NEW
- ❌ `config/templates/buyer_criteria.yaml.template` - NEW
- ❌ `config/templates/.env.template` - NEW
- ❌ `tests/unit/config/test_config_loader.py` - NEW
- ❌ `tests/unit/validation/test_config_schemas.py` - NEW

**Dependencies:**
- ✅ `pydantic==2.12.5` - Already installed
- ✅ `pyyaml>=6.0.0` - Already installed
- ❌ `pydantic-settings==2.8.1` - NEED TO ADD
- ❌ `watchfiles==1.0.4` - NEED TO ADD

### Error Message Format Example

```
================================================================================
Configuration Validation Error
================================================================================
Source: /path/to/config/scoring_weights.yaml
Field: section_weights -> location -> points
Error: Value must be greater than or equal to 0

Current value: -50
Valid range: 0 to 600
Example:
  section_weights:
    location:
      points: 230

================================================================================
```

### Hot-Reload Usage Example

```bash
# Terminal 1: Start analyzer in watch mode
python scripts/phx_home_analyzer.py --watch

# Terminal 2: Edit config file
vim config/scoring_weights.yaml
# Change location points from 230 to 250
# Save file

# Terminal 1 output:
# Config file changed: {(<Change.modified: 2>, '/path/to/scoring_weights.yaml')}
# Configuration reloaded - rerunning analysis...
# ✓ Configuration reloaded successfully
```

### Configuration Precedence Example

Given:
- `config/buyer_criteria.yaml`: `hard_criteria.min_beds: 4`
- `.env`: `BUYER_HARD_CRITERIA__MIN_BEDS=5`

Result: `config.buyer_criteria.hard_criteria.min_beds == 5` (env overrides YAML)

### Related Stories

**Depends On:**
- None (P0 foundation story)

**Blocks:**
- E1.S2: Scoring service refactoring (needs ConfigLoader)
- E1.S3: Kill-switch service refactoring (needs ConfigLoader)
- E2.S1: CLI tool implementation (needs hot-reload)

### Open Questions

None - All decisions made in YOLO mode.

### Risk Assessment

**Risk 1: Backward Compatibility Break**
- **Likelihood:** Medium
- **Impact:** High (breaks existing scripts)
- **Mitigation:** Maintain settings.py with deprecation warnings, provide migration helpers, gradual rollout

**Risk 2: Complex Nested Env Overrides**
- **Likelihood:** Low
- **Impact:** Medium (confusing for users)
- **Mitigation:** Clear documentation, examples in .env.template, validation error messages

**Risk 3: Hot-Reload Race Conditions**
- **Likelihood:** Low
- **Impact:** Low (dev feature only)
- **Mitigation:** File watching library handles debouncing, graceful error handling on invalid reload

## Implementation Order

1. **Phase 1: Schema Foundation** (blocking)
   - Add dependencies
   - Create config_schemas.py
   - Unit tests for schemas

2. **Phase 2: Loader Implementation** (blocking)
   - Create loader.py with ConfigLoader class
   - Implement YAML loading and validation
   - Unit tests for loader

3. **Phase 3: Environment Overrides** (non-blocking)
   - Implement env override logic
   - Create .env.template
   - Unit tests for overrides

4. **Phase 4: Hot-Reload** (non-blocking, dev feature)
   - Implement watch() method
   - Add CLI --watch flag
   - Integration tests

5. **Phase 5: Templates & Docs** (non-blocking)
   - Create YAML templates
   - Update CLAUDE.md files
   - Add usage examples

6. **Phase 6: Integration & Migration** (non-blocking)
   - Add deprecation warnings to settings.py
   - Update __init__.py exports
   - Integration tests with scoring/kill-switch

---

**Story Created:** 2025-12-03
**Created By:** PM Agent (YOLO Mode + ULTRATHINK)
**Epic File:** `docs/epics/epic-1-foundation-data-infrastructure.md`
