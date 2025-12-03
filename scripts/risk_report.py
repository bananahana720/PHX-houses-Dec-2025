#!/usr/bin/env python3
"""
Due Diligence Risk Report Generator for Phoenix Home Buying Analysis

Analyzes properties across 6 risk categories:
- Noise Risk (highway proximity)
- Infrastructure Risk (building age/codes)
- Solar Risk (lease complications)
- Cooling Cost Risk (sun orientation)
- School Stability (rating trends)
- Lot Size Margin (minimum requirement proximity)

Outputs:
- risk_report.html (interactive table with color-coded badges)
- risk_report.csv (data for analysis)
- risk_checklists/ folder (due diligence TODOs for high-risk properties)
"""

import csv
import json
from pathlib import Path


class RiskCategory:
    """Risk assessment levels"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    POSITIVE = "POSITIVE"
    UNKNOWN = "UNKNOWN"


class RiskScores:
    """Point values for risk levels"""
    HIGH = 3
    MEDIUM = 1
    LOW = 0
    POSITIVE = 0
    UNKNOWN = 1


def assess_noise_risk(distance_to_highway_miles: float) -> tuple[str, str]:
    """
    Assess highway noise risk based on distance.

    Returns: (risk_level, description)
    """
    if distance_to_highway_miles is None:
        return RiskCategory.UNKNOWN, "Highway distance unknown"

    if distance_to_highway_miles < 0.5:
        return RiskCategory.HIGH, "Highway noise likely audible"
    elif distance_to_highway_miles < 1.0:
        return RiskCategory.MEDIUM, "Some highway noise possible"
    else:
        return RiskCategory.LOW, "Quiet location"


def assess_infrastructure_risk(year_built: int) -> tuple[str, str]:
    """
    Assess building infrastructure risk based on construction era.

    Returns: (risk_level, description)
    """
    if year_built is None:
        return RiskCategory.UNKNOWN, "Year built unknown"

    if year_built < 1970:
        return RiskCategory.HIGH, "Pre-modern building codes, verify permits"
    elif year_built < 1990:
        return RiskCategory.MEDIUM, "May have dated systems"
    else:
        return RiskCategory.LOW, "Modern construction"


def assess_solar_risk(solar_status: str) -> tuple[str, str]:
    """
    Assess solar panel risk based on ownership status.

    Returns: (risk_level, description)
    """
    if solar_status is None or solar_status == "":
        return RiskCategory.UNKNOWN, "Verify solar status"

    solar_status_lower = str(solar_status).lower()

    if solar_status_lower == "leased":
        return RiskCategory.HIGH, "Solar lease transfer required, verify terms"
    elif solar_status_lower == "owned":
        return RiskCategory.POSITIVE, "Value-add, transferable"
    elif solar_status_lower == "none":
        return RiskCategory.LOW, "No solar complications"
    else:
        return RiskCategory.UNKNOWN, "Verify solar status"


def assess_cooling_risk(orientation: str) -> tuple[str, str]:
    """
    Assess cooling cost risk based on sun orientation.

    Returns: (risk_level, description)
    """
    if orientation is None or orientation == "" or orientation == "Unknown":
        return RiskCategory.UNKNOWN, "Verify sun orientation"

    orientation_upper = str(orientation).upper()

    # West and southwest facing = highest cooling costs
    if 'W' in orientation_upper and orientation_upper != 'NW':
        return RiskCategory.HIGH, "West-facing, expect high cooling costs"
    # South and southeast = moderate
    elif 'S' in orientation_upper and orientation_upper not in ['SW', 'NW']:
        return RiskCategory.MEDIUM, "Moderate cooling impact"
    # North, northeast, northwest, east = best for Arizona
    else:
        return RiskCategory.LOW, "Favorable orientation"


def assess_school_risk(school_rating: float) -> tuple[str, str]:
    """
    Assess school quality risk based on GreatSchools rating.

    Returns: (risk_level, description)
    """
    if school_rating is None:
        return RiskCategory.UNKNOWN, "School rating unknown"

    if school_rating < 6.0:
        return RiskCategory.HIGH, "Below-average schools, verify trends"
    elif school_rating < 7.5:
        return RiskCategory.MEDIUM, "Average schools"
    else:
        return RiskCategory.LOW, "Strong school district"


def assess_lot_size_risk(lot_sqft: int) -> tuple[str, str]:
    """
    Assess lot size margin risk (proximity to minimum requirement).

    Returns: (risk_level, description)
    """
    if lot_sqft is None:
        return RiskCategory.UNKNOWN, "Lot size unknown"

    # Kill switch minimum is 7,000 sqft
    if lot_sqft < 7500:
        return RiskCategory.MEDIUM, "Near minimum requirement"
    else:
        return RiskCategory.LOW, "Comfortable lot size"


def calculate_overall_risk_score(risks: dict[str, str]) -> int:
    """
    Calculate overall risk score by summing individual risk values.

    Args:
        risks: Dictionary of risk category -> risk level

    Returns:
        Total risk score (higher = riskier)
    """
    score = 0
    for risk_level in risks.values():
        if risk_level == RiskCategory.HIGH:
            score += RiskScores.HIGH
        elif risk_level == RiskCategory.MEDIUM:
            score += RiskScores.MEDIUM
        elif risk_level == RiskCategory.UNKNOWN:
            score += RiskScores.UNKNOWN
        # LOW and POSITIVE = 0 points

    return score


def load_enrichment_data(file_path: str) -> dict[str, dict]:
    """Load enrichment data indexed by full_address."""
    with open(file_path) as f:
        data_list = json.load(f)

    return {item['full_address']: item for item in data_list}


def load_orientation_data(file_path: str) -> dict[str, str]:
    """Load orientation estimates indexed by full_address."""
    with open(file_path) as f:
        data_list = json.load(f)

    return {item['full_address']: item['estimated_orientation'] for item in data_list}


def load_ranked_properties(file_path: str) -> list[dict]:
    """Load property rankings from CSV."""
    properties = []
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)

    return properties


def analyze_property_risks(property_data: dict, enrichment: dict, orientation: str) -> dict:
    """
    Analyze all risk categories for a single property.

    Returns:
        Dictionary with risk assessments and descriptions
    """
    # Get data from various sources
    distance_to_highway = float(enrichment.get('distance_to_highway_miles', 0)) if enrichment.get('distance_to_highway_miles') else None
    year_built = int(enrichment.get('year_built', 0)) if enrichment.get('year_built') else None
    solar_status = enrichment.get('solar_status')
    school_rating = float(enrichment.get('school_rating', 0)) if enrichment.get('school_rating') else None
    lot_sqft = int(enrichment.get('lot_sqft', 0)) if enrichment.get('lot_sqft') else None

    # Assess each risk category
    noise_risk, noise_desc = assess_noise_risk(distance_to_highway)
    infra_risk, infra_desc = assess_infrastructure_risk(year_built)
    solar_risk, solar_desc = assess_solar_risk(solar_status)
    cooling_risk, cooling_desc = assess_cooling_risk(orientation)
    school_risk, school_desc = assess_school_risk(school_rating)
    lot_risk, lot_desc = assess_lot_size_risk(lot_sqft)

    # Calculate overall risk score
    risks = {
        'noise': noise_risk,
        'infrastructure': infra_risk,
        'solar': solar_risk,
        'cooling': cooling_risk,
        'school': school_risk,
        'lot': lot_risk
    }
    overall_score = calculate_overall_risk_score(risks)

    return {
        'noise_risk': noise_risk,
        'noise_desc': noise_desc,
        'infrastructure_risk': infra_risk,
        'infrastructure_desc': infra_desc,
        'solar_risk': solar_risk,
        'solar_desc': solar_desc,
        'cooling_risk': cooling_risk,
        'cooling_desc': cooling_desc,
        'school_risk': school_risk,
        'school_desc': school_desc,
        'lot_risk': lot_risk,
        'lot_desc': lot_desc,
        'overall_risk_score': overall_score
    }


def generate_risk_badge_html(risk_level: str) -> str:
    """Generate HTML badge for risk level with color coding."""
    colors = {
        RiskCategory.HIGH: 'background-color: #dc3545; color: white;',
        RiskCategory.MEDIUM: 'background-color: #ffc107; color: black;',
        RiskCategory.LOW: 'background-color: #28a745; color: white;',
        RiskCategory.POSITIVE: 'background-color: #007bff; color: white;',
        RiskCategory.UNKNOWN: 'background-color: #6c757d; color: white;'
    }

    style = colors.get(risk_level, 'background-color: #6c757d; color: white;')
    return f'<span style="padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.85em; {style}">{risk_level}</span>'


def generate_html_report(properties_with_risks: list[dict], output_file: str):
    """Generate HTML report with color-coded risk badges."""

    from datetime import datetime
    analysis_date = datetime.now().strftime('%Y-%m-%d')

    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Due Diligence Risk Report - Phoenix Homes</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-top: 20px;
        }
        th {
            background-color: #007bff;
            color: white;
            padding: 12px 8px;
            text-align: left;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        td {
            padding: 10px 8px;
            border-bottom: 1px solid #ddd;
            vertical-align: middle;
        }
        tr:hover {
            background-color: #f8f9fa;
        }
        .address-col {
            font-weight: 500;
            color: #007bff;
            max-width: 250px;
        }
        .price-col {
            font-weight: 600;
            color: #28a745;
        }
        .risk-score-col {
            font-weight: bold;
            font-size: 1.2em;
            text-align: center;
        }
        .score-low {
            color: #28a745;
        }
        .score-medium {
            color: #ffc107;
        }
        .score-high {
            color: #dc3545;
        }
        .legend {
            margin: 20px 0;
            padding: 15px;
            background-color: white;
            border-left: 4px solid #007bff;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .legend h3 {
            margin-top: 0;
            color: #333;
        }
        .legend-item {
            display: inline-block;
            margin-right: 20px;
            margin-bottom: 8px;
        }
    </style>
</head>
<body>
    <h1>Due Diligence Risk Report - Phoenix Homes</h1>
    <p><strong>Analysis Date:</strong> {{ANALYSIS_DATE}}</p>

    <div class="legend">
        <h3>Risk Scoring Guide</h3>
        <div class="legend-item">Overall Risk Score: Sum of individual risks</div>
        <div class="legend-item">HIGH = 3 points</div>
        <div class="legend-item">MEDIUM = 1 point</div>
        <div class="legend-item">UNKNOWN = 1 point</div>
        <div class="legend-item">LOW/POSITIVE = 0 points</div>
        <br>
        <div class="legend-item"><strong>Low Risk:</strong> 0-2 points (safest)</div>
        <div class="legend-item"><strong>Medium Risk:</strong> 3-5 points (moderate caution)</div>
        <div class="legend-item"><strong>High Risk:</strong> 6+ points (extensive due diligence needed)</div>
    </div>

    <table>
        <thead>
            <tr>
                <th>Address</th>
                <th>Price</th>
                <th>Noise</th>
                <th>Infrastructure</th>
                <th>Solar</th>
                <th>Cooling</th>
                <th>Schools</th>
                <th>Lot Size</th>
                <th>Overall Risk</th>
            </tr>
        </thead>
        <tbody>
"""

    # Sort by overall risk score (lowest = safest first)
    sorted_properties = sorted(properties_with_risks, key=lambda x: x['overall_risk_score'])

    for prop in sorted_properties:
        # Color-code overall risk score
        score = prop['overall_risk_score']
        if score <= 2:
            score_class = 'score-low'
        elif score <= 5:
            score_class = 'score-medium'
        else:
            score_class = 'score-high'

        # Format price (price is already formatted)
        price = prop['price'] if prop['price'] else "N/A"

        html += f"""
            <tr>
                <td class="address-col" title="{prop['full_address']}">{prop['full_address']}</td>
                <td class="price-col">{price}</td>
                <td title="{prop['noise_desc']}">{generate_risk_badge_html(prop['noise_risk'])}</td>
                <td title="{prop['infrastructure_desc']}">{generate_risk_badge_html(prop['infrastructure_risk'])}</td>
                <td title="{prop['solar_desc']}">{generate_risk_badge_html(prop['solar_risk'])}</td>
                <td title="{prop['cooling_desc']}">{generate_risk_badge_html(prop['cooling_risk'])}</td>
                <td title="{prop['school_desc']}">{generate_risk_badge_html(prop['school_risk'])}</td>
                <td title="{prop['lot_desc']}">{generate_risk_badge_html(prop['lot_risk'])}</td>
                <td class="risk-score-col {score_class}">{score}</td>
            </tr>
"""

    html += """
        </tbody>
    </table>

    <div style="margin-top: 30px; padding: 15px; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h3>Risk Category Definitions</h3>
        <ul>
            <li><strong>Noise Risk:</strong> Based on highway distance (&lt;0.5mi = HIGH, 0.5-1.0mi = MEDIUM, &gt;1.0mi = LOW)</li>
            <li><strong>Infrastructure Risk:</strong> Based on year built (pre-1970 = HIGH, 1970-1989 = MEDIUM, 1990+ = LOW)</li>
            <li><strong>Solar Risk:</strong> Based on solar status (leased = HIGH, owned = POSITIVE, none = LOW)</li>
            <li><strong>Cooling Cost Risk:</strong> Based on orientation (W/SW = HIGH, S/SE = MEDIUM, N/NE/NW/E = LOW)</li>
            <li><strong>School Stability:</strong> Based on GreatSchools rating (&lt;6.0 = HIGH, 6.0-7.5 = MEDIUM, &gt;7.5 = LOW)</li>
            <li><strong>Lot Size Margin:</strong> Based on proximity to 7,000 sqft minimum (7000-7500 = MEDIUM, &gt;7500 = LOW)</li>
        </ul>
    </div>
</body>
</html>
"""

    # Replace placeholder
    html = html.replace('{{ANALYSIS_DATE}}', analysis_date)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)


