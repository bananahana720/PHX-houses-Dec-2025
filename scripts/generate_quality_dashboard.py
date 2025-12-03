#!/usr/bin/env python3
"""
Data Quality Dashboard for Phoenix Home Buying Analysis

Creates an interactive Plotly dashboard showing:
- Field completeness percentages
- Data freshness by phase
- Properties with missing critical fields
- Validation error summary

Usage:
    python scripts/generate_quality_dashboard.py
"""

import json
import logging
from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Critical fields that should always be populated
CRITICAL_FIELDS = [
    "full_address",
    "beds",
    "baths",
    "list_price",
    "year_built",
    "lot_sqft",
    "hoa_fee",
    "latitude",
    "longitude",
]

# Phase 1 fields (listing extraction)
PHASE1_FIELDS = [
    "school_rating",
    "orientation",
    "days_on_market",
    "violent_crime_index",
    "walk_score",
    "noise_score",
    "flood_zone",
]

# Phase 2 fields (image/API enrichment)
PHASE2_FIELDS = [
    "kitchen_layout_score",
    "master_suite_score",
    "natural_light_score",
    "roof_visual_condition",
    "hvac_age_visual_estimate",
    "air_quality_aqi",
    "permit_count",
]


def load_enrichment_data(enrichment_path: Path) -> list[dict]:
    """Load property data from enrichment_data.json."""
    with open(enrichment_path) as f:
        return json.load(f)


def calculate_field_completeness(
    properties: list[dict], fields: list[str]
) -> dict[str, float]:
    """Calculate completeness percentage for each field."""
    total = len(properties)
    if total == 0:
        return dict.fromkeys(fields, 0.0)

    completeness = {}
    for field in fields:
        count = sum(1 for p in properties if p.get(field) is not None)
        completeness[field] = round(count / total * 100, 1)

    return completeness


def count_missing_critical(properties: list[dict]) -> list[dict]:
    """Identify properties missing critical fields."""
    missing = []
    for prop in properties:
        missing_fields = [f for f in CRITICAL_FIELDS if prop.get(f) is None]
        if missing_fields:
            missing.append({
                "address": prop.get("full_address", "Unknown"),
                "missing": missing_fields,
                "count": len(missing_fields),
            })
    return sorted(missing, key=lambda x: x["count"], reverse=True)


