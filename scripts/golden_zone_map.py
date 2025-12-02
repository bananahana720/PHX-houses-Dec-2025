#!/usr/bin/env python3
"""
Golden Zone Heatmap Generator for Phoenix Home Buying Analysis

Creates an interactive Folium map showing optimal home locations based on:
- Kill switch pass/fail status (green/red markers)
- Total score (marker size)
- Proximity zones for grocery stores (1.5 mile radius)
- Highway buffer zones (1 mile from major highways)
"""

import json

import folium
import pandas as pd
from folium import Circle, CircleMarker

# Configuration
PHOENIX_CENTER = (33.55, -112.05)
ZOOM_LEVEL = 10
GROCERY_RADIUS_MILES = 1.5
HIGHWAY_BUFFER_MILES = 1.0

# Convert miles to meters for circle radius
MILES_TO_METERS = 1609.34
GROCERY_RADIUS_METERS = GROCERY_RADIUS_MILES * MILES_TO_METERS
HIGHWAY_BUFFER_METERS = HIGHWAY_BUFFER_MILES * MILES_TO_METERS

# Major Phoenix highways (approximate coordinates)
HIGHWAYS = {
    'I-17': [
        (33.45, -112.10),
        (33.50, -112.10),
        (33.55, -112.10),
        (33.60, -112.10),
        (33.65, -112.10),
        (33.70, -112.10),
    ],
    'I-10': [
        (33.45, -112.20),
        (33.45, -112.10),
        (33.45, -112.00),
        (33.45, -111.90),
    ],
    'Loop-101': [
        (33.50, -111.95),
        (33.55, -111.90),
        (33.60, -111.90),
        (33.65, -111.95),
        (33.65, -112.00),
        (33.65, -112.10),
        (33.65, -112.20),
        (33.60, -112.25),
    ],
}


def load_data():
    """Load and merge geocoded homes, enrichment data, and ranked scores."""
    from pathlib import Path
    base_dir = Path(__file__).parent.parent

    # Load geocoded coordinates
    with open(base_dir / 'data' / 'geocoded_homes.json') as f:
        geocoded = json.load(f)

    # Load ranked homes with scores
    ranked_df = pd.read_csv(base_dir / 'data' / 'phx_homes_ranked.csv')

    # Create geocoded dataframe
    geo_df = pd.DataFrame(geocoded)

    # Merge on full_address
    merged_df = geo_df.merge(ranked_df, on='full_address', how='inner')

    return merged_df


def create_base_map():
    """Create the base Folium map centered on Phoenix."""
    m = folium.Map(
        location=PHOENIX_CENTER,
        zoom_start=ZOOM_LEVEL,
        tiles='OpenStreetMap'
    )
    return m


