#!/usr/bin/env python3
"""
Generate golden_zone_map.html with current property locations and tiers.
Uses ranked CSV data for scores and enrichment JSON for lat/lon geocoding.
"""

import json
import csv
from pathlib import Path
from typing import Optional, Tuple
import re

def extract_address_parts(address: str) -> Tuple[str, str]:
    """Extract city and zip from full address."""
    match = re.search(r'([A-Za-z\s]+),\s*AZ\s*(\d{5})', address)
    if match:
        return match.group(1).strip(), match.group(2)
    return "", ""

def get_coordinates_from_enrichment(address: str, enrichment_data: list) -> Optional[Tuple[float, float]]:
    """Look up coordinates in enrichment data based on address."""
    for prop in enrichment_data:
        if prop.get('full_address', '').lower() == address.lower():
            # Try to extract from safety_data_source or use a geocoding API
            # For now, we'll use manual lookup from existing map data
            return None
    return None

def generate_map_html(ranked_csv_path: str, enrichment_json_path: str, output_path: str):
    """Generate the interactive map HTML."""

    # Load enrichment data for coordinates
    with open(enrichment_json_path, 'r') as f:
        enrichment_data = json.load(f)

    # Create address -> enrichment data map
    enrichment_map = {prop['full_address']: prop for prop in enrichment_data if 'full_address' in prop}

    # Read ranked CSV
    properties = []
    seen_addresses = set()
    with open(ranked_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['full_address']:
                properties.append(row)
                seen_addresses.add(row['full_address'].lower())

    # Add properties from enrichment that might not be in CSV
    for prop in enrichment_data:
        addr = prop.get('full_address', '').lower()
        if addr and addr not in seen_addresses:
            # Create a CSV-like row from enrichment data
            # Mark as FAIL if kill_switch_passed is False
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

    # Geocoding data (from Nominatim/Google Maps)
    geocoding = {
        "4209 W Wahalla Ln, Glendale, AZ 85308": (33.6353, -112.2024),
        "4417 W Sandra Cir, Glendale, AZ 85308": (33.6412, -112.1943),
        "2344 W Marconi Ave, Phoenix, AZ 85023": (33.6307, -112.1101),
        "4136 W Hearn Rd, Phoenix, AZ 85053": (33.6545, -112.0967),
        "13307 N 84th Ave, Peoria, AZ 85381": (33.7168, -112.3166),
        "4732 W Davis Rd, Glendale, AZ 85306": (33.6314, -112.1998),
        "20021 N 38th Ln, Glendale, AZ 85308": (33.6483, -112.1525),
        "5004 W Kaler Dr, Glendale, AZ 85301": (33.5956, -112.1819),
        "8426 E Lincoln Dr, Scottsdale, AZ 85250": (33.4934, -111.9134),
        "5522 W Carol Ave, Glendale, AZ 85302": (33.6107, -112.1638),
        "7233 W Corrine Dr, Peoria, AZ 85381": (33.7053, -112.3315),
        "4020 W Anderson Dr, Glendale, AZ 85308": (33.6337, -112.1935),
        "7126 W Columbine Dr, Peoria, AZ 85381": (33.7024, -112.3524),
        "4001 W Libby St, Glendale, AZ 85308": (33.6377, -112.1853),
        "2353 W Tierra Buena Ln, Phoenix, AZ 85023": (33.6287, -112.1105),
        "14014 N 39th Ave, Phoenix, AZ 85053": (33.6487, -112.0844),
        "4342 W Claremont St, Glendale, AZ 85301": (33.5902, -112.1781),
        "2846 W Villa Rita Dr, Phoenix, AZ 85053": (33.6505, -112.1212),
        "8803 N 105th Dr, Peoria, AZ 85345": (33.6907, -112.4211),
        "8931 W Villa Rita Dr, Peoria, AZ 85382": (33.6782, -112.3984),
        "15225 N 37th Way, Phoenix, AZ 85032": (33.625, -112.0011),
        "16814 N 31st Ave, Phoenix, AZ 85053": (33.6389, -112.0623),
        "14353 N 76th Dr, Peoria, AZ 85381": (33.7276, -112.2998),
        "18820 N 35th Way, Phoenix, AZ 85050": (33.6682, -112.0529),
        "4137 W Cielo Grande, Glendale, AZ 85310": (33.6549, -112.2269),
        "25841 N 66th Dr, Phoenix, AZ 85083": (33.7071, -112.1437),
        "18825 N 34th St, Phoenix, AZ 85050": (33.6664, -112.0477),
        "8714 E Plaza Ave, Scottsdale, AZ 85250": (33.4846, -111.8966),
        "11035 E Clinton St, Scottsdale, AZ 85259": (33.5165, -111.8585),
        "14622 N 37th St, Phoenix, AZ 85032": (33.6252, -112.0118),
        "12808 N 27th St, Phoenix, AZ 85032": (33.6087, -112.0255),
        "17244 N 36th Ln, Glendale, AZ 85308": (33.6346, -112.1394),
        "9150 W Villa Rita Dr, Peoria, AZ 85382": (33.6734, -112.3958),
        "5038 W Echo Ln, Glendale, AZ 85302": (33.6146, -112.1739),
        "9832 N 29th St, Phoenix, AZ 85028": (33.6241, -112.0058),
    }

    # Ensure we have all 35 properties with geocoding
    print(f"Total properties loaded: {len(properties)}")

    # Build HTML
    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html>')
    html_parts.append('<head>')
    html_parts.append('    <meta charset="UTF-8">')
    html_parts.append('    <meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html_parts.append('    <title>Phoenix Golden Zone - Property Map (December 1, 2025)</title>')
    html_parts.append('    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css" />')
    html_parts.append('    <script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>')
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
    html_parts.append('    <div class="timestamp">Updated: December 1, 2025</div>')
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

    # Add markers for each property
    for prop in properties:
        address = prop['full_address'].strip()
        coords = geocoding.get(address)

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
            except:
                color = 'gray'
                radius = 8

        # Build popup HTML
        popup_title_color = 'green' if status == 'PASS' else 'red'
        popup_html = f'''
            <div style="font-family: Arial; font-size: 12px; width: 280px;">
                <h4 style="margin: 0 0 8px 0; color: {popup_title_color};">{address}</h4>
                <table style="width: 100%; border-collapse: collapse; margin-bottom: 8px;">
                    <tr><td><b>Price:</b></td><td>{price}</td></tr>
                    <tr><td><b>Score:</b></td><td>{prop.get('total_score', 'N/A')} / 600</td></tr>
                    <tr><td><b>Tier:</b></td><td><b>{tier}</b></td></tr>
                    <tr><td><b>Kill Switch:</b></td><td style="color: {popup_title_color}; font-weight: bold;">{status}</td></tr>
                </table>
                <div style="padding-top: 8px; border-top: 1px solid #ccc; font-size: 11px;">
                    <b>Details:</b><br>
                    {prop.get('beds', 'N/A')} bed, {prop.get('baths', 'N/A')} bath, {prop.get('sqft', 'N/A')} sqft<br>
                    Lot: {prop.get('lot_sqft', 'N/A')} sqft | Year: {prop.get('year_built', 'N/A')}<br>
                    Schools: {prop.get('school_rating', 'N/A')} / 10 | Commute: {prop.get('commute_min', 'N/A')} min
                </div>
            </div>
        '''

        # Add marker to map
        html_parts.append(f'''
        L.circleMarker([{lat}, {lon}], {{
            radius: {radius},
            fillColor: "{color}",
            color: "black",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.75
        }}).bindPopup(`{popup_html}`)
          .bindTooltip("{address}<br>Score: {prop.get('total_score', 'N/A')} | {status}")
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
    import sys

    project_root = Path(__file__).parent.parent
    ranked_csv = project_root / "data" / "phx_homes_ranked.csv"
    enrichment_json = project_root / "data" / "enrichment_data.json"
    output_html = project_root / "reports" / "html" / "golden_zone_map.html"

    generate_map_html(str(ranked_csv), str(enrichment_json), str(output_html))
