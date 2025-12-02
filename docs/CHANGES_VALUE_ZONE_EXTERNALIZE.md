# Value Zone Thresholds Externalization

## Overview
Externalized hardcoded value zone thresholds from `scripts/value_spotter.py` to the new `config/scoring_weights.yaml` configuration file. This improves maintainability and allows configuration changes without modifying Python code.

## Changes Made

### 1. Created New Configuration File
**File:** `config/scoring_weights.yaml`

Added comprehensive scoring and value zone configuration with the following sections:

#### Value Zones Section
```yaml
value_zones:
  sweet_spot:
    min_score: 365              # Minimum score to be considered "high value"
    max_price: 550000           # Maximum price to be considered "affordable"
    label: "Value Sweet Spot"
    description: "High-quality properties (score > 365) at affordable prices (< $550k)"

  premium:
    min_score: 480              # Unicorn-tier threshold
    max_price: null             # No upper price limit
    label: "Unicorn Territory"
    description: "Top-tier properties scoring above 480 points"
```

#### Additional Sections (for future use)
- **section_weights:** Score point allocation (Section A: Location 230pts, B: Systems 180pts, C: Interior 190pts)
- **tier_thresholds:** Property tier classification (Unicorn, Contender, Pass)
- **defaults:** Fallback values for backward compatibility

### 2. Updated value_spotter.py Script

#### Added Imports
- Imported `yaml` module for YAML parsing

#### Added Configuration Loading Function
```python
def load_value_zone_config():
    """Load value zone thresholds from config file with fallback defaults."""
    # Returns dict with 'min_score' and 'max_price' keys
    # Falls back to hardcoded defaults if config file missing
    # Handles exceptions gracefully with warning messages
```

#### Removed Hardcoded Thresholds
**Before:**
```python
value_zone_min_score = 365
value_zone_max_price = 550000
```

**After:**
```python
value_zone_config = load_value_zone_config()
value_zone_min_score = value_zone_config['min_score']
value_zone_max_price = value_zone_config['max_price']
```

## Backward Compatibility

The implementation includes robust fallback behavior:

1. **Config File Missing:** Uses hardcoded defaults (365 and 550000)
2. **Config File Invalid:** Catches YAML parsing errors, prints warning, uses defaults
3. **Missing Config Keys:** Uses `.get()` with fallback defaults
4. **Graceful Degradation:** Script continues functioning even if config unavailable

## Usage

### Viewing Current Configuration
```bash
cat config/scoring_weights.yaml
```

### Modifying Value Zone Thresholds
Edit `config/scoring_weights.yaml`:
```yaml
value_zones:
  sweet_spot:
    min_score: 370           # Change min_score from 365
    max_price: 600000        # Change max_price from 550000
```

Next run of `scripts/value_spotter.py` will use the new values.

### Using Different Value Zones
To use the premium zone instead of sweet_spot, modify the config loading in value_spotter.py:
```python
zone_name = 'premium'  # or 'sweet_spot'
zone = config['value_zones'][zone_name]
```

## Testing

### Verify Config Loading
```bash
python -c "
import yaml
from pathlib import Path

config_path = Path('config/scoring_weights.yaml')
with open(config_path) as f:
    config = yaml.safe_load(f)

zone = config['value_zones']['sweet_spot']
print(f'Min Score: {zone[\"min_score\"]}')
print(f'Max Price: {zone[\"max_price\"]}')
"
```

### Verify Script Loading
```bash
# This will show the loaded values and any warnings
python scripts/value_spotter.py
```

## Files Modified

1. **Created:** `config/scoring_weights.yaml` - New configuration file
2. **Modified:** `scripts/value_spotter.py` - Added config loading, removed hardcoded values

## Configuration Structure

### Full Path Reference
- **min_score:** `config/scoring_weights.yaml` → `value_zones` → `sweet_spot` → `min_score`
- **max_price:** `config/scoring_weights.yaml` → `value_zones` → `sweet_spot` → `max_price`

### Example Values Currently Set
- `min_score: 365` - Properties scoring above this are considered "high value"
- `max_price: 550000` - Properties below this price are considered "affordable"

## Benefits

1. **Configurability:** Change thresholds without modifying Python code
2. **Maintainability:** Single source of truth for configuration
3. **Documentation:** Comments in YAML explain each threshold
4. **Extensibility:** Easy to add new zones (premium, economy, etc.)
5. **Robustness:** Fallback defaults ensure script works even if config missing
6. **Future-Proof:** Foundation for other configuration needs

## Migration Notes

- No code changes required for end users
- Existing functionality remains unchanged
- Default values remain the same (365 and 550000)
- Script will continue to work with or without the config file
