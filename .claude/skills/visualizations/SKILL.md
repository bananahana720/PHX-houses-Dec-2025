---
name: visualizations
description: Generate property analysis visualizations including radar charts, value spotter scatter plots, and comparison charts. Use for visual property comparison, identifying value opportunities, or presentation graphics.
allowed-tools: Read, Bash(python:*)
---

# Property Visualization Skill

Expert at creating visual analysis tools for property comparison and value identification.

## Available Visualizations

| Script | Output | Purpose |
|--------|--------|---------|
| `value_spotter.py` | value_spotter.html | Interactive score vs price scatter |
| `radar_charts.py` | radar_{address}.png | Property score breakdown |
| `golden_zone_map.py` | golden_zone.html | Geographic analysis |

## Value Spotter

### Purpose

Interactive scatter plot showing score vs price relationship to identify underpriced properties.

### CLI

```bash
python scripts/value_spotter.py
```

### Output

- `scripts/value_spotter.html` - Interactive Plotly chart
- `scripts/value_spotter.png` - Static image (requires kaleido)

### Features

- X-axis: Total Score (0-600)
- Y-axis: Price
- Color: Lot size gradient
- Markers: Circle (PASS), X (FAIL)
- Quadrants: Median lines divide chart
- **Value Zone**: Bottom-right (high score, low price)

### Key Metrics

```python
# Value ratio calculation
value_ratio = total_score / (price / 1000)  # Points per $1k

# Higher ratio = better value
# Example: 400 pts / $450k = 0.89 pts/$1k
```

### Quadrant Analysis

```
                    |
  OVERPRICED        |  PREMIUM
  (Low Score,       |  (High Score,
   High Price)      |   High Price)
                    |
--------------------+--------------------
                    |
  BUDGET            |  VALUE ZONE ★
  (Low Score,       |  (High Score,
   Low Price)       |   Low Price)
                    |
```

### Value Zone Definition

```python
VALUE_ZONE_CRITERIA = {
    "min_score": 365,      # Above 60%
    "max_price": 550000,   # Below $550k
    "kill_switch": "PASS"  # Must pass
}
```

## Radar Charts

### Purpose

Visual breakdown of score components showing strengths/weaknesses at a glance.

### CLI

```bash
python scripts/radar_charts.py
python scripts/radar_charts.py --address "123 Main St, Phoenix, AZ"
```

### Chart Structure

```
        Schools
           ▲
          /|\
         / | \
   Parks/  |  \Quietness
       /   |   \
      /    |    \
     ▼─────┼─────▶ Safety
      \    |    /
       \   |   /
  Orient\  |  /Grocery
          \|/
           ▼
```

### Categories Displayed

| Section | Categories |
|---------|------------|
| A: Location | Schools, Quietness, Safety, Grocery, Parks, Orientation |
| B: Systems | Roof, Backyard, Plumbing, Pool |
| C: Interior | Kitchen, Master, Light, Ceilings, Fireplace, Laundry |

### Normalization

```python
def normalize_score(raw_score: float, max_score: float) -> float:
    """Normalize to 0-10 scale for radar chart."""
    return (raw_score / max_score) * 10
```

## Golden Zone Map

### Purpose

Geographic visualization of property locations with tier coloring.

### CLI

```bash
python scripts/golden_zone_map.py
```

### Features

- Interactive Folium map
- Property markers colored by tier:
  - Green: UNICORN
  - Blue: CONTENDER
  - Gray: PASS
  - Red: FAILED
- Popup with property details
- Overlay options: Schools, Crime, Traffic

## Comparison Charts

### Side-by-Side Comparison

```python
def create_comparison_chart(properties: list[dict]) -> go.Figure:
    """Create side-by-side bar chart for property comparison."""
    import plotly.graph_objects as go

    categories = ["Location", "Systems", "Interior"]

    fig = go.Figure()
    for prop in properties:
        fig.add_trace(go.Bar(
            name=prop["address"][:20] + "...",
            x=categories,
            y=[
                prop["score_location"],
                prop["score_lot_systems"],
                prop["score_interior"]
            ]
        ))

    fig.update_layout(
        title="Property Score Comparison",
        barmode="group",
        yaxis_title="Points"
    )
    return fig
```

### Price vs Score Trend

```python
def create_price_score_trend(df: pd.DataFrame) -> go.Figure:
    """Show price vs score with trendline."""
    import plotly.express as px

    fig = px.scatter(
        df,
        x="total_score",
        y="price",
        color="tier",
        trendline="ols",
        hover_data=["full_address", "beds", "baths"]
    )
    return fig
```

## Data Requirements

### For Value Spotter

```python
required_columns = [
    "full_address",
    "price",
    "total_score",
    "kill_switch_passed",
    "lot_sqft",  # For color gradient
    "city",
    "beds",
    "baths"
]

# Source: data/phx_homes_ranked.csv
```

### For Radar Charts

```python
required_fields = {
    # Raw 1-10 scores from enrichment
    "school_rating",
    "safety_neighborhood_score",
    "parks_walkability_score",
    "kitchen_layout_score",
    "master_suite_score",
    "natural_light_score",
    "high_ceilings_score",
    "fireplace_score",
    "laundry_area_score",
    "aesthetics_score",
    # Derived scores
    "orientation",  # Convert to 1-10
    "distance_to_grocery_miles",  # Convert to 1-10
    "distance_to_highway_miles",  # Convert to 1-10
    "roof_age",  # Convert to 1-10
}

# Source: data/enrichment_data.json
```

## Custom Visualization Code

### Plotly Setup

```python
import plotly.graph_objects as go
import plotly.express as px

# PHX Houses color scheme
COLORS = {
    "unicorn": "#2ecc71",    # Green
    "contender": "#3498db",  # Blue
    "pass": "#95a5a6",       # Gray
    "failed": "#e74c3c",     # Red
    "value_zone": "#27ae60", # Dark green
}
```

### Save Outputs

```python
def save_visualization(fig: go.Figure, name: str):
    """Save as both HTML and PNG."""
    html_path = f"scripts/{name}.html"
    png_path = f"scripts/{name}.png"

    fig.write_html(html_path)
    print(f"Saved: {html_path}")

    try:
        fig.write_image(png_path, width=1200, height=800)
        print(f"Saved: {png_path}")
    except Exception as e:
        print(f"PNG export failed (requires kaleido): {e}")
```

## Integration with Analysis

### After analyze.py

```python
# Typical workflow
subprocess.run(["python", "scripts/analyze.py"])
subprocess.run(["python", "scripts/value_spotter.py"])
subprocess.run(["python", "scripts/radar_charts.py"])
```

### In Deal Sheets

```markdown
## VISUAL ANALYSIS

![Radar Chart](../scripts/radar_123_main_st.png)

See [Interactive Value Comparison](../scripts/value_spotter.html)
```

## Best Practices

1. **Run after scoring** - Requires ranked CSV to exist
2. **Interactive preferred** - HTML files for exploration
3. **PNG for reports** - Static images for deal sheets
4. **Consistent colors** - Use COLORS dict for tier consistency
5. **Include context** - Median lines, value zones labeled
