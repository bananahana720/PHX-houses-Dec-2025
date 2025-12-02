#!/usr/bin/env python3
"""
Renovation Gap Analysis for Phoenix Home Buying Project

Calculates "True Cost" by adding estimated renovation/repair costs to list prices.
Arizona-specific cost estimates based on property age and condition data.

Output:
- renovation_gap_report.csv: Detailed cost breakdown per property
- renovation_gap_report.html: Interactive sortable table with color coding
"""

import csv
import json
from pathlib import Path


# Arizona-specific cost estimation rules
def estimate_roof_cost(roof_age) -> int:
    """Estimate roof replacement/repair cost based on age."""
    if roof_age is None:
        return 8000  # Contingency for unknown
    elif roof_age < 10:
        return 0
    elif roof_age <= 15:
        return 5000  # Minor repairs
    elif roof_age <= 20:
        return 10000  # Partial replacement
    else:
        return 18000  # Full replacement


def estimate_hvac_cost(hvac_age) -> int:
    """Estimate HVAC cost (AZ lifespan: 12-15 years vs 20+ elsewhere)."""
    if hvac_age is None:
        return 4000  # Contingency for unknown
    elif hvac_age < 8:
        return 0
    elif hvac_age <= 12:
        return 3000  # Potential repairs
    else:
        return 8000  # Replacement needed


def estimate_pool_cost(has_pool: bool, pool_equipment_age) -> int:
    """Estimate pool equipment replacement cost."""
    if not has_pool:
        return 0

    if pool_equipment_age is None:
        return 5000  # Contingency for unknown
    elif pool_equipment_age < 5:
        return 0
    elif pool_equipment_age <= 10:
        return 3000  # Pump/filter replacement
    else:
        return 8000  # Full equipment overhaul


def estimate_plumbing_cost(year_built: int) -> int:
    """Estimate plumbing/electrical updates based on build year."""
    if year_built >= 2000:
        return 0
    elif year_built >= 1990:
        return 2000  # Potential updates
    elif year_built >= 1980:
        return 5000  # Likely needs inspection/updates
    else:
        return 10000  # Galvanized pipes, old wiring


def estimate_kitchen_cost(year_built: int, score_interior: float) -> int:
    """Estimate kitchen update cost for older homes with neutral interior scores."""
    # If built before 1990 and interior score is neutral (95.0 default)
    if year_built < 1990 and abs(score_interior - 95.0) < 0.1:
        return 15000
    return 0


