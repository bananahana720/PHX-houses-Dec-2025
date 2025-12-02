"""
PHX Home Value Spotter: Interactive scatter plot to identify underpriced gems.

Visualizes the relationship between total_score and price, with lot size as color gradient.
Highlights the "Value Zone" (bottom-right quadrant: high score, low price).
"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import yaml

# Load data
project_root = Path(__file__).parent.parent
csv_path = project_root / "data" / "phx_homes_ranked.csv"
json_path = project_root / "data" / "enrichment_data.json"
config_path = project_root / "config" / "scoring_weights.yaml"

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

# Read CSV
df = pd.read_csv(csv_path)

# Read JSON enrichment data
with open(json_path) as f:
    enrichment_data = json.load(f)

# Create lookup dictionary for lot_sqft
lot_sqft_lookup = {entry['full_address']: entry['lot_sqft'] for entry in enrichment_data}

# Add lot_sqft to dataframe
df['lot_sqft_enriched'] = df['full_address'].map(lot_sqft_lookup)

# Use lot_sqft from enrichment if available, otherwise from CSV
# Replace empty strings with NaN before fillna (CSV may have empty strings instead of NaN)
df['lot_sqft'] = df['lot_sqft'].replace('', pd.NA)
df['lot_sqft_final'] = df['lot_sqft_enriched'].fillna(df['lot_sqft'])

# Calculate score/price ratio (points per $1000) for value ranking
# Only for PASSing properties
df['value_ratio'] = df.apply(
    lambda row: row['total_score'] / (row['price'] / 1000) if row['kill_switch_passed'] == 'PASS' else 0,
    axis=1
)

# Calculate medians
median_score = df['total_score'].median()
median_price = df['price'].median()

# Note: Value zone boundaries loaded from config above
# Identify properties in value zone (PASS only)
df['in_value_zone'] = (
    (df['total_score'] > value_zone_min_score) &
    (df['price'] < value_zone_max_price) &
    (df['kill_switch_passed'] == 'PASS')
)

# Get top 3 value picks (highest value_ratio among PASSing properties)
top_value_picks = df[df['kill_switch_passed'] == 'PASS'].nlargest(3, 'value_ratio')

# Separate PASS and FAIL properties
df_pass = df[df['kill_switch_passed'] == 'PASS']
df_fail = df[df['kill_switch_passed'] == 'FAIL']

# Create figure
fig = go.Figure()

# Add quadrant shading (value zone - bottom-right)
fig.add_shape(
    type="rect",
    x0=value_zone_min_score, x1=df['total_score'].max() + 10,
    y0=df['price'].min() - 10000, y1=value_zone_max_price,
    fillcolor="lightgreen",
    opacity=0.2,
    layer="below",
    line_width=0,
)

# Add median lines
fig.add_hline(
    y=median_price,
    line_dash="dash",
    line_color="gray",
    annotation_text=f"Median Price: ${median_price:,.0f}",
    annotation_position="left"
)
fig.add_vline(
    x=median_score,
    line_dash="dash",
    line_color="gray",
    annotation_text=f"Median Score: {median_score:.1f}",
    annotation_position="top"
)

# Add PASS properties (circles)
fig.add_trace(go.Scatter(
    x=df_pass['total_score'],
    y=df_pass['price'],
    mode='markers',
    name='PASS',
    marker={
        "size": 12,
        "color": df_pass['lot_sqft_final'],
        "colorscale": 'Blues',
        "colorbar": {
            "title": "Lot Size<br>(sqft)",
            "x": 1.15
        },
        "line": {"width": 1, "color": 'DarkSlateGrey'},
        "symbol": 'circle',
        "cmin": 7000,  # Min lot size for color scale
        "cmax": 15000,  # Max lot size for color scale
    },
    text=df_pass.apply(lambda row: (
        f"{row['full_address']}<br>"
        f"Score: {row['total_score']:.1f}<br>"
        f"Price: {row['price']}<br>"
        f"Lot: {row['lot_sqft_final']:,} sqft<br>"
        f"Value Ratio: {row['value_ratio']:.2f} pts/$1k"
    ), axis=1),
    hovertemplate='%{text}<extra></extra>',
))

# Add FAIL properties (X marks)
fig.add_trace(go.Scatter(
    x=df_fail['total_score'],
    y=df_fail['price'],
    mode='markers',
    name='FAIL',
    marker={
        "size": 12,
        "color": df_fail['lot_sqft_final'],
        "colorscale": 'Reds',
        "showscale": False,
        "line": {"width": 1, "color": 'DarkRed'},
        "symbol": 'x',
    },
    text=df_fail.apply(lambda row: (
        f"{row['full_address']}<br>"
        f"Score: {row['total_score']:.1f}<br>"
        f"Price: {row['price']}<br>"
        f"Lot: {row['lot_sqft_final']:,} sqft<br>"
        f"Kill Switch: {row['kill_switch_passed']}"
    ), axis=1),
    hovertemplate='%{text}<extra></extra>',
))

# Highlight top 3 value picks with annotations
for idx, row in top_value_picks.iterrows():
    fig.add_annotation(
        x=row['total_score'],
        y=row['price'],
        text=f"★ Top {top_value_picks.index.get_loc(idx) + 1}",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="gold",
        ax=40,
        ay=-40,
        font={"color": "gold", "size": 12, "family": "Arial Black"},
        bgcolor="rgba(255,215,0,0.3)",
        bordercolor="gold",
        borderwidth=2,
    )

# Add value zone label
fig.add_annotation(
    x=value_zone_min_score + 10,
    y=value_zone_max_price - 20000,
    text="VALUE ZONE<br>(High Score, Low Price)",
    showarrow=False,
    font={"size": 14, "color": "darkgreen", "family": "Arial Black"},
    bgcolor="rgba(144,238,144,0.5)",
    bordercolor="darkgreen",
    borderwidth=2,
)

# Update layout
fig.update_layout(
    title={
        "text": "PHX Home Value Spotter: Score vs Price",
        "font": {"size": 20, "family": "Arial Black"},
        "x": 0.5,
        "xanchor": 'center'
    },
    xaxis_title="Total Score (Max 600 points)",
    yaxis_title="Price ($)",
    hovermode='closest',
    width=1200,
    height=800,
    showlegend=True,
    legend={
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255,255,255,0.8)",
        "bordercolor": "black",
        "borderwidth": 1
    },
    plot_bgcolor='white',
    yaxis={
        "gridcolor": 'lightgray',
        "tickformat": '$,.0f',
    },
    xaxis={
        "gridcolor": 'lightgray',
    }
)

# Save as HTML (interactive)
output_html = Path(__file__).parent.parent / "reports" / "html" / "value_spotter.html"
output_html.parent.mkdir(parents=True, exist_ok=True)
fig.write_html(str(output_html))
print(f"[OK] Saved interactive plot: {output_html}")

# Save as PNG (static)
output_png = Path(__file__).parent.parent / "reports" / "html" / "value_spotter.png"
try:
    fig.write_image(str(output_png), width=1200, height=800)
    print(f"[OK] Saved static plot: {output_png}")
except Exception as e:
    print(f"[WARNING] Could not save PNG: {e}")
    print("[INFO] HTML version saved successfully. PNG export requires kaleido.")

# Calculate quadrant statistics
quadrants = {
    'Top-Left (Low Score, High Price)': ((df['total_score'] <= median_score) & (df['price'] > median_price)),
    'Top-Right (High Score, High Price)': ((df['total_score'] > median_score) & (df['price'] > median_price)),
    'Bottom-Left (Low Score, Low Price)': ((df['total_score'] <= median_score) & (df['price'] <= median_price)),
    'Bottom-Right (High Score, Low Price)': ((df['total_score'] > median_score) & (df['price'] <= median_price)),
}

print("\n" + "="*70)
print("QUADRANT ANALYSIS (by median lines)")
print("="*70)
for quadrant_name, mask in quadrants.items():
    count = mask.sum()
    print(f"{quadrant_name}: {count} properties")

print("\n" + "="*70)
print("VALUE ZONE ANALYSIS (Score > 365, Price < $550k, PASS only)")
print("="*70)
value_zone_count = df['in_value_zone'].sum()
print(f"Properties in Value Zone: {value_zone_count}")

print("\n" + "="*70)
print("TOP 3 VALUE PICKS (Highest Score/Price Ratio, PASS only)")
print("="*70)
for i, (_idx, row) in enumerate(top_value_picks.iterrows(), 1):
    print(f"\n{i}. {row['full_address']}")
    print(f"   Score: {row['total_score']:.1f} | Price: {row['price']}")
    print(f"   Lot Size: {row['lot_sqft_final']:,} sqft")
    print(f"   Value Ratio: {row['value_ratio']:.3f} points per $1,000")
    print(f"   Beds/Baths: {row['beds']}/{row['baths']}")

# File size reporting
html_size = output_html.stat().st_size

print("\n" + "="*70)
print("OUTPUT FILE SIZES")
print("="*70)
print(f"value_spotter.html: {html_size:,} bytes ({html_size/1024:.1f} KB)")
if output_png.exists():
    png_size = output_png.stat().st_size
    print(f"value_spotter.png: {png_size:,} bytes ({png_size/1024:.1f} KB)")
else:
    print("value_spotter.png: Not generated (kaleido issue)")
print("="*70)