def generate_csv_report(properties_with_risks: list[dict], output_file: str):
    """Generate CSV report for data analysis."""

    # Sort by overall risk score
    sorted_properties = sorted(properties_with_risks, key=lambda x: x['overall_risk_score'])

    fieldnames = [
        'full_address', 'price', 'noise_risk', 'noise_desc', 'infrastructure_risk',
        'infrastructure_desc', 'solar_risk', 'solar_desc', 'cooling_risk', 'cooling_desc',
        'school_risk', 'school_desc', 'lot_risk', 'lot_desc', 'overall_risk_score'
    ]

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for prop in sorted_properties:
            writer.writerow({k: prop.get(k, '') for k in fieldnames})


def generate_due_diligence_checklist(prop: dict, output_dir: str):
    """Generate detailed due diligence checklist for high-risk properties."""

    address = prop['full_address']
    safe_filename = address.replace(',', '').replace(' ', '_').replace('/', '-')
    filepath = Path(output_dir) / f"{safe_filename}_checklist.txt"

    checklist_items = []
    checklist_items.append(f"DUE DILIGENCE CHECKLIST: {address}")
    checklist_items.append("=" * 80)
    checklist_items.append(f"Overall Risk Score: {prop['overall_risk_score']} (High Risk)")
    checklist_items.append("")

    # Add items based on specific risk factors
    if prop['noise_risk'] == RiskCategory.HIGH:
        checklist_items.append("[HIGH PRIORITY] NOISE RISK")
        checklist_items.append("  [ ] Visit property during rush hour to assess highway noise levels")
        checklist_items.append("  [ ] Check noise levels at different times of day")
        checklist_items.append("  [ ] Inspect windows for noise insulation quality")
        checklist_items.append("  [ ] Ask neighbors about noise complaints")
        checklist_items.append("")

    if prop['infrastructure_risk'] == RiskCategory.HIGH:
        checklist_items.append("[HIGH PRIORITY] INFRASTRUCTURE RISK")
        checklist_items.append("  [ ] Request comprehensive home inspection focusing on outdated systems")
        checklist_items.append("  [ ] Verify all building permits and additions are code-compliant")
        checklist_items.append("  [ ] Check electrical panel for aluminum wiring or other hazards")
        checklist_items.append("  [ ] Inspect plumbing for galvanized pipes or polybutylene")
        checklist_items.append("  [ ] Request HVAC inspection and service records")
        checklist_items.append("  [ ] Check for asbestos and lead paint (pre-1978 homes)")
        checklist_items.append("")
    elif prop['infrastructure_risk'] == RiskCategory.MEDIUM:
        checklist_items.append("[MEDIUM PRIORITY] INFRASTRUCTURE RISK")
        checklist_items.append("  [ ] Request standard home inspection with focus on major systems")
        checklist_items.append("  [ ] Verify HVAC age and condition (Arizona climate stressor)")
        checklist_items.append("  [ ] Check roof age and remaining lifespan")
        checklist_items.append("")

    if prop['solar_risk'] == RiskCategory.HIGH:
        checklist_items.append("[HIGH PRIORITY] SOLAR LEASE RISK")
        checklist_items.append("  [ ] Obtain complete solar lease agreement and review terms")
        checklist_items.append("  [ ] Verify monthly lease payment amount and escalation clauses")
        checklist_items.append("  [ ] Check lease buyout cost and conditions")
        checklist_items.append("  [ ] Confirm lease transferability and approval process")
        checklist_items.append("  [ ] Review solar system warranty coverage")
        checklist_items.append("  [ ] Contact solar company about transfer requirements")
        checklist_items.append("  [ ] Factor lease payment into monthly housing cost")
        checklist_items.append("")

    if prop['cooling_risk'] == RiskCategory.HIGH:
        checklist_items.append("[HIGH PRIORITY] COOLING COST RISK")
        checklist_items.append("  [ ] Request 12 months of utility bills to verify summer cooling costs")
        checklist_items.append("  [ ] Inspect window coverings and insulation quality")
        checklist_items.append("  [ ] Check HVAC SEER rating (higher = more efficient)")
        checklist_items.append("  [ ] Assess quality of insulation in attic and walls")
        checklist_items.append("  [ ] Consider cost of energy-efficiency upgrades (windows, insulation)")
        checklist_items.append("  [ ] Verify dual-zone HVAC for multi-story homes")
        checklist_items.append("")
    elif prop['cooling_risk'] == RiskCategory.MEDIUM:
        checklist_items.append("[MEDIUM PRIORITY] COOLING COST RISK")
        checklist_items.append("  [ ] Request summer utility bills to estimate cooling costs")
        checklist_items.append("  [ ] Check HVAC efficiency rating")
        checklist_items.append("")

    if prop['school_risk'] == RiskCategory.HIGH:
        checklist_items.append("[HIGH PRIORITY] SCHOOL QUALITY RISK")
        checklist_items.append("  [ ] Research school rating trends on GreatSchools.org")
        checklist_items.append("  [ ] Visit schools and meet with administration")
        checklist_items.append("  [ ] Review recent test scores and district funding")
        checklist_items.append("  [ ] Check for planned school closures or boundary changes")
        checklist_items.append("  [ ] Assess impact on resale value and buyer pool")
        checklist_items.append("  [ ] Consider private school costs as alternative")
        checklist_items.append("")
    elif prop['school_risk'] == RiskCategory.MEDIUM:
        checklist_items.append("[MEDIUM PRIORITY] SCHOOL QUALITY")
        checklist_items.append("  [ ] Review school ratings and trends")
        checklist_items.append("  [ ] Verify school boundaries haven't changed recently")
        checklist_items.append("")

    if prop['lot_risk'] == RiskCategory.MEDIUM:
        checklist_items.append("[MEDIUM PRIORITY] LOT SIZE MARGIN")
        checklist_items.append("  [ ] Verify actual lot size with county assessor records")
        checklist_items.append("  [ ] Check for encroachments or easements reducing usable space")
        checklist_items.append("  [ ] Assess whether lot feels too small for needs")
        checklist_items.append("  [ ] Consider impact on resale value (smaller lot = smaller buyer pool)")
        checklist_items.append("")

    if prop['noise_risk'] == RiskCategory.MEDIUM:
        checklist_items.append("[MEDIUM PRIORITY] NOISE RISK")
        checklist_items.append("  [ ] Visit property to assess ambient noise levels")
        checklist_items.append("  [ ] Check noise levels in backyard and bedrooms")
        checklist_items.append("")

    # Add general due diligence items
    checklist_items.append("GENERAL DUE DILIGENCE (ALL PROPERTIES)")
    checklist_items.append("  [ ] Order professional home inspection")
    checklist_items.append("  [ ] Schedule termite/pest inspection")
    checklist_items.append("  [ ] Review HOA documents and CC&Rs (if applicable)")
    checklist_items.append("  [ ] Verify property taxes and special assessments")
    checklist_items.append("  [ ] Check for liens or title issues")
    checklist_items.append("  [ ] Confirm sewer type (city vs septic)")
    checklist_items.append("  [ ] Inspect pool equipment if present (pump, filter, heater)")
    checklist_items.append("  [ ] Walk the neighborhood at different times")
    checklist_items.append("  [ ] Research crime statistics for area")
    checklist_items.append("  [ ] Verify flood zone status")
    checklist_items.append("  [ ] Check for planned development or zoning changes nearby")
    checklist_items.append("")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(checklist_items))


