# Value Zone Configuration Implementation Guide

## Overview

This guide shows how the value zone thresholds were externalized from hardcoded Python values to a YAML configuration file.

## Before and After

### BEFORE: Hardcoded in Python

**File:** `scripts/value_spotter.py` (lines 46-48)

```python
# Define value zone boundaries (bottom-right quadrant)
value_zone_min_score = 365
value_zone_max_price = 550000
```

Problems with this approach:
- Hardcoded values scattered in code
- Requires code modification to change thresholds
- No documentation of what these values mean
- Difficult to use different thresholds for different analyses
- Not centralized with other configuration

### AFTER: Configuration-Driven

**File:** `config/scoring_weights.yaml`

```yaml
value_zones:
  sweet_spot:
    min_score: 365              # Minimum score to be considered "high value"
    max_price: 550000           # Maximum price to be considered "affordable"
    label: "Value Sweet Spot"
    description: "High-quality properties (score > 365) at affordable prices (< $550k)"
```

**File:** `scripts/value_spotter.py` (lines 21-46)

```python
# Load value zone config with fallback defaults
def load_value_zone_config():
    """Load value zone thresholds from config file with fallback defaults."""
    defaults = {
        'min_score': 365,
        'max_price': 550000,
    }

    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            if config and 'value_zones' in config and 'sweet_spot' in config['value_zones']:
                zone = config['value_zones']['sweet_spot']
                return {
                    'min_score': zone.get('min_score', defaults['min_score']),
                    'max_price': zone.get('max_price', defaults['max_price']),
                }
        except Exception as e:
            print(f"[WARNING] Failed to load config: {e}. Using defaults.")

    return defaults

value_zone_config = load_value_zone_config()
value_zone_min_score = value_zone_config['min_score']
value_zone_max_price = value_zone_config['max_price']
```

Benefits:
- Single source of truth for configuration
- Change thresholds without touching code
- Documented in configuration file with comments
- Supports multiple configurations (sweet_spot, premium, etc.)
- Centralized with other project configuration
- Graceful fallback if config file missing

## Configuration Structure

### File Location
```
C:\Users\Andrew\.vscode\PHX-houses-Dec-2025\
├── config/
│   ├── scoring_weights.yaml        [NEW - Contains value zones]
│   ├── buyer_criteria.yaml         [EXISTING - Kill-switch config]
│   ├── README.md                   [NEW - Config directory guide]
│   └── proxies.txt
└── scripts/
    └── value_spotter.py            [MODIFIED - Now loads from config]
```

### Value Zones Schema

```yaml
value_zones:
  <zone_name>:                       # Identifier (e.g., 'sweet_spot', 'premium')
    min_score: <number>             # Minimum score threshold
    max_price: <number or null>     # Maximum price threshold (null = no limit)
    label: <string>                 # Display label for UI
    description: <string>           # Human-readable description
```

### Current Zones

#### sweet_spot (Primary)
- **min_score:** 365 (properties scoring above this are "high value")
- **max_price:** 550000 (properties below this are "affordable")
- **Use case:** Identifying value opportunities

#### premium (Reference)
- **min_score:** 480 (unicorn-tier threshold)
- **max_price:** null (no upper limit)
- **Use case:** Identifying top-tier properties

## How to Modify Values

### Step 1: Open Configuration File
```bash
nano config/scoring_weights.yaml
```

### Step 2: Find Value Zone Section
```yaml
value_zones:
  sweet_spot:
    min_score: 365
    max_price: 550000
```

### Step 3: Update Thresholds
Example: Increase min_score to 370 and max_price to 600000
```yaml
value_zones:
  sweet_spot:
    min_score: 370              # Changed from 365
    max_price: 600000           # Changed from 550000
```

### Step 4: Save and Test
```bash
python scripts/value_spotter.py
```

The script will automatically load the new values.

## Configuration Hierarchy

The script uses this priority order:

1. **YAML Config File** (highest priority when available)
   - Loaded from `config/scoring_weights.yaml`
   - User-editable, human-readable
   - Supports version control

