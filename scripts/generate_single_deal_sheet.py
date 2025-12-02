#!/usr/bin/env python3
"""Generate a deal sheet for a single property with kill-switch override."""
import json
from datetime import datetime
from pathlib import Path


def generate_deal_sheet(address: str) -> str:
    """Generate HTML deal sheet for a property."""

    # Load enrichment data
    enrichment = json.load(open('data/enrichment_data.json'))
    prop = next((p for p in enrichment if address.lower() in p.get('full_address', '').lower()), None)

    if not prop:
        raise ValueError(f"Property not found: {address}")

    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Deal Sheet: {prop.get('full_address', address)}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
        .tier-badge {{ background: #3498db; padding: 8px 16px; border-radius: 20px; font-weight: bold; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 8px; }}
        .section h3 {{ margin-top: 0; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .score-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; }}
        .score-box {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .score-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
        .score-label {{ color: #7f8c8d; font-size: 12px; }}
        .detail-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }}
        .detail-item {{ display: flex; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid #eee; }}
        .warning {{ background: #fff3cd; border: 1px solid #ffc107; padding: 10px; border-radius: 8px; margin: 10px 0; }}
        .strength {{ color: #27ae60; }}
        .concern {{ color: #e74c3c; }}
        .override-badge {{ background: #f39c12; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{prop.get('full_address', address)}</h1>
        <span class="tier-badge">{prop.get('tier', 'CONTENDER')} TIER</span>
        <span class="override-badge">GARAGE OVERRIDE</span>
        <p style="margin-top:15px">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>

    <div class="section">
        <h3>FINAL SCORE: {prop.get('total_score', 386)} / 600</h3>
        <div class="score-grid">
            <div class="score-box">
                <div class="score-value">{int(prop.get('score_location', 165))}</div>
                <div class="score-label">LOCATION (250 max)</div>
            </div>
            <div class="score-box">
                <div class="score-value">{prop.get('score_lot_systems', 107)}</div>
                <div class="score-label">LOT/SYSTEMS (160 max)</div>
            </div>
            <div class="score-box">
                <div class="score-value">{prop.get('score_interior', 114)}</div>
                <div class="score-label">INTERIOR (190 max)</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h3>Property Details</h3>
        <div class="detail-grid">
            <div class="detail-item"><span>Price:</span><b>$634,000</b></div>
            <div class="detail-item"><span>Price/sqft:</span><b>$225.38</b></div>
            <div class="detail-item"><span>Beds/Baths:</span><b>6 bed / 3 bath</b></div>
            <div class="detail-item"><span>Living Area:</span><b>{prop.get('livable_sqft', 2813):,} sqft</b></div>
            <div class="detail-item"><span>Lot Size:</span><b>{prop.get('lot_sqft', 10115):,} sqft</b></div>
            <div class="detail-item"><span>Year Built:</span><b>{prop.get('year_built', 1976)}</b></div>
            <div class="detail-item"><span>Garage:</span><b>{prop.get('garage_spaces', 1)}-car</b></div>
            <div class="detail-item"><span>Pool:</span><b>{'Yes (diving + spa)' if prop.get('has_pool') else 'No'}</b></div>
            <div class="detail-item"><span>HOA:</span><b>${prop.get('hoa_fee', 0)}/month</b></div>
            <div class="detail-item"><span>Sewer:</span><b>{prop.get('sewer_type', 'city').title()}</b></div>
        </div>
    </div>

    <div class="section">
        <h3>Location Analysis</h3>
        <div class="detail-grid">
            <div class="detail-item"><span>School Rating:</span><b>{prop.get('school_rating', 'N/A')}/10</b></div>
            <div class="detail-item"><span>School District:</span><b>{prop.get('school_district', 'N/A')}</b></div>
            <div class="detail-item"><span>Orientation:</span><b>{prop.get('orientation', 'N/A').title()}-facing</b></div>
            <div class="detail-item"><span>Grocery Distance:</span><b>{prop.get('distance_to_grocery_miles', 'N/A')} mi</b></div>
            <div class="detail-item"><span>Highway Distance:</span><b>{prop.get('distance_to_highway_miles', 'N/A')} mi</b></div>
            <div class="detail-item"><span>Commute to Desert Ridge:</span><b>{prop.get('commute_minutes', 'N/A')} min</b></div>
        </div>
    </div>

    <div class="section">
        <h3>Interior Scores ({prop.get('interior_confidence', 'low').title()} Confidence)</h3>
        <div class="warning">Interior assessment based on limited photos ({prop.get('interior_photos_count', 5)} images matched property)</div>
        <div class="detail-grid">
            <div class="detail-item"><span>Kitchen Layout:</span><b>{prop.get('kitchen_layout_score', 5)}/10</b></div>
            <div class="detail-item"><span>Master Suite:</span><b>{prop.get('master_suite_score', 5)}/10</b></div>
            <div class="detail-item"><span>Natural Light:</span><b>{prop.get('natural_light_score', 7)}/10</b></div>
            <div class="detail-item"><span>High Ceilings:</span><b>{prop.get('high_ceilings_score', 9)}/10</b></div>
            <div class="detail-item"><span>Fireplace:</span><b>{prop.get('fireplace_score', 5)}/10</b></div>
            <div class="detail-item"><span>Laundry:</span><b>{prop.get('laundry_area_score', 5)}/10</b></div>
            <div class="detail-item"><span>Aesthetics:</span><b>{prop.get('aesthetics_score', 6)}/10</b></div>
        </div>
    </div>

    <div class="section">
        <h3>Strengths</h3>
        <ul>
            <li class="strength">Vaulted ceilings with exposed wood beams - dramatic living space</li>
            <li class="strength">Excellent grocery proximity (0.7 mi)</li>
            <li class="strength">Quiet location - 2.0 mi from highway</li>
            <li class="strength">Large lot (10,115 sqft) with diving pool, spa, covered patio</li>
            <li class="strength">6 bedrooms - rare for the area</li>
            <li class="strength">No HOA - $0/month</li>
        </ul>
    </div>

    <div class="section">
        <h3>Concerns</h3>
        <ul>
            <li class="concern">1-car garage - below typical buyer requirements</li>
            <li class="concern">Interior assessment low confidence - image data quality issue</li>
            <li class="concern">South-facing - moderate cooling costs in AZ summer</li>
            <li class="concern">1976 build - potential for dated systems (roof, HVAC age unknown)</li>
            <li class="concern">School rating 6.0/10 - average</li>
        </ul>
    </div>

    <div class="section">
        <h3>Recommended Next Steps</h3>
        <ol>
            <li>Verify interior features with in-person showing</li>
            <li>Confirm roof/HVAC ages during inspection</li>
            <li>Evaluate 1-car garage impact on buyer needs</li>
            <li>Check pool equipment condition</li>
            <li>Request seller disclosure for system ages</li>
        </ol>
    </div>

    <div class="section">
        <h3>Kill Switch Status</h3>
        <table style="width:100%; border-collapse:collapse;">
            <tr style="background:#f8f9fa;"><th style="text-align:left;padding:8px;">Criterion</th><th>Required</th><th>Actual</th><th>Status</th></tr>
            <tr><td style="padding:8px;">HOA Fee</td><td>$0</td><td>${prop.get('hoa_fee', 0)}</td><td>PASS</td></tr>
            <tr><td style="padding:8px;">Sewer</td><td>City</td><td>{prop.get('sewer_type', 'city').title()}</td><td>PASS</td></tr>
            <tr style="background:#fff3cd;"><td style="padding:8px;">Garage</td><td>2+ cars</td><td>{prop.get('garage_spaces', 1)} car</td><td>OVERRIDE</td></tr>
            <tr><td style="padding:8px;">Bedrooms</td><td>4+</td><td>6</td><td>PASS</td></tr>
            <tr><td style="padding:8px;">Bathrooms</td><td>2+</td><td>3</td><td>PASS</td></tr>
            <tr><td style="padding:8px;">Lot Size</td><td>7k-15k sqft</td><td>{prop.get('lot_sqft', 10115):,} sqft</td><td>PASS</td></tr>
            <tr><td style="padding:8px;">Year Built</td><td>&lt;2024</td><td>{prop.get('year_built', 1976)}</td><td>PASS</td></tr>
        </table>
    </div>
</body>
</html>'''

    return html


def main():
    address = "5038 W Echo Ln"
    html = generate_deal_sheet(address)

    output_path = Path('reports/deal_sheets/5038_w_echo_ln_override.html')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"Deal sheet generated: {output_path}")
    print(f"Open in browser: file:///{output_path.absolute()}")


if __name__ == "__main__":
    main()
