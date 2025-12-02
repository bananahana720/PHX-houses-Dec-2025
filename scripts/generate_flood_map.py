#!/usr/bin/env python3
"""
Flood Zone Map Generator for Phoenix Home Buying Analysis

Creates an interactive Folium map showing properties colored by flood zone risk:
- Zone X (minimal): Green
- Zone X-Shaded (moderate): Yellow
- Zone A/AE/AH/AO (high): Orange/Red
- Zone VE (coastal): Dark Red
- Unknown: Gray

Displays flood insurance requirements and risk levels in popups.
"""

import argparse
import json
from pathlib import Path

import folium
from folium import CircleMarker

# Flood zone color mapping
ZONE_COLORS = {
    "x": "green",
    "x_minimal": "green",
    "x_shaded": "yellow",
    "x_500yr": "yellow",
    "a": "orange",
    "ae": "red",
    "ah": "orange",
    "ao": "orange",
    "ve": "darkred",
    "v": "darkred",
    "unknown": "gray",
    "none": "gray",
}

ZONE_LABELS = {
    "x": "Zone X (Minimal Risk)",
    "x_minimal": "Zone X (Minimal Risk)",
    "x_shaded": "Zone X-Shaded (Moderate - 500yr)",
    "x_500yr": "Zone X-Shaded (Moderate - 500yr)",
    "a": "Zone A (High Risk - No BFE)",
    "ae": "Zone AE (High Risk + BFE)",
    "ah": "Zone AH (High Risk - Shallow Flooding)",
    "ao": "Zone AO (High Risk - Sheet Flow)",
    "ve": "Zone VE (Coastal High Hazard)",
    "v": "Zone V (Coastal High Hazard)",
    "unknown": "Unknown",
    "none": "Not Determined",
}


def load_enrichment_data(enrichment_path: Path) -> list[dict]:
    """Load property data from enrichment_data.json."""
    if not enrichment_path.exists():
        raise FileNotFoundError(f"Enrichment data not found: {enrichment_path}")

    with open(enrichment_path) as f:
        data = json.load(f)

    return data


def get_coordinates(prop: dict) -> tuple[float, float] | None:
    """Extract coordinates from property data."""
    lat = prop.get("latitude") or prop.get("lat")
    lng = prop.get("longitude") or prop.get("lng")

    if lat is not None and lng is not None:
        return (float(lat), float(lng))

    return None


def normalize_flood_zone(zone: str | None) -> str:
    """Normalize flood zone string for lookup."""
    if not zone:
        return "unknown"

    zone_lower = zone.lower().strip().replace(" ", "_").replace("-", "_")

    # Map common variants
    if zone_lower in ["x", "zone_x", "minimal"]:
        return "x"
    elif zone_lower in ["x_shaded", "x_500yr", "moderate"]:
        return "x_shaded"
    elif zone_lower == "ae":
        return "ae"
    elif zone_lower == "a":
        return "a"
    elif zone_lower == "ah":
        return "ah"
    elif zone_lower == "ao":
        return "ao"
    elif zone_lower in ["ve", "v"]:
        return "ve"

    return zone_lower if zone_lower in ZONE_COLORS else "unknown"