def main():
    """Main execution function."""

    # File paths
    base_dir = Path(__file__).parent.parent
    ranked_csv = base_dir / 'data' / 'phx_homes_ranked.csv'
    enrichment_json = base_dir / 'data' / 'enrichment_data.json'
    orientation_json = base_dir / 'data' / 'orientation_estimates.json'
    output_dir = base_dir / 'reports' / 'html'
    output_dir.mkdir(parents=True, exist_ok=True)
    html_output = output_dir / 'risk_report.html'
    csv_output = output_dir / 'risk_report.csv'
    checklist_dir = output_dir / 'risk_checklists'

    # Load data
    print("Loading data files...")
    properties = load_ranked_properties(ranked_csv)
    enrichment_data = load_enrichment_data(enrichment_json)
    orientation_data = load_orientation_data(orientation_json)

    # Analyze risks for all properties
    print(f"Analyzing {len(properties)} properties...")
    properties_with_risks = []

    for prop in properties:
        address = prop['full_address']
        enrichment = enrichment_data.get(address, {})
        orientation = orientation_data.get(address, "Unknown")

        # Analyze risks
        risk_analysis = analyze_property_risks(prop, enrichment, orientation)

        # Combine with property data (price is already formatted in CSV)
        combined = {
            'full_address': address,
            'price': prop.get('price', 'N/A'),
            **risk_analysis
        }
        properties_with_risks.append(combined)

    # Generate reports
    print("Generating HTML report...")
    generate_html_report(properties_with_risks, html_output)

    print("Generating CSV report...")
    generate_csv_report(properties_with_risks, csv_output)

    # Generate checklists for high-risk properties (score > 5)
    high_risk_properties = [p for p in properties_with_risks if p['overall_risk_score'] > 5]

    if high_risk_properties:
        print(f"Generating due diligence checklists for {len(high_risk_properties)} high-risk properties...")
        checklist_dir.mkdir(exist_ok=True)

        for prop in high_risk_properties:
            generate_due_diligence_checklist(prop, checklist_dir)

    # Print summary statistics
    print("\n" + "="*80)
    print("RISK ANALYSIS SUMMARY")
    print("="*80)

    # Risk tier breakdown
    low_risk = [p for p in properties_with_risks if p['overall_risk_score'] <= 2]
    medium_risk = [p for p in properties_with_risks if 3 <= p['overall_risk_score'] <= 5]
    high_risk = [p for p in properties_with_risks if p['overall_risk_score'] > 5]

    print("\nRisk Tier Distribution:")
    print(f"  Low Risk (0-2 points):    {len(low_risk)} properties")
    print(f"  Medium Risk (3-5 points): {len(medium_risk)} properties")
    print(f"  High Risk (6+ points):    {len(high_risk)} properties")

    # Top 3 safest properties
    safest = sorted(properties_with_risks, key=lambda x: x['overall_risk_score'])[:3]
    print("\nTop 3 Safest Properties (Lowest Risk):")
    for i, prop in enumerate(safest, 1):
        price = prop.get('price', 'N/A')
        print(f"  {i}. {prop['full_address']}")
        print(f"     Price: {price}, Risk Score: {prop['overall_risk_score']}")

    # Most common risk factors
    risk_counts = {
        'HIGH Noise': sum(1 for p in properties_with_risks if p['noise_risk'] == RiskCategory.HIGH),
        'HIGH Infrastructure': sum(1 for p in properties_with_risks if p['infrastructure_risk'] == RiskCategory.HIGH),
        'HIGH Solar': sum(1 for p in properties_with_risks if p['solar_risk'] == RiskCategory.HIGH),
        'HIGH Cooling': sum(1 for p in properties_with_risks if p['cooling_risk'] == RiskCategory.HIGH),
        'HIGH Schools': sum(1 for p in properties_with_risks if p['school_risk'] == RiskCategory.HIGH),
        'MEDIUM Lot Size': sum(1 for p in properties_with_risks if p['lot_risk'] == RiskCategory.MEDIUM),
    }

    print("\nMost Common Risk Factors:")
    sorted_risks = sorted(risk_counts.items(), key=lambda x: x[1], reverse=True)
    for risk_name, count in sorted_risks[:5]:
        if count > 0:
            print(f"  {risk_name}: {count} properties")

    print("\nReports generated:")
    print(f"  - {html_output}")
    print(f"  - {csv_output}")
    if high_risk_properties:
        print(f"  - {checklist_dir}/ ({len(high_risk_properties)} checklists)")
    print("="*80)


if __name__ == '__main__':
    main()
