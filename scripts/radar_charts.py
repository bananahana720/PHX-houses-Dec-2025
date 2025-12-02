"""
Radar Chart Visualization for Top 3 Passing Phoenix Properties

Generates comparative radar charts showing 5-dimensional property analysis:
- Price Value: Lower price = higher score
- Location: Composite location metrics
- Lot & Systems: Property infrastructure quality
- Interior: Interior features and aesthetics
- Schools: School district ratings
"""

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
CSV_FILE = PROJECT_ROOT / "data" / "phx_homes_ranked.csv"
JSON_FILE = PROJECT_ROOT / "data" / "enrichment_data.json"
OUTPUT_DIR = PROJECT_ROOT / "reports" / "html"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_HTML = OUTPUT_DIR / "radar_comparison.html"
OUTPUT_PNG = OUTPUT_DIR / "radar_comparison.png"

def load_data():
    """Load ranked CSV and enrichment data"""
    df = pd.read_csv(CSV_FILE)

    with open(JSON_FILE) as f:
        enrichment = json.load(f)

    return df, enrichment

def get_top_3_passing(df):
    """Get top 3 properties that passed kill switches"""
    passing = df[df['kill_switch_passed'] == 'PASS'].copy()
    top_3 = passing.nsmallest(3, 'rank')  # Lowest rank = best
    return top_3

def normalize_price_value(prices):
    """
    Normalize price to 0-10 scale (inverted: lower price = higher score)
    Formula: 10 - (price - min_price)/(max_price - min_price)*10
    """
    import pandas as pd
    # Handle Series or list
    if not isinstance(prices, pd.Series):
        prices = pd.Series(prices)

    min_price = prices.min()
    max_price = prices.max()

    if max_price == min_price:
        return [5.0] * len(prices)

    normalized = 10 - ((prices - min_price) / (max_price - min_price)) * 10
    return normalized.tolist()

def calculate_radar_scores(top_3):
    """Calculate 5-axis radar scores normalized to 0-10 scale"""
    scores = []

    # Extract prices for normalization
    prices = top_3['price'].values
    price_values = normalize_price_value(prices)

    for idx, (i, row) in enumerate(top_3.iterrows()):
        # Handle both old (section_*) and new (score_*) column names
        location_score = row.get('score_location', row.get('section_a_score', 0))
        systems_score = row.get('score_lot_systems', row.get('section_b_score', 0))
        interior_score = row.get('score_interior', row.get('section_c_score', 0))

        property_scores = {
            'address': row['full_address'],
            'price': row['price'],
            'total_score': row['total_score'],
            'axes': {
                'Price Value': round(price_values[idx], 2),
                'Location': round((location_score / 230.0) * 10, 2),  # Max 230, scale to 10
                'Lot & Systems': round((systems_score / 180.0) * 10, 2),  # Max 180, scale to 10
                'Interior': round((interior_score / 190.0) * 10, 2),  # Max 190, scale to 10
                'Schools': round(row['school_rating'], 2)  # Already 0-10 scale
            }
        }
        scores.append(property_scores)

    return scores

def create_radar_chart(scores):
    """Create interactive radar chart with 3 overlapping traces"""
    fig = go.Figure()

    # Define colors for each property
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']

    categories = list(scores[0]['axes'].keys())

    # Add trace for each property
    for idx, prop in enumerate(scores):
        values = list(prop['axes'].values())
        # Close the radar by repeating first value
        values_closed = values + [values[0]]
        categories_closed = categories + [categories[0]]

        # Shorten address for legend
        address_parts = prop['address'].split(',')
        short_address = f"{address_parts[0]}, {address_parts[1]}"

        fig.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=categories_closed,
            fill='toself',
            fillcolor=colors[idx],
            opacity=0.25,
            name=f"{short_address} (${prop['price']:,.0f})",
            line=dict(color=colors[idx], width=2),
            marker=dict(size=8)
        ))

    # Update layout
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                showticklabels=True,
                ticks='outside',
                tickvals=[0, 2, 4, 6, 8, 10],
                tickfont=dict(size=10)
            ),
            angularaxis=dict(
                tickfont=dict(size=12, weight='bold')
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=1.05,
            font=dict(size=11)
        ),
        title=dict(
            text="Top 3 Phoenix Properties - Radar Comparison<br><sub>All scores normalized to 0-10 scale</sub>",
            x=0.5,
            xanchor='center',
            font=dict(size=18, weight='bold')
        ),
        width=1000,
        height=700,
        margin=dict(l=100, r=200, t=100, b=150)
    )

    return fig

