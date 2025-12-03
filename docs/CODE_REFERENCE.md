# Code Reference: Value Zone Configuration Implementation

## Quick Code Snippets

### Load Configuration Function

**Location:** `scripts/value_spotter.py` (lines 21-46)

```python
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

### Configuration File Structure

**Location:** `config/scoring_weights.yaml`

```yaml
# Value zones configuration
value_zones:
  sweet_spot:
    min_score: 365              # Minimum score to be considered "high value"
    max_price: 550000           # Maximum price to be considered "affordable"
    label: "Value Sweet Spot"   # Display label for analysis
    description: "High-quality properties (score > 365) at affordable prices (< $550k)"

  premium:
    min_score: 480              # Unicorn-tier threshold
    max_price: null             # No upper price limit for premium properties
    label: "Unicorn Territory"
    description: "Top-tier properties scoring above 480 points"

# Fallback defaults (used if config file missing)
defaults:
  value_zone_min_score: 365
  value_zone_max_price: 550000
```

## Python Implementation Details

### Imports Required

```python
import yaml
from pathlib import Path
```

### Configuration Path Setup

```python
project_root = Path(__file__).parent.parent
config_path = project_root / "config" / "scoring_weights.yaml"
```

### Error Handling Pattern

```python
try:
    with open(config_path) as f:
        config = yaml.safe_load(f)
    # Process configuration
except Exception as e:
    print(f"[WARNING] Failed to load config: {e}. Using defaults.")
```

### Safe Key Access

```python
# Use .get() with defaults to handle missing keys
min_score = zone.get('min_score', defaults['min_score'])
max_price = zone.get('max_price', defaults['max_price'])
```

## YAML Structure

### Nested Access Pattern

```python
config['value_zones']['sweet_spot']['min_score']  # 365
config['value_zones']['sweet_spot']['max_price']  # 550000
config['value_zones']['premium']['min_score']     # 480
```

### Safe Nested Access

```python
# Check existence at each level
if config and 'value_zones' in config and 'sweet_spot' in config['value_zones']:
    zone = config['value_zones']['sweet_spot']
    value = zone.get('min_score', default_value)
```

## Integration in value_spotter.py

### Before Modification
```python
# Lines 46-48 (REMOVED)
# Define value zone boundaries (bottom-right quadrant)
value_zone_min_score = 365
value_zone_max_price = 550000
```

### After Modification
```python
# Lines 19-46 (ADDED)
config_path = project_root / "config" / "scoring_weights.yaml"

def load_value_zone_config():
    # ... implementation ...

value_zone_config = load_value_zone_config()
value_zone_min_score = value_zone_config['min_score']
value_zone_max_price = value_zone_config['max_price']

# Lines 75-76 (REPLACED COMMENT)
# Note: Value zone boundaries loaded from config above
# Identify properties in value zone (PASS only)
```

## Usage in Script

The loaded values are used in the same way as before:

```python
# Lines 77-81 (UNCHANGED)
df['in_value_zone'] = (
    (df['total_score'] > value_zone_min_score) &
    (df['price'] < value_zone_max_price) &
    (df['kill_switch_passed'] == 'PASS')
)

# Lines 97-98 (UNCHANGED - use loaded values)
fig.add_shape(
    type="rect",
    x0=value_zone_min_score, x1=df['total_score'].max() + 10,
    y0=df['price'].min() - 10000, y1=value_zone_max_price,
    # ...
)
```

## Testing the Implementation

### Test 1: Verify YAML Parsing

```python
import yaml
from pathlib import Path

config_path = Path('config/scoring_weights.yaml')
with open(config_path) as f:
    config = yaml.safe_load(f)

print("YAML parsed successfully")
print(f"Config keys: {list(config.keys())}")
```

### Test 2: Verify Value Loading

```python
import yaml
from pathlib import Path

config = yaml.safe_load(open('config/scoring_weights.yaml'))
zone = config['value_zones']['sweet_spot']