def generate_flood_map(enrichment_path: Path, output_path: Path, filter_zip: str | None = None, filter_tier: str | None = None):
    """Generate flood zone map visualization."""

    print("Loading enrichment data...")
    enrichment = load_enrichment_data(enrichment_path)

    # Filter if requested
    if filter_zip:
        enrichment = [p for p in enrichment if p.get("zip_code") == filter_zip or p.get("zip") == filter_zip]
        print(f"  Filtered to ZIP {filter_zip}: {len(enrichment)} properties")

    if filter_tier:
        enrichment = [p for p in enrichment if p.get("tier", "").upper() == filter_tier.upper()]
        print(f"  Filtered to tier {filter_tier}: {len(enrichment)} properties")

    # Center on Phoenix metro
    phoenix_center = [33.4484, -112.0740]
    m = folium.Map(location=phoenix_center, zoom_start=10, tiles='OpenStreetMap')

    # Track statistics
    zone_counts = {}
    plotted = 0
    skipped = 0

    # Add markers for each property
    for prop in enrichment:
        coords = get_coordinates(prop)
        if not coords:
            skipped += 1
            continue

        lat, lng = coords
        address = prop.get("full_address", "Unknown Address")

        # Get flood zone data
        flood_zone_raw = prop.get("flood_zone", "unknown")
        flood_zone = normalize_flood_zone(flood_zone_raw)
        flood_insurance_required = prop.get("flood_insurance_required", "Unknown")

        # Track counts
        zone_counts[flood_zone] = zone_counts.get(flood_zone, 0) + 1

        # Get color and label
        color = ZONE_COLORS.get(flood_zone, "gray")
        label = ZONE_LABELS.get(flood_zone, flood_zone_raw or "Unknown")

        # Build popup
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; width: 280px;">
            <h4 style="margin: 0 0 8px 0; color: {color};">{address}</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 4px;"><b>Flood Zone:</b></td>
                    <td style="padding: 4px;">{label}</td>
                </tr>
                <tr>
                    <td style="padding: 4px;"><b>Insurance Required:</b></td>
                    <td style="padding: 4px;">{flood_insurance_required}</td>
                </tr>
                <tr>
                    <td style="padding: 4px;"><b>Price:</b></td>
                    <td style="padding: 4px;">${prop.get('price', 'N/A')}</td>
                </tr>
                <tr>
                    <td style="padding: 4px;"><b>Tier:</b></td>
                    <td style="padding: 4px;">{prop.get('tier', 'N/A')}</td>
                </tr>
            </table>
        </div>
        """

        CircleMarker(
            location=[lat, lng],
            radius=8,
            color='black',
            weight=1,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{address}<br>{label}"
        ).add_to(m)

        plotted += 1

    # Add legend
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px;
                background: white; padding: 15px; border: 2px solid gray;
                border-radius: 8px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                font-family: Arial; z-index: 9999;">
        <h4 style="margin: 0 0 10px 0; font-size: 16px;">Flood Zone Risk</h4>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: green; border: 1px solid black; border-radius: 50%;
                         vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Zone X (Minimal)</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: yellow; border: 1px solid black; border-radius: 50%;
                         vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Zone X-Shaded (500yr)</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: orange; border: 1px solid black; border-radius: 50%;
                         vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Zone A/AH/AO (High Risk)</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: red; border: 1px solid black; border-radius: 50%;
                         vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Zone AE (High + BFE)</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: darkred; border: 1px solid black; border-radius: 50%;
                         vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Zone VE (Coastal)</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: gray; border: 1px solid black; border-radius: 50%;
                         vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Unknown</span>
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save map
    output_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(output_path))

    # Print summary
    print(f"\nFlood zone map generated: {output_path}")
    print(f"  Properties plotted: {plotted}")
    print(f"  Properties skipped (no coords): {skipped}")
    print("\nFlood zone distribution:")
    for zone in sorted(zone_counts.keys()):
        label = ZONE_LABELS.get(zone, zone)
        print(f"  {label}: {zone_counts[zone]}")


def main():
    parser = argparse.ArgumentParser(description="Generate flood zone map")
    parser.add_argument("--zip", help="Filter to specific ZIP code")
    parser.add_argument("--tier", help="Filter to specific tier (UNICORN, CONTENDER, PASS)")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    enrichment_path = project_root / "data" / "enrichment_data.json"
    output_path = project_root / "reports" / "html" / "flood_zone_map.html"

    try:
        generate_flood_map(enrichment_path, output_path, args.zip, args.tier)
        print(f"\nOpen {output_path} in your browser to view the interactive map!")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