def analyze_properties(scores):
    """Generate textual analysis of property trade-offs"""
    analysis = []

    # Calculate balance (std deviation - lower is more balanced)
    for prop in scores:
        values = list(prop['axes'].values())
        std_dev = pd.Series(values).std()
        prop['balance'] = std_dev

    # Find most balanced
    most_balanced = min(scores, key=lambda x: x['balance'])
    analysis.append(f"**Most Balanced**: {most_balanced['address']} (std dev: {most_balanced['balance']:.2f})")

    # Find location winner
    location_winner = max(scores, key=lambda x: x['axes']['Location'])
    analysis.append(f"**Location Winner**: {location_winner['address']} ({location_winner['axes']['Location']:.2f}/10)")

    # Find value leader (best price-to-score ratio)
    for prop in scores:
        prop['value_ratio'] = prop['total_score'] / (prop['price'] / 1000)  # Score per $1000
    value_leader = max(scores, key=lambda x: x['value_ratio'])
    analysis.append(f"**Value Leader**: {value_leader['address']} ({value_leader['value_ratio']:.3f} pts/$1k)")

    # Find schools winner
    schools_winner = max(scores, key=lambda x: x['axes']['Schools'])
    analysis.append(f"**Schools Winner**: {schools_winner['address']} ({schools_winner['axes']['Schools']:.1f}/10)")

    # Find systems winner
    systems_winner = max(scores, key=lambda x: x['axes']['Lot & Systems'])
    analysis.append(f"**Lot & Systems Winner**: {systems_winner['address']} ({systems_winner['axes']['Lot & Systems']:.2f}/10)")

    return "\n".join(analysis)

def add_analysis_box(fig, analysis_text):
    """Add analysis annotation box below chart"""
    fig.add_annotation(
        text=analysis_text.replace('\n', '<br>'),
        xref="paper", yref="paper",
        x=0.5, y=-0.15,
        xanchor='center', yanchor='top',
        showarrow=False,
        font=dict(size=11, family="monospace"),
        align="left",
        bordercolor="black",
        borderwidth=1,
        borderpad=10,
        bgcolor="lightyellow",
        opacity=0.9
    )

def print_detailed_scores(scores):
    """Print detailed score breakdown to console"""
    print("\n" + "="*80)
    print("TOP 3 PASSING PROPERTIES - RADAR SCORES (0-10 Scale)")
    print("="*80 + "\n")

    for i, prop in enumerate(scores, 1):
        print(f"{i}. {prop['address']}")
        print(f"   Price: ${prop['price']:,.0f} | Total Score: {prop['total_score']:.1f}/600")
        print("   Radar Dimensions:")
        for dim, score in prop['axes'].items():
            bar = '#' * int(score) + '-' * (10 - int(score))
            print(f"     {dim:15s}: {score:5.2f}/10  [{bar}]")
        print(f"   Balance (std dev): {prop['balance']:.2f}")
        print()

    print("="*80 + "\n")

def main():
    """Main execution"""
    print("Loading data...")
    df, enrichment = load_data()

    print("Identifying top 3 passing properties...")
    top_3 = get_top_3_passing(df)

    print("Top 3 Properties:")
    for i, row in top_3.iterrows():
        print(f"  {row['rank']}. {row['full_address']} - Score: {row['total_score']}")

    print("\nCalculating radar scores...")
    scores = calculate_radar_scores(top_3)

    print("Generating analysis...")
    analysis = analyze_properties(scores)

    print_detailed_scores(scores)
    print("\nANALYSIS:")
    print(analysis)

    print("\nCreating radar chart...")
    fig = create_radar_chart(scores)
    add_analysis_box(fig, analysis)

    print(f"Saving interactive HTML to: {OUTPUT_HTML}")
    fig.write_html(str(OUTPUT_HTML))

    try:
        print(f"Saving static PNG to: {OUTPUT_PNG}")
        fig.write_image(str(OUTPUT_PNG), width=1000, height=700)
        print(f"  - Static: {OUTPUT_PNG}")
    except (ValueError, ImportError):
        print("  [SKIP] PNG export unavailable (kaleido not installed)")

    print("\n[SUCCESS] Radar charts generated successfully!")
    print(f"  - Interactive: {OUTPUT_HTML}")

if __name__ == "__main__":
    main()