2. **Fallback Defaults** (if config missing or invalid)
   - Built-in to `load_value_zone_config()` function
   - Ensures script always works
   - Provides documentation of expected values

3. **Error Handling**
   - Catches YAML parsing errors
   - Prints informative warnings
   - Gracefully falls back to defaults
   - Script continues functioning

## Adding New Value Zones

To add a new value zone (e.g., "budget" zone):

### Step 1: Update Configuration
```yaml
value_zones:
  sweet_spot:
    min_score: 365
    max_price: 550000
    label: "Value Sweet Spot"
    description: "..."

  budget:                         # NEW ZONE
    min_score: 300                # Lower threshold
    max_price: 400000             # More affordable
    label: "Budget Zone"
    description: "Affordable properties with decent value"
```

### Step 2: Update Script to Use New Zone
```python
# Modify the load_value_zone_config() call to use desired zone
zone_name = 'budget'  # or 'sweet_spot' or 'premium'
zone = config['value_zones'][zone_name]
```

Or enhance the function to accept a zone parameter:
```python
def load_value_zone_config(zone_name='sweet_spot'):
    """Load specific value zone from configuration."""
    # ... load config ...
    zone = config['value_zones'][zone_name]
    # ... return zone values ...
```

## Integration with Other Configs

### Related Configuration Files

**buyer_criteria.yaml:**
- Kill-switch filtering criteria
- Hard requirements (HOA, beds, baths)
- Soft criteria with severity weights
- Separate from value zones

**scoring_weights.yaml:**
- Value zones (new, this file)
- Section weights (location, systems, interior)
- Tier thresholds (unicorn, contender, pass)
- Unified configuration file

### Future Enhancement: Unified Config

Consider consolidating all project configuration into a single `config.yaml` file:

```yaml
# Single configuration file for entire project
buyer_criteria:
  hard_criteria: {...}
  soft_criteria: {...}
  thresholds: {...}

scoring:
  section_weights: {...}
  tier_thresholds: {...}

value_zones:
  sweet_spot: {...}
  premium: {...}
```

## Error Handling Examples

### Missing Config File
```
Script output: [WARNING] Failed to load config: [Errno 2] No such file or directory: 'config/scoring_weights.yaml'. Using defaults.
Behavior: Uses min_score=365, max_price=550000
```

### Invalid YAML Syntax
```
Script output: [WARNING] Failed to load config: mapping values are not allowed here. Using defaults.
Behavior: Uses min_score=365, max_price=550000
```

### Missing Value Zones Section
```
Behavior: Uses min_score=365, max_price=550000 (defaults)
Message: None (gracefully falls back)
```

## Testing Configuration

### Verify YAML Syntax
```bash
python -c "
import yaml
with open('config/scoring_weights.yaml') as f:
    config = yaml.safe_load(f)
print('Config loaded successfully')
"
```

### Verify Values Loaded in Script
```bash
python -c "
from pathlib import Path
import sys
sys.path.insert(0, 'scripts')

# Quick test
import yaml
config_path = Path('config/scoring_weights.yaml')
with open(config_path) as f:
    config = yaml.safe_load(f)

zone = config['value_zones']['sweet_spot']
print(f'Min Score: {zone[\"min_score\"]}')
print(f'Max Price: {zone[\"max_price\"]}')
"
```

### Run Full Script
```bash
python scripts/value_spotter.py
```

## Documentation References

- **Change Documentation:** `docs/CHANGES_VALUE_ZONE_EXTERNALIZE.md`
- **Configuration Guide:** `config/README.md`
- **Implementation Summary:** `EXTERNALIZE_SUMMARY.md`
- **This File:** `docs/CONFIG_IMPLEMENTATION_GUIDE.md`

## Summary

The value zone thresholds are now:
- **Configurable** without code changes
- **Documented** in the configuration file with comments
- **Centralized** with other project configuration
- **Extensible** supporting multiple zones
- **Robust** with fallback defaults and error handling
- **Maintainable** with clear structure and guides

Change configuration in `config/scoring_weights.yaml` anytime; changes take effect on next script run.
