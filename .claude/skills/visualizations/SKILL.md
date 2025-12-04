---
name: visualizations
description: Generate property analysis visualizations including radar charts, value spotter scatter plots, golden zone maps, and comparison charts. Use for visual property comparison, identifying value opportunities, generating presentation graphics, or creating deal sheet visuals.
allowed-tools: Read, Bash(python:*)
---

# Property Visualization Skill

Create visual analysis tools for property comparison and value identification.

## Available Visualizations

| Script | Output | Purpose |
|--------|--------|---------|
| `value_spotter.py` | value_spotter.html | Interactive score vs price scatter |
| `radar_charts.py` | radar_{address}.png | Property score breakdown |
| `golden_zone_map.py` | golden_zone.html | Geographic tier visualization |

## CLI Usage

```bash
python scripts/value_spotter.py
python scripts/radar_charts.py
python scripts/radar_charts.py --address "123 Main St, Phoenix, AZ"
python scripts/golden_zone_map.py
```

## Value Spotter

Interactive scatter plot: score vs price to identify underpriced properties.

- X-axis: Total Score (0-600)
- Y-axis: Price
- Color: Lot size gradient
- Markers: Circle (PASS), X (FAIL)
- **Value Zone**: Bottom-right (high score, low price)

```python
value_ratio = total_score / (price / 1000)  # Points per $1k
```

## Radar Charts

Visual breakdown of score components showing strengths/weaknesses.

| Section | Categories |
|---------|------------|
| A: Location | Schools, Quietness, Safety, Grocery, Parks, Orientation |
| B: Systems | Roof, Backyard, Plumbing, Pool |
| C: Interior | Kitchen, Master, Light, Ceilings, Fireplace, Laundry |

## Color Scheme

```python
COLORS = {
    "unicorn": "#2ecc71",    # Green
    "contender": "#3498db",  # Blue
    "pass": "#95a5a6",       # Gray
    "failed": "#e74c3c",     # Red
}
```

## Reference Files

| File | Content |
|------|---------|
| `code-examples.md` | Comparison chart code, Plotly setup |
| `data-requirements.md` | Required columns for each visualization |

**Load detail:** `Read .claude/skills/visualizations/code-examples.md`

## Best Practices

1. Run after scoring - requires ranked CSV
2. Interactive HTML for exploration
3. PNG for reports/deal sheets
4. Use consistent color scheme
