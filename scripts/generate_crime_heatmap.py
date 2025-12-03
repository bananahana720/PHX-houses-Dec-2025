#!/usr/bin/env python3
"""
Crime Index Heatmap Generator for Phoenix Home Buying Analysis

Creates an interactive Folium map showing properties colored by crime safety index:
- Red (dangerous): Crime index < 30
- Orange (below average): Crime index 30-50
- Yellow (average): Crime index 50-70
- Green (safe): Crime index >= 70

Groups properties by ZIP code and displays crime statistics in popups.
Note: Higher crime index = SAFER (100 = safest, 0 = most dangerous)
"""

import argparse
import json
from pathlib import Path

import folium
from folium import CircleMarker


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


def get_zip_code(prop: dict) -> str | None:
    """Extract ZIP code from property data."""
    import re

    # Try direct fields first
    zip_code = prop.get("zip_code") or prop.get("zip")
    if zip_code:
        return str(zip_code)

    # Extract from full_address (format: "address, city, AZ zipcode")
    address = prop.get("full_address", "")
    match = re.search(r'\b(\d{5})\b', address)
    if match:
        return match.group(1)

    return None


def calculate_composite_crime_index(violent: float | None, property_crime: float | None) -> float:
    """Calculate composite crime safety index.

    Weights: 60% violent crime, 40% property crime
    Returns: 0-100 where 100 = safest, 0 = most dangerous
    """
    if violent is None and property_crime is None:
        return 50.0  # Unknown = neutral

    if violent is None:
        violent = 50.0
    if property_crime is None:
        property_crime = 50.0

    return (violent * 0.6) + (property_crime * 0.4)


def get_crime_color(composite_index: float) -> str:
    """Get color based on composite crime index."""
    if composite_index >= 70:
        return "green"
    elif composite_index >= 50:
        return "yellow"
    elif composite_index >= 30:
        return "orange"
    else:
        return "red"


def get_crime_risk_level(composite_index: float) -> str:
    """Get risk level label based on composite crime index."""
    if composite_index >= 70:
        return "SAFE"
    elif composite_index >= 50:
        return "AVERAGE"
    elif composite_index >= 30:
        return "BELOW AVERAGE"
    else:
        return "DANGEROUS"


