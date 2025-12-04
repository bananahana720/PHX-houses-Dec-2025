# Configuration Files

This directory contains all configuration files for the PHX Home Analysis project.

## Files Overview

### buyer_criteria.yaml
Kill-switch filtering criteria for property evaluation.

**Contains:**
- Hard criteria (instant fail): HOA, min beds, min baths
- Soft criteria (weighted): Sewer type, year built, garage spaces, lot size
- Severity thresholds for pass/warning/fail verdicts

**Used by:** Kill-switch evaluation pipeline

### scoring_weights.yaml
Scoring system configuration and value zone definitions.

**Contains:**
- **value_zones:** Score/price zones for identifying value opportunities
  - sweet_spot: High-quality properties at affordable prices (score > 365, price < $550k)
  - premium: Top-tier properties (score > 480)
- **section_weights:** Point allocation for 605-point scoring system
  - Location (250 pts), Systems (175 pts), Interior (180 pts)
- **tier_thresholds:** Property classification tiers
- **defaults:** Fallback values for backward compatibility

**Used by:**
- value_spotter.py (value zones)
- scoring system (point allocation)
- property tier classification

### proxies.txt
List of proxy servers for web scraping (if needed).

**Format:** One proxy per line (IP:PORT)

**Used by:** Image extraction and listing browser scripts

## Quick Reference

### How to Update Thresholds

#### Value Zone Thresholds
Edit `scoring_weights.yaml`:
```yaml
value_zones:
  sweet_spot:
    min_score: 365       # Change this for minimum score threshold
    max_price: 550000    # Change this for maximum price threshold
```

Then run:
```bash
python scripts/value_spotter.py
```

#### Kill Switch Criteria
Edit `buyer_criteria.yaml`:
```yaml
hard_criteria:
  hoa_fee: 0             # Must be 0 (no HOA allowed)
  min_beds: 4            # Minimum bedrooms
  min_baths: 2           # Minimum bathrooms

soft_criteria:
  sewer_type:
    required: "city"     # Must be city sewer
    severity: 2.5
  # ... more criteria
```

Then run:
```bash
python scripts/phx_home_analyzer.py
```

## Configuration Hierarchy

1. **Default Values** (hardcoded in Python) - Ultimate fallback
2. **YAML Configuration** (config files) - Primary source
3. **Runtime Overrides** (command-line args) - Highest priority

## Adding New Configuration

1. Add new section to appropriate YAML file
2. Update Python code to load from config using `yaml.safe_load()`
3. Include fallback defaults for robustness
4. Document the configuration in this README

## File Format

All configuration files use YAML format:
```yaml
# Comments start with hash
key: value
nested:
  sub_key: sub_value
  list:
    - item1
    - item2
```

For syntax help, see: https://yaml.org/
