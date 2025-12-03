#!/usr/bin/env python3
"""
Generate golden_zone_map.html with current property locations and tiers.
Uses ranked CSV data for scores and enrichment JSON for lat/lon geocoding.

Security: Uses html.escape() for XSS prevention and SRI hashes for CDN integrity.
"""

import csv
import json
import re
from pathlib import Path

# SRI hashes for CDN resources (SHA-384)
LEAFLET_CSS_SRI = "sha384-sHL9NAb7lN7rfvG5lfHpm643Xkcjzp4jFvuavGOndn6pjVqS6ny56CAt3nsEVT4H"
LEAFLET_JS_SRI = "sha384-cxOPjt7s7Iz04uaHJceBmS+qpjv2JkIHNVcuOrM+YHwZOmJGBXI00mdUXEq65HTH"


def extract_address_parts(address: str) -> tuple[str, str]:
    """Extract city and zip from full address."""
    match = re.search(r'([A-Za-z\s]+),\s*AZ\s*(\d{5})', address)
    if match:
        return match.group(1).strip(), match.group(2)
    return "", ""


def load_geocoded_data(geocoded_path: Path) -> dict[str, tuple[float, float]]:
    """Load coordinates from geocoded_homes.json.

    Returns:
        Dictionary mapping lowercase address to (lat, lng) tuple
    """
    if not geocoded_path.exists():
        return {}

    with open(geocoded_path) as f:
        data = json.load(f)

    coords = {}
    for entry in data:
        addr = entry.get("full_address", "").lower()
        lat = entry.get("lat")
        lng = entry.get("lng")
        if addr and lat is not None and lng is not None:
            coords[addr] = (lat, lng)

    return coords


def get_coordinates(address: str, enrichment_data: list, geocoded_lookup: dict) -> tuple[float, float] | None:
    """Look up coordinates from multiple sources.

    Priority:
    1. enrichment_data.json (lat/lng fields)
    2. geocoded_homes.json (via geocoded_lookup)

    Args:
        address: Property address
        enrichment_data: List of property dicts from enrichment_data.json
        geocoded_lookup: Dict from load_geocoded_data()

    Returns:
        (lat, lng) tuple or None if not found
    """
    addr_lower = address.lower()

    # Try enrichment data first (single source of truth after migration)
    for prop in enrichment_data:
        if prop.get('full_address', '').lower() == addr_lower:
            lat = prop.get('lat')
            lng = prop.get('lng')
            if lat is not None and lng is not None:
                return (lat, lng)

    # Fallback to geocoded_homes.json
    if addr_lower in geocoded_lookup:
        return geocoded_lookup[addr_lower]

    return None