def add_property_markers(m, df):
    """Add color-coded property markers to the map."""
    # Create separate feature groups for pass/fail properties
    pass_group = folium.FeatureGroup(name='Properties PASSING Kill Switches', show=True)
    fail_group = folium.FeatureGroup(name='Properties FAILING Kill Switches', show=True)

    for _, row in df.iterrows():
        # Determine marker color based on kill switch status
        passed = row['kill_switch_passed'] == 'PASS'
        color = 'green' if passed else 'red'

        # Scale marker size based on total score (range: 300-400, size: 5-15)
        score = row['total_score']
        radius = 5 + (score - 300) / 10  # Scales from ~5 to ~15
        radius = max(5, min(15, radius))  # Clamp between 5 and 15

        # Format popup information
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; width: 250px;">
            <h4 style="margin-bottom: 8px; color: {'green' if passed else 'red'};">
                {row['full_address']}
            </h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td><b>Price:</b></td>
                    <td>{row['price']}</td>
                </tr>
                <tr>
                    <td><b>Total Score:</b></td>
                    <td>{row['total_score']:.1f} / 600</td>
                </tr>
                <tr>
                    <td><b>Tier:</b></td>
                    <td>{row['tier']}</td>
                </tr>
                <tr>
                    <td><b>Kill Switch:</b></td>
                    <td style="color: {'green' if passed else 'red'}; font-weight: bold;">
                        {row['kill_switch_passed']}
                    </td>
                </tr>
            </table>
            <div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #ccc;">
                <b>Details:</b><br>
                {row['beds']} bed, {row['baths']} bath, {row['sqft']:,.0f} sqft<br>
                School Rating: {row['school_rating']}<br>
                Commute: {row.get('commute_min', 'N/A')} min
            </div>
            {'<div style="margin-top: 4px; color: red; font-size: 11px;"><b>Failed Kill Switches</b></div>' if not passed else ''}
        </div>
        """

        # Create marker
        marker = CircleMarker(
            location=[row['lat'], row['lng']],
            radius=radius,
            popup=folium.Popup(popup_html, max_width=300),
            color='black',
            weight=1,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            tooltip=f"{row['full_address']}<br>Score: {row['total_score']:.1f}"
        )

        # Add to appropriate group
        if passed:
            marker.add_to(pass_group)
        else:
            marker.add_to(fail_group)

    # Add groups to map
    pass_group.add_to(m)
    fail_group.add_to(m)


def add_grocery_proximity_zones(m, df):
    """Add 1.5-mile radius circles around each property (grocery proximity)."""
    grocery_group = folium.FeatureGroup(name='Grocery Proximity Zones (1.5 mi)', show=False)

    for _, row in df.iterrows():
        # Only show for properties that pass kill switches
        if row['kill_switch_passed'] == 'PASS':
            Circle(
                location=[row['lat'], row['lng']],
                radius=GROCERY_RADIUS_METERS,
                color='blue',
                weight=1,
                fill=True,
                fillColor='lightblue',
                fillOpacity=0.1,
                popup=f"1.5 mi radius from {row['full_address']}",
                tooltip=f"Grocery zone: {row['full_address']}"
            ).add_to(grocery_group)

    grocery_group.add_to(m)


def add_highway_buffer_zones(m):
    """Add highway buffer zones (areas within 1 mile of major highways)."""
    highway_group = folium.FeatureGroup(name='Highway Buffer Zones (1 mi)', show=False)

    for highway_name, coords in HIGHWAYS.items():
        for coord in coords:
            Circle(
                location=coord,
                radius=HIGHWAY_BUFFER_METERS,
                color='orange',
                weight=1,
                fill=True,
                fillColor='orange',
                fillOpacity=0.15,
                popup=f"{highway_name} (1 mi buffer)",
                tooltip=f"{highway_name} noise zone"
            ).add_to(highway_group)

    highway_group.add_to(m)


def add_legend(m):
    """Add a color legend to the map."""
    legend_html = '''
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 280px;
        background-color: white;
        border: 2px solid grey;
        z-index: 9999;
        font-size: 14px;
        padding: 10px;
        border-radius: 5px;
        box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
        font-family: Arial, sans-serif;
    ">
        <h4 style="margin-top: 0; margin-bottom: 10px; text-align: center;">
            Golden Zone Legend
        </h4>
        <p style="margin: 5px 0;">
            <span style="color: green; font-size: 20px;">●</span>
            <b>PASS</b> - Meets all kill switches
        </p>
        <p style="margin: 5px 0;">
            <span style="color: red; font-size: 20px;">●</span>
            <b>FAIL</b> - Failed one or more kill switches
        </p>
        <p style="margin: 5px 0; margin-top: 10px; font-size: 12px;">
            <b>Marker Size:</b> Larger = Higher total score
        </p>
        <hr style="margin: 10px 0;">
        <p style="margin: 5px 0; font-size: 12px;">
            <b>Buyer Priorities:</b><br>
            • Schools: 8+ rating<br>
            • Grocery: &lt; 1.5 mi<br>
            • Highway: &gt; 1 mi (quiet)
        </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))


def main():
    """Main execution function."""
    print("Loading data...")
    df = load_data()
    print(f"Loaded {len(df)} geocoded properties")

    # Check for properties that pass kill switches
    pass_count = (df['kill_switch_passed'] == 'PASS').sum()
    fail_count = (df['kill_switch_passed'] == 'FAIL').sum()
    print(f"  - {pass_count} properties PASS kill switches")
    print(f"  - {fail_count} properties FAIL kill switches")

    print("\nCreating base map...")
    m = create_base_map()

    print("Adding property markers...")
    add_property_markers(m, df)

    print("Adding grocery proximity zones...")
    add_grocery_proximity_zones(m, df)

    print("Adding highway buffer zones...")
    add_highway_buffer_zones(m)

    print("Adding legend...")
    add_legend(m)

    # Add layer control for toggling overlays
    folium.LayerControl(collapsed=False).add_to(m)

    # Save map
    from pathlib import Path
    base_dir = Path(__file__).parent.parent
    output_dir = base_dir / 'reports' / 'html'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'golden_zone_map.html'

    print(f"\nSaving map to {output_file}...")
    m.save(str(output_file))

    # Get file size
    import os
    file_size = os.path.getsize(output_file)
    file_size_kb = file_size / 1024

    print("\nSuccess! Map generated:")
    print(f"  - File: {output_file}")
    print(f"  - Size: {file_size_kb:.1f} KB ({file_size:,} bytes)")
    print(f"  - Markers placed: {len(df)}")
    print(f"  - Green markers (PASS): {pass_count}")
    print(f"  - Red markers (FAIL): {fail_count}")
    print(f"\nOpen {output_file} in your browser to view the interactive map!")


if __name__ == '__main__':
    main()