def load_csv_data(csv_path: Path) -> list[dict]:
    """Load property data from ranked CSV."""
    properties = []
    with open(csv_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            properties.append(row)
    return properties


def load_enrichment_data(json_path: Path) -> dict[str, dict]:
    """Load enrichment data and index by full_address."""
    with open(json_path, encoding='utf-8') as f:
        enrichment_list = json.load(f)

    # Index by address
    enrichment_dict = {}
    for entry in enrichment_list:
        address = entry.get('full_address')
        if address:
            enrichment_dict[address] = entry

    return enrichment_dict


def calculate_renovation_costs(property_data: dict, enrichment: dict) -> tuple[int, int, int, int, int]:
    """
    Calculate all renovation costs for a property.

    Returns: (roof_cost, hvac_cost, pool_cost, plumbing_cost, kitchen_cost)
    """
    # Get data from enrichment
    roof_age = enrichment.get('roof_age')
    hvac_age = enrichment.get('hvac_age')
    has_pool = enrichment.get('has_pool', False)
    pool_equipment_age = enrichment.get('pool_equipment_age')
    # Safely handle year_built
    try:
        year_built = enrichment.get('year_built')
        if not year_built:
            year_built_str = property_data.get('year_built', '1970')
            year_built = int(year_built_str) if year_built_str and year_built_str != '' else 1970
    except (ValueError, TypeError):
        year_built = 1970

    # Get section_c_score from CSV (defaults to 95.0 if not enriched)
    try:
        score_interior = float(property_data.get('section_c_score', 95.0))
    except (ValueError, TypeError):
        score_interior = 95.0

    # Calculate each component
    roof_cost = estimate_roof_cost(roof_age)
    hvac_cost = estimate_hvac_cost(hvac_age)
    pool_cost = estimate_pool_cost(has_pool, pool_equipment_age)
    plumbing_cost = estimate_plumbing_cost(year_built)
    kitchen_cost = estimate_kitchen_cost(year_built, score_interior)

    return roof_cost, hvac_cost, pool_cost, plumbing_cost, kitchen_cost


def format_currency(amount: float) -> str:
    """Format number as currency."""
    return f"${amount:,.0f}"


def format_percentage(value: float) -> str:
    """Format as percentage."""
    return f"{value:.1f}%"


def generate_csv_report(results: list[dict], output_path: Path):
    """Generate CSV report with renovation costs."""
    fieldnames = [
        'rank', 'address', 'kill_switch_passed', 'tier', 'total_score',
        'list_price', 'roof_cost', 'hvac_cost', 'pool_cost',
        'plumbing_cost', 'kitchen_cost', 'total_renovation',
        'true_cost', 'price_delta_pct'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"[OK] CSV report saved: {output_path}")


def generate_html_report(results: list[dict], output_path: Path):
    """Generate interactive HTML report with sortable table."""

    html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Renovation Gap Report - Phoenix Homes</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            margin: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #2196F3;
            padding-bottom: 10px;
        }
        .summary {
            background: #e3f2fd;
            padding: 20px;
            border-radius: 6px;
            margin: 20px 0;
        }
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .stat {
            background: white;
            padding: 15px;
            border-radius: 4px;
            border-left: 4px solid #2196F3;
        }
        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            font-size: 14px;
        }
        th {
            background: #2196F3;
            color: white;
            padding: 12px 8px;
            text-align: left;
            cursor: pointer;
            user-select: none;
            position: sticky;
            top: 0;
        }
        th:hover {
            background: #1976D2;
        }
        th::after {
            content: ' ⇅';
            opacity: 0.5;
        }
        td {
            padding: 10px 8px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background: #f5f5f5;
        }
        .delta-low {
            background: #c8e6c9;
        }
        .delta-medium {
            background: #fff9c4;
        }
        .delta-high {
            background: #ffcdd2;
        }
        .best-value {
            border-left: 4px solid #4CAF50;
            font-weight: bold;
        }
        .fail {
            opacity: 0.5;
            background: #f0f0f0;
        }
        .pass {
            /* Normal styling */
        }
        .currency {
            text-align: right;
            font-family: 'Courier New', monospace;
        }
        .tier-contender {
            color: #2196F3;
            font-weight: bold;
        }
        .tier-unicorn {
            color: #9C27B0;
            font-weight: bold;
        }
        .tier-pass {
            color: #666;
        }
        .legend {
            margin: 20px 0;
            padding: 15px;
            background: #fafafa;
            border-radius: 4px;
        }
        .legend-item {
            display: inline-block;
            margin-right: 20px;
            font-size: 13px;
        }
        .legend-box {
            display: inline-block;
            width: 20px;
            height: 20px;
            margin-right: 5px;
            vertical-align: middle;
            border: 1px solid #ccc;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Renovation Gap Analysis - Phoenix Homes</h1>
        <p><strong>Analysis Date:</strong> {{ANALYSIS_DATE}}</p>

        <div class="summary">
            <h2>Summary Statistics</h2>
            <div class="summary-grid">
                <div class="stat">
                    <div class="stat-label">Total Properties</div>
                    <div class="stat-value">{{TOTAL_PROPERTIES}}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Average Renovation</div>
                    <div class="stat-value">{{AVG_RENOVATION}}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Min Renovation</div>
                    <div class="stat-value">{{MIN_RENOVATION}}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Max Renovation</div>
                    <div class="stat-value">{{MAX_RENOVATION}}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">High Cost (>$20k)</div>
                    <div class="stat-value">{{HIGH_COST_COUNT}}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">Best True Value</div>
                    <div class="stat-value">{{BEST_VALUE}}</div>
                </div>
            </div>
        </div>

        <div class="legend">
            <strong>Color Legend:</strong>
            <div class="legend-item">
                <span class="legend-box delta-low"></span> Green: &lt;5% renovation cost
            </div>
            <div class="legend-item">
                <span class="legend-box delta-medium"></span> Yellow: 5-10% renovation cost
            </div>
            <div class="legend-item">
                <span class="legend-box delta-high"></span> Red: &gt;10% renovation cost
            </div>
            <div class="legend-item" style="margin-top: 10px;">
                <span style="border-left: 4px solid #4CAF50; padding-left: 10px;">Bold border = Best True Value (lowest among PASS)</span>
            </div>
        </div>

        <table id="dataTable">
            <thead>
                <tr>
                    <th onclick="sortTable(0)">Rank</th>
                    <th onclick="sortTable(1)">Address</th>
                    <th onclick="sortTable(2)">Status</th>
                    <th onclick="sortTable(3)">Tier</th>
                    <th onclick="sortTable(4)">Score</th>
                    <th onclick="sortTable(5)">List Price</th>
                    <th onclick="sortTable(6)">Roof</th>
                    <th onclick="sortTable(7)">HVAC</th>
                    <th onclick="sortTable(8)">Pool</th>
                    <th onclick="sortTable(9)">Plumbing</th>
                    <th onclick="sortTable(10)">Kitchen</th>
                    <th onclick="sortTable(11)">Total Reno</th>
                    <th onclick="sortTable(12)">True Cost</th>
                    <th onclick="sortTable(13)">Delta %</th>
                </tr>
            </thead>
            <tbody>
                {{TABLE_ROWS}}
            </tbody>
        </table>
    </div>

    <script>
        function sortTable(columnIndex) {
            const table = document.getElementById("dataTable");
            const tbody = table.querySelector("tbody");
            const rows = Array.from(tbody.querySelectorAll("tr"));

            // Determine sort direction
            const currentDirection = table.dataset.sortDirection || 'asc';
            const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';
            table.dataset.sortDirection = newDirection;

            rows.sort((a, b) => {
                let aValue = a.cells[columnIndex].textContent.trim();
                let bValue = b.cells[columnIndex].textContent.trim();

                // Try to parse as number (remove $ and , for currency)
                const aNum = parseFloat(aValue.replace(/[$,]/g, ''));
                const bNum = parseFloat(bValue.replace(/[$,]/g, ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return newDirection === 'asc' ? aNum - bNum : bNum - aNum;
                } else {
                    return newDirection === 'asc'
                        ? aValue.localeCompare(bValue)
                        : bValue.localeCompare(aValue);
                }
            });

            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
        }
    </script>
</body>
</html>
"""

    # Calculate summary statistics
    total_properties = len(results)
    renovations = [r['total_renovation'] for r in results]
    avg_renovation = sum(renovations) / len(renovations) if renovations else 0
    min_renovation = min(renovations) if renovations else 0
    max_renovation = max(renovations) if renovations else 0
    high_cost_count = sum(1 for r in renovations if r > 20000)

    # Find best value (lowest true_cost among PASS properties)
    passing_properties = [r for r in results if r['kill_switch_passed'] == 'PASS']
    if passing_properties:
        best_value_property = min(passing_properties, key=lambda x: x['true_cost'])
        best_value = best_value_property['address']
    else:
        best_value = "N/A"

    # Generate table rows
    table_rows = []
    for result in results:
        delta_pct = result['price_delta_pct']

        # Determine row class based on delta percentage
        if delta_pct < 5:
            delta_class = 'delta-low'
        elif delta_pct <= 10:
            delta_class = 'delta-medium'
        else:
            delta_class = 'delta-high'

        # Add fail class if not passing kill switches
        status_class = 'pass' if result['kill_switch_passed'] == 'PASS' else 'fail'

        # Combine classes
        row_class = f"{delta_class} {status_class}"

        # Check if this is the best value
        if result['kill_switch_passed'] == 'PASS' and result['address'] == best_value:
            row_class += ' best-value'

        # Tier styling
        tier = result['tier']
        if tier == 'Unicorn':
            tier_class = 'tier-unicorn'
        elif tier == 'Contender':
            tier_class = 'tier-contender'
        else:
            tier_class = 'tier-pass'

        row = f"""
                <tr class="{row_class}">
                    <td>{result['rank']}</td>
                    <td>{result['address']}</td>
                    <td>{result['kill_switch_passed']}</td>
                    <td class="{tier_class}">{tier}</td>
                    <td>{result['total_score']:.1f}</td>
                    <td class="currency">{format_currency(result['list_price'])}</td>
                    <td class="currency">{format_currency(result['roof_cost'])}</td>
                    <td class="currency">{format_currency(result['hvac_cost'])}</td>
                    <td class="currency">{format_currency(result['pool_cost'])}</td>
                    <td class="currency">{format_currency(result['plumbing_cost'])}</td>
                    <td class="currency">{format_currency(result['kitchen_cost'])}</td>
                    <td class="currency">{format_currency(result['total_renovation'])}</td>
                    <td class="currency">{format_currency(result['true_cost'])}</td>
                    <td class="currency">{format_percentage(delta_pct)}</td>
                </tr>"""
        table_rows.append(row)

    # Replace placeholders
    from datetime import datetime
    html = html.replace('{{ANALYSIS_DATE}}', datetime.now().strftime('%Y-%m-%d'))
    html = html.replace('{{TOTAL_PROPERTIES}}', str(total_properties))
    html = html.replace('{{AVG_RENOVATION}}', format_currency(avg_renovation))
    html = html.replace('{{MIN_RENOVATION}}', format_currency(min_renovation))
    html = html.replace('{{MAX_RENOVATION}}', format_currency(max_renovation))
    html = html.replace('{{HIGH_COST_COUNT}}', str(high_cost_count))
    html = html.replace('{{BEST_VALUE}}', best_value)
    html = html.replace('{{TABLE_ROWS}}', '\n'.join(table_rows))

    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[OK] HTML report saved: {output_path}")


def print_summary_report(results: list[dict]):
    """Print summary statistics to console."""
    print("\n" + "="*80)
    print("RENOVATION GAP ANALYSIS SUMMARY")
    print("="*80)

    # Overall statistics
    total_properties = len(results)
    renovations = [r['total_renovation'] for r in results]
    avg_renovation = sum(renovations) / len(renovations) if renovations else 0

    print(f"\nTotal Properties Analyzed: {total_properties}")
    print(f"Average Renovation Estimate: {format_currency(avg_renovation)}")
    print(f"Range: {format_currency(min(renovations))} - {format_currency(max(renovations))}")

    # Properties with high renovation costs
    high_cost = [r for r in results if r['total_renovation'] > 20000]
    print(f"\nProperties with >$20k Renovation Estimate: {len(high_cost)}")

    # Top 3 by True Cost (lowest among PASS)
    passing_properties = [r for r in results if r['kill_switch_passed'] == 'PASS']
    if passing_properties:
        top_by_true_cost = sorted(passing_properties, key=lambda x: x['true_cost'])[:3]

        print("\n" + "-"*80)
        print("TOP 3 PROPERTIES BY TRUE COST (Lowest among PASS)")
        print("-"*80)

        for i, prop in enumerate(top_by_true_cost, 1):
            print(f"\n#{i}: {prop['address']}")
            print(f"    Rank: #{prop['rank']} | Tier: {prop['tier']} | Score: {prop['total_score']:.1f}")
            print(f"    List Price: {format_currency(prop['list_price'])}")
            print("    Renovation Costs:")
            print(f"      - Roof: {format_currency(prop['roof_cost'])}")
            print(f"      - HVAC: {format_currency(prop['hvac_cost'])}")
            print(f"      - Pool: {format_currency(prop['pool_cost'])}")
            print(f"      - Plumbing/Electrical: {format_currency(prop['plumbing_cost'])}")
            print(f"      - Kitchen: {format_currency(prop['kitchen_cost'])}")
            print(f"    Total Renovation: {format_currency(prop['total_renovation'])}")
            print(f"    TRUE COST: {format_currency(prop['true_cost'])} (+{format_percentage(prop['price_delta_pct'])})")

    # Properties with highest hidden costs
    highest_costs = sorted(results, key=lambda x: x['total_renovation'], reverse=True)[:5]

    print("\n" + "-"*80)
    print("TOP 5 PROPERTIES WITH HIGHEST HIDDEN COSTS")
    print("-"*80)

    for i, prop in enumerate(highest_costs, 1):
        status = "[PASS]" if prop['kill_switch_passed'] == 'PASS' else "[FAIL]"
        print(f"\n#{i}: {prop['address']} [{status}]")
        print(f"    Rank: #{prop['rank']} | Tier: {prop['tier']}")
        print(f"    List: {format_currency(prop['list_price'])} -> True: {format_currency(prop['true_cost'])} (+{format_percentage(prop['price_delta_pct'])})")
        print(f"    Total Renovation: {format_currency(prop['total_renovation'])}")

        # Show breakdown of major costs
        costs = []
        if prop['roof_cost'] > 0:
            costs.append(f"Roof {format_currency(prop['roof_cost'])}")
        if prop['hvac_cost'] > 0:
            costs.append(f"HVAC {format_currency(prop['hvac_cost'])}")
        if prop['pool_cost'] > 0:
            costs.append(f"Pool {format_currency(prop['pool_cost'])}")
        if prop['plumbing_cost'] > 0:
            costs.append(f"Plumbing {format_currency(prop['plumbing_cost'])}")
        if prop['kitchen_cost'] > 0:
            costs.append(f"Kitchen {format_currency(prop['kitchen_cost'])}")

        if costs:
            print(f"    Breakdown: {', '.join(costs)}")

    print("\n" + "="*80 + "\n")


def main():
    """Main analysis pipeline."""
    # Paths
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / 'data' / 'phx_homes_ranked.csv'
    json_path = base_dir / 'data' / 'enrichment_data.json'
    output_dir = base_dir / 'reports' / 'html'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_csv = output_dir / 'renovation_gap_report.csv'
    output_html = output_dir / 'renovation_gap_report.html'

    # Load data
    print("Loading property data...")
    properties = load_csv_data(csv_path)
    enrichment = load_enrichment_data(json_path)

    print(f"Loaded {len(properties)} properties")
    print(f"Loaded enrichment data for {len(enrichment)} properties")

    # Calculate renovation costs for each property
    print("\nCalculating renovation costs...")
    results = []

    for prop in properties:
        address = prop['full_address']
        enrich_data = enrichment.get(address, {})

        # Calculate costs
        roof_cost, hvac_cost, pool_cost, plumbing_cost, kitchen_cost = \
            calculate_renovation_costs(prop, enrich_data)

        total_renovation = roof_cost + hvac_cost + pool_cost + plumbing_cost + kitchen_cost

        # Parse list price - use price_num if available, otherwise parse price string
        try:
            list_price = float(prop.get('price_num', 0))
            if list_price == 0:
                list_price_str = prop.get('price', '0').replace('$', '').replace(',', '')
                list_price = float(list_price_str) if list_price_str else 0
        except (ValueError, TypeError):
            list_price = 0

        # Calculate true cost
        true_cost = list_price + total_renovation

        # Calculate delta percentage
        price_delta_pct = (total_renovation / list_price * 100) if list_price > 0 else 0

        # Build result record
        try:
            rank = int(prop['rank']) if prop.get('rank') and prop['rank'] != '' else 999
        except (ValueError, TypeError):
            rank = 999

        try:
            total_score = float(prop.get('total_score', 0)) if prop.get('total_score') and prop['total_score'] != '' else 0.0
        except (ValueError, TypeError):
            total_score = 0.0

        result = {
            'rank': rank,
            'address': address,
            'kill_switch_passed': prop.get('kill_switch_status', 'N/A'),
            'tier': prop.get('tier', 'N/A'),
            'total_score': total_score,
            'list_price': list_price,
            'roof_cost': roof_cost,
            'hvac_cost': hvac_cost,
            'pool_cost': pool_cost,
            'plumbing_cost': plumbing_cost,
            'kitchen_cost': kitchen_cost,
            'total_renovation': total_renovation,
            'true_cost': true_cost,
            'price_delta_pct': price_delta_pct
        }

        results.append(result)

    # Generate reports
    print("\nGenerating reports...")
    generate_csv_report(results, output_csv)
    generate_html_report(results, output_html)

    # Print summary
    print_summary_report(results)

    print("[OK] Analysis complete!")
    print("\nOutput files:")
    print(f"  - {output_csv}")
    print(f"  - {output_html}")


if __name__ == '__main__':
    main()