def generate_map_html(ranked_csv_path: str, enrichment_json_path: str, output_path: str):
    """Generate the interactive map HTML."""

    project_root = Path(ranked_csv_path).parent.parent
    geocoded_path = project_root / "data" / "geocoded_homes.json"

    # Load enrichment data for coordinates and property data
    with open(enrichment_json_path) as f:
        enrichment_data = json.load(f)

    # Load geocoded data as fallback
    geocoded_lookup = load_geocoded_data(geocoded_path)

    # Read ranked CSV
    properties = []
    seen_addresses = set()
    with open(ranked_csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['full_address']:
                properties.append(row)
                seen_addresses.add(row['full_address'].lower())

    # Add properties from enrichment that might not be in CSV
    for prop in enrichment_data:
        addr = prop.get('full_address', '').lower()
        if addr and addr not in seen_addresses:
            tier = prop.get('tier', 'INCOMPLETE')
            kill_status = 'FAIL' if prop.get('kill_switch_passed') is False else 'UNKNOWN'

            row = {
                'full_address': prop.get('full_address'),
                'price': 'TBD',
                'beds': prop.get('beds', 'N/A'),
                'baths': prop.get('baths', 'N/A'),
                'sqft': 'TBD',
                'lot_sqft': prop.get('lot_sqft', 'N/A'),
                'year_built': prop.get('year_built', 'N/A'),
                'school_rating': prop.get('school_rating', 'N/A'),
                'commute_min': prop.get('commute_minutes', 'N/A'),
                'total_score': prop.get('total_score', 'N/A'),
                'tier': tier,
                'kill_switch_status': kill_status
            }
            properties.append(row)

    print(f"Total properties loaded: {len(properties)}")

    # Build HTML
    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html>')
    html_parts.append('<head>')
    html_parts.append('    <meta charset="UTF-8">')
    html_parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html_parts.append('    <title>Phoenix Golden Zone - Property Map (December 2025)</title>')
    html_parts.append(f'    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css" integrity="{LEAFLET_CSS_SRI}" crossorigin="anonymous" />')
    html_parts.append(f'    <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js" integrity="{LEAFLET_JS_SRI}" crossorigin="anonymous"></script>')
    html_parts.append('    <style>')
    html_parts.append('        html, body { width: 100%; height: 100%; margin: 0; padding: 0; }')
    html_parts.append('        #map { position: absolute; top: 0; bottom: 0; left: 0; right: 0; }')
    html_parts.append('        .legend {')
    html_parts.append('            position: fixed; bottom: 20px; right: 20px;')
    html_parts.append('            background-color: white; padding: 15px; border: 2px solid #ccc;')
    html_parts.append('            border-radius: 5px; font-size: 13px; z-index: 1000;')
    html_parts.append('            box-shadow: 0 0 15px rgba(0,0,0,0.2);')
    html_parts.append('        }')
    html_parts.append('        .legend h4 { margin: 0 0 10px 0; }')
    html_parts.append('        .legend-item { margin: 8px 0; }')
    html_parts.append('        .legend-color { display: inline-block; width: 20px; height: 20px; margin-right: 8px; border-radius: 50%; border: 2px solid black; }')
    html_parts.append('        .timestamp { position: fixed; top: 10px; left: 10px; background: rgba(255,255,255,0.9); padding: 10px 15px; border-radius: 5px; z-index: 1000; font-size: 12px; }')
    html_parts.append('    </style>')
    html_parts.append('</head>')
    html_parts.append('<body>')
    html_parts.append('    <div id="map"></div>')
    html_parts.append('    <div class="timestamp">Updated: December 2025</div>')
    html_parts.append('    <div class="legend">')
    html_parts.append('        <h4>Golden Zone Legend</h4>')
    html_parts.append('        <div class="legend-item"><span class="legend-color" style="background: green;"></span>CONTENDER (340+)</div>')
    html_parts.append('        <div class="legend-item"><span class="legend-color" style="background: #FF9500;"></span>CONTENDER (320-340)</div>')
    html_parts.append('        <div class="legend-item"><span class="legend-color" style="background: orange;"></span>CONTENDER (<320)</div>')
    html_parts.append('        <div class="legend-item"><span class="legend-color" style="background: red;"></span>FAILED Kill Switch</div>')
    html_parts.append('        <hr style="margin: 10px 0;"><p style="margin: 5px 0; font-size: 11px;"><b>23 CONTENDERS</b> | <b>12 FAILED</b><br>Total: 35 properties</p>')
    html_parts.append('    </div>')
    html_parts.append('    <script>')
    html_parts.append('        var map = L.map("map").setView([33.4484, -112.0740], 11);')
    html_parts.append('        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {')
    html_parts.append('            attribution: "&copy; OpenStreetMap contributors",')
    html_parts.append('            maxZoom: 19')
    html_parts.append('        }).addTo(map);')
    html_parts.append('')

    # Helper for XSS prevention
    def esc(value):
        """Escape HTML special characters."""
        import html as html_mod
        return html_mod.escape(str(value)) if value is not None else 'N/A'

    # Add markers for each property
    for prop in properties:
        address = prop['full_address'].strip()
        coords = get_coordinates(address, enrichment_data, geocoded_lookup)

        if not coords:
            print(f"Warning: No coordinates found for {address}")
            continue

        lat, lon = coords
        price = prop.get('price', 'N/A')
        tier = prop.get('tier', 'N/A')
        status = prop.get('kill_switch_status', 'UNKNOWN')

        # Determine color based on tier and score
        if status == 'FAIL':
            color = 'red'
            radius = 8
        else:
            try:
                score = float(prop.get('total_score', 0))
                if score >= 340:
                    color = 'green'
                    radius = 12
                elif score >= 320:
                    color = '#FF9500'
                    radius = 10
                else:
                    color = 'orange'
                    radius = 9
            except Exception:
                color = 'gray'
                radius = 8

        # Build popup HTML (with XSS escaping for user data)
        popup_title_color = 'green' if status == 'PASS' else 'red'
        popup_html = f'''
            <div style="font-family: Arial; font-size: 12px; width: 280px;">
                <h4 style="margin: 0 0 8px 0; color: {popup_title_color};">{esc(address)}</h4>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 8px;">
                    <tr><td><b>Price:</b></td><td>{esc(price)}</td></tr>
                    <tr><td><b>Score:</b></td><td>{esc(prop.get('total_score', 'N/A'))} / 600</td></tr>
                    <tr><td><b>Tier:</b></td><td><b>{esc(tier)}</b></td></tr>
                    <tr><td><b>Kill Switch:</b></td><td style="color: {popup_title_color}; font-weight: bold;">{esc(status)}</td></tr>
                </table>
                <div style="padding-top: 8px; border-top: 1px solid #ccc; font-size: 11px;">
                    <b>Details:</b><br>
                    {esc(prop.get('beds', 'N/A'))} bed, {esc(prop.get('baths', 'N/A'))} bath, {esc(prop.get('sqft', 'N/A'))} sqft<br>
                    Lot: {esc(prop.get('lot_sqft', 'N/A'))} sqft | Year: {esc(prop.get('year_built', 'N/A'))}<br>
                    Schools: {esc(prop.get('school_rating', 'N/A'))} / 10 | Commute: {esc(prop.get('commute_min', 'N/A'))} min
                </div>
            </div>
        '''

        # Add marker to map (escape tooltip text too)
        tooltip_text = f"{esc(address)}<br>Score: {esc(prop.get('total_score', 'N/A'))} | {esc(status)}"
        html_parts.append(f'''
        L.circleMarker([{lat}, {lon}], {{
            radius: {radius},
            fillColor: "{color}",
            color: "black",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.75
        }}).bindPopup(`{popup_html}`)
          .bindTooltip("{tooltip_text}")
          .addTo(map);
        ''')

    html_parts.append('    </script>')
    html_parts.append('</body>')
    html_parts.append('</html>')

    # Write output
    with open(output_path, 'w') as f:
        f.write('\n'.join(html_parts))

    print(f"Map generated: {output_path}")
    print(f"Total properties plotted: {len(properties)}")
    contenders = [p for p in properties if p.get('tier') == 'CONTENDER']
    failed = [p for p in properties if p.get('kill_switch_status') == 'FAIL']
    print(f"  Contenders: {len(contenders)}")
    print(f"  Failed: {len(failed)}")

if __name__ == "__main__":

    project_root = Path(__file__).parent.parent
    ranked_csv = project_root / "data" / "phx_homes_ranked.csv"
    enrichment_json = project_root / "data" / "enrichment_data.json"
    output_html = project_root / "reports" / "html" / "golden_zone_map.html"

    generate_map_html(str(ranked_csv), str(enrichment_json), str(output_html))
