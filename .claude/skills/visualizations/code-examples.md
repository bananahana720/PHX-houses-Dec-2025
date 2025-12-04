# Visualization Code Examples

This reference file contains detailed code examples for property visualizations.

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