def generate_crime_heatmap(enrichment_path: Path, output_path: Path, filter_zip: str | None = None, filter_tier: str | None = None):
    """Generate crime index heatmap visualization."""

    print("Loading enrichment data...")
    enrichment = load_enrichment_data(enrichment_path)

    # Filter if requested
    if filter_zip:
        enrichment = [p for p in enrichment if get_zip_code(p) == filter_zip]
        print(f"  Filtered to ZIP {filter_zip}: {len(enrichment)} properties")

    if filter_tier:
        enrichment = [p for p in enrichment if p.get("tier", "").upper() == filter_tier.upper()]
        print(f"  Filtered to tier {filter_tier}: {len(enrichment)} properties")

    # Group by ZIP code
    zip_data = {}
    for prop in enrichment:
        zip_code = get_zip_code(prop)
        if not zip_code:
            continue

        if zip_code not in zip_data:
            zip_data[zip_code] = {
                "properties": [],
                "violent_index": None,
                "property_index": None,
            }

        zip_data[zip_code]["properties"].append(prop)

        # Use first crime index found for ZIP
        if zip_data[zip_code]["violent_index"] is None:
            violent = prop.get("violent_crime_index")
            prop_crime = prop.get("property_crime_index")
            if violent is not None or prop_crime is not None:
                zip_data[zip_code]["violent_index"] = violent
                zip_data[zip_code]["property_index"] = prop_crime

    # Create map
    phoenix_center = [33.4484, -112.0740]
    m = folium.Map(location=phoenix_center, zoom_start=10, tiles='OpenStreetMap')

    # Track statistics
    risk_counts = {"SAFE": 0, "AVERAGE": 0, "BELOW AVERAGE": 0, "DANGEROUS": 0, "UNKNOWN": 0}
    plotted = 0
    skipped = 0

    # Add property markers
    for zip_code, data in zip_data.items():
        violent = data["violent_index"]
        property_crime = data["property_index"]

        # Calculate composite index
        composite = calculate_composite_crime_index(violent, property_crime)
        color = get_crime_color(composite)
        risk_level = get_crime_risk_level(composite)

        for prop in data["properties"]:
            coords = get_coordinates(prop)
            if not coords:
                skipped += 1
                continue

            lat, lng = coords
            address = prop.get("full_address", "Unknown Address")

            # Track risk level
            if violent is None and property_crime is None:
                risk_counts["UNKNOWN"] += 1
            else:
                risk_counts[risk_level] += 1

            # Build popup
            popup_html = f"""
            <div style="font-family: Arial; font-size: 12px; width: 300px;">
                <h4 style="margin: 0 0 8px 0; color: {color};">{address}</h4>
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 4px;"><b>ZIP Code:</b></td>
                        <td style="padding: 4px;">{zip_code}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;"><b>Violent Crime Index:</b></td>
                        <td style="padding: 4px;">{violent if violent is not None else 'N/A'}/100</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;"><b>Property Crime Index:</b></td>
                        <td style="padding: 4px;">{property_crime if property_crime is not None else 'N/A'}/100</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;"><b>Composite Index:</b></td>
                        <td style="padding: 4px; font-weight: bold;">{composite:.0f}/100</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;"><b>Risk Level:</b></td>
                        <td style="padding: 4px; font-weight: bold; color: {color};">{risk_level}</td>
                    </tr>
                    <tr style="border-top: 1px solid #ccc;">
                        <td style="padding: 4px;"><b>Price:</b></td>
                        <td style="padding: 4px;">${prop.get('price', 'N/A')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;"><b>Tier:</b></td>
                        <td style="padding: 4px;">{prop.get('tier', 'N/A')}</td>
                    </tr>
                </table>
                <div style="margin-top: 8px; font-size: 11px; color: #666;">
                    Higher index = safer (100 = safest)
                </div>
            </div>
            """

            CircleMarker(
                location=[lat, lng],
                radius=10,
                color='black',
                weight=1,
                fill=True,
                fillColor=color,
                fillOpacity=0.7,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=f"{address}<br>Crime Index: {composite:.0f}/100 ({risk_level})"
            ).add_to(m)

            plotted += 1

    # Add legend
    legend_html = '''
    <div style="position: fixed; bottom: 50px; left: 50px;
                background: white; padding: 15px; border: 2px solid gray;
                border-radius: 8px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                font-family: Arial; z-index: 9999;">
        <h4 style="margin: 0 0 10px 0; font-size: 16px;">Crime Safety Index</h4>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: green; border: 1px solid black; border-radius: 50%;
                         vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">SAFE (70-100)</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: yellow; border: 1px solid black; border-radius: 50%;
                         vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">AVERAGE (50-70)</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: orange; border: 1px solid black; border-radius: 50%;
                         vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">BELOW AVG (30-50)</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: red; border: 1px solid black; border-radius: 50%;
                         vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">DANGEROUS (<30)</span>
        </div>
        <hr style="margin: 10px 0; border: none; border-top: 1px solid #ccc;">
        <div style="font-size: 11px; color: #666;">
            Higher = Safer (100 = safest)
        </div>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save map
    output_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(output_path))

    # Print summary
    print(f"\nCrime heatmap generated: {output_path}")
    print(f"  Properties plotted: {plotted}")
    print(f"  Properties skipped (no coords): {skipped}")
    print("\nRisk level distribution:")
    for level in ["SAFE", "AVERAGE", "BELOW AVERAGE", "DANGEROUS", "UNKNOWN"]:
        if risk_counts[level] > 0:
            print(f"  {level}: {risk_counts[level]}")


def main():
    parser = argparse.ArgumentParser(description="Generate crime index heatmap")
    parser.add_argument("--zip", help="Filter to specific ZIP code")
    parser.add_argument("--tier", help="Filter to specific tier (UNICORN, CONTENDER, PASS)")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    enrichment_path = project_root / "data" / "enrichment_data.json"
    output_path = project_root / "reports" / "html" / "crime_heatmap.html"

    try:
        generate_crime_heatmap(enrichment_path, output_path, args.zip, args.tier)
        print(f"\nOpen {output_path} in your browser to view the interactive map!")
    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