def generate_dashboard(enrichment_path: Path, output_path: Path):
    """Generate the data quality dashboard."""
    logger.info("Loading enrichment data...")
    properties = load_enrichment_data(enrichment_path)
    total = len(properties)
    logger.info(f"Analyzing {total} properties")

    # Calculate completeness
    critical_completeness = calculate_field_completeness(properties, CRITICAL_FIELDS)
    phase1_completeness = calculate_field_completeness(properties, PHASE1_FIELDS)
    phase2_completeness = calculate_field_completeness(properties, PHASE2_FIELDS)

    # Find properties with missing critical data
    missing_critical = count_missing_critical(properties)

    # Create dashboard with subplots
    fig = make_subplots(
        rows=2,
        cols=2,
        subplot_titles=(
            "Critical Field Completeness",
            "Phase 1 (Listing) Completeness",
            "Phase 2 (Enrichment) Completeness",
            f"Properties Missing Critical Data ({len(missing_critical)}/{total})",
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "bar"}],
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
    )

    # Critical fields bar chart
    fields = list(critical_completeness.keys())
    values = list(critical_completeness.values())
    colors = ["#22c55e" if v >= 90 else "#eab308" if v >= 70 else "#dc2626" for v in values]

    fig.add_trace(
        go.Bar(
            x=fields,
            y=values,
            marker_color=colors,
            text=[f"{v}%" for v in values],
            textposition="auto",
            name="Critical",
        ),
        row=1,
        col=1,
    )

    # Phase 1 fields
    fields1 = list(phase1_completeness.keys())
    values1 = list(phase1_completeness.values())
    colors1 = ["#22c55e" if v >= 80 else "#eab308" if v >= 50 else "#dc2626" for v in values1]

    fig.add_trace(
        go.Bar(
            x=fields1,
            y=values1,
            marker_color=colors1,
            text=[f"{v}%" for v in values1],
            textposition="auto",
            name="Phase 1",
        ),
        row=1,
        col=2,
    )

    # Phase 2 fields
    fields2 = list(phase2_completeness.keys())
    values2 = list(phase2_completeness.values())
    colors2 = ["#22c55e" if v >= 80 else "#eab308" if v >= 50 else "#dc2626" for v in values2]

    fig.add_trace(
        go.Bar(
            x=fields2,
            y=values2,
            marker_color=colors2,
            text=[f"{v}%" for v in values2],
            textposition="auto",
            name="Phase 2",
        ),
        row=2,
        col=1,
    )

    # Missing critical data (top 10)
    top_missing = missing_critical[:10]
    if top_missing:
        addresses = [m["address"][:30] + "..." if len(m["address"]) > 30 else m["address"]
                     for m in top_missing]
        missing_counts = [m["count"] for m in top_missing]

        fig.add_trace(
            go.Bar(
                x=addresses,
                y=missing_counts,
                marker_color="#dc2626",
                text=missing_counts,
                textposition="auto",
                name="Missing Fields",
            ),
            row=2,
            col=2,
        )
    else:
        # No missing - show success message
        fig.add_annotation(
            text="All properties have complete critical data!",
            xref="x4",
            yref="y4",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 16, "color": "#22c55e"},
            row=2,
            col=2,
        )

    # Calculate overall scores
    critical_avg = sum(critical_completeness.values()) / len(critical_completeness)
    phase1_avg = sum(phase1_completeness.values()) / len(phase1_completeness)
    phase2_avg = sum(phase2_completeness.values()) / len(phase2_completeness)
    overall_score = (critical_avg * 0.5 + phase1_avg * 0.3 + phase2_avg * 0.2)

    # Update layout
    fig.update_layout(
        title={
            "text": f"Data Quality Dashboard - Overall Score: {overall_score:.1f}%",
            "font": {"size": 24},
            "x": 0.5,
            "xanchor": "center",
        },
        showlegend=False,
        height=800,
        width=1400,
        plot_bgcolor="white",
    )

    # Update all y-axes
    fig.update_yaxes(title_text="Completeness %", range=[0, 105], row=1, col=1)
    fig.update_yaxes(title_text="Completeness %", range=[0, 105], row=1, col=2)
    fig.update_yaxes(title_text="Completeness %", range=[0, 105], row=2, col=1)
    fig.update_yaxes(title_text="Missing Fields", row=2, col=2)

    # Rotate x-axis labels
    fig.update_xaxes(tickangle=45)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(str(output_path))
    logger.info(f"Dashboard saved: {output_path}")

    # Try PNG export
    try:
        png_path = output_path.with_suffix(".png")
        fig.write_image(str(png_path), width=1400, height=800)
        logger.info(f"PNG saved: {png_path}")
    except Exception as e:
        logger.warning(f"PNG export failed (install kaleido): {e}")

    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("DATA QUALITY SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total properties: {total}")
    logger.info(f"Critical completeness: {critical_avg:.1f}%")
    logger.info(f"Phase 1 completeness: {phase1_avg:.1f}%")
    logger.info(f"Phase 2 completeness: {phase2_avg:.1f}%")
    logger.info(f"Overall score: {overall_score:.1f}%")
    logger.info(f"Properties missing critical data: {len(missing_critical)}")


def main():
    project_root = Path(__file__).parent.parent
    enrichment_path = project_root / "data" / "enrichment_data.json"
    output_path = project_root / "reports" / "html" / "quality_dashboard.html"

    if not enrichment_path.exists():
        logger.error(f"Enrichment data not found: {enrichment_path}")
        return 1

    generate_dashboard(enrichment_path, output_path)
    return 0


if __name__ == "__main__":
    exit(main())
