#!/usr/bin/env python3
"""
Market Activity Map for Phoenix Home Buying Analysis

Creates an interactive Folium map showing:
- Days on Market (DOM) - Green (<30) -> Yellow (30-60) -> Red (>60)
- Price reductions - Highlighted markers for price cuts
- Market hotspots - Cluster analysis of listing activity

Usage:
    python scripts/generate_market_map.py [--zip ZIP_CODE]
"""

import argparse
import json
import logging
from pathlib import Path

import folium
from folium import CircleMarker

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Configuration
PHOENIX_CENTER = (33.4484, -112.0740)
ZOOM_LEVEL = 10

# Color mappings for DOM
DOM_COLORS = {
    "fresh": "#22c55e",       # Green - <30 days (hot market)
    "moderate": "#eab308",    # Yellow - 30-60 days
    "stale": "#f97316",       # Orange - 60-90 days
    "old": "#dc2626",         # Red - 90+ days (buyer leverage)
    "unknown": "#9ca3af",     # Gray - no data
}


def get_dom_category(days: int | None) -> str:
    """Categorize days on market."""
    if days is None:
        return "unknown"
    if days < 30:
        return "fresh"
    if days < 60:
        return "moderate"
    if days < 90:
        return "stale"
    return "old"


def get_coordinates(prop: dict) -> tuple[float, float] | None:
    """Extract coordinates from property data."""
    lat = prop.get("latitude") or prop.get("lat")
    lng = prop.get("longitude") or prop.get("lng")
    if lat is not None and lng is not None:
        try:
            return (float(lat), float(lng))
        except (ValueError, TypeError):
            return None
    return None


def load_enrichment_data(enrichment_path: Path) -> list[dict]:
    """Load property data from enrichment_data.json."""
    with open(enrichment_path) as f:
        return json.load(f)


def generate_map(
    enrichment_path: Path,
    output_path: Path,
    filter_zip: str | None = None,
):
    """Generate the market activity map."""
    logger.info("Loading enrichment data...")
    enrichment = load_enrichment_data(enrichment_path)
    logger.info(f"Loaded {len(enrichment)} properties")

    # Optional filtering
    if filter_zip:
        enrichment = [p for p in enrichment if p.get("zip_code") == filter_zip]
        logger.info(f"Filtered to {len(enrichment)} properties in ZIP {filter_zip}")

    # Create base map
    m = folium.Map(
        location=PHOENIX_CENTER,
        zoom_start=ZOOM_LEVEL,
        tiles="OpenStreetMap",
    )

    # Track statistics
    dom_counts = {"fresh": 0, "moderate": 0, "stale": 0, "old": 0, "unknown": 0}
    price_reduced_count = 0
    plotted = 0
    skipped = 0

    # Add markers
    for prop in enrichment:
        coords = get_coordinates(prop)
        if not coords:
            skipped += 1
            continue

        lat, lng = coords
        address = prop.get("full_address", "Unknown")
        dom = prop.get("days_on_market")
        price_reduced = prop.get("price_reduced", False)
        price = prop.get("list_price") or prop.get("price")

        # Determine category and color
        category = get_dom_category(dom)
        color = DOM_COLORS[category]
        dom_counts[category] += 1

        if price_reduced:
            price_reduced_count += 1

        # Format price
        price_str = f"${price:,.0f}" if price else "N/A"

        # Build popup HTML
        popup_html = f"""
        <div style="font-family: Arial; font-size: 12px; width: 280px;">
            <h4 style="margin: 0 0 8px 0; color: {color};">{address}</h4>
            <table style="width: 100%; border-collapse: collapse;">
                <tr><td style="padding: 4px;"><b>Price:</b></td>
                    <td style="padding: 4px;">{price_str}</td></tr>
                <tr><td style="padding: 4px;"><b>Days on Market:</b></td>
                    <td style="padding: 4px;">{dom if dom is not None else 'N/A'}</td></tr>
                <tr><td style="padding: 4px;"><b>Price Reduced:</b></td>
                    <td style="padding: 4px;">{'Yes' if price_reduced else 'No'}</td></tr>
            </table>
        </div>
        """

        # Marker size based on price (larger = more expensive)
        radius = 6 if not price else 5 + min(10, price / 100000)

        # Add extra ring for price-reduced properties
        if price_reduced:
            CircleMarker(
                location=[lat, lng],
                radius=radius + 4,
                color="#7c3aed",  # Purple ring
                weight=3,
                fill=False,
                tooltip="PRICE REDUCED",
            ).add_to(m)

        CircleMarker(
            location=[lat, lng],
            radius=radius,
            color="black",
            weight=1,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{address}<br>DOM: {dom if dom else 'N/A'}",
        ).add_to(m)

        plotted += 1

    # Add legend
    legend_html = f"""
    <div style="position: fixed; bottom: 50px; left: 50px;
                background: white; padding: 15px; border: 2px solid gray;
                border-radius: 8px; box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
                font-family: Arial; z-index: 9999;">
        <h4 style="margin: 0 0 10px 0; font-size: 16px;">Market Activity</h4>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: {DOM_COLORS['fresh']}; border: 1px solid black;
                         border-radius: 50%; vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Fresh (&lt;30 days) [{dom_counts['fresh']}]</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: {DOM_COLORS['moderate']}; border: 1px solid black;
                         border-radius: 50%; vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Moderate (30-60 days) [{dom_counts['moderate']}]</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: {DOM_COLORS['stale']}; border: 1px solid black;
                         border-radius: 50%; vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Stale (60-90 days) [{dom_counts['stale']}]</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: {DOM_COLORS['old']}; border: 1px solid black;
                         border-radius: 50%; vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Old (90+ days) [{dom_counts['old']}]</span>
        </div>
        <div style="margin: 6px 0;">
            <span style="display: inline-block; width: 16px; height: 16px;
                         background: transparent; border: 3px solid #7c3aed;
                         border-radius: 50%; vertical-align: middle; margin-right: 8px;"></span>
            <span style="font-size: 13px;">Price Reduced [{price_reduced_count}]</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    m.save(str(output_path))

    # Print summary
    logger.info(f"\nMap generated: {output_path}")
    logger.info(f"  Properties plotted: {plotted}")
    logger.info(f"  Properties skipped (no coords): {skipped}")
    logger.info(f"  Price reductions: {price_reduced_count}")
    logger.info(f"  DOM breakdown: {dom_counts}")


def main():
    parser = argparse.ArgumentParser(description="Generate market activity map")
    parser.add_argument("--zip", help="Filter to specific ZIP code")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    enrichment_path = project_root / "data" / "enrichment_data.json"
    output_path = project_root / "reports" / "html" / "market_map.html"

    if not enrichment_path.exists():
        logger.error(f"Enrichment data not found: {enrichment_path}")
        return 1

    generate_map(enrichment_path, output_path, args.zip)
    return 0


if __name__ == "__main__":
    exit(main())