assert zone['min_score'] == 365, f"Expected 365, got {zone['min_score']}"
assert zone['max_price'] == 550000, f"Expected 550000, got {zone['max_price']}"
print("Configuration values correct")
```

### Test 3: Verify Function

```python
import sys
sys.path.insert(0, 'scripts')

# Simulate the function
from pathlib import Path
import yaml

config_path = Path('config/scoring_weights.yaml')

def load_value_zone_config():
    defaults = {'min_score': 365, 'max_price': 550000}
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

result = load_value_zone_config()
print(f"Function returned: {result}")
assert result['min_score'] == 365
assert result['max_price'] == 550000
print("Function test passed")
```

## Common Modifications

### Change Threshold Values

**File:** `config/scoring_weights.yaml`

```yaml
# Before
value_zones:
  sweet_spot:
    min_score: 365
    max_price: 550000

# After (example: increase both)
value_zones:
  sweet_spot:
    min_score: 370      # Changed from 365
    max_price: 600000   # Changed from 550000
```

### Add New Zone

**File:** `config/scoring_weights.yaml`

```yaml
value_zones:
  sweet_spot:
    min_score: 365
    max_price: 550000

  budget:              # NEW ZONE
    min_score: 300
    max_price: 400000
    label: "Budget Zone"
    description: "Affordable properties for value hunters"
```

**File:** `scripts/value_spotter.py` (modify function)

```python
def load_value_zone_config(zone_name='sweet_spot'):
    """Load value zone thresholds from config file."""
    defaults = {
        'min_score': 365,
        'max_price': 550000,
    }

    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            if config and 'value_zones' in config:
                zones = config['value_zones']
                if zone_name in zones:
                    zone = zones[zone_name]
                    return {
                        'min_score': zone.get('min_score', defaults['min_score']),
                        'max_price': zone.get('max_price', defaults['max_price']),
                    }
        except Exception as e:
            print(f"[WARNING] Failed to load config: {e}. Using defaults.")

    return defaults

# Usage:
value_zone_config = load_value_zone_config('sweet_spot')  # or 'budget' or 'premium'
```

## Dependencies

### Required Python Packages

```
PyYAML>=6.0     # For YAML parsing
pandas          # Already required by value_spotter.py
plotly          # Already required by value_spotter.py
```

### Import Statements

```python
import json          # Existing
from pathlib import Path  # Existing
import pandas as pd  # Existing
import plotly.graph_objects as go  # Existing
import yaml          # NEW
```

## Error Messages and Recovery

### Warning: Configuration File Not Found

```
[WARNING] Failed to load config: [Errno 2] No such file or directory: 'config/scoring_weights.yaml'. Using defaults.
```

Recovery: Script continues with defaults (min_score=365, max_price=550000)

### Warning: Invalid YAML Syntax

```
[WARNING] Failed to load config: mapping values are not allowed here. Using defaults.
```

Recovery: Script continues with defaults

### Warning: Missing value_zones Section

```
No warning - script silently falls back to defaults
```

Recovery: Script continues with defaults

## Performance Considerations

- Configuration loading occurs once at script startup
- File I/O happens once (not in loops)
- YAML parsing is negligible overhead (<1ms)
- No performance impact compared to hardcoded values

## Maintenance Notes

1. Configuration values in `config/scoring_weights.yaml` are the source of truth
2. Defaults in code are fallback only, keep them in sync
3. When modifying configuration, document changes in CHANGELOG
4. Test configuration changes with `python scripts/value_spotter.py`
5. Version control both config file and script changes together

## Related Configuration

**File:** `config/buyer_criteria.yaml`
- Contains kill-switch criteria
- Separate from value zones configuration
- Uses same YAML format and patterns

**File:** `config/scoring_weights.yaml` (this file)
- Contains value zones
- Also contains section weights and tier thresholds
- Unified configuration for all scoring-related values
